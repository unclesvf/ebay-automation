"""
Transcript Analyzer - Extract structured information from YouTube transcripts
Extracts tools, commands, techniques, tips, URLs, and key topics.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import re
from datetime import datetime
from pathlib import Path
from collections import Counter, defaultdict

# Import centralized config
from kb_config import (
    get_logger, backup_database, ProgressTracker,
    MASTER_DB, TRANSCRIPTS_DIR, ANALYSIS_DIR, EXTRACTED_DIR
)

# Setup logger
logger = get_logger("TranscriptAnalyzer")

# Paths - use centralized config
MASTER_DB_PATH = str(MASTER_DB)
TRANSCRIPTS_PATH = str(TRANSCRIPTS_DIR)
ANALYSIS_PATH = str(ANALYSIS_DIR)
EXTRACTED_PATH = str(EXTRACTED_DIR)

# =============================================================================
# DETECTION PATTERNS
# =============================================================================

# AI/Coding Tools to detect
TOOLS = {
    # AI Coding Assistants
    'claude code': ['claude code', 'claudecode'],
    'cursor': ['cursor'],
    'github copilot': ['copilot', 'github copilot'],
    'codeium': ['codeium'],
    'tabnine': ['tabnine'],
    'replit': ['replit'],
    'windsurf': ['windsurf'],
    'aider': ['aider'],
    'cline': ['cline'],
    'continue': ['continue dev', 'continue.dev'],
    'bolt': ['bolt.new', 'bolt new'],
    'lovable': ['lovable'],
    'v0': ['v0.dev', 'v zero'],

    # AI Models/Services
    'claude': ['claude', 'anthropic'],
    'chatgpt': ['chatgpt', 'chat gpt', 'gpt-4', 'gpt 4', 'openai'],
    'gemini': ['gemini', 'google ai'],
    'grok': ['grok'],
    'llama': ['llama', 'meta ai'],
    'mistral': ['mistral'],
    'perplexity': ['perplexity'],

    # Development Tools
    'vs code': ['vs code', 'vscode', 'visual studio code'],
    'neovim': ['neovim', 'nvim'],
    'vim': ['vim'],
    'terminal': ['terminal', 'command line', 'cli'],
    'git': ['git', 'github', 'gitlab'],
    'docker': ['docker', 'container'],
    'node': ['node', 'nodejs', 'npm'],
    'python': ['python', 'pip'],

    # AI Image/Video
    'midjourney': ['midjourney', 'mid journey'],
    'stable diffusion': ['stable diffusion', 'sdxl', 'sd3'],
    'dall-e': ['dall-e', 'dalle'],
    'flux': ['flux'],
    'comfyui': ['comfyui', 'comfy ui'],

    # Productivity
    'notion': ['notion'],
    'obsidian': ['obsidian'],
    'notebooklm': ['notebooklm', 'notebook lm'],
}

# Command patterns to detect
COMMAND_PATTERNS = [
    # Claude Code commands
    (r'/init\b', '/init'),
    (r'/plan\b', '/plan'),
    (r'/compact\b', '/compact'),
    (r'/clear\b', '/clear'),
    (r'/help\b', '/help'),
    (r'/config\b', '/config'),
    (r'/cost\b', '/cost'),
    (r'/doctor\b', '/doctor'),
    (r'/memory\b', '/memory'),
    (r'/review\b', '/review'),
    (r'/pr\b', '/pr'),
    (r'/commit\b', '/commit'),

    # CLI commands
    (r'\bclaude\s+[a-z]+', 'claude <command>'),
    (r'\bnpm\s+(?:install|i|run|start|build|test)\b', 'npm'),
    (r'\bnpx\s+\w+', 'npx'),
    (r'\bpip\s+install\b', 'pip install'),
    (r'\bgit\s+(?:clone|pull|push|commit|add|status|checkout|branch)\b', 'git'),
    (r'\bcd\s+\S+', 'cd'),
    (r'\bmkdir\s+\S+', 'mkdir'),
    (r'\bcurl\s+', 'curl'),
    (r'\bcode\s+\.', 'code .'),
]

# Technique/concept patterns
TECHNIQUES = {
    'claude.md': ['claude.md', 'claude md', 'claude dot md'],
    'plan mode': ['plan mode', 'planning mode'],
    'system prompt': ['system prompt', 'system message'],
    'mcp server': ['mcp server', 'mcp servers', 'model context protocol'],
    'context window': ['context window', 'context length'],
    'prompt engineering': ['prompt engineering', 'prompting'],
    'few-shot': ['few shot', 'few-shot'],
    'chain of thought': ['chain of thought', 'cot'],
    'rag': ['rag', 'retrieval augmented'],
    'fine-tuning': ['fine tuning', 'fine-tuning', 'finetuning'],
    'embeddings': ['embeddings', 'vector embeddings'],
    'api key': ['api key', 'api keys'],
    'environment variables': ['environment variable', 'env var', '.env'],
    'vibe coding': ['vibe coding', 'vibe code'],
    'agentic': ['agentic', 'ai agent', 'autonomous agent'],
}

# Tip indicator phrases
TIP_INDICATORS = [
    r'\b(?:pro tip|tip|trick|hack|advice)\b[:\s]',
    r'\balways\s+(?:make sure|remember|use|start|create|add)\b',
    r'\bnever\s+(?:use|do|start|forget)\b',
    r'\bthe (?:key|secret|trick) (?:is|to)\b',
    r'\bi (?:always|never|recommend|suggest)\b',
    r'\bmake sure (?:to|you)\b',
    r'\bdon\'t forget to\b',
    r'\bthe best (?:way|approach|practice)\b',
    r'\bhere\'s (?:a tip|the trick|what i do)\b',
    r'\bimportant(?:ly)?[:\s]\b',
    r'\bone thing (?:i|you) should\b',
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_db():
    """Load the master database."""
    if os.path.exists(MASTER_DB_PATH):
        with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_db(db):
    """Save the master database."""
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(MASTER_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def ensure_dirs():
    """Ensure output directories exist."""
    Path(ANALYSIS_PATH).mkdir(parents=True, exist_ok=True)
    Path(EXTRACTED_PATH).mkdir(parents=True, exist_ok=True)

def load_transcript(video_id):
    """Load transcript text from file."""
    # Find transcript file
    for filename in os.listdir(TRANSCRIPTS_PATH):
        if filename.startswith(video_id):
            filepath = os.path.join(TRANSCRIPTS_PATH, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract just the transcript portion (after TRANSCRIPT header)
            if 'TRANSCRIPT\n' in content:
                parts = content.split('TRANSCRIPT\n', 1)
                if len(parts) > 1:
                    transcript_part = parts[1]
                    # Stop at TIMESTAMPED SEGMENTS if present
                    if 'TIMESTAMPED SEGMENTS' in transcript_part:
                        transcript_part = transcript_part.split('TIMESTAMPED SEGMENTS')[0]
                    return transcript_part.strip(), filepath

            return content, filepath

    return None, None

def load_timestamped_transcript(video_id):
    """Load transcript with timestamps."""
    for filename in os.listdir(TRANSCRIPTS_PATH):
        if filename.startswith(video_id):
            filepath = os.path.join(TRANSCRIPTS_PATH, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract timestamped portion
            if 'TIMESTAMPED SEGMENTS' in content:
                parts = content.split('TIMESTAMPED SEGMENTS\n', 1)
                if len(parts) > 1:
                    timestamped = parts[1].strip()
                    # Parse into segments
                    segments = []
                    for line in timestamped.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        # Format: [MM:SS] or [HH:MM:SS] text
                        match = re.match(r'\[(\d+:\d+(?::\d+)?)\]\s*(.*)', line)
                        if match:
                            segments.append({
                                'timestamp': match.group(1),
                                'text': match.group(2)
                            })
                    return segments

    return []

# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_tools(text):
    """Extract mentioned tools from transcript."""
    text_lower = text.lower()
    found_tools = {}

    for tool_name, patterns in TOOLS.items():
        count = 0
        for pattern in patterns:
            count += len(re.findall(r'\b' + re.escape(pattern) + r'\b', text_lower))
        if count > 0:
            found_tools[tool_name] = count

    # Sort by frequency
    return dict(sorted(found_tools.items(), key=lambda x: x[1], reverse=True))

def extract_commands(text):
    """Extract CLI commands from transcript."""
    found_commands = []
    text_lower = text.lower()

    for pattern, cmd_name in COMMAND_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            for match in matches:
                if match not in [c['command'] for c in found_commands]:
                    found_commands.append({
                        'command': match if isinstance(match, str) else cmd_name,
                        'type': cmd_name
                    })

    return found_commands

def extract_techniques(text):
    """Extract techniques/concepts mentioned."""
    text_lower = text.lower()
    found_techniques = {}

    for technique, patterns in TECHNIQUES.items():
        count = 0
        for pattern in patterns:
            count += len(re.findall(re.escape(pattern), text_lower))
        if count > 0:
            found_techniques[technique] = count

    return dict(sorted(found_techniques.items(), key=lambda x: x[1], reverse=True))

def extract_urls(text):
    """Extract URLs mentioned in transcript."""
    # URL pattern
    url_pattern = r'https?://[^\s<>"\']+|(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:/[^\s<>"\']*)?'
    urls = re.findall(url_pattern, text)

    # Clean and dedupe
    clean_urls = []
    seen = set()
    for url in urls:
        url = url.rstrip('.,;:!?)')
        if url not in seen and len(url) > 5:
            seen.add(url)
            clean_urls.append(url)

    return clean_urls

def extract_tips(segments):
    """Extract tips/advice with timestamps."""
    tips = []

    for seg in segments:
        text = seg['text']
        text_lower = text.lower()

        for pattern in TIP_INDICATORS:
            if re.search(pattern, text_lower):
                tips.append({
                    'timestamp': seg['timestamp'],
                    'text': text,
                    'indicator': pattern
                })
                break

    return tips

def extract_key_moments(segments, tools, techniques):
    """Identify key moments based on tool/technique mentions."""
    key_moments = []
    tool_names = set(tools.keys())
    technique_names = set(techniques.keys())

    for seg in segments:
        text_lower = seg['text'].lower()
        matches = []

        # Check for tool mentions
        for tool in tool_names:
            for pattern in TOOLS.get(tool, []):
                if pattern in text_lower:
                    matches.append(('tool', tool))
                    break

        # Check for technique mentions
        for tech in technique_names:
            for pattern in TECHNIQUES.get(tech, []):
                if pattern in text_lower:
                    matches.append(('technique', tech))
                    break

        if matches:
            key_moments.append({
                'timestamp': seg['timestamp'],
                'text': seg['text'],
                'mentions': matches
            })

    return key_moments

def identify_topics(tools, techniques, text):
    """Identify main topics of the video."""
    topics = []

    # Based on tool frequency
    if 'claude code' in tools:
        topics.append('claude-code')
    if 'cursor' in tools:
        topics.append('cursor')
    if any(t in tools for t in ['midjourney', 'stable diffusion', 'dall-e', 'flux']):
        topics.append('ai-image-generation')
    if 'chatgpt' in tools or 'claude' in tools:
        topics.append('ai-chat')

    # Based on techniques
    if 'claude.md' in techniques:
        topics.append('project-setup')
    if 'plan mode' in techniques:
        topics.append('planning')
    if 'mcp server' in techniques:
        topics.append('mcp-servers')
    if 'prompt engineering' in techniques:
        topics.append('prompting')
    if 'vibe coding' in techniques:
        topics.append('vibe-coding')

    # Based on keywords in text
    text_lower = text.lower()
    if 'beginner' in text_lower or 'getting started' in text_lower:
        topics.append('beginner')
    if 'advanced' in text_lower or 'deep dive' in text_lower:
        topics.append('advanced')
    if 'tutorial' in text_lower or 'how to' in text_lower:
        topics.append('tutorial')
    if 'project' in text_lower and 'setup' in text_lower:
        topics.append('project-setup')

    return list(set(topics))

# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def analyze_transcript(video_id, title=None):
    """Perform full analysis on a transcript."""
    print(f"\nAnalyzing: {video_id}")
    print("-" * 50)

    # Load transcript
    text, filepath = load_transcript(video_id)
    if not text:
        print(f"  ERROR: Transcript not found for {video_id}")
        return None

    segments = load_timestamped_transcript(video_id)
    print(f"  Loaded transcript: {len(text)} chars, {len(segments)} segments")

    # Extract all components
    print("  Extracting tools...")
    tools = extract_tools(text)

    print("  Extracting commands...")
    commands = extract_commands(text)

    print("  Extracting techniques...")
    techniques = extract_techniques(text)

    print("  Extracting URLs...")
    urls = extract_urls(text)

    print("  Extracting tips...")
    tips = extract_tips(segments) if segments else []

    print("  Identifying key moments...")
    key_moments = extract_key_moments(segments, tools, techniques) if segments else []

    print("  Identifying topics...")
    topics = identify_topics(tools, techniques, text)

    # Build analysis result
    analysis = {
        'video_id': video_id,
        'title': title,
        'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'transcript_length': len(text),
        'segment_count': len(segments),
        'tools_mentioned': tools,
        'commands': commands,
        'techniques': techniques,
        'urls_mentioned': urls,
        'tips': tips[:20],  # Limit to top 20
        'key_moments': key_moments[:30],  # Limit to top 30
        'topics': topics,
        'summary': {
            'total_tools': len(tools),
            'total_commands': len(commands),
            'total_techniques': len(techniques),
            'total_tips': len(tips),
            'total_urls': len(urls)
        }
    }

    # Print summary
    print(f"\n  SUMMARY:")
    print(f"    Tools: {len(tools)} - {', '.join(list(tools.keys())[:5])}")
    print(f"    Commands: {len(commands)}")
    print(f"    Techniques: {len(techniques)} - {', '.join(list(techniques.keys())[:5])}")
    print(f"    Tips: {len(tips)}")
    print(f"    URLs: {len(urls)}")
    print(f"    Topics: {', '.join(topics)}")

    return analysis

def save_analysis(analysis):
    """Save analysis to JSON file."""
    ensure_dirs()

    video_id = analysis['video_id']
    filepath = os.path.join(ANALYSIS_PATH, f"{video_id}_analysis.json")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {filepath}")
    return filepath

def update_db_with_analysis(db, video_id, analysis):
    """Update the database with analysis results."""
    for tutorial in db['tutorials']:
        if tutorial.get('video_id') == video_id:
            tutorial['analyzed'] = True
            tutorial['analysis_date'] = analysis['analyzed_at']
            tutorial['topics'] = analysis['topics']
            tutorial['tools_mentioned'] = list(analysis['tools_mentioned'].keys())
            tutorial['techniques_mentioned'] = list(analysis['techniques'].keys())
            tutorial['tip_count'] = len(analysis['tips'])
            return True
    return False

# =============================================================================
# AGGREGATE FUNCTIONS
# =============================================================================

def aggregate_all_analyses():
    """Aggregate all individual analyses into combined files."""
    ensure_dirs()

    all_tips = []
    all_tools = Counter()
    all_techniques = Counter()
    all_topics = Counter()

    # Load all analysis files
    if not os.path.exists(ANALYSIS_PATH):
        print("No analyses found.")
        return

    for filename in os.listdir(ANALYSIS_PATH):
        if filename.endswith('_analysis.json'):
            filepath = os.path.join(ANALYSIS_PATH, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                analysis = json.load(f)

            video_id = analysis['video_id']
            title = analysis.get('title', video_id)

            # Aggregate tips
            for tip in analysis.get('tips', []):
                all_tips.append({
                    'video_id': video_id,
                    'video_title': title,
                    'timestamp': tip['timestamp'],
                    'text': tip['text']
                })

            # Aggregate tools
            for tool, count in analysis.get('tools_mentioned', {}).items():
                all_tools[tool] += count

            # Aggregate techniques
            for tech, count in analysis.get('techniques', {}).items():
                all_techniques[tech] += count

            # Aggregate topics
            for topic in analysis.get('topics', []):
                all_topics[topic] += 1

    # Save aggregated tips
    tips_file = os.path.join(EXTRACTED_PATH, 'tips.json')
    with open(tips_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_tips': len(all_tips),
            'tips': all_tips
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_tips)} tips to {tips_file}")

    # Save tool frequency
    tools_file = os.path.join(EXTRACTED_PATH, 'tool_mentions.json')
    with open(tools_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tools': dict(all_tools.most_common())
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved tool mentions to {tools_file}")

    # Save technique frequency
    techniques_file = os.path.join(EXTRACTED_PATH, 'technique_mentions.json')
    with open(techniques_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'techniques': dict(all_techniques.most_common())
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved technique mentions to {techniques_file}")

    # Save topic frequency
    topics_file = os.path.join(EXTRACTED_PATH, 'topics.json')
    with open(topics_file, 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'topics': dict(all_topics.most_common())
        }, f, indent=2, ensure_ascii=False)
    print(f"Saved topics to {topics_file}")

# =============================================================================
# MAIN
# =============================================================================

def process_all_transcripts(force=False):
    """
    Analyze all transcripts in the database.

    Args:
        force: If True, reanalyze all transcripts. If False (default),
               only analyze new/unanalyzed transcripts (incremental mode).
    """
    logger.info("=" * 70)
    logger.info("TRANSCRIPT ANALYZER")
    logger.info("=" * 70)

    # Backup database before processing
    backup_path = backup_database(reason="transcript_analysis")
    if backup_path:
        logger.info(f"Database backed up to: {backup_path}")

    db = load_db()
    if not db:
        logger.error("Could not load database")
        return

    tutorials = db.get('tutorials', [])

    # Filter to only tutorials that need analysis
    to_analyze = []
    for tutorial in tutorials:
        video_id = tutorial.get('video_id')
        if not video_id:
            continue

        # Check if has transcript
        if not tutorial.get('has_transcript'):
            continue

        # Check if already analyzed (unless force mode)
        if not force and tutorial.get('analyzed'):
            continue

        to_analyze.append(tutorial)

    if not to_analyze:
        if force:
            logger.info("No tutorials with transcripts found.")
        else:
            logger.info("All tutorials already analyzed. Use --force to reanalyze.")
        return

    logger.info(f"Found {len(to_analyze)} tutorials to analyze" +
                (" (incremental)" if not force else " (full reanalysis)"))

    # Initialize progress tracker
    tracker = ProgressTracker(total=len(to_analyze), description="Transcript analysis")

    analyzed = 0
    errors = 0

    for tutorial in to_analyze:
        video_id = tutorial.get('video_id')
        title = tutorial.get('title', video_id)

        try:
            analysis = analyze_transcript(video_id, title)
            if analysis:
                save_analysis(analysis)
                update_db_with_analysis(db, video_id, analysis)
                analyzed += 1
                tracker.update(message=title[:30] if title else video_id)
        except Exception as e:
            logger.error(f"Error analyzing {video_id}: {e}")
            errors += 1
            tracker.update()

    # Save updated database
    save_db(db)
    tracker.finish()

    # Aggregate all analyses
    logger.info("=" * 70)
    logger.info("AGGREGATING ANALYSES")
    logger.info("=" * 70)
    aggregate_all_analyses()

    logger.info("=" * 70)
    logger.info("SUMMARY")
    print("=" * 70)
    print(f"  Analyzed: {analyzed}")
    print(f"  Errors: {errors}")
    print(f"\nAnalysis files: {ANALYSIS_PATH}")
    print(f"Extracted data: {EXTRACTED_PATH}")

def show_analysis(video_id):
    """Show analysis for a specific video."""
    filepath = os.path.join(ANALYSIS_PATH, f"{video_id}_analysis.json")

    if not os.path.exists(filepath):
        print(f"No analysis found for {video_id}")
        print("Run: python transcript_analyzer.py all")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    print("\n" + "=" * 70)
    print(f"ANALYSIS: {analysis.get('title', video_id)}")
    print("=" * 70)

    print(f"\nVideo ID: {video_id}")
    print(f"Analyzed: {analysis.get('analyzed_at')}")
    print(f"Topics: {', '.join(analysis.get('topics', []))}")

    print("\n" + "-" * 40)
    print("TOOLS MENTIONED")
    print("-" * 40)
    for tool, count in analysis.get('tools_mentioned', {}).items():
        print(f"  {tool}: {count}")

    print("\n" + "-" * 40)
    print("TECHNIQUES")
    print("-" * 40)
    for tech, count in analysis.get('techniques', {}).items():
        print(f"  {tech}: {count}")

    print("\n" + "-" * 40)
    print(f"TIPS ({len(analysis.get('tips', []))})")
    print("-" * 40)
    for tip in analysis.get('tips', [])[:10]:
        print(f"  [{tip['timestamp']}] {tip['text'][:80]}...")

    print("\n" + "-" * 40)
    print("COMMANDS")
    print("-" * 40)
    for cmd in analysis.get('commands', []):
        print(f"  {cmd['command']}")

def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Transcript Analyzer - Extract information from YouTube transcripts")
        print("=" * 60)
        print("\nUsage:")
        print("  python transcript_analyzer.py <command> [args]")
        print("\nCommands:")
        print("  all                  Analyze new/unanalyzed transcripts (incremental)")
        print("  all --force          Reanalyze ALL transcripts")
        print("  video <video_id>     Analyze specific video")
        print("  show <video_id>      Show existing analysis")
        print("  aggregate            Aggregate all analyses")
        return

    cmd = sys.argv[1].lower()

    if cmd == 'all':
        force = '--force' in sys.argv
        process_all_transcripts(force=force)

    elif cmd == 'video' and len(sys.argv) > 2:
        video_id = sys.argv[2]
        db = load_db()
        title = None
        if db:
            for t in db.get('tutorials', []):
                if t.get('video_id') == video_id:
                    title = t.get('title')
                    break

        analysis = analyze_transcript(video_id, title)
        if analysis:
            save_analysis(analysis)
            if db:
                update_db_with_analysis(db, video_id, analysis)
                save_db(db)

    elif cmd == 'show' and len(sys.argv) > 2:
        show_analysis(sys.argv[2])

    elif cmd == 'aggregate':
        aggregate_all_analyses()

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")

if __name__ == "__main__":
    main()
