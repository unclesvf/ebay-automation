"""
AI Content Extractor - Enhanced extraction for AI Knowledge Management System
Extracts GitHub repos, HuggingFace models, YouTube tutorials, Midjourney style codes,
and AI model references from Scott folder emails.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


from outlook_reader import OutlookReader
from datetime import datetime
from kb_config import DEFAULT_EXTRACT_FOLDERS, AI_CONTENT_FOLDERS, RELATED_CONTENT_FOLDERS
import re
import json
import os
import urllib.request
import time
import logging

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AIContentExtractor")

# Cache for expanded URLs to avoid re-fetching
_url_cache = {}
_cache_file = r'D:\AI-Knowledge-Base\url_cache.json'

# Paths
MASTER_DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'
# Use config for path if available, or fallback
try:
    from kb_config import SOURCE_DIR
    TWITTER_JSON_PATH = os.path.join(SOURCE_DIR, 'twitter_data_extract.json')
except ImportError:
    TWITTER_JSON_PATH = r'C:\Users\scott\ebay-automation\twitter_data_extract.json'


# =============================================================================
# EXTRACTION PATTERNS
# =============================================================================

PATTERNS = {
    # Repository URLs - capture full path including potential additional segments
    # Match full URLs first, then the captured groups
    'github_full': re.compile(r'https?://github\.com/([\w\-\.]+)/([\w\-\.]+)(?:/[\w\-\./]*)?', re.IGNORECASE),
    'github': re.compile(r'github\.com/([\w\-\.]+)/([\w\-\.]+)', re.IGNORECASE),
    'huggingface_full': re.compile(r'https?://huggingface\.co/([\w\-\.]+)/([\w\-\.]+)', re.IGNORECASE),
    'huggingface': re.compile(r'huggingface\.co/([\w\-\.]+)/([\w\-\.]+)', re.IGNORECASE),

    # YouTube URLs
    'youtube_full': re.compile(r'youtube\.com/watch\?v=([\w\-]+)', re.IGNORECASE),
    'youtube_short': re.compile(r'youtu\.be/([\w\-]+)', re.IGNORECASE),

    # Midjourney style codes
    'sref': re.compile(r'--sref\s+(\d+)', re.IGNORECASE),
    'style': re.compile(r'--style\s+(\w+)', re.IGNORECASE),
    'niji': re.compile(r'--niji\s*(\d*)', re.IGNORECASE),
    'personalize': re.compile(r'--(?:p|personalize)\s+([a-z0-9]+)', re.IGNORECASE),

    # Full URL extraction (for finding all URLs in text)
    'any_url': re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE),

    # t.co short links (Twitter/X shortened URLs)
    'tco': re.compile(r'https?://t\.co/[\w]+', re.IGNORECASE),
}

# =============================================================================
# METRIC PATTERNS
# =============================================================================

METRIC_PATTERNS = {
    'views': re.compile(r'([\d\.,]+[KMB]?\+?)\s+Views?', re.IGNORECASE),
    'likes': re.compile(r'([\d\.,]+[KMB]?\+?)\s+Likes?', re.IGNORECASE),
    'reposts': re.compile(r'([\d\.,]+[KMB]?\+?)\s+Reposts?', re.IGNORECASE),
    'retweets': re.compile(r'([\d\.,]+[KMB]?\+?)\s+Retweets?', re.IGNORECASE),
    'saves': re.compile(r'([\d\.,]+[KMB]?\+?)\s+Bookmarl?s?|([\d\.,]+[KMB]?\+?)\s+Saves?', re.IGNORECASE),
    'impressions': re.compile(r'([\d\.,]+[KMB]?\+?)\s+Impressions?', re.IGNORECASE),
}


# =============================================================================
# MODEL DETECTION KEYWORDS
# =============================================================================

TTS_MODELS = [
    'soprano', 'kokoro', 'bark', 'tortoise', 'xtts', 'coqui',
    'elevenlabs', 'playht', 'fish speech', 'fishspeech',
    'parler', 'metavoice', 'openvoice', 'piper', 'silero'
]

IMAGE_CLOUD_MODELS = [
    'midjourney', 'niji', 'dall-e', 'dalle', 'grok imagine',
    'ideogram', 'leonardo', 'bing image', 'adobe firefly',
    'clipdrop', 'nightcafe', 'playground'
]

IMAGE_LOCAL_MODELS = [
    'flux', 'sd3', 'sdxl', 'stable diffusion', 'comfyui', 'comfy ui',
    'forge', 'a1111', 'automatic1111', 'fooocus', 'invoke',
    'kohya', 'lora', 'controlnet', 'ip-adapter', 'ltx'
]

CODING_TOOLS = [
    'claude code', 'codex', 'gemini cli', 'aider', 'cursor',
    'windsurf', 'continue', 'cline', 'copilot', 'codeium',
    'tabnine', 'replit', 'lovable', 'bolt', 'v0', 'vercel'
]

VIDEO_MODELS = [
    'sora', 'runway', 'pika', 'kling', 'minimax', 'luma',
    'ltx', 'mochi', 'hunyuan', 'cogvideox', 'veo'
]

# =============================================================================
# URL CACHE FUNCTIONS
# =============================================================================

def load_url_cache():
    """Load the URL expansion cache from disk."""
    global _url_cache
    if os.path.exists(_cache_file):
        try:
            with open(_cache_file, 'r', encoding='utf-8') as f:
                _url_cache = json.load(f)
        except (json.JSONDecodeError, IOError, OSError):
            _url_cache = {}
    return _url_cache

def save_url_cache():
    """Save the URL expansion cache to disk."""
    with open(_cache_file, 'w', encoding='utf-8') as f:
        json.dump(_url_cache, f, indent=2)

def expand_tco_url(short_url, timeout=5):
    """
    Expand a t.co shortened URL by following redirects.
    Returns the final URL or None if expansion fails.
    """
    global _url_cache

    # Check cache first
    if short_url in _url_cache:
        return _url_cache[short_url]

    try:
        # Create a request that follows redirects
        req = urllib.request.Request(
            short_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )

        # Use HEAD request to just get the redirect without downloading content
        req.get_method = lambda: 'HEAD'

        with urllib.request.urlopen(req, timeout=timeout) as response:
            final_url = response.geturl()
            _url_cache[short_url] = final_url
            return final_url

    except urllib.request.HTTPError as e:
        # Some servers don't support HEAD, try GET
        try:
            req = urllib.request.Request(
                short_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                final_url = response.geturl()
                _url_cache[short_url] = final_url
                return final_url
        except:
            _url_cache[short_url] = None
            return None

    except Exception as e:
        _url_cache[short_url] = None
        return None

def extract_tco_urls(text):
    """Extract all t.co URLs from text."""
    return list(set(PATTERNS['tco'].findall(text)))

def expand_all_tco_urls(text, verbose=False):
    """
    Find all t.co URLs in text and expand them.
    Returns a dict mapping short URLs to expanded URLs.
    """
    tco_urls = extract_tco_urls(text)
    expanded = {}

    for url in tco_urls:
        if verbose:
            print(f"    Expanding: {url}...", end=' ', flush=True)

        final_url = expand_tco_url(url)

        if final_url and final_url != url:
            expanded[url] = final_url
            if verbose:
                # Show just the domain and path
                short_display = final_url[:60] + '...' if len(final_url) > 60 else final_url
                print(f"-> {short_display}")
        else:
            if verbose:
                print("(failed)")

        # Small delay to be nice to servers
        time.sleep(0.1)

    return expanded


def parse_metric_value(value_str):
    """
    Parse metric strings like '1.2K', '1M', '500' into integers.
    """
    if not value_str:
        return 0
    
    value_str = value_str.upper().replace(',', '').replace('+', '').strip()
    multiplier = 1
    
    if value_str.endswith('K'):
        multiplier = 1000
        value_str = value_str[:-1]
    elif value_str.endswith('M'):
        multiplier = 1000000
        value_str = value_str[:-1]
    elif value_str.endswith('B'):
        multiplier = 1000000000
        value_str = value_str[:-1]
        
    try:
        return int(float(value_str) * multiplier)
    except (ValueError, TypeError):
        return 0


def extract_metrics(text):
    """
    Extract engagement metrics, calculate impact score, and determine relevance tags.
    Returns: (metrics dict, impact_score int, confidence float, relevance_tags list)
    """
    metrics = {
        'views': 0,
        'likes': 0,
        'reposts': 0,
        'saves': 0
    }

    # Views/Impressions
    for match in METRIC_PATTERNS['views'].finditer(text):
        metrics['views'] = max(metrics['views'], parse_metric_value(match.group(1)))
    for match in METRIC_PATTERNS['impressions'].finditer(text):
        metrics['views'] = max(metrics['views'], parse_metric_value(match.group(1)))

    # Likes
    for match in METRIC_PATTERNS['likes'].finditer(text):
        metrics['likes'] = max(metrics['likes'], parse_metric_value(match.group(1)))

    # Reposts/Retweets
    for match in METRIC_PATTERNS['reposts'].finditer(text):
        metrics['reposts'] = max(metrics['reposts'], parse_metric_value(match.group(1)))
    for match in METRIC_PATTERNS['retweets'].finditer(text):
        metrics['reposts'] = max(metrics['reposts'], parse_metric_value(match.group(1)))

    # Saves/Bookmarks
    for match in METRIC_PATTERNS['saves'].finditer(text):
        val = match.group(1) or match.group(2)
        metrics['saves'] = max(metrics['saves'], parse_metric_value(val))

    # Calculate Impact Score
    # Formula: Views/1000 + Likes + Reposts*2 + Saves*2
    impact_score = (
        (metrics['views'] / 1000) +
        metrics['likes'] +
        (metrics['reposts'] * 2) +
        (metrics['saves'] * 2)
    )

    # =========================================================================
    # CONFIDENCE SCORE (0.0 to 1.0)
    # Based on source quality indicators
    # =========================================================================
    confidence = 0.5  # Default baseline

    text_lower = text.lower()

    # Increase confidence for verifiable sources
    if any(url in text_lower for url in ['github.com', 'huggingface.co', 'youtube.com']):
        confidence += 0.2  # Has direct link to authoritative source

    # Increase for engagement signals (real metrics suggest real content)
    if metrics['views'] > 1000 or metrics['likes'] > 100:
        confidence += 0.15
    if metrics['reposts'] > 50 or metrics['saves'] > 20:
        confidence += 0.1

    # Decrease for spam-like indicators
    if text_lower.count('free') > 2 or 'click here' in text_lower:
        confidence -= 0.2
    if len(text) < 50:  # Very short text less reliable
        confidence -= 0.1

    # Clamp to 0.0-1.0 range
    confidence = max(0.0, min(1.0, confidence))

    # =========================================================================
    # RELEVANCE TAGS
    # Categorize content by topic for filtering
    # =========================================================================
    relevance_tags = []

    # Content type tags
    if 'tutorial' in text_lower or 'guide' in text_lower or 'how to' in text_lower:
        relevance_tags.append('tutorial')
        impact_score += 2
    if 'release' in text_lower or 'launch' in text_lower or 'announced' in text_lower:
        relevance_tags.append('release')
        impact_score += 4
    if 'viral' in text_lower or 'breaking' in text_lower:
        relevance_tags.append('trending')
        impact_score += 5
    if 'open source' in text_lower or 'oss' in text_lower:
        relevance_tags.append('open-source')
        impact_score += 2

    # Technology domain tags
    if any(model in text_lower for model in ['flux', 'sdxl', 'stable diffusion', 'midjourney', 'dall-e']):
        relevance_tags.append('image-gen')
    if any(model in text_lower for model in ['claude', 'gpt', 'gemini', 'llama', 'mistral']):
        relevance_tags.append('llm')
    if any(tool in text_lower for tool in ['cursor', 'windsurf', 'cline', 'aider', 'claude code']):
        relevance_tags.append('coding-tool')
    if any(model in text_lower for model in ['sora', 'runway', 'pika', 'kling', 'luma']):
        relevance_tags.append('video-gen')
    if any(model in text_lower for model in ['kokoro', 'bark', 'elevenlabs', 'xtts']):
        relevance_tags.append('tts')
    if 'agent' in text_lower or 'mcp' in text_lower or 'tool use' in text_lower:
        relevance_tags.append('agents')
    if 'prompt' in text_lower:
        relevance_tags.append('prompting')

    # Quality indicators
    if 'huge' in text_lower or 'incredible' in text_lower or 'amazing' in text_lower:
        impact_score += 3

    return metrics, int(impact_score), round(confidence, 2), relevance_tags

# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def clean_url_ending(url):
    """Clean up URL endings - remove trailing punctuation, ellipsis, etc."""
    # Remove common trailing characters
    while url and url[-1] in '.,;:!?)]\u2026>':
        url = url[:-1]
    # Remove ellipsis character
    url = url.rstrip('\u2026')
    return url

def extract_github_repos(text):
    """Extract GitHub repository references."""
    repos = []
    seen = set()

    # First try full URL pattern
    for match in PATTERNS['github_full'].finditer(text):
        owner, repo = match.groups()[:2]
        # Clean up repo name
        repo = clean_url_ending(repo)
        
        if not repo or len(repo) < 3:
            continue

        # Skip user profiles, status pages
        if repo.startswith('status'):
            continue
            
        full_url = f"github.com/{owner}/{repo}"
        if full_url not in seen:
                seen.add(full_url)
                repos.append({
                    'url': full_url,
                    'owner': owner,
                    'repo': repo,
                    'date_found': datetime.now().strftime('%Y-%m-%d')
                })

    # Also try basic pattern for any we missed
    for match in PATTERNS['github'].finditer(text):
        owner, repo = match.groups()
        repo = clean_url_ending(repo)
        if repo and not repo.startswith('status') and len(repo) > 2:
            full_url = f"github.com/{owner}/{repo}"
            if full_url not in seen:
                seen.add(full_url)
                repos.append({
                    'url': full_url,
                    'owner': owner,
                    'repo': repo,
                    'date_found': datetime.now().strftime('%Y-%m-%d')
                })

    return repos

def extract_huggingface_refs(text):
    """Extract HuggingFace model/dataset references."""
    refs = []
    seen = set()

    # Try full URL pattern first
    for match in PATTERNS['huggingface_full'].finditer(text):
        owner, item = match.groups()
        item = clean_url_ending(item)
        if item and len(item) > 2:
            full_url = f"huggingface.co/{owner}/{item}"
            if full_url not in seen:
                seen.add(full_url)
                refs.append({
                    'url': full_url,
                    'owner': owner,
                    'item': item,
                    'date_found': datetime.now().strftime('%Y-%m-%d')
                })

    # Also try basic pattern
    for match in PATTERNS['huggingface'].finditer(text):
        owner, item = match.groups()
        item = clean_url_ending(item)
        if item and len(item) > 2:
            full_url = f"huggingface.co/{owner}/{item}"
            if full_url not in seen:
                seen.add(full_url)
                refs.append({
                    'url': full_url,
                    'owner': owner,
                    'item': item,
                    'date_found': datetime.now().strftime('%Y-%m-%d')
                })

    return refs

def extract_youtube_urls(text):
    """
    Extract YouTube URLs and attempt to find titles in surrounding text.
    YouTube video IDs are always exactly 11 characters.
    """
    videos = []

    # Simple line-based title extraction
    lines = text.split('\n')
    for i, line in enumerate(lines):
        found_in_line = []
        # Full URLs
        for match in PATTERNS['youtube_full'].finditer(line):
            video_id = match.group(1)[:11]  # YouTube IDs are exactly 11 chars
            if len(video_id) == 11:  # Only accept valid-length IDs
                found_in_line.append({'id': video_id, 'url': f"https://www.youtube.com/watch?v={video_id}"})
        # Short URLs
        for match in PATTERNS['youtube_short'].finditer(line):
            video_id = match.group(1)[:11]  # YouTube IDs are exactly 11 chars
            if len(video_id) == 11:  # Only accept valid-length IDs
                found_in_line.append({'id': video_id, 'url': f"https://youtu.be/{video_id}"})

        for v in found_in_line:
            # Try to get title from same line
            title = line.replace(v['url'], '').strip()
            # Or previous line if current is just URL
            if len(title) < 5 and i > 0:
                prev = lines[i-1].strip()
                if len(prev) > 10: title = prev

            title = title.strip(' -:[]()') or "Unknown Title"

            videos.append({
                'video_id': v['id'],
                'url': v['url'],
                'title': title,
                'date_found': datetime.now().strftime('%Y-%m-%d')
            })

    return videos


def extract_style_codes(text):
    """Extract Midjourney --sref and --style codes."""
    codes = {
        'sref': [],
        'style': [],
        'niji': [],
        'personalize': []
    }

    for match in PATTERNS['sref'].finditer(text):
        codes['sref'].append(match.group(1))

    for match in PATTERNS['style'].finditer(text):
        codes['style'].append(match.group(1))

    for match in PATTERNS['niji'].finditer(text):
        version = match.group(1) or '6'
        codes['niji'].append(version)

    for match in PATTERNS['personalize'].finditer(text):
        codes['personalize'].append(match.group(1))

    return codes

def detect_models(text):
    """Detect AI model mentions in text."""
    text_lower = text.lower()
    detected = {
        'tts': [],
        'image_cloud': [],
        'image_local': [],
        'coding_tools': [],
        'video': []
    }

    for model in TTS_MODELS:
        if model in text_lower:
            detected['tts'].append(model.title())

    for model in IMAGE_CLOUD_MODELS:
        if model in text_lower:
            detected['image_cloud'].append(model.title())

    for model in IMAGE_LOCAL_MODELS:
        if model in text_lower:
            detected['image_local'].append(model.title())

    for tool in CODING_TOOLS:
        if tool in text_lower:
            detected['coding_tools'].append(tool.title())

    for model in VIDEO_MODELS:
        if model in text_lower:
            detected['video'].append(model.title())

    return detected

def extract_all_from_text(text, source_info=None, expand_tco=False, verbose=False):
    """
    Extract all patterns from a text block.
    If expand_tco=True, also expands t.co links and extracts from those.
    """
    # Start with direct extraction from text
    github_repos = extract_github_repos(text)
    huggingface_refs = extract_huggingface_refs(text)
    youtube_videos = extract_youtube_urls(text)

    # If t.co expansion is enabled, expand those URLs and extract from them too
    expanded_urls = []
    if expand_tco:
        tco_expanded = expand_all_tco_urls(text, verbose=verbose)
        for short_url, full_url in tco_expanded.items():
            if full_url:
                expanded_urls.append(full_url)
                # Extract from the expanded URL
                github_repos.extend(extract_github_repos(full_url))
                huggingface_refs.extend(extract_huggingface_refs(full_url))
                youtube_videos.extend(extract_youtube_urls(full_url))

    # Deduplicate
    seen_github = set()
    unique_github = []
    for r in github_repos:
        if r['url'] not in seen_github:
            seen_github.add(r['url'])
            unique_github.append(r)

    seen_hf = set()
    unique_hf = []
    for r in huggingface_refs:
        if r['url'] not in seen_hf:
            seen_hf.add(r['url'])
            unique_hf.append(r)

    seen_yt = set()
    unique_yt = []
    for v in youtube_videos:
        if v['video_id'] not in seen_yt:
            seen_yt.add(v['video_id'])
            unique_yt.append(v)


    # Extract metrics, confidence, and relevance tags
    metrics, impact_score, confidence, relevance_tags = extract_metrics(text)

    # Enrich source info if provided
    if source_info:
        source_info['metrics'] = metrics
        source_info['impact_score'] = impact_score
        source_info['confidence'] = confidence
        source_info['relevance_tags'] = relevance_tags

    result = {
        'github_repos': unique_github,
        'huggingface_refs': unique_hf,
        'youtube_videos': unique_yt,
        'style_codes': extract_style_codes(text),
        'models_detected': detect_models(text),
        'expanded_urls': expanded_urls,
        'source': source_info,
        'confidence': confidence,
        'relevance_tags': relevance_tags
    }
    return result

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def load_master_db():
    """Load the master database."""
    if os.path.exists(MASTER_DB_PATH):
        try:
            with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Master DB JSON is corrupted: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load master DB: {e}")
            return None
    return None

def save_master_db(db):
    """Save the master database."""
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(MASTER_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"Saved master_db.json with {db['metadata']['total_entries']} entries")

def add_to_db(db, extractions, source_text=""):
    """Add extracted content to the database."""
    added = 0

    # Add GitHub repos
    for repo in extractions['github_repos']:
        existing_urls = [r['url'] for r in db['repositories']['github']]
        if repo['url'] not in existing_urls:
            db['repositories']['github'].append({
                'url': repo['url'],
                'name': repo['repo'],
                'owner': repo['owner'],
                'category': 'unknown',
                'date_found': repo['date_found'],
                'source': extractions.get('source', {})
            })
            added += 1

    # Add HuggingFace refs
    for ref in extractions['huggingface_refs']:
        existing_urls = [r['url'] for r in db['repositories']['huggingface']]
        if ref['url'] not in existing_urls:
            db['repositories']['huggingface'].append({
                'url': ref['url'],
                'name': ref['item'],
                'owner': ref['owner'],
                'date_found': ref['date_found'],
                'source': extractions.get('source', {})
            })
            added += 1

    # Add YouTube tutorials
    for video in extractions['youtube_videos']:
        existing_ids = [t.get('video_id') for t in db['tutorials']]
        if video['video_id'] not in existing_ids:
            db['tutorials'].append({
                'video_id': video['video_id'],
                'url': video['url'],
                'title': None,  # To be fetched later
                'topic': 'unknown',
                'date_found': video['date_found'],
                'source': extractions.get('source', {})
            })
            added += 1

    # Add Midjourney sref codes
    for code in extractions['style_codes']['sref']:
        existing_codes = [s['code'] for s in db['styles']['midjourney_sref']]
        if code not in existing_codes:
            db['styles']['midjourney_sref'].append({
                'code': code,
                'description': None,
                'date_found': datetime.now().strftime('%Y-%m-%d'),
                'source': extractions.get('source', {})
            })
            added += 1

    # Add Midjourney personalize codes
    # Ensure list exists (for migration)
    if 'midjourney_personalize' not in db['styles']:
        db['styles']['midjourney_personalize'] = []

    for code in extractions['style_codes']['personalize']:
        existing_codes = [s['code'] for s in db['styles']['midjourney_personalize']]
        if code not in existing_codes:
            db['styles']['midjourney_personalize'].append({
                'code': code,
                'description': None,
                'date_found': datetime.now().strftime('%Y-%m-%d'),
                'source': extractions.get('source', {})
            })
            added += 1

    # Update total entries
    db['metadata']['total_entries'] = (
        len(db['repositories']['github']) +
        len(db['repositories']['huggingface']) +
        len(db['tutorials']) +
        len(db['styles']['midjourney_sref']) +
        len(db['styles'].get('midjourney_personalize', [])) +
        len(db['models']['tts']) +
        len(db['models']['image_cloud']) +
        len(db['models']['image_local'])
    )

    return added

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_existing_json():
    """Process existing twitter_data_extract.json to populate master_db."""
    print("=" * 80)
    print("PROCESSING EXISTING TWITTER DATA")
    print("=" * 80)

    if not os.path.exists(TWITTER_JSON_PATH):
        print(f"Twitter JSON not found: {TWITTER_JSON_PATH}")
        return

    try:
        with open(TWITTER_JSON_PATH, 'r', encoding='utf-8') as f:
            twitter_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Twitter JSON is corrupted: {e}")
        return
    except Exception as e:
        print(f"ERROR: Failed to load Twitter JSON: {e}")
        return

    db = load_master_db()
    if not db:
        print("Master DB not found!")
        return

    total_added = 0

    for entry in twitter_data:
        text = f"{entry.get('subject', '')} {entry.get('content', '')}"
        source_info = {
            'type': 'twitter_email',
            'author': entry.get('author', ''),
            'date': entry.get('date', ''),
            'subject': entry.get('subject', '')
        }

        extractions = extract_all_from_text(text, source_info)
        added = add_to_db(db, extractions, text)

        if added > 0:
            print(f"  [{entry.get('date')}] Added {added} items from: {entry.get('author', 'Unknown')[:30]}")
            total_added += added

    save_master_db(db)

    print("\n" + "-" * 80)
    print("SUMMARY")
    print("-" * 80)
    print(f"Processed {len(twitter_data)} emails")
    print(f"Added {total_added} new entries to master_db")
    print(f"GitHub repos: {len(db['repositories']['github'])}")
    print(f"HuggingFace refs: {len(db['repositories']['huggingface'])}")
    print(f"YouTube tutorials: {len(db['tutorials'])}")
    print(f"YouTube tutorials: {len(db['tutorials'])}")
    print(f"Midjourney sref codes: {len(db['styles']['midjourney_sref'])}")
    print(f"Midjourney customize codes: {len(db['styles'].get('midjourney_personalize', []))}")

def process_subfolder(subfolder, db):
    """
    Process a single Outlook subfolder for AI content extraction.
    Returns a dict with stats: {emails, github, hf, yt, sref, added}
    """
    stats = {'emails': 0, 'github': 0, 'hf': 0, 'yt': 0, 'sref': 0, 'pers': 0, 'added': 0}
    subfolder_name = subfolder.Name

    items = subfolder.Items
    items.Sort("[ReceivedTime]", True)

    for item in items:
        if item.Class != 43:  # Not a mail item
            continue

        stats['emails'] += 1

        try:
            subject = item.Subject or ''
            body = item.Body or ''
            text = f"{subject} {body}"

            try:
                sender = item.SenderName or 'Unknown Sender'
                # Clean sender name (remove email address if present)
                if ' <' in sender:
                    sender = sender.split(' <')[0].strip()
            except (AttributeError, TypeError, Exception) as e:
                # COM object access can fail in various ways
                sender = 'Unknown Sender'

            # Try to extract original author from email body (for forwarded emails)
            original_author = None
            import re
            
            # Common patterns for original author in forwarded X/Twitter posts
            author_patterns = [
                r'Post by ([^<>\n]+?) on X',      # "Post by Author on X"
                r'Posted by ([^<>\n]+)',           # "Posted by Author"
                r'From: ([^<>\n]+)',               # "From: Author"
                r'Author: ([^<>\n]+)',             # "Author: Name"
                r'By ([^<>\n]+?) \|',              # "By Author |" (newsletter style)
                r'Written by ([^<>\n]+)',          # "Written by Author"
                r'\n([A-Z][a-z]+ [A-Z][a-z]+)\n.*@',  # Name followed by @ on next line
                r'(?:^|\n)([A-Z][a-z]+ [A-Z][a-z]+) shared',  # "Name shared"
                r'@([A-Za-z0-9_]{3,20})',          # Twitter handle @username (3-20 chars)
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, body)
                if match:
                    original_author = match.group(1).strip()
                    # Clean up extracted author
                    original_author = original_author.strip(' -:')
                    if len(original_author) > 2 and len(original_author) < 50:
                        break
                    else:
                        original_author = None
            
            # Use original author if found, otherwise fall back to sender
            author = original_author if original_author else sender

            source_info = {
                'type': 'outlook_email',
                'folder': subfolder_name,
                'subject': subject[:100],
                'author': author,
                'date': str(item.ReceivedTime)[:10]
            }


            # Enable t.co expansion to recover full URLs
            extractions = extract_all_from_text(text, source_info, expand_tco=True)

            # Smart Deduplication: Remove truncated GitHub URLs if a full version exists
            def is_truncated_version(trunc, full):
                return trunc.endswith('...') and full.startswith(trunc.rstrip('...'))

            full_repos = [r['url'] for r in extractions['github_repos'] if not r['url'].endswith('...')]
            
            unique_repos = []
            for repo in extractions['github_repos']:
                is_redundant = False
                if repo['url'].endswith('...'):
                    for full in full_repos:
                        if is_truncated_version(repo['url'], full):
                            is_redundant = True
                            break
                if not is_redundant:
                    unique_repos.append(repo)
            
            extractions['github_repos'] = unique_repos


            # Track what was found (before dedup)
            stats['github'] += len(extractions['github_repos'])
            stats['hf'] += len(extractions['huggingface_refs'])
            stats['yt'] += len(extractions['youtube_videos'])
            stats['yt'] += len(extractions['youtube_videos'])
            stats['sref'] += len(extractions['style_codes']['sref'])
            stats['pers'] += len(extractions['style_codes']['personalize'])

            added = add_to_db(db, extractions, text)
            stats['added'] += added

            if added > 0:
                author = subject.replace('Post by ', '').split(' on X')[0]
                print(f"    [{source_info['date']}] +{added}: {author[:40]}")

        except Exception as e:
            stats['errors'] = stats.get('errors', 0) + 1
            logger.warning(f"Failed to process email '{subject[:50]}...': {e}")

    return stats


def process_outlook_emails(folders_to_process=None):
    """
    Process emails from multiple Outlook Scott subfolders.

    IMPORTANT: Also processes the MAIN Scott folder first to capture new emails
    BEFORE they get moved to subfolders by the organizer.

    Args:
        folders_to_process: List of folder names to process. If None, uses DEFAULT_EXTRACT_FOLDERS.
    """
    print("=" * 80)
    print("PROCESSING OUTLOOK EMAILS (Multi-Folder)")
    print("=" * 80)

    if folders_to_process is None:
        folders_to_process = DEFAULT_EXTRACT_FOLDERS

    reader = OutlookReader()
    if not reader.connect():
        print("ERROR: Failed to connect to Outlook")
        return

    db = load_master_db()
    if not db:
        print("Master DB not found!")
        return

    # Get Scott folder
    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")
    if not scott_folder:
        print("ERROR: Could not find 'scott' folder")
        return

    # =========================================================================
    # STEP 1: Process MAIN Scott folder first (new emails before organization)
    # =========================================================================
    # =========================================================================
    main_folder_count = scott_folder.Items.Count
    main_folder_stats = {'emails': 0, 'github': 0, 'hf': 0, 'yt': 0, 'sref': 0, 'pers': 0, 'added': 0}

    if main_folder_count > 0:
        print(f"\n>>> MAIN SCOTT FOLDER: {main_folder_count} new emails <<<")
        print("-" * 60)
        main_folder_stats = process_subfolder(scott_folder, db)
        print(f"    Extracted: {main_folder_stats['added']} new items from main folder")
        save_master_db(db)  # Save immediately to preserve extractions
    else:
        print(f"\n>>> MAIN SCOTT FOLDER: empty (all organized) <<<")

    # =========================================================================
    # STEP 2: Process configured subfolders
    # =========================================================================
    # Build a map of available subfolders
    available_folders = {}
    for sf in scott_folder.Folders:
        available_folders[sf.Name] = sf

    print(f"\nConfigured folders: {len(folders_to_process)}")
    print(f"Available in Outlook: {len(available_folders)}")

    # Track stats per folder (include main folder if it had emails)
    folder_stats = {}
    if main_folder_stats['emails'] > 0:
        folder_stats['[MAIN FOLDER]'] = main_folder_stats
    total_added = main_folder_stats['added']

    for folder_name in folders_to_process:
        if folder_name not in available_folders:
            print(f"\n--- Skipping: {folder_name} (not found) ---")
            continue

        subfolder = available_folders[folder_name]
        email_count = subfolder.Items.Count

        print(f"\n--- Processing: {folder_name} ({email_count} emails) ---")

        stats = process_subfolder(subfolder, db)
        folder_stats[folder_name] = stats
        total_added += stats['added']

    save_master_db(db)

    # Print summary by folder
    print("\n" + "=" * 80)
    print("SUMMARY BY FOLDER")
    print("=" * 80)
    print("=" * 80)
    print(f"{'Folder':<25} {'Emails':>7} {'GitHub':>8} {'HF':>6} {'YT':>6} {'Sref':>6} {'Pers':>6} {'Added':>7}")
    print("-" * 80)
    print("-" * 80)

    for folder_name, stats in folder_stats.items():
        print(f"{folder_name:<25} {stats['emails']:>7} {stats['github']:>8} {stats['hf']:>6} {stats['yt']:>6} {stats['sref']:>6} {stats['pers']:>6} {stats['added']:>7}")

    print("-" * 80)
    totals = {
        'emails': sum(s['emails'] for s in folder_stats.values()),
        'github': sum(s['github'] for s in folder_stats.values()),
        'hf': sum(s['hf'] for s in folder_stats.values()),
        'yt': sum(s['yt'] for s in folder_stats.values()),
        'sref': sum(s['sref'] for s in folder_stats.values()),
        'pers': sum(s['pers'] for s in folder_stats.values()),
    }
    print(f"{'TOTAL':<25} {totals['emails']:>7} {totals['github']:>8} {totals['hf']:>6} {totals['yt']:>6} {totals['sref']:>6} {totals['pers']:>6} {total_added:>7}")

    print("\n" + "-" * 80)
    print("DATABASE TOTALS")
    print("-" * 80)
    print(f"GitHub repos: {len(db['repositories']['github'])}")
    print(f"HuggingFace refs: {len(db['repositories']['huggingface'])}")
    print(f"YouTube tutorials: {len(db['tutorials'])}")
    print(f"Midjourney sref codes: {len(db['styles']['midjourney_sref'])}")

def show_stats():
    """Show current database statistics."""
    print("=" * 80)
    print("AI KNOWLEDGE BASE STATISTICS")
    print("=" * 80)

    db = load_master_db()
    if not db:
        print("Master DB not found!")
        return

    print(f"\nLast updated: {db['metadata']['last_updated']}")
    print(f"Total entries: {db['metadata']['total_entries']}")

    print("\n" + "-" * 40)
    print("REPOSITORIES")
    print("-" * 40)
    print(f"  GitHub repos: {len(db['repositories']['github'])}")
    for repo in db['repositories']['github'][:5]:
        print(f"    - {repo['url']}")
    if len(db['repositories']['github']) > 5:
        print(f"    ... and {len(db['repositories']['github']) - 5} more")

    print(f"\n  HuggingFace refs: {len(db['repositories']['huggingface'])}")
    for ref in db['repositories']['huggingface'][:5]:
        print(f"    - {ref['url']}")
    if len(db['repositories']['huggingface']) > 5:
        print(f"    ... and {len(db['repositories']['huggingface']) - 5} more")

    print("\n" + "-" * 40)
    print("TUTORIALS")
    print("-" * 40)
    print(f"  YouTube videos: {len(db['tutorials'])}")
    for vid in db['tutorials'][:5]:
        print(f"    - {vid['url']}")
    if len(db['tutorials']) > 5:
        print(f"    ... and {len(db['tutorials']) - 5} more")

    print("\n" + "-" * 40)
    print("STYLES")
    print("-" * 40)
    print(f"  Midjourney sref codes: {len(db['styles']['midjourney_sref'])}")
    for style in db['styles']['midjourney_sref'][:5]:
        print(f"    - --sref {style['code']}")
    if len(db['styles']['midjourney_sref']) > 5:
        print(f"    ... and {len(db['styles']['midjourney_sref']) - 5} more")

    print(f"\n  Midjourney personalize codes: {len(db['styles'].get('midjourney_personalize', []))}")
    for style in db['styles'].get('midjourney_personalize', [])[:5]:
        print(f"    - --p {style['code']}")
    if len(db['styles'].get('midjourney_personalize', [])) > 5:
        print(f"    ... and {len(db['styles']['midjourney_personalize']) - 5} more")

def process_with_tco_expansion():
    """Process emails with t.co link expansion enabled."""
    print("=" * 80)
    print("PROCESSING WITH T.CO LINK EXPANSION")
    print("=" * 80)

    # Load URL cache
    load_url_cache()

    if not os.path.exists(TWITTER_JSON_PATH):
        print(f"Twitter JSON not found: {TWITTER_JSON_PATH}")
        return

    try:
        with open(TWITTER_JSON_PATH, 'r', encoding='utf-8') as f:
            twitter_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Twitter JSON is corrupted: {e}")
        return
    except Exception as e:
        print(f"ERROR: Failed to load Twitter JSON: {e}")
        return

    db = load_master_db()
    if not db:
        print("Master DB not found!")
        return

    total_added = 0
    total_expanded = 0

    for i, entry in enumerate(twitter_data):
        text = f"{entry.get('subject', '')} {entry.get('content', '')}"

        # Check if there are any t.co URLs - from text OR from the tco_urls field
        tco_urls = extract_tco_urls(text)

        # Also check the tco_urls field in the JSON data
        json_tco_urls = entry.get('tco_urls', [])
        if json_tco_urls:
            tco_urls.extend(json_tco_urls)
            tco_urls = list(set(tco_urls))  # Dedupe

        if not tco_urls:
            continue

        print(f"\n[{i+1}/{len(twitter_data)}] {entry.get('author', 'Unknown')[:30]}")
        print(f"  Found {len(tco_urls)} t.co links")

        source_info = {
            'type': 'twitter_email',
            'author': entry.get('author', ''),
            'date': entry.get('date', ''),
            'subject': entry.get('subject', '')
        }

        # Expand t.co URLs directly (including those from JSON field)
        expanded_urls = []
        for tco_url in tco_urls:
            print(f"    Expanding: {tco_url}...", end=' ', flush=True)
            final_url = expand_tco_url(tco_url)
            if final_url and final_url != tco_url:
                expanded_urls.append(final_url)
                short_display = final_url[:60] + '...' if len(final_url) > 60 else final_url
                print(f"-> {short_display}")
            else:
                print("(failed)")
            time.sleep(0.1)

        # Now extract from both original text and expanded URLs
        extractions = extract_all_from_text(text, source_info, expand_tco=False)

        # Also extract from expanded URLs
        for url in expanded_urls:
            extractions['github_repos'].extend(extract_github_repos(url))
            extractions['huggingface_refs'].extend(extract_huggingface_refs(url))
            extractions['youtube_videos'].extend(extract_youtube_urls(url))

        added = add_to_db(db, extractions, text)
        total_expanded += len(expanded_urls)

        if added > 0:
            print(f"  -> Added {added} new items")
            total_added += added

    # Save cache and database
    save_url_cache()
    save_master_db(db)

    print("\n" + "-" * 80)
    print("SUMMARY")
    print("-" * 80)
    print(f"Processed {len(twitter_data)} emails")
    print(f"Expanded {total_expanded} t.co links")
    print(f"Added {total_added} new entries to master_db")
    print(f"GitHub repos: {len(db['repositories']['github'])}")
    print(f"HuggingFace refs: {len(db['repositories']['huggingface'])}")
    print(f"YouTube tutorials: {len(db['tutorials'])}")
    print(f"Midjourney sref codes: {len(db['styles']['midjourney_sref'])}")
    print(f"\nURL cache saved to: {_cache_file}")

def list_folders():
    """List configured folders for extraction."""
    print("=" * 80)
    print("CONFIGURED EXTRACTION FOLDERS")
    print("=" * 80)

    print("\nAI-Specific (High Priority):")
    for folder in AI_CONTENT_FOLDERS:
        print(f"  - {folder}")

    print("\nRelated Content:")
    for folder in RELATED_CONTENT_FOLDERS:
        print(f"  - {folder}")

    print(f"\nTotal: {len(DEFAULT_EXTRACT_FOLDERS)} folders")
    print("\nUse --folders \"Folder1,Folder2\" to process specific folders")


def parse_folders_arg(folders_arg):
    """Parse comma-separated folder names from CLI argument."""
    if not folders_arg:
        return None
    return [f.strip() for f in folders_arg.split(',') if f.strip()]


def main():
    """Main entry point."""
    import sys

    # Check for --folders argument
    folders_to_process = None
    if '--folders' in sys.argv:
        idx = sys.argv.index('--folders')
        if idx + 1 < len(sys.argv):
            folders_to_process = parse_folders_arg(sys.argv[idx + 1])
            print(f"Processing specific folders: {folders_to_process}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == '--json':
            process_existing_json()
        elif cmd == '--outlook':
            process_outlook_emails(folders_to_process)
        elif cmd == '--stats':
            show_stats()
        elif cmd == '--all':
            process_existing_json()
            print("\n")
            process_outlook_emails(folders_to_process)
        elif cmd == '--expand':
            process_with_tco_expansion()
        elif cmd == '--list-folders':
            list_folders()
        else:
            print("Usage:")
            print("  python ai_content_extractor.py --json        Process twitter_data_extract.json")
            print("  python ai_content_extractor.py --outlook     Process Outlook emails (all folders)")
            print("  python ai_content_extractor.py --outlook --folders \"AI Agents,General AI\"")
            print("                                               Process specific folders only")
            print("  python ai_content_extractor.py --list-folders  Show configured folders")
            print("  python ai_content_extractor.py --stats       Show database statistics")
            print("  python ai_content_extractor.py --all         Process both sources")
            print("  python ai_content_extractor.py --expand      Process with t.co link expansion")
    else:
        # Default: process JSON first, then show stats
        process_existing_json()
        print("\n")
        show_stats()

if __name__ == "__main__":
    main()
