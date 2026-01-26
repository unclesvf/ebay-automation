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

# Import centralized config
from kb_config import (
    get_logger, RateLimiter, ProgressTracker, backup_database,
    MASTER_DB, TRANSCRIPTS_DIR, METADATA_CACHE
)

# Setup logger
logger = get_logger("YouTubeMetadata")

# Rate limiter for YouTube API calls
rate_limiter = RateLimiter(delay=1.5, burst=3)  # Be gentle with YouTube

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
    logger.warning("youtube-transcript-api not installed. Run: pip install youtube-transcript-api")

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    logger.warning("yt-dlp not installed. Run: pip install yt-dlp")

# Paths - use centralized config
MASTER_DB_PATH = str(MASTER_DB)
TRANSCRIPTS_PATH = str(TRANSCRIPTS_DIR)
METADATA_CACHE_PATH = str(METADATA_CACHE)

# Permanent failure error types - these will NEVER succeed, don't retry
PERMANENT_FAILURE_ERRORS = {
    'transcripts_disabled',  # Uploader disabled transcripts
    'video_unavailable',     # Video is private/deleted
    'no_transcript',         # No transcript exists (e.g., foreign language)
}

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
    """Extract video ID from various YouTube URL formats.
    YouTube video IDs are always exactly 11 characters."""
    patterns = [
        r'youtube\.com/watch\?v=([\w\-]+)',
        r'youtu\.be/([\w\-]+)',
        r'youtube\.com/embed/([\w\-]+)',
        r'youtube\.com/v/([\w\-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)[:11]  # YouTube IDs are exactly 11 chars
            if len(video_id) == 11:
                return video_id
            return None  # Invalid if not 11 chars

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

def get_transcript(video_id, languages=['en', 'en-US', 'en-GB'], fallback_any_language=True):
    """
    Fetch transcript for a YouTube video.
    Returns dict with transcript text and metadata.

    Args:
        video_id: YouTube video ID
        languages: Preferred languages to try first (default English)
        fallback_any_language: If True, try to get any available language if preferred not found
    """
    if not TRANSCRIPT_API_AVAILABLE:
        return None

    try:
        # Create API instance (new API format)
        api = YouTubeTranscriptApi()

        # First, list available transcripts
        transcript_list = api.list(video_id)
        available = list(transcript_list)

        if not available:
            return {'video_id': video_id, 'error': 'no_transcript'}

        # Try to find preferred language (English)
        transcript_to_use = None
        language_used = None
        is_generated = False

        # First pass: look for manual English transcripts
        for t in available:
            if t.language_code in languages and not t.is_generated:
                transcript_to_use = t
                language_used = t.language_code
                is_generated = False
                break

        # Second pass: look for auto-generated English
        if not transcript_to_use:
            for t in available:
                if t.language_code.startswith('en') and t.is_generated:
                    transcript_to_use = t
                    language_used = t.language_code
                    is_generated = True
                    break

        # Third pass: fallback to any available language
        if not transcript_to_use and fallback_any_language:
            # Prefer manual over auto-generated
            for t in available:
                if not t.is_generated:
                    transcript_to_use = t
                    language_used = t.language_code
                    is_generated = False
                    logger.info(f"  Using non-English transcript: {t.language} ({t.language_code})")
                    break

            if not transcript_to_use:
                transcript_to_use = available[0]
                language_used = available[0].language_code
                is_generated = available[0].is_generated
                logger.info(f"  Using auto-generated non-English: {available[0].language}")

        if not transcript_to_use:
            return {'video_id': video_id, 'error': 'no_transcript'}

        # Fetch the selected transcript
        transcript_data = transcript_to_use.fetch()

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

        # Mark if translation is needed (non-English)
        needs_translation = not language_used.startswith('en')

        return {
            'video_id': video_id,
            'language': language_used,
            'transcript_type': 'auto' if is_generated else 'manual',
            'full_text': ' '.join(full_text),
            'segments': segments,
            'segment_count': len(segments),
            'word_count': len(' '.join(full_text).split()),
            'needs_translation': needs_translation,
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
    """Update a tutorial entry in the database with metadata and transcript info.

    CRITICAL: This function protects existing successful transcript data.
    If a tutorial already has has_transcript=True, we NEVER overwrite it with
    error states or null data. This prevents database corruption from temporary
    API failures (like IP rate limiting).

    Also marks permanent failures (transcripts_disabled, video_unavailable, no_transcript)
    so they are never retried.
    """
    for tutorial in db['tutorials']:
        if tutorial.get('video_id') == video_id:
            # Update metadata (always safe to update)
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

            # Update transcript info - WITH DATA PROTECTION
            existing_has_transcript = tutorial.get('has_transcript', False)

            if transcript_data and not transcript_data.get('error'):
                # Success case: always update with good data
                tutorial['has_transcript'] = True
                tutorial['transcript_language'] = transcript_data.get('language')
                tutorial['transcript_type'] = transcript_data.get('transcript_type')
                tutorial['transcript_word_count'] = transcript_data.get('word_count')
                tutorial['transcript_fetched'] = transcript_data.get('fetched_at')
                # Track if translation is needed (non-English transcripts)
                if transcript_data.get('needs_translation'):
                    tutorial['needs_translation'] = True
                elif 'needs_translation' in tutorial:
                    del tutorial['needs_translation']
                # Clear any previous error and permanent failure flag
                if 'transcript_error' in tutorial:
                    del tutorial['transcript_error']
                if 'transcript_permanent_failure' in tutorial:
                    del tutorial['transcript_permanent_failure']
            elif transcript_data and transcript_data.get('error'):
                error_type = transcript_data.get('error')
                is_permanent = error_type in PERMANENT_FAILURE_ERRORS

                # Error case: ONLY update if we don't already have a successful transcript
                if not existing_has_transcript:
                    tutorial['has_transcript'] = False
                    tutorial['transcript_error'] = error_type
                    # Mark permanent failures so they're never retried
                    if is_permanent:
                        tutorial['transcript_permanent_failure'] = True
                        logger.info(f"  Marked {video_id} as permanent failure: {error_type}")
                else:
                    # PROTECT existing data - log but don't overwrite
                    logger.warning(f"  Skipping error update for {video_id} - preserving existing transcript")

            return True

    return False

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_all_tutorials(skip_existing=True, fetch_transcripts=True, retry_failed=False):
    """Process all tutorials in the database.

    Args:
        skip_existing: Skip tutorials that already have metadata fetched
        fetch_transcripts: Whether to fetch transcripts (default True)
        retry_failed: Only process videos that failed to get transcripts (safe retry mode)
    """
    logger.info("=" * 70)
    logger.info("YOUTUBE METADATA & TRANSCRIPT EXTRACTOR")
    logger.info("=" * 70)

    if retry_failed:
        logger.info("MODE: Retry failed transcripts only (existing data protected)")

    # Backup database before processing
    backup_path = backup_database(reason="youtube_fetch")
    if backup_path:
        logger.info(f"Database backed up to: {backup_path}")

    db = load_db()
    if not db:
        logger.error("Could not load database")
        return

    cache = load_metadata_cache()
    tutorials = db.get('tutorials', [])

    if not tutorials:
        logger.info("No tutorials found in database.")
        return

    # Count tutorials that need processing
    if retry_failed:
        # Only process videos without transcripts AND not permanently failed
        to_process = [t for t in tutorials if t.get('video_id') and
                      not t.get('has_transcript', False) and
                      not t.get('transcript_permanent_failure', False)]
        # Also count permanent failures for reporting
        permanent_failures = [t for t in tutorials if t.get('transcript_permanent_failure', False)]
        logger.info(f"Found {len(tutorials)} tutorials, {len(to_process)} can be retried")
        if permanent_failures:
            logger.info(f"Skipping {len(permanent_failures)} permanent failures (transcripts disabled/unavailable)")
    else:
        to_process = [t for t in tutorials if t.get('video_id') and
                      (not skip_existing or not t.get('metadata_fetched'))]
        logger.info(f"Found {len(tutorials)} tutorials, {len(to_process)} need processing")

    if not to_process:
        logger.info("All tutorials already processed. Use --force to reprocess.")
        return

    # Initialize progress tracker
    tracker = ProgressTracker(total=len(to_process), description="YouTube fetch")

    processed = 0
    metadata_fetched = 0
    transcripts_fetched = 0
    errors = 0

    for i, tutorial in enumerate(tutorials):
        video_id = tutorial.get('video_id')
        if not video_id:
            continue

        # Check if should skip this tutorial
        if retry_failed:
            # In retry mode, skip videos that already have transcripts
            if tutorial.get('has_transcript', False):
                continue
            # Also skip permanent failures (transcripts disabled, video unavailable, etc.)
            if tutorial.get('transcript_permanent_failure', False):
                continue
        elif skip_existing and tutorial.get('metadata_fetched'):
            # In normal mode, skip already processed videos
            continue

        logger.info(f"Processing: {video_id}")

        # Rate limit API calls
        rate_limiter.wait()

        # Fetch metadata
        metadata = None

        if video_id in cache:
            metadata = cache[video_id]
            logger.info(f"  Using cached metadata: {metadata.get('title', 'Unknown')[:50]}")
        else:
            metadata = get_video_metadata(video_id)
            if metadata:
                cache[video_id] = metadata
                logger.info(f"  Title: {metadata.get('title', 'Unknown')[:50]}")
                metadata_fetched += 1
            else:
                logger.warning(f"  Failed to fetch metadata")
                errors += 1

        # Fetch transcript
        transcript_data = None
        if fetch_transcripts:
            rate_limiter.wait()  # Rate limit transcript API too
            transcript_data = get_transcript(video_id)

            if transcript_data and not transcript_data.get('error'):
                logger.info(f"  Transcript: {transcript_data.get('word_count', 0)} words")
                transcripts_fetched += 1

                # Save transcript file
                filepath = save_transcript_file(video_id, transcript_data, metadata)
                logger.info(f"  Saved: {os.path.basename(filepath)}")
            elif transcript_data and transcript_data.get('error'):
                logger.warning(f"  Transcript error: {transcript_data.get('error')}")

        # Update database
        update_tutorial_in_db(db, video_id, metadata, transcript_data)
        processed += 1

        # Update progress
        tracker.update(message=f"{video_id}")

    # Save everything
    save_db(db)
    save_metadata_cache(cache)
    tracker.finish()

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

    # Separate permanent failures from retryable failures
    without_transcript = [t for t in tutorials if not t.get('has_transcript', False)]
    permanent_failures = [t for t in without_transcript if t.get('transcript_permanent_failure', False)]
    retryable_failures = [t for t in without_transcript if not t.get('transcript_permanent_failure', False)]

    # Show retryable failures (candidates for --retry-failed)
    if retryable_failures:
        print("\n" + "-" * 50)
        print(f"RETRYABLE FAILURES ({len(retryable_failures)} - use --retry-failed)")
        print("-" * 50)
        for t in retryable_failures:
            title = t.get('title', t.get('video_id', 'Unknown'))[:40]
            error = t.get('transcript_error', 'not attempted')
            # Truncate long IP blocking error messages
            if 'YouTube is blocking' in str(error):
                error = 'IP rate limited (temporary)'
            print(f"  - {title}: {error}")

    # Show permanent failures (will never be retried)
    if permanent_failures:
        print("\n" + "-" * 50)
        print(f"PERMANENT FAILURES ({len(permanent_failures)} - will not retry)")
        print("-" * 50)
        for t in permanent_failures:
            title = t.get('title', t.get('video_id', 'Unknown'))[:40]
            error = t.get('transcript_error', 'unknown')
            print(f"  - {title}: {error}")

def mark_permanent_failures():
    """Mark existing videos with permanent failure errors in the database.

    This is a one-time migration to flag videos that have errors like
    'transcripts_disabled', 'no_transcript', 'video_unavailable' so they
    won't be retried in the future.
    """
    db = load_db()
    if not db:
        print("ERROR: Could not load database")
        return

    tutorials = db.get('tutorials', [])
    marked = 0

    for tutorial in tutorials:
        # Check if already marked
        if tutorial.get('transcript_permanent_failure'):
            continue

        # Check if has a permanent failure error
        error = tutorial.get('transcript_error', '')
        if error in PERMANENT_FAILURE_ERRORS:
            tutorial['transcript_permanent_failure'] = True
            title = tutorial.get('title', tutorial.get('video_id', 'Unknown'))[:40]
            print(f"  Marked: {title} ({error})")
            marked += 1

    if marked > 0:
        save_db(db)
        print(f"\nMarked {marked} videos as permanent failures.")
    else:
        print("No videos needed to be marked.")

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
        print("  all --retry-failed   SAFE: Only retry videos without transcripts")
        print("  all --no-transcript  Only fetch metadata, skip transcripts")
        print("  video <id_or_url>    Process a single video")
        print("  stats                Show transcript statistics")
        print("  mark-permanent       Mark existing permanent failures (one-time)")
        print("\nData Protection:")
        print("  --retry-failed is the SAFE way to retry. It only processes videos")
        print("  that don't have transcripts yet, protecting existing data from")
        print("  being overwritten by temporary API errors (rate limiting, etc.)")
        return

    cmd = sys.argv[1].lower()

    if cmd == 'all':
        skip_existing = '--force' not in sys.argv
        fetch_transcripts = '--no-transcript' not in sys.argv
        retry_failed = '--retry-failed' in sys.argv
        process_all_tutorials(skip_existing=skip_existing, fetch_transcripts=fetch_transcripts,
                              retry_failed=retry_failed)

    elif cmd == 'video' and len(sys.argv) > 2:
        process_single_video(sys.argv[2])

    elif cmd == 'stats':
        show_stats()

    elif cmd == 'mark-permanent':
        mark_permanent_failures()

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")

if __name__ == "__main__":
    main()
