"""
Knowledge DB - Database manager for AI Knowledge Base
Provides add, query, dedupe, export, and management functions.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import re
import csv
from datetime import datetime
from collections import defaultdict

# Paths
MASTER_DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'
URL_CACHE_PATH = r'D:\AI-Knowledge-Base\url_cache.json'
EXPORTS_PATH = r'D:\AI-Knowledge-Base\exports'

# =============================================================================
# DATABASE LOADING/SAVING
# =============================================================================

def load_db():
    """Load the master database."""
    if os.path.exists(MASTER_DB_PATH):
        with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return create_empty_db()

def save_db(db):
    """Save the master database."""
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    update_total_entries(db)
    with open(MASTER_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    return True

def create_empty_db():
    """Create an empty database structure."""
    return {
        "metadata": {
            "created": datetime.now().strftime('%Y-%m-%d'),
            "last_updated": datetime.now().strftime('%Y-%m-%d'),
            "total_entries": 0,
            "version": "1.0"
        },
        "models": {
            "tts": [],
            "image_cloud": [],
            "image_local": []
        },
        "repositories": {
            "github": [],
            "huggingface": []
        },
        "tutorials": [],
        "styles": {
            "midjourney_sref": [],
            "midjourney_style": []
        },
        "prompts": {
            "system_prompts": [],
            "techniques": []
        },
        "coding_tools": []
    }

def update_total_entries(db):
    """Update the total entries count."""
    total = (
        len(db['repositories']['github']) +
        len(db['repositories']['huggingface']) +
        len(db['tutorials']) +
        len(db['styles']['midjourney_sref']) +
        len(db['styles'].get('midjourney_style', [])) +
        len(db['models']['tts']) +
        len(db['models']['image_cloud']) +
        len(db['models']['image_local']) +
        len(db['prompts'].get('system_prompts', [])) +
        len(db['prompts'].get('techniques', [])) +
        len(db['coding_tools'])
    )
    db['metadata']['total_entries'] = total
    return total

# =============================================================================
# ADD FUNCTIONS
# =============================================================================

def add_github_repo(db, url, name=None, owner=None, category='unknown', source=None):
    """Add a GitHub repository to the database."""
    # Parse URL if name/owner not provided
    if not name or not owner:
        match = re.search(r'github\.com/([\w\-\.]+)/([\w\-\.]+)', url)
        if match:
            owner = owner or match.group(1)
            name = name or match.group(2)

    # Check for duplicates
    for repo in db['repositories']['github']:
        if repo['url'] == url or (repo['owner'] == owner and repo['name'] == name):
            return False, "Repository already exists"

    entry = {
        'url': url if url.startswith('github.com') else f"github.com/{owner}/{name}",
        'name': name,
        'owner': owner,
        'category': category,
        'date_found': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    db['repositories']['github'].append(entry)
    return True, f"Added: {owner}/{name}"

def add_huggingface(db, url, name=None, owner=None, source=None):
    """Add a HuggingFace model/dataset to the database."""
    if not name or not owner:
        match = re.search(r'huggingface\.co/([\w\-\.]+)/([\w\-\.]+)', url)
        if match:
            owner = owner or match.group(1)
            name = name or match.group(2)

    for ref in db['repositories']['huggingface']:
        if ref['url'] == url:
            return False, "Model already exists"

    entry = {
        'url': url if url.startswith('huggingface.co') else f"huggingface.co/{owner}/{name}",
        'name': name,
        'owner': owner,
        'date_found': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    db['repositories']['huggingface'].append(entry)
    return True, f"Added: {owner}/{name}"

def add_tutorial(db, url, video_id=None, title=None, topic='unknown', source=None):
    """Add a YouTube tutorial to the database."""
    if not video_id:
        match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)', url)
        if match:
            video_id = match.group(1)

    for tutorial in db['tutorials']:
        if tutorial.get('video_id') == video_id:
            return False, "Tutorial already exists"

    entry = {
        'video_id': video_id,
        'url': url,
        'title': title,
        'topic': topic,
        'date_found': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    db['tutorials'].append(entry)
    return True, f"Added tutorial: {video_id}"

def add_sref_code(db, code, description=None, source=None):
    """Add a Midjourney --sref code to the database."""
    code = str(code)

    for style in db['styles']['midjourney_sref']:
        if style['code'] == code:
            return False, "Style code already exists"

    entry = {
        'code': code,
        'description': description,
        'date_found': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    db['styles']['midjourney_sref'].append(entry)
    return True, f"Added --sref {code}"

def add_model(db, model_type, name, url=None, local_capable=False, notes=None, source=None):
    """Add an AI model to the database."""
    valid_types = ['tts', 'image_cloud', 'image_local']
    if model_type not in valid_types:
        return False, f"Invalid model type. Use: {valid_types}"

    for model in db['models'][model_type]:
        if model['name'].lower() == name.lower():
            return False, f"Model {name} already exists in {model_type}"

    entry = {
        'name': name,
        'url': url,
        'local_capable': local_capable,
        'notes': notes,
        'date_found': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    db['models'][model_type].append(entry)
    return True, f"Added {name} to {model_type}"

def add_coding_tool(db, name, url=None, category=None, notes=None, source=None):
    """Add a coding tool to the database."""
    for tool in db['coding_tools']:
        if tool['name'].lower() == name.lower():
            return False, f"Tool {name} already exists"

    entry = {
        'name': name,
        'url': url,
        'category': category,
        'notes': notes,
        'date_found': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    db['coding_tools'].append(entry)
    return True, f"Added coding tool: {name}"

# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def search_all(db, query, case_sensitive=False):
    """Search all entries for a query string."""
    results = {
        'github': [],
        'huggingface': [],
        'tutorials': [],
        'styles': [],
        'models': [],
        'coding_tools': []
    }

    if not case_sensitive:
        query = query.lower()

    def matches(text):
        if text is None:
            return False
        if not case_sensitive:
            return query in str(text).lower()
        return query in str(text)

    # Search GitHub repos
    for repo in db['repositories']['github']:
        if matches(repo.get('url')) or matches(repo.get('name')) or matches(repo.get('owner')):
            results['github'].append(repo)

    # Search HuggingFace
    for ref in db['repositories']['huggingface']:
        if matches(ref.get('url')) or matches(ref.get('name')) or matches(ref.get('owner')):
            results['huggingface'].append(ref)

    # Search tutorials
    for tutorial in db['tutorials']:
        if matches(tutorial.get('url')) or matches(tutorial.get('title')) or matches(tutorial.get('topic')):
            results['tutorials'].append(tutorial)

    # Search styles
    for style in db['styles']['midjourney_sref']:
        if matches(style.get('code')) or matches(style.get('description')):
            results['styles'].append(style)

    # Search models
    for model_type in ['tts', 'image_cloud', 'image_local']:
        for model in db['models'][model_type]:
            if matches(model.get('name')) or matches(model.get('notes')):
                results['models'].append({**model, 'type': model_type})

    # Search coding tools
    for tool in db['coding_tools']:
        if matches(tool.get('name')) or matches(tool.get('notes')) or matches(tool.get('category')):
            results['coding_tools'].append(tool)

    return results

def get_by_category(db, category):
    """Get all entries of a specific category."""
    category = category.lower()

    if category == 'github':
        return db['repositories']['github']
    elif category == 'huggingface':
        return db['repositories']['huggingface']
    elif category == 'tutorials':
        return db['tutorials']
    elif category == 'sref' or category == 'styles':
        return db['styles']['midjourney_sref']
    elif category == 'tts':
        return db['models']['tts']
    elif category == 'image_cloud':
        return db['models']['image_cloud']
    elif category == 'image_local':
        return db['models']['image_local']
    elif category == 'coding_tools':
        return db['coding_tools']
    else:
        return None

def get_by_date(db, date_str):
    """Get all entries found on a specific date."""
    results = []

    for repo in db['repositories']['github']:
        if repo.get('date_found') == date_str:
            results.append({'type': 'github', **repo})

    for ref in db['repositories']['huggingface']:
        if ref.get('date_found') == date_str:
            results.append({'type': 'huggingface', **ref})

    for tutorial in db['tutorials']:
        if tutorial.get('date_found') == date_str:
            results.append({'type': 'tutorial', **tutorial})

    for style in db['styles']['midjourney_sref']:
        if style.get('date_found') == date_str:
            results.append({'type': 'sref', **style})

    return results

def get_stats(db):
    """Get database statistics."""
    stats = {
        'total_entries': db['metadata']['total_entries'],
        'last_updated': db['metadata']['last_updated'],
        'created': db['metadata']['created'],
        'github_repos': len(db['repositories']['github']),
        'huggingface_models': len(db['repositories']['huggingface']),
        'tutorials': len(db['tutorials']),
        'sref_codes': len(db['styles']['midjourney_sref']),
        'tts_models': len(db['models']['tts']),
        'image_cloud_models': len(db['models']['image_cloud']),
        'image_local_models': len(db['models']['image_local']),
        'coding_tools': len(db['coding_tools'])
    }
    return stats

# =============================================================================
# DEDUPE FUNCTIONS
# =============================================================================

def dedupe_github_repos(db, dry_run=True):
    """
    Remove duplicate GitHub repos, preferring longer/more complete URLs.
    Returns list of removed entries.
    """
    repos = db['repositories']['github']
    to_remove = []
    seen = {}  # owner/name -> best entry

    for repo in repos:
        key = f"{repo['owner']}/{repo['name']}".lower()
        url = repo['url']

        if key in seen:
            existing = seen[key]
            # Prefer longer URL (more complete)
            if len(url) > len(existing['url']):
                to_remove.append(existing)
                seen[key] = repo
            else:
                to_remove.append(repo)
        else:
            seen[key] = repo

    if not dry_run:
        for repo in to_remove:
            if repo in db['repositories']['github']:
                db['repositories']['github'].remove(repo)

    return to_remove

def dedupe_huggingface(db, dry_run=True):
    """Remove duplicate HuggingFace entries, preferring longer URLs."""
    refs = db['repositories']['huggingface']
    to_remove = []
    seen = {}

    for ref in refs:
        key = f"{ref['owner']}/{ref['name']}".lower()
        url = ref['url']

        if key in seen:
            existing = seen[key]
            if len(url) > len(existing['url']):
                to_remove.append(existing)
                seen[key] = ref
            else:
                to_remove.append(ref)
        else:
            seen[key] = ref

    if not dry_run:
        for ref in to_remove:
            if ref in db['repositories']['huggingface']:
                db['repositories']['huggingface'].remove(ref)

    return to_remove

def dedupe_all(db, dry_run=True):
    """Run all deduplication checks."""
    results = {
        'github': dedupe_github_repos(db, dry_run),
        'huggingface': dedupe_huggingface(db, dry_run)
    }
    return results

def find_truncated_urls(db):
    """Find URLs that appear to be truncated."""
    truncated = []

    # Common truncation indicators
    indicators = ['...', '\u2026', '/sta', '/st']

    for repo in db['repositories']['github']:
        url = repo['url']
        name = repo['name']
        if any(url.endswith(ind) or name.endswith(ind) for ind in indicators):
            truncated.append({'type': 'github', 'entry': repo})
        elif len(name) <= 3:  # Very short name likely truncated
            truncated.append({'type': 'github', 'entry': repo, 'reason': 'short_name'})

    for ref in db['repositories']['huggingface']:
        url = ref['url']
        name = ref['name']
        if any(url.endswith(ind) or name.endswith(ind) for ind in indicators):
            truncated.append({'type': 'huggingface', 'entry': ref})

    return truncated

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_to_csv(db, filepath, category=None):
    """Export database entries to CSV."""
    rows = []

    if category is None or category == 'github':
        for repo in db['repositories']['github']:
            rows.append({
                'type': 'github',
                'name': repo.get('name'),
                'owner': repo.get('owner'),
                'url': f"https://{repo.get('url')}",
                'date_found': repo.get('date_found'),
                'category': repo.get('category')
            })

    if category is None or category == 'huggingface':
        for ref in db['repositories']['huggingface']:
            rows.append({
                'type': 'huggingface',
                'name': ref.get('name'),
                'owner': ref.get('owner'),
                'url': f"https://{ref.get('url')}",
                'date_found': ref.get('date_found'),
                'category': ''
            })

    if category is None or category == 'tutorials':
        for tutorial in db['tutorials']:
            rows.append({
                'type': 'tutorial',
                'name': tutorial.get('title') or tutorial.get('video_id'),
                'owner': '',
                'url': f"https://{tutorial.get('url')}",
                'date_found': tutorial.get('date_found'),
                'category': tutorial.get('topic')
            })

    if category is None or category == 'sref':
        for style in db['styles']['midjourney_sref']:
            rows.append({
                'type': 'sref',
                'name': f"--sref {style.get('code')}",
                'owner': '',
                'url': '',
                'date_found': style.get('date_found'),
                'category': style.get('description', '')
            })

    if rows:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['type', 'name', 'owner', 'url', 'date_found', 'category'])
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    return 0

def export_urls_txt(db, filepath):
    """Export all URLs to a plain text file."""
    urls = []

    for repo in db['repositories']['github']:
        urls.append(f"https://{repo['url']}")

    for ref in db['repositories']['huggingface']:
        urls.append(f"https://{ref['url']}")

    for tutorial in db['tutorials']:
        urls.append(f"https://{tutorial['url']}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(urls))

    return len(urls)

def export_markdown(db, filepath):
    """Export database to a markdown document."""
    lines = [
        f"# AI Knowledge Base",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"Total entries: {db['metadata']['total_entries']}",
        f"",
    ]

    # GitHub repos
    lines.append("## GitHub Repositories")
    lines.append("")
    for repo in db['repositories']['github']:
        lines.append(f"- [{repo['owner']}/{repo['name']}](https://{repo['url']})")
    lines.append("")

    # HuggingFace
    lines.append("## HuggingFace Models")
    lines.append("")
    for ref in db['repositories']['huggingface']:
        lines.append(f"- [{ref['owner']}/{ref['name']}](https://{ref['url']})")
    lines.append("")

    # Tutorials
    lines.append("## Tutorials")
    lines.append("")
    for tutorial in db['tutorials']:
        title = tutorial.get('title') or tutorial.get('video_id')
        lines.append(f"- [{title}](https://{tutorial['url']})")
    lines.append("")

    # Style codes
    if db['styles']['midjourney_sref']:
        lines.append("## Midjourney Style Codes")
        lines.append("")
        for style in db['styles']['midjourney_sref']:
            desc = f" - {style['description']}" if style.get('description') else ""
            lines.append(f"- `--sref {style['code']}`{desc}")
        lines.append("")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return len(lines)

# =============================================================================
# DELETE FUNCTIONS
# =============================================================================

def delete_github_repo(db, url=None, name=None, owner=None):
    """Delete a GitHub repo by URL or owner/name."""
    for i, repo in enumerate(db['repositories']['github']):
        if url and repo['url'] == url:
            return db['repositories']['github'].pop(i)
        if name and owner and repo['name'] == name and repo['owner'] == owner:
            return db['repositories']['github'].pop(i)
    return None

def delete_by_index(db, category, index):
    """Delete an entry by category and index."""
    entries = get_by_category(db, category)
    if entries and 0 <= index < len(entries):
        return entries.pop(index)
    return None

# =============================================================================
# CLI INTERFACE
# =============================================================================

def print_results(results, title="Results"):
    """Pretty print search results."""
    print(f"\n{title}")
    print("=" * 60)

    total = 0
    for category, items in results.items():
        if items:
            print(f"\n{category.upper()} ({len(items)})")
            print("-" * 40)
            for item in items[:10]:  # Limit to 10 per category
                if 'url' in item:
                    print(f"  - {item.get('name', item.get('url', 'Unknown'))}")
                    print(f"    {item.get('url', '')}")
                elif 'code' in item:
                    print(f"  - --sref {item['code']}")
                else:
                    print(f"  - {item.get('name', 'Unknown')}")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more")
            total += len(items)

    print(f"\nTotal: {total} results")

def print_stats(stats):
    """Pretty print database statistics."""
    print("\n" + "=" * 60)
    print("AI KNOWLEDGE BASE STATISTICS")
    print("=" * 60)
    print(f"  Created:        {stats['created']}")
    print(f"  Last updated:   {stats['last_updated']}")
    print(f"  Total entries:  {stats['total_entries']}")
    print("-" * 60)
    print(f"  GitHub repos:       {stats['github_repos']}")
    print(f"  HuggingFace models: {stats['huggingface_models']}")
    print(f"  Tutorials:          {stats['tutorials']}")
    print(f"  Style codes:        {stats['sref_codes']}")
    print(f"  TTS models:         {stats['tts_models']}")
    print(f"  Image cloud models: {stats['image_cloud_models']}")
    print(f"  Image local models: {stats['image_local_models']}")
    print(f"  Coding tools:       {stats['coding_tools']}")
    print("=" * 60)

def main():
    """Main CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Knowledge DB - AI Knowledge Base Manager")
        print("=" * 50)
        print("\nUsage:")
        print("  python knowledge_db.py <command> [args]")
        print("\nCommands:")
        print("  stats                    Show database statistics")
        print("  search <query>           Search all entries")
        print("  list <category>          List entries by category")
        print("                           (github, huggingface, tutorials, sref, coding_tools)")
        print("  dedupe                   Find duplicate entries (dry run)")
        print("  dedupe --apply           Remove duplicates")
        print("  truncated                Find truncated URLs")
        print("  export csv <file>        Export to CSV")
        print("  export md <file>         Export to Markdown")
        print("  export urls <file>       Export URLs to text file")
        print("  add github <url>         Add a GitHub repo")
        print("  add huggingface <url>    Add a HuggingFace model")
        print("  add sref <code>          Add a --sref code")
        return

    db = load_db()
    cmd = sys.argv[1].lower()

    if cmd == 'stats':
        stats = get_stats(db)
        print_stats(stats)

    elif cmd == 'search' and len(sys.argv) > 2:
        query = ' '.join(sys.argv[2:])
        results = search_all(db, query)
        print_results(results, f"Search: '{query}'")

    elif cmd == 'list' and len(sys.argv) > 2:
        category = sys.argv[2]
        entries = get_by_category(db, category)
        if entries is not None:
            print(f"\n{category.upper()} ({len(entries)} entries)")
            print("=" * 60)
            for i, entry in enumerate(entries):
                if 'url' in entry:
                    name = entry.get('name', entry.get('owner', 'Unknown'))
                    print(f"  [{i}] {name}")
                    print(f"      https://{entry['url']}")
                elif 'code' in entry:
                    print(f"  [{i}] --sref {entry['code']}")
                else:
                    print(f"  [{i}] {entry.get('name', 'Unknown')}")
        else:
            print(f"Unknown category: {category}")

    elif cmd == 'dedupe':
        dry_run = '--apply' not in sys.argv
        results = dedupe_all(db, dry_run=dry_run)

        print("\nDEDUPLICATION RESULTS")
        print("=" * 60)

        total = 0
        for category, dupes in results.items():
            if dupes:
                print(f"\n{category.upper()} ({len(dupes)} duplicates)")
                for dupe in dupes:
                    print(f"  - {dupe.get('url', dupe.get('name', 'Unknown'))}")
                total += len(dupes)

        if total == 0:
            print("\nNo duplicates found.")
        elif dry_run:
            print(f"\nFound {total} duplicates. Run with --apply to remove them.")
        else:
            save_db(db)
            print(f"\nRemoved {total} duplicates. Database saved.")

    elif cmd == 'truncated':
        truncated = find_truncated_urls(db)
        print("\nPOTENTIALLY TRUNCATED URLs")
        print("=" * 60)
        if truncated:
            for item in truncated:
                entry = item['entry']
                print(f"  [{item['type']}] {entry.get('url', entry.get('name', 'Unknown'))}")
                if item.get('reason'):
                    print(f"           Reason: {item['reason']}")
            print(f"\nFound {len(truncated)} potentially truncated entries.")
        else:
            print("\nNo truncated URLs found.")

    elif cmd == 'export' and len(sys.argv) > 3:
        format_type = sys.argv[2].lower()
        filepath = sys.argv[3]

        if format_type == 'csv':
            count = export_to_csv(db, filepath)
            print(f"Exported {count} entries to {filepath}")
        elif format_type == 'md':
            count = export_markdown(db, filepath)
            print(f"Exported {count} lines to {filepath}")
        elif format_type == 'urls':
            count = export_urls_txt(db, filepath)
            print(f"Exported {count} URLs to {filepath}")
        else:
            print(f"Unknown format: {format_type}")

    elif cmd == 'add' and len(sys.argv) > 3:
        add_type = sys.argv[2].lower()
        value = sys.argv[3]

        if add_type == 'github':
            success, msg = add_github_repo(db, value)
        elif add_type == 'huggingface':
            success, msg = add_huggingface(db, value)
        elif add_type == 'sref':
            success, msg = add_sref_code(db, value)
        else:
            print(f"Unknown type: {add_type}")
            return

        if success:
            save_db(db)
            print(f"SUCCESS: {msg}")
        else:
            print(f"FAILED: {msg}")

    else:
        print(f"Unknown command or missing arguments: {cmd}")
        print("Run without arguments for help.")

if __name__ == "__main__":
    main()
