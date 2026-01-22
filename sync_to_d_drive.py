#!/usr/bin/env python3
"""
Sync to D: Drive - Copy and organize AI Knowledge Base files.

Syncs:
- Scripts from ebay-automation to knowledge base
- Database and export files
- Transcripts and analysis
- Course materials

Usage:
    python sync_to_d_drive.py                # Full sync
    python sync_to_d_drive.py --dry-run      # Preview changes
    python sync_to_d_drive.py status         # Show sync status
    python sync_to_d_drive.py scripts        # Sync scripts only
    python sync_to_d_drive.py data           # Sync data only
    python sync_to_d_drive.py backup         # Create backup
    python sync_to_d_drive.py verify         # Verify integrity
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from datetime import datetime
from pathlib import Path

# Source and destination paths
SOURCE_DIR = Path(r"C:\Users\scott\ebay-automation")
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")

# Scripts to sync (knowledge base related)
KB_SCRIPTS = [
    'ai_content_extractor.py',
    'generate_reports.py',
    'knowledge_db.py',
    'youtube_metadata.py',
    'transcript_analyzer.py',
    'transcript_search.py',
    'style_code_gallery.py',
    'model_tracker.py',
    'course_materials.py',
    'extract_knowledge.py',
    'sync_to_d_drive.py',
    'run_pipeline.py',
    'kb_config.py',
    'scott_folder_organizer.py',
]

# Directory structure
DIRECTORIES = {
    'scripts': KNOWLEDGE_BASE / 'scripts',
    'models': KNOWLEDGE_BASE / 'models',
    'models_tts': KNOWLEDGE_BASE / 'models' / 'tts',
    'models_image_cloud': KNOWLEDGE_BASE / 'models' / 'image-cloud',
    'models_image_local': KNOWLEDGE_BASE / 'models' / 'image-local',
    'repositories': KNOWLEDGE_BASE / 'repositories',
    'repositories_github': KNOWLEDGE_BASE / 'repositories' / 'github',
    'repositories_huggingface': KNOWLEDGE_BASE / 'repositories' / 'huggingface',
    'coding_tools': KNOWLEDGE_BASE / 'coding-tools',
    'coding_claude': KNOWLEDGE_BASE / 'coding-tools' / 'claude-code',
    'tutorials': KNOWLEDGE_BASE / 'tutorials',
    'tutorials_transcripts': KNOWLEDGE_BASE / 'tutorials' / 'transcripts',
    'tutorials_analysis': KNOWLEDGE_BASE / 'tutorials' / 'analysis',
    'prompts': KNOWLEDGE_BASE / 'prompts',
    'prompts_system': KNOWLEDGE_BASE / 'prompts' / 'system-prompts',
    'prompts_techniques': KNOWLEDGE_BASE / 'prompts' / 'techniques',
    'styles': KNOWLEDGE_BASE / 'styles',
    'styles_sref': KNOWLEDGE_BASE / 'styles' / 'midjourney-sref',
    'exports': KNOWLEDGE_BASE / 'exports',
    'extracted': KNOWLEDGE_BASE / 'extracted',
    'course_materials': KNOWLEDGE_BASE / 'course_materials',
    'backups': KNOWLEDGE_BASE / 'backups',
}


def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def files_are_identical(src, dst):
    """Check if two files are identical."""
    if not dst.exists():
        return False
    if src.stat().st_size != dst.stat().st_size:
        return False
    return get_file_hash(src) == get_file_hash(dst)


def ensure_directories():
    """Create all required directories."""
    created = []
    for name, path in DIRECTORIES.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
    return created


def sync_scripts(dry_run=False):
    """Sync knowledge base scripts to D: drive."""
    scripts_dir = DIRECTORIES['scripts']
    synced = []
    skipped = []
    errors = []

    print("\n=== SYNCING SCRIPTS ===")

    for script_name in KB_SCRIPTS:
        src = SOURCE_DIR / script_name
        dst = scripts_dir / script_name

        if not src.exists():
            errors.append(f"Source not found: {src}")
            continue

        if files_are_identical(src, dst):
            skipped.append(script_name)
            continue

        action = "Would copy" if dry_run else "Copying"
        status = "NEW" if not dst.exists() else "UPDATED"
        print(f"  [{status}] {action}: {script_name}")

        if not dry_run:
            shutil.copy2(src, dst)
            synced.append(script_name)
        else:
            synced.append(script_name)

    print(f"\n  Synced: {len(synced)} | Skipped (unchanged): {len(skipped)} | Errors: {len(errors)}")

    for error in errors:
        print(f"  ERROR: {error}")

    return synced, skipped, errors


def sync_data_files(dry_run=False):
    """Sync data files (JSON databases, etc.)."""
    synced = []
    skipped = []

    print("\n=== SYNCING DATA FILES ===")

    # Files to sync from source to knowledge base
    data_files = [
        (SOURCE_DIR / 'twitter_data_extract.json', KNOWLEDGE_BASE / 'twitter_data_extract.json'),
        (SOURCE_DIR / 'url_cache.json', KNOWLEDGE_BASE / 'url_cache.json'),
    ]

    for src, dst in data_files:
        if not src.exists():
            continue

        if files_are_identical(src, dst):
            skipped.append(src.name)
            continue

        action = "Would copy" if dry_run else "Copying"
        status = "NEW" if not dst.exists() else "UPDATED"
        print(f"  [{status}] {action}: {src.name}")

        if not dry_run:
            shutil.copy2(src, dst)
            synced.append(src.name)
        else:
            synced.append(src.name)

    print(f"\n  Synced: {len(synced)} | Skipped (unchanged): {len(skipped)}")

    return synced, skipped


def create_backup(dry_run=False):
    """Create a backup of the knowledge base."""
    backup_dir = DIRECTORIES['backups']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"backup_{timestamp}"
    backup_path = backup_dir / backup_name

    print("\n=== CREATING BACKUP ===")

    # Files to backup
    files_to_backup = [
        KNOWLEDGE_BASE / 'master_db.json',
        KNOWLEDGE_BASE / 'url_cache.json',
    ]

    # Add all JSON files in extracted
    extracted_dir = DIRECTORIES['extracted']
    if extracted_dir.exists():
        files_to_backup.extend(extracted_dir.glob('*.json'))

    if dry_run:
        print(f"  Would create backup: {backup_path}")
        print(f"  Would backup {len(files_to_backup)} files")
        return backup_path

    backup_path.mkdir(parents=True, exist_ok=True)

    backed_up = 0
    for src in files_to_backup:
        if src.exists():
            dst = backup_path / src.name
            shutil.copy2(src, dst)
            backed_up += 1

    print(f"  Backup created: {backup_path}")
    print(f"  Files backed up: {backed_up}")

    # Clean old backups (keep last 5)
    backups = sorted(backup_dir.glob('backup_*'), reverse=True)
    for old_backup in backups[5:]:
        if old_backup.is_dir():
            shutil.rmtree(old_backup)
            print(f"  Removed old backup: {old_backup.name}")

    return backup_path


def show_status():
    """Show sync status and file counts."""
    print("\n" + "="*60)
    print("AI KNOWLEDGE BASE - SYNC STATUS")
    print("="*60)

    print(f"\nSource: {SOURCE_DIR}")
    print(f"Destination: {KNOWLEDGE_BASE}")

    # Check directory structure
    print("\n--- Directory Structure ---")
    for name, path in DIRECTORIES.items():
        exists = "[OK]" if path.exists() else "[MISSING]"
        file_count = len(list(path.glob('*'))) if path.exists() else 0
        print(f"  {exists} {path.relative_to(KNOWLEDGE_BASE)}: {file_count} files")

    # Check scripts sync status
    print("\n--- Scripts Sync Status ---")
    scripts_dir = DIRECTORIES['scripts']
    for script_name in KB_SCRIPTS:
        src = SOURCE_DIR / script_name
        dst = scripts_dir / script_name

        if not src.exists():
            status = "[NO SRC]"
        elif not dst.exists():
            status = "[NOT SYNCED]"
        elif files_are_identical(src, dst):
            status = "[SYNCED]"
        else:
            status = "[OUT OF DATE]"

        print(f"  {status} {script_name}")

    # Database stats
    print("\n--- Database Stats ---")
    master_db = KNOWLEDGE_BASE / 'master_db.json'
    if master_db.exists():
        with open(master_db, 'r', encoding='utf-8') as f:
            db = json.load(f)
        print(f"  Last updated: {db.get('metadata', {}).get('last_updated', 'Unknown')}")
        print(f"  Total entries: {db.get('metadata', {}).get('total_entries', 0)}")

        # Count by section
        for section in ['tutorials', 'repositories', 'styles', 'models']:
            if section in db:
                if isinstance(db[section], list):
                    print(f"  {section.title()}: {len(db[section])}")
                elif isinstance(db[section], dict):
                    total = sum(len(v) for v in db[section].values() if isinstance(v, list))
                    print(f"  {section.title()}: {total}")

    # Disk usage
    print("\n--- Disk Usage ---")
    total_size = 0
    for path in KNOWLEDGE_BASE.rglob('*'):
        if path.is_file():
            total_size += path.stat().st_size

    print(f"  Total size: {total_size / 1024 / 1024:.2f} MB")

    # Count by type
    extensions = {}
    for path in KNOWLEDGE_BASE.rglob('*'):
        if path.is_file():
            ext = path.suffix.lower() or 'no extension'
            extensions[ext] = extensions.get(ext, 0) + 1

    print("\n  Files by type:")
    for ext, count in sorted(extensions.items(), key=lambda x: -x[1])[:10]:
        print(f"    {ext}: {count}")


def verify_integrity():
    """Verify integrity of synced files."""
    print("\n=== VERIFYING INTEGRITY ===")

    issues = []

    # Check master database
    master_db = KNOWLEDGE_BASE / 'master_db.json'
    if master_db.exists():
        try:
            with open(master_db, 'r', encoding='utf-8') as f:
                json.load(f)
            print("  [OK] master_db.json is valid JSON")
        except json.JSONDecodeError as e:
            issues.append(f"master_db.json: Invalid JSON - {e}")
            print(f"  [ERROR] master_db.json: {e}")
    else:
        issues.append("master_db.json not found")
        print("  [MISSING] master_db.json")

    # Check all JSON files in extracted
    extracted_dir = DIRECTORIES['extracted']
    if extracted_dir.exists():
        for json_file in extracted_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                print(f"  [OK] {json_file.name}")
            except json.JSONDecodeError as e:
                issues.append(f"{json_file.name}: Invalid JSON - {e}")
                print(f"  [ERROR] {json_file.name}: {e}")

    # Check scripts are valid Python
    scripts_dir = DIRECTORIES['scripts']
    if scripts_dir.exists():
        for script in scripts_dir.glob('*.py'):
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    compile(f.read(), script.name, 'exec')
                print(f"  [OK] {script.name} (valid Python)")
            except SyntaxError as e:
                issues.append(f"{script.name}: Syntax error - {e}")
                print(f"  [ERROR] {script.name}: {e}")

    # Check search index
    search_db = KNOWLEDGE_BASE / 'tutorials' / 'search_index.db'
    if search_db.exists():
        print(f"  [OK] search_index.db ({search_db.stat().st_size / 1024:.1f} KB)")
    else:
        print("  [INFO] search_index.db not created yet")

    print(f"\n  Total issues: {len(issues)}")
    return issues


def full_sync(dry_run=False):
    """Perform full synchronization."""
    print("\n" + "="*60)
    print("AI KNOWLEDGE BASE - FULL SYNC")
    print("="*60)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Ensure directories exist
    if not dry_run:
        created = ensure_directories()
        if created:
            print(f"\nCreated {len(created)} directories")

    # Sync scripts
    scripts_synced, scripts_skipped, scripts_errors = sync_scripts(dry_run)

    # Sync data files
    data_synced, data_skipped = sync_data_files(dry_run)

    # Summary
    print("\n" + "="*60)
    print("SYNC SUMMARY")
    print("="*60)
    print(f"  Scripts synced: {len(scripts_synced)}")
    print(f"  Scripts unchanged: {len(scripts_skipped)}")
    print(f"  Data files synced: {len(data_synced)}")
    print(f"  Errors: {len(scripts_errors)}")

    if dry_run:
        print("\n  This was a dry run. No files were modified.")
        print("  Run without --dry-run to apply changes.")


def generate_readme():
    """Generate README for the knowledge base."""
    readme_content = f"""# AI Knowledge Base

