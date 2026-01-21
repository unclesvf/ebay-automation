#!/usr/bin/env python3
"""
Transcript Search - Full-text search across YouTube transcripts using SQLite FTS5.

Usage:
    python transcript_search.py "search query"
    python transcript_search.py "claude.md setup" --channel "AI with Avthar"
    python transcript_search.py "best practices" --topic claude-code
    python transcript_search.py --index          # Rebuild search index
    python transcript_search.py --stats          # Show index statistics
"""

import os
import sys
import json
import re
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# Paths
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / "tutorials" / "transcripts"
INDEX_DB = KNOWLEDGE_BASE / "tutorials" / "search_index.db"
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"


def create_database():
    """Create SQLite database with FTS5 virtual table."""
    conn = sqlite3.connect(INDEX_DB)
    cursor = conn.cursor()

    # Main transcripts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT UNIQUE NOT NULL,
            title TEXT,
            channel TEXT,
            duration INTEGER,
            upload_date TEXT,
            topics TEXT,
            indexed_at TEXT
        )
    ''')

    # FTS5 virtual table for full-text search (standalone, not linked to content table)
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
            video_id,
            timestamp_seconds UNINDEXED,
            text
        )
    ''')

    # Index for faster video lookups in main table
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transcripts_video
        ON transcripts(video_id)
    ''')

    conn.commit()
    return conn


def parse_transcript_file(filepath):
    """Parse transcript file and extract timestamped segments."""
    segments = []

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for timestamp format: [00:00:00] or [00:00] followed by text
    # Also handles plain text transcripts (group sentences into chunks)
    timestamp_pattern = re.compile(r'\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*(.+?)(?=\[\d{1,2}:\d{2}|\Z)', re.DOTALL)

    matches = timestamp_pattern.findall(content)

    if matches:
        # Timestamped transcript
        for timestamp_str, text in matches:
            # Convert timestamp to seconds
            parts = timestamp_str.split(':')
            if len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            else:
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

            clean_text = ' '.join(text.split())
            if clean_text:
                segments.append({
                    'timestamp': seconds,
                    'text': clean_text
                })
    else:
        # Plain text transcript - chunk into ~100 word segments
        words = content.split()
        chunk_size = 100

        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            # Estimate timestamp based on position (assume ~150 words/minute)
            estimated_seconds = (i / 150) * 60
            segments.append({
                'timestamp': estimated_seconds,
                'text': chunk
            })

    return segments


def get_video_metadata(video_id):
    """Get video metadata from master_db.json."""
    if not MASTER_DB.exists():
        return {}

    with open(MASTER_DB, 'r', encoding='utf-8') as f:
        db = json.load(f)

    for tutorial in db.get('tutorials', []):
        if tutorial.get('video_id') == video_id:
            return tutorial

    return {}


def index_transcripts(conn, force=False):
    """Index all transcripts into the FTS5 database."""
    cursor = conn.cursor()

    if not TRANSCRIPTS_DIR.exists():
        print(f"Transcripts directory not found: {TRANSCRIPTS_DIR}")
        return 0

    transcript_files = list(TRANSCRIPTS_DIR.glob("*.txt"))
    print(f"Found {len(transcript_files)} transcript files")

    indexed_count = 0

    for filepath in transcript_files:
        # Extract video_id from filename (format: video_id_title.txt)
        filename = filepath.stem
        video_id = filename.split('_')[0] if '_' in filename else filename

        # Check if already indexed
        if not force:
            cursor.execute('SELECT id FROM transcripts WHERE video_id = ?', (video_id,))
            if cursor.fetchone():
                print(f"  Skipping {video_id} (already indexed)")
                continue
        else:
            # Remove existing entries for re-indexing
            cursor.execute('DELETE FROM transcript_fts WHERE video_id = ?', (video_id,))
            cursor.execute('DELETE FROM transcripts WHERE video_id = ?', (video_id,))

        print(f"  Indexing {video_id}...")

        # Get metadata
        metadata = get_video_metadata(video_id)

        # Parse transcript
        segments = parse_transcript_file(filepath)

        if not segments:
            print(f"    No segments found in {filepath.name}")
            continue

        # Insert transcript record
        cursor.execute('''
            INSERT OR REPLACE INTO transcripts (video_id, title, channel, duration, upload_date, topics, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            video_id,
            metadata.get('title', filename),
            metadata.get('channel', 'Unknown'),
            metadata.get('duration', 0),
            metadata.get('upload_date', ''),
            json.dumps(metadata.get('topics', [])),
            datetime.now().isoformat()
        ))

        # Insert segments into FTS table
        for segment in segments:
            cursor.execute('''
                INSERT INTO transcript_fts (video_id, timestamp_seconds, text)
                VALUES (?, ?, ?)
            ''', (video_id, segment['timestamp'], segment['text']))

        indexed_count += 1
        print(f"    Added {len(segments)} segments")

    conn.commit()
    print(f"\nIndexed {indexed_count} transcripts")
    return indexed_count


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS or MM:SS format."""
    seconds = int(seconds)
    if seconds >= 3600:
        return f"{seconds // 3600}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"
    else:
        return f"{seconds // 60}:{seconds % 60:02d}"


def generate_youtube_url(video_id, timestamp_seconds):
    """Generate YouTube URL with timestamp."""
    timestamp = int(timestamp_seconds)
    return f"https://youtube.com/watch?v={video_id}&t={timestamp}s"


def escape_fts_query(query):
    """Escape special FTS5 characters in the query."""
    # FTS5 special characters that need escaping: . * + - ^ $ ( ) [ ] { } | \ : "
    # For simple queries, we quote terms that contain special chars
    words = query.split()
    escaped_words = []

    for word in words:
        # If word contains special chars and isn't already quoted, quote it
        if any(c in word for c in '.+-^$()[]{}|\\:') and not word.startswith('"'):
            escaped_words.append(f'"{word}"')
        else:
            escaped_words.append(word)

    return ' '.join(escaped_words)


def search_transcripts(conn, query, channel=None, topic=None, limit=20):
    """Search transcripts using FTS5."""
    cursor = conn.cursor()

    # Escape special characters in the query
    fts_query = escape_fts_query(query)

    # Base query with FTS5 match
    sql = '''
        SELECT
            fts.video_id,
            t.title,
            t.channel,
            t.topics,
            fts.timestamp_seconds,
            fts.text,
            bm25(transcript_fts) as score
        FROM transcript_fts fts
        JOIN transcripts t ON fts.video_id = t.video_id
        WHERE transcript_fts MATCH ?
    '''
    params = [fts_query]

    # Add filters
    if channel:
        sql += ' AND t.channel LIKE ?'
        params.append(f'%{channel}%')

    if topic:
        sql += ' AND t.topics LIKE ?'
        params.append(f'%{topic}%')

    sql += ' ORDER BY score LIMIT ?'
    params.append(limit)

    try:
        cursor.execute(sql, params)
        results = cursor.fetchall()
    except sqlite3.OperationalError as e:
        # Handle FTS5 syntax errors gracefully
        print(f"Search error: {e}")
        print("Tip: Use double quotes for exact phrases, OR for alternatives")
        return []

    return results


def display_results(results):
    """Display search results in a readable format."""
    if not results:
        print("No results found.")
        return

    print(f"\n{'='*80}")
    print(f"Found {len(results)} results")
    print(f"{'='*80}\n")

    current_video = None

    for video_id, title, channel, topics_json, timestamp, text, score in results:
        # Print video header when it changes
        if video_id != current_video:
            current_video = video_id
            topics = json.loads(topics_json) if topics_json else []
            print(f"\n[VIDEO] {title}")
            print(f"   Channel: {channel}")
            if topics:
                print(f"   Topics: {', '.join(topics)}")
            print(f"   {'-'*70}")

        # Print result
        timestamp_str = format_timestamp(timestamp)
        url = generate_youtube_url(video_id, timestamp)

        # Truncate text for display
        display_text = text[:200] + "..." if len(text) > 200 else text

        print(f"\n   [{timestamp_str}] {display_text}")
        print(f"   -> {url}")

    print(f"\n{'='*80}")


def show_stats(conn):
    """Show index statistics."""
    cursor = conn.cursor()

    print("\n=== TRANSCRIPT SEARCH INDEX STATISTICS ===")
    print("="*50)

    # Total transcripts
    cursor.execute('SELECT COUNT(*) FROM transcripts')
    total_transcripts = cursor.fetchone()[0]
    print(f"\nTotal transcripts indexed: {total_transcripts}")

    # Total segments
    cursor.execute('SELECT COUNT(*) FROM transcript_fts')
    total_segments = cursor.fetchone()[0]
    print(f"Total searchable segments: {total_segments}")

    # By channel
    cursor.execute('''
        SELECT channel, COUNT(*) as count
        FROM transcripts
        GROUP BY channel
        ORDER BY count DESC
    ''')
    channels = cursor.fetchall()

    if channels:
        print(f"\nBy Channel:")
        for channel, count in channels:
            print(f"  - {channel}: {count} videos")

    # By topic
    cursor.execute('SELECT topics FROM transcripts')
    all_topics = {}
    for (topics_json,) in cursor.fetchall():
        if topics_json:
            topics = json.loads(topics_json)
            for topic in topics:
                all_topics[topic] = all_topics.get(topic, 0) + 1

    if all_topics:
        print(f"\nBy Topic:")
        for topic, count in sorted(all_topics.items(), key=lambda x: -x[1])[:10]:
            print(f"  - {topic}: {count} videos")

    # Database size
    db_size = INDEX_DB.stat().st_size if INDEX_DB.exists() else 0
    print(f"\nDatabase size: {db_size / 1024:.1f} KB")
    print(f"Database location: {INDEX_DB}")


def export_results_json(results, output_file):
    """Export search results to JSON."""
    export_data = []

    for video_id, title, channel, topics_json, timestamp, text, score in results:
        export_data.append({
            'video_id': video_id,
            'title': title,
            'channel': channel,
            'topics': json.loads(topics_json) if topics_json else [],
            'timestamp': format_timestamp(timestamp),
            'timestamp_seconds': timestamp,
            'text': text,
            'url': generate_youtube_url(video_id, timestamp),
            'relevance_score': score
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2)

    print(f"Results exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Search YouTube transcripts using full-text search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python transcript_search.py "CLAUDE.md setup"
  python transcript_search.py "best practices" --channel "AI with Avthar"
  python transcript_search.py "MCP server" --topic claude-code
  python transcript_search.py "plan mode" --limit 10
  python transcript_search.py --index
  python transcript_search.py --index --force
  python transcript_search.py --stats

Search Tips:
  -Use quotes for exact phrases: "plan mode"
  -Use OR for alternatives: cursor OR vscode
  -Use * for prefix matching: config*
        '''
    )

    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--channel', '-c', help='Filter by channel name')
    parser.add_argument('--topic', '-t', help='Filter by topic')
    parser.add_argument('--limit', '-l', type=int, default=20, help='Max results (default: 20)')
    parser.add_argument('--index', '-i', action='store_true', help='Build/rebuild search index')
    parser.add_argument('--force', '-f', action='store_true', help='Force re-index all transcripts')
    parser.add_argument('--stats', '-s', action='store_true', help='Show index statistics')
    parser.add_argument('--export', '-e', help='Export results to JSON file')

    args = parser.parse_args()

    # Ensure directory exists
    INDEX_DB.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = create_database()

    try:
        if args.index:
            print("Building transcript search index...")
            index_transcripts(conn, force=args.force)
        elif args.stats:
            show_stats(conn)
        elif args.query:
            results = search_transcripts(
                conn,
                args.query,
                channel=args.channel,
                topic=args.topic,
                limit=args.limit
            )
            display_results(results)

            if args.export and results:
                export_results_json(results, args.export)
        else:
            parser.print_help()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
