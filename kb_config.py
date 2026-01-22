"""
Shared Configuration for AI Knowledge Base Scripts

Centralizes paths and settings used across all knowledge base scripts.
"""
from pathlib import Path

# Base paths
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
SOURCE_DIR = Path(r"C:\Users\scott\ebay-automation")

# Database paths
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"
URL_CACHE = KNOWLEDGE_BASE / "url_cache.json"
METADATA_CACHE = KNOWLEDGE_BASE / "youtube_metadata_cache.json"
TOKEN_USAGE = KNOWLEDGE_BASE / "token_usage.json"

# Directory paths
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / "tutorials" / "transcripts"
ANALYSIS_DIR = KNOWLEDGE_BASE / "tutorials" / "analysis"
SEARCH_INDEX = KNOWLEDGE_BASE / "tutorials" / "search_index.db"
EXTRACTED_DIR = KNOWLEDGE_BASE / "extracted"
EXPORTS_DIR = KNOWLEDGE_BASE / "exports"
STYLES_DIR = KNOWLEDGE_BASE / "styles" / "midjourney-sref"
COURSE_DIR = KNOWLEDGE_BASE / "course_materials"
BACKUPS_DIR = KNOWLEDGE_BASE / "backups"
SCRIPTS_DIR = KNOWLEDGE_BASE / "scripts"

# Outlook settings
OUTLOOK_ACCOUNT = "scott@unclesvf.com"
SCOTT_FOLDER = "scott"

# Folders to process for AI content extraction
AI_CONTENT_FOLDERS = [
    'AI Agents', 'AI Art-Images', 'AI Music-Audio',
    'General AI', 'Claude-Anthropic', 'ChatGPT-OpenAI', 'Google-Gemini'
]
RELATED_CONTENT_FOLDERS = [
    'GitHub Projects', 'Software-Apps', 'YouTube Videos',
    'Coding-Development', 'X-Twitter Posts'
]
DEFAULT_EXTRACT_FOLDERS = AI_CONTENT_FOLDERS + RELATED_CONTENT_FOLDERS

# Default settings
DEFAULT_BATCH_SIZE = 5