Personal collection of AI resources, tutorials, and tools.

## Directory Structure

```
D:\\AI-Knowledge-Base\\
├── scripts/              # Python scripts for managing the knowledge base
├── models/               # AI model references
│   ├── tts/              # Text-to-Speech models
│   ├── image-cloud/      # Cloud image generation (Midjourney, DALL-E)
│   └── image-local/      # Local image generation (Flux, SDXL)
├── repositories/         # GitHub and HuggingFace references
├── coding-tools/         # AI coding tools documentation
├── tutorials/            # Video tutorials
│   ├── transcripts/      # Downloaded transcripts
│   └── analysis/         # Extracted insights
├── prompts/              # Prompt templates and techniques
├── styles/               # Midjourney style codes
├── exports/              # Generated HTML reports
├── extracted/            # Extracted tips, techniques, tools
├── course_materials/     # Generated course content
└── backups/              # Database backups
```

## Quick Start

```bash
# Show status
python scripts/sync_to_d_drive.py status

# Search transcripts
python scripts/transcript_search.py "search query"

# Track models
python scripts/model_tracker.py list

# Generate reports
python scripts/generate_reports.py
```

## Key Files

- `master_db.json` - Central database
- `url_cache.json` - Expanded URLs from t.co links
- `exports/*.html` - Generated HTML reports

