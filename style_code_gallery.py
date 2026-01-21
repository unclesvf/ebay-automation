#!/usr/bin/env python3
"""
Style Code Gallery - Generate visual gallery of Midjourney --sref codes.

Usage:
    python style_code_gallery.py                    # Generate HTML gallery
    python style_code_gallery.py add 123456789      # Add new sref code
    python style_code_gallery.py add 123456789 --desc "Cyberpunk neon style"
    python style_code_gallery.py add 123456789 --image "path/to/example.jpg"
    python style_code_gallery.py list               # List all sref codes
    python style_code_gallery.py stats              # Show statistics
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Paths
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"
STYLES_DIR = KNOWLEDGE_BASE / "styles" / "midjourney-sref"
EXPORTS_DIR = KNOWLEDGE_BASE / "exports"
GALLERY_HTML = EXPORTS_DIR / "sref_gallery.html"


def load_database():
    """Load the master database."""
    if not MASTER_DB.exists():
        return {"styles": {"midjourney_sref": [], "midjourney_style": []}}

    with open(MASTER_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_database(db):
    """Save the master database."""
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    with open(MASTER_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2)


def add_sref_code(code, description=None, source=None, image_path=None):
    """Add a new sref code to the database."""
    db = load_database()

    # Normalize code (remove --sref prefix if present)
    code = code.replace('--sref', '').strip()

    # Check for duplicates
    existing_codes = [s['code'] for s in db.get('styles', {}).get('midjourney_sref', [])]
    if code in existing_codes:
        print(f"Sref code {code} already exists in database")
        return False

    # Create entry
    entry = {
        'code': code,
        'description': description,
        'date_found': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    # Handle image if provided
    if image_path:
        image_path = Path(image_path)
        if image_path.exists():
            # Create styles directory if needed
            STYLES_DIR.mkdir(parents=True, exist_ok=True)

            # Copy image to styles directory
            dest_path = STYLES_DIR / f"sref_{code}{image_path.suffix}"
            shutil.copy2(image_path, dest_path)
            entry['example_image'] = str(dest_path.relative_to(KNOWLEDGE_BASE))
            print(f"Copied example image to {dest_path}")

    # Add to database
    if 'styles' not in db:
        db['styles'] = {'midjourney_sref': [], 'midjourney_style': []}
    if 'midjourney_sref' not in db['styles']:
        db['styles']['midjourney_sref'] = []

    db['styles']['midjourney_sref'].append(entry)
    save_database(db)

    print(f"Added sref code: --sref {code}")
    if description:
        print(f"  Description: {description}")

    return True


def list_sref_codes():
    """List all sref codes in the database."""
    db = load_database()
    codes = db.get('styles', {}).get('midjourney_sref', [])

    if not codes:
        print("No sref codes found in database.")
        return

    print(f"\n{'='*60}")
    print(f"MIDJOURNEY SREF CODES ({len(codes)} total)")
    print(f"{'='*60}\n")

    for entry in codes:
        code = entry.get('code', 'unknown')
        desc = entry.get('description', 'No description')
        date = entry.get('date_found', 'Unknown date')
        has_image = 'example_image' in entry

        print(f"  --sref {code}")
        print(f"    Description: {desc}")
        print(f"    Date found: {date}")
        print(f"    Has example: {'Yes' if has_image else 'No'}")
        print()


def show_stats():
    """Show statistics about sref codes."""
    db = load_database()

    sref_codes = db.get('styles', {}).get('midjourney_sref', [])
    style_params = db.get('styles', {}).get('midjourney_style', [])

    print("\n=== STYLE CODE STATISTICS ===")
    print("="*40)
    print(f"\nTotal --sref codes: {len(sref_codes)}")
    print(f"Total --style params: {len(style_params)}")

    # Count with descriptions
    with_desc = sum(1 for s in sref_codes if s.get('description'))
    print(f"Codes with descriptions: {with_desc}")

    # Count with images
    with_images = sum(1 for s in sref_codes if s.get('example_image'))
    print(f"Codes with example images: {with_images}")

    # By source
    sources = {}
    for s in sref_codes:
        source_type = s.get('source', {}).get('type', 'unknown')
        sources[source_type] = sources.get(source_type, 0) + 1

    if sources:
        print(f"\nBy source:")
        for source, count in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"  - {source}: {count}")


def generate_gallery_html():
    """Generate an HTML gallery of sref codes."""
    db = load_database()
    codes = db.get('styles', {}).get('midjourney_sref', [])

    # Sort by date (newest first)
    codes_sorted = sorted(codes, key=lambda x: x.get('date_found', ''), reverse=True)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Midjourney SREF Gallery</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 40px;
        }}

        h1 {{
            font-size: 2.5em;
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}

        .subtitle {{
            color: #888;
            font-size: 1.1em;
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
        }}

        .stat {{
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            color: #e94560;
            font-weight: bold;
        }}

        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}

        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(233, 69, 96, 0.2);
        }}

        .card-image {{
            width: 100%;
            height: 200px;
            background: linear-gradient(45deg, #2a2a4a, #3a3a5a);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
            color: #444;
            position: relative;
        }}

        .card-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .card-image .placeholder {{
            opacity: 0.3;
        }}

        .card-content {{
            padding: 20px;
        }}

        .sref-code {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 1.3em;
            color: #e94560;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .copy-btn {{
            background: rgba(233, 69, 96, 0.2);
            border: 1px solid #e94560;
            color: #e94560;
            padding: 5px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.7em;
            transition: all 0.3s;
        }}

        .copy-btn:hover {{
            background: #e94560;
            color: white;
        }}

        .copy-btn.copied {{
            background: #4caf50;
            border-color: #4caf50;
            color: white;
        }}

        .description {{
            color: #aaa;
            font-size: 0.95em;
            line-height: 1.5;
            margin-bottom: 15px;
        }}

        .meta {{
            display: flex;
            justify-content: space-between;
            color: #666;
            font-size: 0.85em;
            border-top: 1px solid rgba(255,255,255,0.1);
            padding-top: 15px;
        }}

        .no-codes {{
            text-align: center;
            padding: 60px;
            color: #666;
        }}

        .no-codes h2 {{
            margin-bottom: 20px;
        }}

        .usage-tip {{
            background: rgba(233, 69, 96, 0.1);
            border: 1px solid rgba(233, 69, 96, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 40px;
            text-align: center;
        }}

        .usage-tip h3 {{
            color: #e94560;
            margin-bottom: 10px;
        }}

        .usage-tip code {{
            background: rgba(0,0,0,0.3);
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-block;
            margin-top: 10px;
            font-family: 'Consolas', monospace;
        }}

        footer {{
            text-align: center;
            padding: 40px;
            color: #555;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .stats {{
                flex-direction: column;
                gap: 20px;
            }}

            .gallery {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Midjourney SREF Gallery</h1>
            <p class="subtitle">Style Reference Codes Collection</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{len(codes)}</div>
                    <div class="stat-label">Total Codes</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{sum(1 for c in codes if c.get('description'))}</div>
                    <div class="stat-label">With Descriptions</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{sum(1 for c in codes if c.get('example_image'))}</div>
                    <div class="stat-label">With Examples</div>
                </div>
            </div>
        </header>

        <main>
'''

    if not codes:
        html += '''
            <div class="no-codes">
                <h2>No SREF Codes Yet</h2>
                <p>Add codes using: <code>python style_code_gallery.py add 123456789</code></p>
            </div>
'''
    else:
        html += '            <div class="gallery">\n'

        for entry in codes_sorted:
            code = entry.get('code', 'unknown')
            description = entry.get('description', 'No description available')
            date_found = entry.get('date_found', 'Unknown')
            example_image = entry.get('example_image', '')
            source = entry.get('source', {})
            source_type = source.get('type', 'manual')

            # Image section
            if example_image:
                image_html = f'<img src="../{example_image}" alt="Example for sref {code}">'
            else:
                image_html = '<div class="placeholder">No Preview</div>'

            html += f'''
                <div class="card">
                    <div class="card-image">
                        {image_html}
                    </div>
                    <div class="card-content">
                        <div class="sref-code">
                            --sref {code}
                            <button class="copy-btn" onclick="copyCode(this, '--sref {code}')">Copy</button>
                        </div>
                        <p class="description">{description}</p>
                        <div class="meta">
                            <span>Found: {date_found}</span>
                            <span>Source: {source_type}</span>
                        </div>
                    </div>
                </div>
'''

        html += '            </div>\n'

    html += '''
            <div class="usage-tip">
                <h3>How to Use SREF Codes</h3>
                <p>Add the code to any Midjourney prompt to apply the style:</p>
                <code>/imagine prompt: a beautiful landscape --sref 123456789</code>
            </div>
        </main>

        <footer>
            <p>Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + '''</p>
            <p>AI Knowledge Base - Style Code Gallery</p>
        </footer>
    </div>

    <script>
        function copyCode(btn, code) {
            navigator.clipboard.writeText(code).then(() => {
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = 'Copy';
                    btn.classList.remove('copied');
                }, 2000);
            });
        }
    </script>
</body>
</html>
'''

    # Ensure export directory exists
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write HTML file
    with open(GALLERY_HTML, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Gallery generated: {GALLERY_HTML}")
    print(f"Total codes: {len(codes)}")

    return str(GALLERY_HTML)


def main():
    parser = argparse.ArgumentParser(
        description='Midjourney SREF code gallery generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python style_code_gallery.py                           # Generate gallery
  python style_code_gallery.py add 123456789             # Add code
  python style_code_gallery.py add 123456789 --desc "Neon cyberpunk"
  python style_code_gallery.py add 123456789 --image example.jpg
  python style_code_gallery.py list                      # List all codes
  python style_code_gallery.py stats                     # Show statistics
        '''
    )

    subparsers = parser.add_subparsers(dest='command')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new sref code')
    add_parser.add_argument('code', help='The sref code (numbers only)')
    add_parser.add_argument('--desc', '-d', help='Description of the style')
    add_parser.add_argument('--image', '-i', help='Path to example image')
    add_parser.add_argument('--source', '-s', help='Source (e.g., twitter, reddit)')

    # List command
    subparsers.add_parser('list', help='List all sref codes')

    # Stats command
    subparsers.add_parser('stats', help='Show statistics')

    args = parser.parse_args()

    if args.command == 'add':
        source = {'type': args.source} if args.source else None
        add_sref_code(args.code, description=args.desc, source=source, image_path=args.image)
        # Regenerate gallery after adding
        generate_gallery_html()
    elif args.command == 'list':
        list_sref_codes()
    elif args.command == 'stats':
        show_stats()
    else:
        # Default: generate gallery
        generate_gallery_html()


if __name__ == '__main__':
    main()
