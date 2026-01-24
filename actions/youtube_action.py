from typing import Dict, Any, List
import re
import requests
import json
from actions.base_action import Action
from actions.knowledge_base import KnowledgeBase
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

class YouTubeAction(Action):
    """
    Action: Detect YouTube links, fetch transcripts, summarize via Local LLM (Ollama),
    and ingest into Knowledge Base.
    """

    def __init__(self, automator, params):
        super().__init__(automator, params)
        # Initialize Knowledge Base
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            default_db_path = os.path.join(base_dir, 'data', 'knowledge_base')
            
            db_path = self.automator.config.get('vector_db_path', default_db_path)
            self.kb = KnowledgeBase(db_path=db_path)
        except Exception as e:
            self.logger.error(f"Failed to load KnowledgeBase: {e}")
            self.kb = None
            
        self.ollama_url = self.params.get('ollama_url', 'http://localhost:11434/api/generate')
        self.model = self.params.get('model', 'llama2')

    def execute(self):
        if not YouTubeTranscriptApi:
            self.logger.error("youtube_transcript_api not installed. Skipping YouTube action.")
            return

        limit = self.params.get('limit', 10)
        items = self.automator.folder.Items
        items.Sort("[ReceivedTime]", True)
        
        processed_count = 0
        
        for item in items:
            if processed_count >= limit:
                break
            
            if item.Class != 43: continue
            
            subject = getattr(item, 'Subject', '') or ''
            try:
                body = getattr(item, 'Body', '') or ''
            except:
                body = ''
            
            # Find YouTube Links
            video_ids = self._extract_video_ids(body)
            if not video_ids:
                continue

            processed_count += 1
            
            for vid in video_ids:
                self.logger.info(f"Found YouTube Video: {vid} in '{subject[:30]}...'")
                
                # 1. Fetch Transcript
                transcript_text = self._get_transcript(vid)
                if not transcript_text:
                    self.logger.warning(f"  No transcript found for {vid}. Flagging item.")
                    if not self.automator.dry_run:
                        try:
                            # Append 'YouTube-Failed' to categories
                            current_cats = getattr(item, 'Categories', '') or ''
                            if 'YouTube-Failed' not in current_cats:
                                new_cats = f"{current_cats}, YouTube-Failed" if current_cats else "YouTube-Failed"
                                item.Categories = new_cats
                                item.Save()
                                self.logger.info("  Item flagged as 'YouTube-Failed'")
                        except Exception as e:
                            self.logger.error(f"  Failed to flag item: {e}")
                    continue
                    
                # 2. Summarize via Local LLM
                if self.automator.dry_run:
                    self.logger.info(f"  [DRY RUN] Would send {len(transcript_text)} chars to Ollama ({self.model})")
                    summary = f"Simulated summary for video {vid}"
                else:
                    self.logger.info(f"  Sending to Ollama ({self.model})...")
                    summary = self._summarize_with_ollama(transcript_text)
                    if not summary:
                        self.logger.error("  Ollama summarization failed.")
                        continue
                
                # 3. Ingest to KB
                doc_text = f"VIDEO SUMMARY: https://youtu.be/{vid}\nSOURCE EMAIL: {subject}\n\n{summary}"
                metadata = {
                    "subject": f"Video: {vid}",
                    "sender": getattr(item, 'SenderName', 'Unknown'),
                    "date": str(getattr(item, 'ReceivedTime', '')),
                    "folder": self.automator.folder_name,
                    "project_tags": "YouTube, Social-Feed, AI-Learning",
                    "source_type": "youtube_video"
                }
                
                if self.automator.dry_run:
                    self.logger.info(f"  [DRY RUN] Would ingest summary for {vid}")
                else:
                    self.kb.add_documents([doc_text], [metadata], [f"yt_{vid}"])
                    self.logger.info(f"  Ingested summary for {vid}")

    def _extract_video_ids(self, text: str) -> List[str]:
        """Extract YouTube IDs from text."""
        patterns = [
            r'youtube\.com/watch\?v=([\w\-]+)',
            r'youtu\.be/([\w\-]+)'
        ]
        ids = set()
        for p in patterns:
            matches = re.findall(p, text)
            ids.update(matches)
        return list(ids)

    def _get_transcript(self, video_id: str) -> str:
        try:
            # Match pattern from legacy youtube_metadata.py
            # The environment seems to use an instance-based API
            api = YouTubeTranscriptApi()
            transcript_list = api.fetch(video_id)
            
            # Helper to extract text from whatever object calls back
            full_text = []
            for entry in transcript_list:
                # Handle both dict and object formats
                if hasattr(entry, 'text'):
                    text = entry.text
                else:
                    text = entry.get('text', '')
                
                if text:
                    full_text.append(text)
            
            return " ".join(full_text)
            
        except Exception as e:
            self.logger.warning(f"  Transcript API Error for {video_id}: {e}")
            return None

    def _summarize_with_ollama(self, transcript: str) -> str:
        """
        Call local Ollama instance to summarize using a Map-Reduce strategy
        to handle long transcripts within context limits.
        """
        # 1. Configuration matches specific model (qwen2.5:32b)
        CHUNK_SIZE = 6000  # Approx 1.5k-2k tokens (safe for 8k-32k context)
        OVERLAP = 500
        
        # 2. Split Transcript
        chunks = []
        start = 0
        while start < len(transcript):
            end = start + CHUNK_SIZE
            chunk_text = transcript[start:end]
            chunks.append(chunk_text)
            start += (CHUNK_SIZE - OVERLAP)
        
        self.logger.info(f"  Transcript length: {len(transcript)} chars. Split into {len(chunks)} chunks.")

        # 3. Map Phase: Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            self.logger.info(f"  Summarizing chunk {i+1}/{len(chunks)}...")
            prompt = (
                f"Analyze this segment of a YouTube transcript (Part {i+1}/{len(chunks)}).\n"
                f"Specific Focus: Extract any named TOOLS, CLI COMMANDS, or specific TIPS mentioned.\n\n"
                f"TEXT SEGMENT:\n{chunk}\n\n"
                f"BRIEF EXTRACTION:"
            )
            
            summary = self._call_ollama(prompt)
            if summary:
                chunk_summaries.append(summary)

        if not chunk_summaries:
            return None

        # 4. Reduce Phase: Combine into final report
        # If chunks are small, we might fit all summaries in one go. 
        # If still too big, we just concatenate them (Map-Reduce-Reduce could be needed for massive videos).
        combined_text = "\n\n".join(chunk_summaries)
        
        final_prompt = (
            f"Below are extracted notes from multiple segments of a video tutorial.\n"
            f"Consolidate them into a single clean Knowledge Base entry.\n\n"
            f"Format:\n"
            f"- **Summary**: High-level overview\n"
            f"- **Tools Mentioned**: List of software/libraries\n"
            f"- **Key Tips/Commands**: Bullet points of technical details\n\n"
            f"SOURCE NOTES:\n{combined_text}\n\n"
            f"FINAL REPORT:"
        )
        
        self.logger.info(f"  Generating Final Report from {len(combined_text)} chars of notes...")
        final_report = self._call_ollama(final_prompt)
        return final_report

    def _call_ollama(self, prompt: str) -> str:
        """Helper to send prompt to Ollama."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 8192 # Request larger context window if possible
            }
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=300) # Higher timeout for large model
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                self.logger.error(f"Ollama Error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Ollama Connection Error: {e}")
            return None
