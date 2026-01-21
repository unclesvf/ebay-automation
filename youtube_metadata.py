"""
YouTube Metadata & Transcript Extractor
Fetches video metadata and transcripts for tutorials in the AI Knowledge Base.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import re
from datetime import datetime
from pathlib import Path

# Third-party imports
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable
    )
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("Warning: youtube-transcript-api not installed. Run: pip install youtube-transcript-api")

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    print("Warning: yt-dlp not installed. Run: pip install yt-dlp")

# Paths
MASTER_DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'
TRANSCRIPTS_PATH = r'D:\AI-Knowledge-Base\tutorials\transcripts'
METADATA_CACHE_PATH = r'D:\AI-Knowledge-Base\youtube_metadata_cache.json'

# =============================================================================
# DATABASE FUNCTIONS
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

def load_metadata_cache():
    """Load the metadata cache."""
    if os.path.exists(METADATA_CACHE_PATH):
        with open(METADATA_CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_metadata_cache(cache):
    """Save the metadata cache."""
    with open(METADATA_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def ensure_transcript_dir():
    """Ensure the transcripts directory exists."""
    Path(TRANSCRIPTS_PATH).mkdir(parents=True, exist_ok=True)

# =============================================================================
# YOUTUBE METADATA EXTRACTION
# =============================================================================

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'youtube\.com/watch\?v=([\w\-]+)',
        r'youtu\.be/([\w\-]+)',
        r'youtube\.com/embed/([\w\-]+)',
        r'youtube\.com/v/([\w\-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # If it looks like just a video ID
    if re.match(r'^[\w\-]{11}$', url):
        return url

    return None

def get_video_metadata(video_id):
    """
    Fetch video metadata using yt-dlp.
    Returns dict with title, description, channel, duration, etc.
    """
    if not YTDLP_AVAILABLE:
        return None

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            return {
                'video_id': video_id,
                'title': info.get('title'),
                'description': info.get('description'),
                'channel': info.get('channel') or info.get('uploader'),
                'channel_id': info.get('channel_id'),
                'duration': info.get('duration'),  # in seconds
                'duration_string': info.get('duration_string'),
                'view_count': info.get('view_count'),
                'like_count': info.get('like_count'),
                'upload_date': info.get('upload_date'),  # YYYYMMDD format
                'categories': info.get('categories', []),
                'tags': info.get('tags', []),
                'thumbnail': info.get('thumbnail'),
                'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    except Exception as e:
        print(f"    Error fetching metadata for {video_id}: {e}")
        return None

# =============================================================================
# TRANSCRIPT EXTRACTION
# =============================================================================

def get_transcript(video_id, languages=['en', 'en-US', 'en-GB']):
    """
    Fetch transcript for a YouTube video.
    Returns dict with transcript text and metadata.
    """
    if not TRANSCRIPT_API_AVAILABLE:
        return None

    try:
        # Create API instance (new API format)
        api = YouTubeTranscriptApi()

        # Fetch transcript
        transcript_data = api.fetch(video_id)
        language_used = 'en'
        transcript_type = 'auto'

        if not transcript_data:
            return None

        # Build full text and timestamped segments
        full_text = []
        segments = []

        for entry in transcript_data:
            # Handle both old dict format and new object format
            if hasattr(entry, 'text'):
                text = entry.text.strip() if entry.text else ''
                start = entry.start if hasattr(entry, 'start') else 0
                duration = entry.duration if hasattr(entry, 'duration') else 0
            else:
                text = entry.get('text', '').strip()
                start = entry.get('start', 0)
                duration = entry.get('duration', 0)

            if text:
                full_text.append(text)
                segments.append({
                    'start': start,
                    'duration': duration,
                    'text': text
                })

        return {
            'video_id': video_id,
            'language': language_used,
            'transcript_type': transcript_type,
            'full_text': ' '.join(full_text),
            'segments': segments,
            'segment_count': len(segments),
            'word_count': len(' '.join(full_text).split()),
            'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except TranscriptsDisabled:
        print(f"    Transcripts disabled for {video_id}")
        return {'video_id': video_id, 'error': 'transcripts_disabled'}

    except NoTranscriptFound:
        print(f"    No transcript found for {video_id}")
        return {'video_id': video_id, 'error': 'no_transcript'}

    except VideoUnavailable:
        print(f"    Video unavailable: {video_id}")
        return {'video_id': video_id, 'error': 'video_unavailable'}

    except Exception as e:
        print(f"    Error fetching transcript for {video_id}: {e}")
        return {'video_id': video_id, 'error': str(e)}

def save_transcript_file(video_id, transcript_data, metadata=None):
    """Save transcript to a text file."""
    ensure_transcript_dir()

    # Build filename from title if available
    if metadata and metadata.get('title'):
        # Clean title for filename
        safe_title = re.sub(r'[<>:"/\\|?*]', '', metadata['title'])
        safe_title = safe_title[:50].strip()
        filename = f"{video_id}_{safe_title}.txt"
    else:
        filename = f"{video_id}.txt"

    filepath = os.path.join(TRANSCRIPTS_PATH, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        # Header
        f.write(f"YouTube Video Transcript\n")
        f.write(f"{'=' * 60}\n\n")

        if metadata:
            f.write(f"Title: {metadata.get('title', 'Unknown')}\n")
            f.write(f"Channel: {metadata.get('channel', 'Unknown')}\n")
            f.write(f"Duration: {metadata.get('duration_string', 'Unknown')}\n")
            f.write(f"URL: https://youtube.com/watch?v={video_id}\n")
            f.write(f"\n{'=' * 60}\n\n")

        if transcript_data.get('full_text'):
            f.write(f"Language: {transcript_data.get('language', 'Unknown')}\n")
            f.write(f"Type: {transcript_data.get('transcript_type', 'Unknown')}\n")
            f.write(f"Word Count: {transcript_data.get('word_count', 0)}\n")
            f.write(f"\n{'-' * 60}\n")
            f.write("TRANSCRIPT\n")
            f.write(f"{'-' * 60}\n\n")
            f.write(transcript_data['full_text'])
            f.write("\n\n")

            # Also save timestamped version
            f.write(f"{'-' * 60}\n")
            f.write("TIMESTAMPED SEGMENTS\n")
            f.write(f"{'-' * 60}\n\n")

            for seg in transcript_data.get('segments', []):
                timestamp = format_timestamp(seg['start'])
                f.write(f"[{timestamp}] {seg['text']}\n")
        else:
            f.write(f"Error: {transcript_data.get('error', 'Unknown error')}\n")

    return filepath

def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

# =============================================================================
# DATABASE UPDATE FUNCTIONS
# =============================================================================

def update_tutorial_in_db(db, video_id, metadata, transcript_data):
    """Update a tutorial entry in the database with metadata and transcript info."""
    for tutorial in db['tutorials']:
        if tutorial.get('video_id') == video_id:
            # Update metadata
            if metadata:
                tutorial['title'] = metadata.get('title')
                tutorial['channel'] = metadata.get('channel')
                tutorial['duration'] = metadata.get('duration')
                tutorial['duration_string'] = metadata.get('duration_string')
                tutorial['description'] = metadata.get('description', '')[:500]  # Truncate
                tutorial['upload_date'] = metadata.get('upload_date')
                tutorial['view_count'] = metadata.get('view_count')
                tutorial['tags'] = metadata.get('tags', [])[:10]  # Limit tags
                tutorial['thumbnail'] = metadata.get('thumbnail')
                tutorial['metadata_fetched'] = metadata.get('fetched_at')

            # Update transcript info
            if transcript_data and not transcript_data.get('error'):
                tutorial['has_transcript'] = True
                tutorial['transcript_language'] = transcript_data.get('language')
                tutorial['transcript_type'] = transcript_data.get('transcript_type')
                tutorial['transcript_word_count'] = transcript_data.get('word_count')
                tutorial['transcript_fetched'] = transcript_data.get('fetched_at')
            elif transcript_data and transcript_data.get('error'):
                tutorial['has_transcript'] = False
                tutorial['transcript_error'] = transcript_data.get('error')

            return True

    return False

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_all_tutorials(skip_existing=True, fetch_transcripts=True):
    """Process all tutorials in the database."""
    print("=" * 70)
    print("YOUTUBE METADATA & TRANSCRIPT EXTRACTOR")
    print("=" * 70)

    db = load_db()
    if not db:
        print("ERROR: Could not load database")
        return

    cache = load_metadata_cache()
    tutorials = db.get('tutorials', [])

    if not tutorials:
        print("\nNo tutorials found in database.")
        return

    print(f"\nFound {len(tutorials)} tutorials in database")

    processed = 0
    metadata_fetched = 0
    transcripts_fetched = 0
    errors = 0

    for i, tutorial in enumerate(tutorials):
        video_id = tutorial.get('video_id')
        if not video_id:
            continue

        print(f"\n[{i+1}/{len(tutorials)}] Processing: {video_id}")

        # Check if already processed
        if skip_existing and tutorial.get('metadata_fetched'):
            print(f"    Skipping (already has metadata)")
            continue

        # Fetch metadata
        print(f"    Fetching metadata...")
        metadata = None

        if video_id in cache:
            metadata = cache[video_id]
            print(f"    Using cached metadata: {metadata.get('title', 'Unknown')[:50]}")
        else:
            metadata = get_video_metadata(video_id)
            if metadata:
                cache[video_id] = metadata
                print(f"    Title: {metadata.get('title', 'Unknown')[:50]}")
                metadata_fetched += 1
            else:
                print(f"    Failed to fetch metadata")
                errors += 1

        # Fetch transcript
        transcript_data = None
        if fetch_transcripts:
            print(f"    Fetching transcript...")
            transcript_data = get_transcript(video_id)

            if transcript_data and not transcript_data.get('error'):
                print(f"    Transcript: {transcript_data.get('word_count', 0)} words ({transcript_data.get('transcript_type')})")
                transcripts_fetched += 1

                # Save transcript file
                filepath = save_transcript_file(video_id, transcript_data, metadata)
                print(f"    Saved: {os.path.basename(filepath)}")
            elif transcript_data and transcript_data.get('error'):
                print(f"    Transcript error: {transcript_data.get('error')}")

        # Update database
        update_tutorial_in_db(db, video_id, metadata, transcript_data)
        processed += 1

    # Save everything
    save_db(db)
    save_metadata_cache(cache)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Processed:           {processed}")
    print(f"  Metadata fetched:    {metadata_fetched}")
    print(f"  Transcripts fetched: {transcripts_fetched}")
    print(f"  Errors:              {errors}")
    print(f"\nTranscripts saved to: {TRANSCRIPTS_PATH}")
    print(f"Metadata cache: {METADATA_CACHE_PATH}")

def process_single_video(video_id_or_url):
    """Process a single video by ID or URL."""
    video_id = extract_video_id(video_id_or_url)
    if not video_id:
        print(f"Could not extract video ID from: {video_id_or_url}")
        return

    print(f"\nProcessing video: {video_id}")
    print("-" * 50)

    # Fetch metadata
    print("Fetching metadata...")
    metadata = get_video_metadata(video_id)

    if metadata:
        print(f"  Title: {metadata.get('title')}")
        print(f"  Channel: {metadata.get('channel')}")
        print(f"  Duration: {metadata.get('duration_string')}")
        print(f"  Views: {metadata.get('view_count'):,}" if metadata.get('view_count') else "  Views: Unknown")
    else:
        print("  Failed to fetch metadata")

    # Fetch transcript
    print("\nFetching transcript...")
    transcript_data = get_transcript(video_id)

    if transcript_data and not transcript_data.get('error'):
        print(f"  Language: {transcript_data.get('language')}")
        print(f"  Type: {transcript_data.get('transcript_type')}")
        print(f"  Words: {transcript_data.get('word_count')}")
        print(f"  Segments: {transcript_data.get('segment_count')}")

        # Save transcript
        filepath = save_transcript_file(video_id, transcript_data, metadata)
        print(f"\nSaved transcript to: {filepath}")

        # Show preview
        print("\n" + "-" * 50)
        print("TRANSCRIPT PREVIEW (first 500 chars)")
        print("-" * 50)
        print(transcript_data['full_text'][:500] + "...")
    else:
        print(f"  Error: {transcript_data.get('error') if transcript_data else 'Unknown'}")

def show_stats():
    """Show statistics about fetched transcripts."""
    db = load_db()
    if not db:
        print("ERROR: Could not load database")
        return

    tutorials = db.get('tutorials', [])

    with_metadata = sum(1 for t in tutorials if t.get('metadata_fetched'))
    with_transcript = sum(1 for t in tutorials if t.get('has_transcript'))
    total_words = sum(t.get('transcript_word_count', 0) for t in tutorials)

    print("\n" + "=" * 50)
    print("YOUTUBE TRANSCRIPT STATISTICS")
    print("=" * 50)
    print(f"  Total tutorials:     {len(tutorials)}")
    print(f"  With metadata:       {with_metadata}")
    print(f"  With transcripts:    {with_transcript}")
    print(f"  Total transcript words: {total_words:,}")

    # List tutorials with transcripts
    if with_transcript > 0:
        print("\n" + "-" * 50)
        print("TUTORIALS WITH TRANSCRIPTS")
        print("-" * 50)
        for t in tutorials:
            if t.get('has_transcript'):
                title = t.get('title', t.get('video_id', 'Unknown'))[:40]
                words = t.get('transcript_word_count', 0)
                print(f"  - {title}: {words:,} words")

# =============================================================================
# CLI
# =============================================================================

def main():
    """Main CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("YouTube Metadata & Transcript Extractor")
        print("=" * 50)
        print("\nUsage:")
        print("  python youtube_metadata.py <command> [args]")
        print("\nCommands:")
        print("  all                  Process all tutorials in database")
        print("  all --force          Process all (including already fetched)")
        print("  all --no-transcript  Only fetch metadata, skip transcripts")
        print("  video <id_or_url>    Process a single video")
        print("  stats                Show transcript statistics")
        return

    cmd = sys.argv[1].lower()

    if cmd == 'all':
        skip_existing = '--force' not in sys.argv
        fetch_transcripts = '--no-transcript' not in sys.argv
        process_all_tutorials(skip_existing=skip_existing, fetch_transcripts=fetch_transcripts)

    elif cmd == 'video' and len(sys.argv) > 2:
        process_single_video(sys.argv[2])

    elif cmd == 'stats':
        show_stats()

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")

if __name__ == "__main__":
    main()
