"""
YouTube Title Enrichment Script
Post-processing script to fetch missing YouTube video titles using oEmbed API.

Run after main email extraction to populate null video titles.
Usage: python enrich_titles.py [--dry-run] [--limit N]
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

MASTER_DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'

def get_video_id(url_or_id):
    """Extract video ID from URL or return if already an ID."""
    if not url_or_id:
        return None
    
    # Already a video ID
    if re.match(r'^[\w\-]{11}$', url_or_id):
        return url_or_id
    
    # Extract from various URL formats
    patterns = [
        r'youtube\.com/watch\?v=([\w\-]{11})',
        r'youtu\.be/([\w\-]{11})',
        r'youtube\.com/embed/([\w\-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None


def fetch_youtube_title(video_id):
    """Fetch video title using YouTube oEmbed API (free, no auth required)."""
    if not video_id:
        return None
    
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('title')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # Video not found or private
        print(f"  HTTP Error {e.code} for {video_id}")
        return None
    except Exception as e:
        print(f"  Error fetching {video_id}: {e}")
        return None


def fetch_title_with_retry(video_id, retries=2):
    """Fetch title with retry logic."""
    for attempt in range(retries):
        title = fetch_youtube_title(video_id)
        if title:
            return title
        if attempt < retries - 1:
            time.sleep(0.5)  # Small delay before retry
    return None


def enrich_titles(dry_run=False, limit=None, concurrent=5):
    """Find and enrich all tutorials with missing titles."""
    
    if not os.path.exists(MASTER_DB_PATH):
        print(f"Database not found: {MASTER_DB_PATH}")
        return
    
    print("Loading database...")
    with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)
    
    tutorials = db.get('tutorials', [])
    
    # Find tutorials with missing titles
    missing_titles = []
    for i, tutorial in enumerate(tutorials):
        title = tutorial.get('title')
        if not title or title.lower() in ['none', 'null', 'unknown', 'unknown title']:
            video_id = tutorial.get('video_id') or get_video_id(tutorial.get('url', ''))
            if video_id:
                missing_titles.append((i, video_id))
    
    print(f"Found {len(missing_titles)} videos with missing titles")
    
    if not missing_titles:
        print("All videos have titles. Nothing to do.")
        return
    
    if limit:
        missing_titles = missing_titles[:limit]
        print(f"Processing first {limit} videos...")
    
    if dry_run:
        print("\n[DRY RUN] Would fetch titles for:")
        for idx, vid_id in missing_titles[:10]:
            print(f"  - {vid_id}")
        if len(missing_titles) > 10:
            print(f"  ... and {len(missing_titles) - 10} more")
        return
    
    # Fetch titles concurrently
    print(f"\nFetching titles (max {concurrent} concurrent requests)...")
    updated_count = 0
    failed_count = 0
    
    def fetch_for_tutorial(item):
        idx, video_id = item
        title = fetch_title_with_retry(video_id)
        return idx, video_id, title
    
    with ThreadPoolExecutor(max_workers=concurrent) as executor:
        futures = {executor.submit(fetch_for_tutorial, item): item for item in missing_titles}
        
        for i, future in enumerate(as_completed(futures)):
            idx, video_id, title = future.result()
            
            if title:
                tutorials[idx]['title'] = title
                updated_count += 1
                print(f"  [{i+1}/{len(missing_titles)}] ✓ {video_id}: {title[:50]}...")
            else:
                failed_count += 1
                print(f"  [{i+1}/{len(missing_titles)}] ✗ {video_id}: Could not fetch title")
            
            # Rate limiting - be nice to YouTube
            if (i + 1) % 10 == 0:
                time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"Results: {updated_count} updated, {failed_count} failed")
    
    if updated_count > 0:
        print("\nSaving database...")
        with open(MASTER_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print("Database saved!")
        print("\nNext steps:")
        print("  1. Run: python ingest_db.py")
        print("  2. Restart server: python server.py")
    else:
        print("\nNo changes made.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich YouTube video titles in master_db.json')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--limit', type=int, help='Limit number of videos to process')
    parser.add_argument('--concurrent', type=int, default=5, help='Number of concurrent requests (default: 5)')
    
    args = parser.parse_args()
    
    enrich_titles(dry_run=args.dry_run, limit=args.limit, concurrent=args.concurrent)
