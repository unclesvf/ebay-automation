#!/usr/bin/env python3
"""
Model Tracker - Track AI model versions, updates, and local installation status.

Tracks:
- TTS models (Soprano, Kokoro, Bark, etc.)
- Image models - Cloud (Midjourney, DALL-E, Grok Imagine)
- Image models - Local (Flux, SD3, SDXL for RTX 4090)
- LLM models (for reference)

Usage:
    python model_tracker.py                           # Show all models
    python model_tracker.py list                      # List all models
    python model_tracker.py list --type tts           # List TTS models only
    python model_tracker.py list --local              # List locally installed
    python model_tracker.py add tts "Kokoro" --url "huggingface.co/..."
    python model_tracker.py add image_local "Flux.1" --installed
    python model_tracker.py update "Flux.1" --version "1.2" --notes "New version"
    python model_tracker.py install "SDXL"            # Mark as installed locally
    python model_tracker.py uninstall "SDXL"          # Mark as not installed
    python model_tracker.py stats                     # Show statistics
    python model_tracker.py report                    # Generate HTML report
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Paths
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"
EXPORTS_DIR = KNOWLEDGE_BASE / "exports"
MODELS_REPORT = EXPORTS_DIR / "models_report.html"

# Model categories
MODEL_TYPES = {
    'tts': 'Text-to-Speech',
    'image_cloud': 'Image Generation (Cloud)',
    'image_local': 'Image Generation (Local/RTX 4090)',
    'llm': 'Large Language Models',
    'video': 'Video Generation',
    'audio': 'Audio/Music Generation'
}

# Known models for reference
KNOWN_MODELS = {
    'tts': [
        {'name': 'Soprano', 'provider': 'Unknown', 'local_capable': True},
        {'name': 'Kokoro', 'provider': 'Hugging Face', 'local_capable': True},
        {'name': 'Bark', 'provider': 'Suno', 'local_capable': True},
        {'name': 'Tortoise TTS', 'provider': 'Open Source', 'local_capable': True},
        {'name': 'XTTS', 'provider': 'Coqui', 'local_capable': True},
        {'name': 'Fish Speech', 'provider': 'Open Source', 'local_capable': True},
        {'name': 'ElevenLabs', 'provider': 'ElevenLabs', 'local_capable': False},
        {'name': 'PlayHT', 'provider': 'PlayHT', 'local_capable': False},
    ],
    'image_cloud': [
        {'name': 'Midjourney', 'provider': 'Midjourney', 'local_capable': False},
        {'name': 'DALL-E 3', 'provider': 'OpenAI', 'local_capable': False},
        {'name': 'Grok Imagine', 'provider': 'xAI', 'local_capable': False},
        {'name': 'Ideogram', 'provider': 'Ideogram', 'local_capable': False},
        {'name': 'Leonardo', 'provider': 'Leonardo.ai', 'local_capable': False},
        {'name': 'niji', 'provider': 'Midjourney', 'local_capable': False},
    ],
    'image_local': [
        {'name': 'Flux.1', 'provider': 'Black Forest Labs', 'local_capable': True, 'vram_req': '24GB'},
        {'name': 'Flux.1 Dev', 'provider': 'Black Forest Labs', 'local_capable': True, 'vram_req': '24GB'},
        {'name': 'Flux.1 Schnell', 'provider': 'Black Forest Labs', 'local_capable': True, 'vram_req': '12GB'},
        {'name': 'SD3', 'provider': 'Stability AI', 'local_capable': True, 'vram_req': '16GB'},
        {'name': 'SD3.5', 'provider': 'Stability AI', 'local_capable': True, 'vram_req': '16GB'},
        {'name': 'SDXL', 'provider': 'Stability AI', 'local_capable': True, 'vram_req': '8GB'},
        {'name': 'SDXL Turbo', 'provider': 'Stability AI', 'local_capable': True, 'vram_req': '8GB'},
        {'name': 'SD 1.5', 'provider': 'Stability AI', 'local_capable': True, 'vram_req': '6GB'},
    ],
}


def load_database():
    """Load the master database."""
    if not MASTER_DB.exists():
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
                "image_local": [],
                "llm": [],
                "video": [],
                "audio": []
            }
        }

    with open(MASTER_DB, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # Ensure models section exists with all categories
    if 'models' not in db:
        db['models'] = {}
    for model_type in MODEL_TYPES.keys():
        if model_type not in db['models']:
            db['models'][model_type] = []

    return db


def save_database(db):
    """Save the master database."""
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    # Update total entries count
    total = 0
    for section in ['models', 'repositories', 'tutorials', 'styles']:
        if section in db:
            if isinstance(db[section], dict):
                for subsection in db[section].values():
                    if isinstance(subsection, list):
                        total += len(subsection)
            elif isinstance(db[section], list):
                total += len(db[section])
    db['metadata']['total_entries'] = total

    with open(MASTER_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2)


def find_model(db, name):
    """Find a model by name across all categories."""
    name_lower = name.lower()
    for model_type, models in db.get('models', {}).items():
        for model in models:
            if model.get('name', '').lower() == name_lower:
                return model_type, model
    return None, None


def add_model(model_type, name, provider=None, url=None, huggingface_url=None,
              version=None, installed=False, local_capable=None, vram_req=None,
              notes=None, source=None):
    """Add a new model to the tracker."""
    db = load_database()

    if model_type not in MODEL_TYPES:
        print(f"Invalid model type: {model_type}")
        print(f"Valid types: {', '.join(MODEL_TYPES.keys())}")
        return False

    # Check for duplicates
    existing_type, existing = find_model(db, name)
    if existing:
        print(f"Model '{name}' already exists in {existing_type}")
        return False

    # Create entry
    entry = {
        'name': name,
        'provider': provider,
        'version': version,
        'url': url,
        'huggingface_url': huggingface_url,
        'local_capable': local_capable if local_capable is not None else (model_type == 'image_local'),
        'installed_locally': installed,
        'vram_requirement': vram_req,
        'notes': notes,
        'date_added': datetime.now().strftime('%Y-%m-%d'),
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'source': source or {}
    }

    # Remove None values
    entry = {k: v for k, v in entry.items() if v is not None}

    db['models'][model_type].append(entry)
    save_database(db)

    print(f"Added {MODEL_TYPES[model_type]} model: {name}")
    if installed:
        print("  Status: Installed locally")
    return True


def update_model(name, version=None, installed=None, notes=None, url=None):
    """Update an existing model."""
    db = load_database()

    model_type, model = find_model(db, name)
    if not model:
        print(f"Model '{name}' not found")
        return False

    if version:
        model['version'] = version
    if installed is not None:
        model['installed_locally'] = installed
    if notes:
        model['notes'] = notes
    if url:
        model['url'] = url

    model['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    save_database(db)
    print(f"Updated model: {name}")
    return True


def set_install_status(name, installed):
    """Set local installation status for a model."""
    db = load_database()

    model_type, model = find_model(db, name)
    if not model:
        print(f"Model '{name}' not found")
        return False

    if not model.get('local_capable', False) and installed:
        print(f"Warning: {name} is not marked as locally capable")

    model['installed_locally'] = installed
    model['last_updated'] = datetime.now().strftime('%Y-%m-%d')

    save_database(db)

    status = "installed" if installed else "not installed"
    print(f"Marked {name} as {status} locally")
    return True


def list_models(model_type=None, local_only=False, installed_only=False):
    """List models in the database."""
    db = load_database()

    types_to_show = [model_type] if model_type else MODEL_TYPES.keys()

    print("\n" + "="*70)
    print("AI MODEL TRACKER")
    print("="*70)

    total_count = 0
    installed_count = 0

    for mtype in types_to_show:
        if mtype not in db.get('models', {}):
            continue

        models = db['models'][mtype]
        if not models:
            continue

        # Apply filters
        if local_only:
            models = [m for m in models if m.get('local_capable', False)]
        if installed_only:
            models = [m for m in models if m.get('installed_locally', False)]

        if not models:
            continue

        print(f"\n{MODEL_TYPES.get(mtype, mtype).upper()}")
        print("-" * 50)

        for model in sorted(models, key=lambda x: x.get('name', '')):
            name = model.get('name', 'Unknown')
            provider = model.get('provider', '')
            version = model.get('version', '')
            installed = model.get('installed_locally', False)
            local_capable = model.get('local_capable', False)
            vram = model.get('vram_requirement', '')

            # Build status indicators
            status_parts = []
            if installed:
                status_parts.append("[INSTALLED]")
                installed_count += 1
            elif local_capable:
                status_parts.append("[Can Install]")

            status = ' '.join(status_parts)

            # Format output
            version_str = f" v{version}" if version else ""
            provider_str = f" ({provider})" if provider else ""
            vram_str = f" [{vram}]" if vram else ""

            print(f"  {name}{version_str}{provider_str}{vram_str} {status}")

            total_count += 1

    print(f"\n{'='*70}")
    print(f"Total: {total_count} models | Installed locally: {installed_count}")
    print("="*70)


def show_stats():
    """Show model statistics."""
    db = load_database()

    print("\n=== MODEL TRACKER STATISTICS ===")
    print("="*45)

    total = 0
    installed = 0
    local_capable = 0

    for model_type, type_name in MODEL_TYPES.items():
        models = db.get('models', {}).get(model_type, [])
        count = len(models)
        inst = sum(1 for m in models if m.get('installed_locally', False))
        capable = sum(1 for m in models if m.get('local_capable', False))

        if count > 0:
            print(f"\n{type_name}:")
            print(f"  Total: {count}")
            if capable > 0:
                print(f"  Local capable: {capable}")
            if inst > 0:
                print(f"  Installed: {inst}")

        total += count
        installed += inst
        local_capable += capable

    print(f"\n{'='*45}")
    print(f"TOTAL MODELS: {total}")
    print(f"LOCAL CAPABLE: {local_capable}")
    print(f"INSTALLED: {installed}")

    # GPU info reminder
    print(f"\n[Local GPU: RTX 4090 - 24GB VRAM]")


def generate_report():
    """Generate HTML report of all models."""
    db = load_database()

    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Model Tracker</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            min-height: 100vh;
            color: #c9d1d9;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #30363d;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #58a6ff, #3fb950);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle { color: #8b949e; margin-top: 10px; }
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .stat {
            text-align: center;
            padding: 15px 25px;
            background: rgba(56, 139, 253, 0.1);
            border-radius: 10px;
            border: 1px solid #30363d;
        }
        .stat-value { font-size: 2em; color: #58a6ff; font-weight: bold; }
        .stat-label { color: #8b949e; font-size: 0.9em; }
        .category {
            margin-bottom: 40px;
            background: rgba(255,255,255,0.02);
            border-radius: 15px;
            border: 1px solid #30363d;
            overflow: hidden;
        }
        .category-header {
            background: rgba(56, 139, 253, 0.1);
            padding: 15px 25px;
            border-bottom: 1px solid #30363d;
        }
        .category-header h2 {
            color: #58a6ff;
            font-size: 1.3em;
        }
        .model-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
            padding: 20px;
        }
        .model-card {
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid #30363d;
            transition: border-color 0.3s;
        }
        .model-card:hover { border-color: #58a6ff; }
        .model-card.installed { border-left: 3px solid #3fb950; }
        .model-name {
            font-size: 1.1em;
            color: #f0f6fc;
            margin-bottom: 5px;
        }
        .model-provider { color: #8b949e; font-size: 0.9em; }
        .model-meta {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .tag {
            font-size: 0.75em;
            padding: 3px 8px;
            border-radius: 5px;
            background: rgba(56, 139, 253, 0.2);
            color: #58a6ff;
        }
        .tag.installed { background: rgba(63, 185, 80, 0.2); color: #3fb950; }
        .tag.vram { background: rgba(210, 153, 34, 0.2); color: #d29922; }
        .gpu-note {
            text-align: center;
            padding: 20px;
            background: rgba(63, 185, 80, 0.1);
            border: 1px solid #3fb950;
            border-radius: 10px;
            margin-top: 30px;
        }
        footer {
            text-align: center;
            padding: 40px;
            color: #484f58;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI Model Tracker</h1>
            <p class="subtitle">TTS, Image Generation, and More</p>
'''

    # Calculate stats
    total = 0
    installed = 0
    local_capable = 0
    for models in db.get('models', {}).values():
        total += len(models)
        installed += sum(1 for m in models if m.get('installed_locally', False))
        local_capable += sum(1 for m in models if m.get('local_capable', False))

    html += f'''
            <div class="stats-bar">
                <div class="stat">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Total Models</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{local_capable}</div>
                    <div class="stat-label">Local Capable</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{installed}</div>
                    <div class="stat-label">Installed</div>
                </div>
            </div>
        </header>
        <main>
'''

    # Generate categories
    for model_type, type_name in MODEL_TYPES.items():
        models = db.get('models', {}).get(model_type, [])
        if not models:
            continue

        html += f'''
            <div class="category">
                <div class="category-header">
                    <h2>{type_name}</h2>
                </div>
                <div class="model-grid">
'''

        for model in sorted(models, key=lambda x: x.get('name', '')):
            name = model.get('name', 'Unknown')
            provider = model.get('provider', '')
            version = model.get('version', '')
            is_installed = model.get('installed_locally', False)
            vram = model.get('vram_requirement', '')

            card_class = "model-card installed" if is_installed else "model-card"
            version_str = f" v{version}" if version else ""

            html += f'''
                    <div class="{card_class}">
                        <div class="model-name">{name}{version_str}</div>
                        <div class="model-provider">{provider}</div>
                        <div class="model-meta">
'''
            if is_installed:
                html += '                            <span class="tag installed">Installed</span>\n'
            if vram:
                html += f'                            <span class="tag vram">{vram}</span>\n'

            html += '''                        </div>
                    </div>
'''

        html += '''                </div>
            </div>
'''

    html += '''
            <div class="gpu-note">
                <strong>Local GPU:</strong> NVIDIA RTX 4090 - 24GB VRAM
            </div>
        </main>
        <footer>
            <p>Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + '''</p>
            <p>AI Knowledge Base - Model Tracker</p>
        </footer>
    </div>
</body>
</html>
'''

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODELS_REPORT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Report generated: {MODELS_REPORT}")
    return str(MODELS_REPORT)


def seed_known_models():
    """Seed database with known models (if empty)."""
    db = load_database()

    added = 0
    for model_type, models in KNOWN_MODELS.items():
        existing_names = [m.get('name', '').lower() for m in db.get('models', {}).get(model_type, [])]

        for model in models:
            if model['name'].lower() not in existing_names:
                entry = {
                    'name': model['name'],
                    'provider': model.get('provider'),
                    'local_capable': model.get('local_capable', False),
                    'installed_locally': False,
                    'vram_requirement': model.get('vram_req'),
                    'date_added': datetime.now().strftime('%Y-%m-%d'),
                    'last_updated': datetime.now().strftime('%Y-%m-%d'),
                }
                entry = {k: v for k, v in entry.items() if v is not None}
                db['models'][model_type].append(entry)
                added += 1

    if added > 0:
        save_database(db)
        print(f"Seeded {added} known models")
    else:
        print("No new models to seed")

    return added


def main():
    parser = argparse.ArgumentParser(
        description='Track AI models - versions, updates, and local installation status',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Model Types:
  tts          Text-to-Speech (Soprano, Kokoro, Bark, etc.)
  image_cloud  Cloud image generation (Midjourney, DALL-E, etc.)
  image_local  Local image generation (Flux, SDXL, etc.)
  llm          Large Language Models
  video        Video generation
  audio        Audio/Music generation

Examples:
  python model_tracker.py list                     # List all models
  python model_tracker.py list --type image_local  # List local image models
  python model_tracker.py list --installed         # List installed models
  python model_tracker.py add tts "Kokoro" --provider "HuggingFace"
  python model_tracker.py add image_local "Flux.1" --installed --vram "24GB"
  python model_tracker.py install "SDXL"           # Mark as installed
  python model_tracker.py uninstall "SDXL"         # Mark as not installed
  python model_tracker.py update "Flux.1" --version "1.2"
  python model_tracker.py stats                    # Show statistics
  python model_tracker.py report                   # Generate HTML report
  python model_tracker.py seed                     # Add known models
        '''
    )

    subparsers = parser.add_subparsers(dest='command')

    # List command
    list_parser = subparsers.add_parser('list', help='List models')
    list_parser.add_argument('--type', '-t', choices=MODEL_TYPES.keys(), help='Filter by type')
    list_parser.add_argument('--local', '-l', action='store_true', help='Show only local-capable')
    list_parser.add_argument('--installed', '-i', action='store_true', help='Show only installed')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new model')
    add_parser.add_argument('type', choices=MODEL_TYPES.keys(), help='Model type')
    add_parser.add_argument('name', help='Model name')
    add_parser.add_argument('--provider', '-p', help='Provider/company')
    add_parser.add_argument('--url', help='Model URL')
    add_parser.add_argument('--hf', '--huggingface', dest='huggingface', help='HuggingFace URL')
    add_parser.add_argument('--version', '-v', help='Version')
    add_parser.add_argument('--installed', '-i', action='store_true', help='Mark as installed')
    add_parser.add_argument('--vram', help='VRAM requirement (e.g., "24GB")')
    add_parser.add_argument('--notes', '-n', help='Notes')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update a model')
    update_parser.add_argument('name', help='Model name')
    update_parser.add_argument('--version', '-v', help='New version')
    update_parser.add_argument('--notes', '-n', help='Notes')
    update_parser.add_argument('--url', help='URL')

    # Install command
    install_parser = subparsers.add_parser('install', help='Mark model as installed')
    install_parser.add_argument('name', help='Model name')

    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Mark model as not installed')
    uninstall_parser.add_argument('name', help='Model name')

    # Stats command
    subparsers.add_parser('stats', help='Show statistics')

    # Report command
    subparsers.add_parser('report', help='Generate HTML report')

    # Seed command
    subparsers.add_parser('seed', help='Seed database with known models')

    args = parser.parse_args()

    if args.command == 'list':
        list_models(model_type=args.type, local_only=args.local, installed_only=args.installed)
    elif args.command == 'add':
        add_model(
            args.type, args.name,
            provider=args.provider,
            url=args.url,
            huggingface_url=args.huggingface,
            version=args.version,
            installed=args.installed,
            vram_req=args.vram,
            notes=args.notes
        )
    elif args.command == 'update':
        update_model(args.name, version=args.version, notes=args.notes, url=args.url)
    elif args.command == 'install':
        set_install_status(args.name, True)
    elif args.command == 'uninstall':
        set_install_status(args.name, False)
    elif args.command == 'stats':
        show_stats()
    elif args.command == 'report':
        generate_report()
    elif args.command == 'seed':
        seed_known_models()
    else:
        # Default: show list
        list_models()


if __name__ == '__main__':
    main()
