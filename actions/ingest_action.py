from typing import Dict, Any, List
from actions.base_action import Action
from actions.knowledge_base import KnowledgeBase
import hashlib

class IngestAction(Action):
    """
    Action: Extract 'Wisdom' from emails and store in Vector DB.
    """
    
    def __init__(self, automator, params):
        super().__init__(automator, params)
        # Initialize DB connection once
        # In a larger system, this might be a shared singleton
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            default_db_path = os.path.join(base_dir, 'data', 'knowledge_base')
            
            db_path = self.automator.config.get('vector_db_path', default_db_path)
            self.kb = KnowledgeBase(db_path=db_path)
        except Exception as e:
            self.logger.error(f"Failed to load KnowledgeBase: {e}")
            self.kb = None

    def execute(self):
        if not self.kb:
            self.logger.error("Knowledge Base not initialized. Skipping ingestion.")
            return

        required_keywords = self.params.get('required_keywords', [])
        min_length = self.params.get('min_body_length', 100)
        project_tags = self.params.get('project_tags', {})
        limit = self.params.get('limit', 50)

        items = self.automator.folder.Items
        items.Sort("[ReceivedTime]", True)
        
        docs_to_add = []
        metadatas = []
        ids = []
        
        count = 0
        processed = 0
        
        for item in items:
            if processed >= limit:
                break
            
            if item.Class != 43:
                continue
            
            processed += 1
            
            subject = getattr(item, 'Subject', '') or ''
            try:
                body = getattr(item, 'Body', '') or ''
            except:
                body = ''
            
            if len(body) < min_length:
                continue
                
            text = f"{subject}\n\n{body}"
            text_lower = text.lower()
            
            # Filter: Must contain at least one "Wisdom Keyword" 
            # OR be from specific senders? For now, keyword based.
            has_keyword = False
            if not required_keywords:
                has_keyword = True # If no keywords valid, ingest all
            else:
                for kw in required_keywords:
                    if kw.lower() in text_lower:
                        has_keyword = True
                        break
            
            if not has_keyword:
                continue

            # Tagging Logic
            tags = []
            for tag_name, tag_keywords in project_tags.items():
                for kw in tag_keywords:
                    if kw.lower() in text_lower:
                        tags.append(tag_name)
                        break
            
            # Create unique ID based on email content prevents duplicates
            doc_id = hashlib.md5(f"{item.EntryID}".encode()).hexdigest()
            
            docs_to_add.append(text)
            metadatas.append({
                "subject": subject,
                "sender": getattr(item, 'SenderName', 'Unknown'),
                "date": str(getattr(item, 'ReceivedTime', '')),
                "folder": self.automator.folder_name,
                "project_tags": ", ".join(tags),
                "source_type": "email"
            })
            ids.append(doc_id)
            count += 1
            
            if self.automator.dry_run:
                self.logger.info(f"[DRY RUN] Would ingest: {subject[:50]} (Tags: {tags})")

        if not self.automator.dry_run and docs_to_add:
            self.kb.add_documents(docs_to_add, metadatas, ids)
            self.logger.info(f"Ingested {len(docs_to_add)} new entries.")
        elif self.automator.dry_run:
             self.logger.info(f"[DRY RUN] Would have ingested {len(docs_to_add)} entries.")