---

Last updated: {datetime.now().strftime('%Y-%m-%d')}
"""

    readme_path = KNOWLEDGE_BASE / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"Generated: {readme_path}")
    return readme_path


def main():
    parser = argparse.ArgumentParser(
        description='Sync AI Knowledge Base files to D: drive',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python sync_to_d_drive.py                # Full sync
  python sync_to_d_drive.py --dry-run      # Preview changes
  python sync_to_d_drive.py status         # Show status
  python sync_to_d_drive.py scripts        # Sync scripts only
  python sync_to_d_drive.py data           # Sync data only
  python sync_to_d_drive.py backup         # Create backup
  python sync_to_d_drive.py verify         # Check integrity
  python sync_to_d_drive.py readme         # Generate README
        '''
    )

    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Preview changes without modifying files')

    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('status', help='Show sync status')
    subparsers.add_parser('scripts', help='Sync scripts only')
    subparsers.add_parser('data', help='Sync data files only')
    subparsers.add_parser('backup', help='Create backup')
    subparsers.add_parser('verify', help='Verify file integrity')
    subparsers.add_parser('readme', help='Generate README')

    args = parser.parse_args()

    if args.command == 'status':
        show_status()
    elif args.command == 'scripts':
        ensure_directories()
        sync_scripts(args.dry_run)
    elif args.command == 'data':
        ensure_directories()
        sync_data_files(args.dry_run)
    elif args.command == 'backup':
        ensure_directories()
        create_backup(args.dry_run)
    elif args.command == 'verify':
        verify_integrity()
    elif args.command == 'readme':
        generate_readme()
    else:
        # Default: full sync
        full_sync(args.dry_run)


if __name__ == '__main__':
    main()
