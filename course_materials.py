#!/usr/bin/env python3
"""
Course Materials Generator - Export organized content for course development.

Generates course materials from:
- Tutorial transcripts and analysis
- Extracted tips and techniques
- Tool documentation
- Workflows and best practices

Usage:
    python course_materials.py                    # Generate all course materials
    python course_materials.py --topic claude-code # Generate for specific topic
    python course_materials.py outline            # Generate course outline only
    python course_materials.py lessons            # Generate lesson plans
    python course_materials.py cheatsheet         # Generate quick reference
    python course_materials.py export --format md # Export as markdown
    python course_materials.py stats              # Show content statistics
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Paths
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"
EXTRACTED_DIR = KNOWLEDGE_BASE / "extracted"
ANALYSIS_DIR = KNOWLEDGE_BASE / "tutorials" / "analysis"
EXPORTS_DIR = KNOWLEDGE_BASE / "exports"
COURSE_DIR = KNOWLEDGE_BASE / "course_materials"

# Course topic definitions
COURSE_TOPICS = {
    'claude-code': {
        'title': 'Mastering Claude Code',
        'description': 'Complete guide to using Claude Code for AI-assisted development',
        'keywords': ['claude code', 'claude.md', 'mcp server', 'plan mode', 'anthropic'],
        'icon': 'code'
    },
    'midjourney': {
        'title': 'Midjourney Masterclass',
        'description': 'Create stunning AI art with Midjourney',
        'keywords': ['midjourney', 'sref', 'niji', 'prompt', 'style'],
        'icon': 'image'
    },
    'image-generation': {
        'title': 'AI Image Generation',
        'description': 'Local and cloud image generation with Flux, SDXL, and more',
        'keywords': ['flux', 'sdxl', 'stable diffusion', 'comfyui', 'image'],
        'icon': 'palette'
    },
    'prompt-engineering': {
        'title': 'Prompt Engineering',
        'description': 'Master the art of crafting effective AI prompts',
        'keywords': ['prompt', 'system prompt', 'instruction', 'context'],
        'icon': 'edit'
    },
    'ai-coding': {
        'title': 'AI-Assisted Coding',
        'description': 'Boost productivity with AI coding tools',
        'keywords': ['cursor', 'copilot', 'codex', 'aider', 'coding'],
        'icon': 'terminal'
    },
    'tts-voice': {
        'title': 'Text-to-Speech & Voice AI',
        'description': 'Create natural speech with AI voice models',
        'keywords': ['tts', 'voice', 'speech', 'kokoro', 'bark'],
        'icon': 'mic'
    }
}


def load_database():
    """Load the master database."""
    if not MASTER_DB.exists():
        return {}
    with open(MASTER_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_extracted_data():
    """Load all extracted data (tips, techniques, etc.)."""
    data = {
        'tips': [],
        'techniques': [],
        'tools': [],
        'topics': {}
    }

    # Load tips
    tips_file = EXTRACTED_DIR / "tips.json"
    if tips_file.exists():
        with open(tips_file, 'r', encoding='utf-8') as f:
            tips_data = json.load(f)
            # Handle nested structure
            data['tips'] = tips_data.get('tips', tips_data) if isinstance(tips_data, dict) else tips_data

    # Load techniques
    techniques_file = EXTRACTED_DIR / "technique_mentions.json"
    if techniques_file.exists():
        with open(techniques_file, 'r', encoding='utf-8') as f:
            data['techniques'] = json.load(f)

    # Load tools
    tools_file = EXTRACTED_DIR / "tool_mentions.json"
    if tools_file.exists():
        with open(tools_file, 'r', encoding='utf-8') as f:
            data['tools'] = json.load(f)

    # Load topics
    topics_file = EXTRACTED_DIR / "topics.json"
    if topics_file.exists():
        with open(topics_file, 'r', encoding='utf-8') as f:
            data['topics'] = json.load(f)

    return data


def load_analysis_files():
    """Load all tutorial analysis files."""
    analyses = []
    if ANALYSIS_DIR.exists():
        for file in ANALYSIS_DIR.glob("*_analysis.json"):
            with open(file, 'r', encoding='utf-8') as f:
                analyses.append(json.load(f))
    return analyses


def categorize_content_by_topic(data, db):
    """Organize content by course topic."""
    categorized = {topic: {
        'tutorials': [],
        'tips': [],
        'techniques': [],
        'tools': [],
        'repositories': []
    } for topic in COURSE_TOPICS}

    # Categorize tutorials
    for tutorial in db.get('tutorials', []):
        tutorial_topics = tutorial.get('topics', [])
        for topic, config in COURSE_TOPICS.items():
            if any(kw in ' '.join(tutorial_topics).lower() for kw in config['keywords']):
                categorized[topic]['tutorials'].append(tutorial)

    # Categorize tips
    for tip in data.get('tips', []):
        tip_text = tip.get('text', '').lower()
        for topic, config in COURSE_TOPICS.items():
            if any(kw in tip_text for kw in config['keywords']):
                categorized[topic]['tips'].append(tip)

    # Categorize techniques from mentions
    for video_id, techniques in data.get('techniques', {}).items():
        for technique in techniques:
            tech_lower = technique.lower()
            for topic, config in COURSE_TOPICS.items():
                if any(kw in tech_lower for kw in config['keywords']):
                    if technique not in categorized[topic]['techniques']:
                        categorized[topic]['techniques'].append(technique)

    # Categorize tools
    for video_id, tools in data.get('tools', {}).items():
        for tool in tools:
            tool_lower = tool.lower()
            for topic, config in COURSE_TOPICS.items():
                if any(kw in tool_lower for kw in config['keywords']):
                    if tool not in categorized[topic]['tools']:
                        categorized[topic]['tools'].append(tool)

    # Categorize repositories
    for repo in db.get('repositories', {}).get('github', []):
        repo_name = repo.get('name', '').lower()
        for topic, config in COURSE_TOPICS.items():
            if any(kw in repo_name for kw in config['keywords']):
                categorized[topic]['repositories'].append(repo)

    return categorized


def generate_course_outline(topic=None):
    """Generate course outline(s)."""
    db = load_database()
    data = load_extracted_data()
    categorized = categorize_content_by_topic(data, db)

    topics_to_generate = [topic] if topic else COURSE_TOPICS.keys()

    outlines = {}

    for t in topics_to_generate:
        if t not in COURSE_TOPICS:
            continue

        config = COURSE_TOPICS[t]
        content = categorized[t]

        outline = {
            'title': config['title'],
            'description': config['description'],
            'modules': []
        }

        # Module 1: Introduction
        outline['modules'].append({
            'number': 1,
            'title': 'Introduction',
            'lessons': [
                'What is ' + config['title'].split()[-1] + '?',
                'Why use it?',
                'Getting started',
                'Prerequisites and setup'
            ]
        })

        # Module 2: Core Concepts (based on techniques)
        if content['techniques']:
            outline['modules'].append({
                'number': 2,
                'title': 'Core Concepts',
                'lessons': content['techniques'][:6]
            })

        # Module 3: Tools & Setup
        if content['tools']:
            outline['modules'].append({
                'number': 3,
                'title': 'Tools & Setup',
                'lessons': [f"Using {tool}" for tool in content['tools'][:5]]
            })

        # Module 4: Best Practices (from tips)
        if content['tips']:
            outline['modules'].append({
                'number': 4,
                'title': 'Best Practices',
                'lessons': [
                    'Tips and tricks',
                    'Common mistakes to avoid',
                    'Optimization techniques',
                    'Real-world examples'
                ]
            })

        # Module 5: Advanced Topics
        outline['modules'].append({
            'number': len(outline['modules']) + 1,
            'title': 'Advanced Topics',
            'lessons': [
                'Advanced techniques',
                'Integration patterns',
                'Troubleshooting',
                'Next steps'
            ]
        })

        outlines[t] = outline

    return outlines


def generate_lesson_plans(topic=None):
    """Generate detailed lesson plans."""
    db = load_database()
    data = load_extracted_data()
    categorized = categorize_content_by_topic(data, db)
    analyses = load_analysis_files()

    topics_to_generate = [topic] if topic else COURSE_TOPICS.keys()
    lessons = {}

    for t in topics_to_generate:
        if t not in COURSE_TOPICS:
            continue

        config = COURSE_TOPICS[t]
        content = categorized[t]

        topic_lessons = []

        # Create lessons from tips
        tips_by_category = defaultdict(list)
        for tip in content['tips']:
            category = tip.get('category', 'general')
            tips_by_category[category].append(tip)

        for category, tips in tips_by_category.items():
            lesson = {
                'title': f"{category.replace('-', ' ').title()} Tips",
                'duration': '15-20 minutes',
                'objectives': [
                    f"Understand {category} best practices",
                    "Apply tips in real projects"
                ],
                'content': [tip.get('text', '') for tip in tips[:5]],
                'resources': []
            }

            # Add video references
            for tip in tips:
                if tip.get('video_id') and tip.get('timestamp'):
                    lesson['resources'].append({
                        'type': 'video',
                        'video_id': tip['video_id'],
                        'timestamp': tip['timestamp'],
                        'url': f"https://youtube.com/watch?v={tip['video_id']}&t={tip.get('timestamp_seconds', 0)}s"
                    })

            topic_lessons.append(lesson)

        # Create lessons from techniques
        for technique in content['techniques'][:5]:
            topic_lessons.append({
                'title': f"Working with {technique}",
                'duration': '20-30 minutes',
                'objectives': [
                    f"Understand {technique}",
                    f"Implement {technique} in your workflow"
                ],
                'content': [f"Deep dive into {technique}"],
                'resources': []
            })

        lessons[t] = {
            'topic': config['title'],
            'lessons': topic_lessons
        }

    return lessons


def generate_cheatsheet(topic=None):
    """Generate quick reference cheatsheet."""
    db = load_database()
    data = load_extracted_data()
    categorized = categorize_content_by_topic(data, db)

    topics_to_generate = [topic] if topic else COURSE_TOPICS.keys()
    cheatsheets = {}

    for t in topics_to_generate:
        if t not in COURSE_TOPICS:
            continue

        config = COURSE_TOPICS[t]
        content = categorized[t]

        sheet = {
            'title': f"{config['title']} - Quick Reference",
            'sections': []
        }

        # Key Techniques
        if content['techniques']:
            sheet['sections'].append({
                'title': 'Key Techniques',
                'items': content['techniques']
            })

        # Tools
        if content['tools']:
            sheet['sections'].append({
                'title': 'Tools',
                'items': content['tools']
            })

        # Top Tips
        if content['tips']:
            sheet['sections'].append({
                'title': 'Top Tips',
                'items': [tip.get('text', '')[:100] for tip in content['tips'][:10]]
            })

        # Useful Repositories
        if content['repositories']:
            sheet['sections'].append({
                'title': 'Repositories',
                'items': [f"{r.get('owner')}/{r.get('name')}" for r in content['repositories']]
            })

        cheatsheets[t] = sheet

    return cheatsheets


def export_markdown(topic=None):
    """Export course materials as markdown."""
    outlines = generate_course_outline(topic)
    lessons = generate_lesson_plans(topic)
    cheatsheets = generate_cheatsheet(topic)

    COURSE_DIR.mkdir(parents=True, exist_ok=True)

    exported_files = []

    for t, outline in outlines.items():
        filename = COURSE_DIR / f"{t}_course.md"

        md = f"# {outline['title']}\n\n"
        md += f"_{outline['description']}_\n\n"
        md += f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        md += "---\n\n"

        # Course Outline
        md += "## Course Outline\n\n"
        for module in outline['modules']:
            md += f"### Module {module['number']}: {module['title']}\n\n"
            for i, lesson in enumerate(module['lessons'], 1):
                md += f"{i}. {lesson}\n"
            md += "\n"

        # Lesson Details
        if t in lessons and lessons[t]['lessons']:
            md += "---\n\n## Lesson Details\n\n"
            for lesson in lessons[t]['lessons']:
                md += f"### {lesson['title']}\n\n"
                md += f"**Duration:** {lesson['duration']}\n\n"
                md += "**Objectives:**\n"
                for obj in lesson['objectives']:
                    md += f"- {obj}\n"
                md += "\n**Content:**\n"
                for item in lesson['content']:
                    md += f"- {item}\n"
                if lesson['resources']:
                    md += "\n**Resources:**\n"
                    for res in lesson['resources'][:3]:
                        if res['type'] == 'video':
                            md += f"- [Video at {res.get('timestamp', 'start')}]({res['url']})\n"
                md += "\n"

        # Cheatsheet
        if t in cheatsheets:
            md += "---\n\n## Quick Reference\n\n"
            for section in cheatsheets[t]['sections']:
                md += f"### {section['title']}\n\n"
                for item in section['items']:
                    md += f"- {item}\n"
                md += "\n"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md)

        exported_files.append(filename)
        print(f"Exported: {filename}")

    return exported_files


def export_html(topic=None):
    """Export course materials as HTML."""
    outlines = generate_course_outline(topic)
    lessons = generate_lesson_plans(topic)
    cheatsheets = generate_cheatsheet(topic)

    COURSE_DIR.mkdir(parents=True, exist_ok=True)

    exported_files = []

    for t, outline in outlines.items():
        config = COURSE_TOPICS[t]
        filename = COURSE_DIR / f"{t}_course.html"

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{outline['title']}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid #e94560;
            margin-bottom: 40px;
        }}
        h1 {{
            font-size: 2.5em;
            color: #e94560;
            margin-bottom: 10px;
        }}
        .subtitle {{ color: #888; font-size: 1.1em; }}
        h2 {{
            color: #58a6ff;
            margin: 40px 0 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }}
        h3 {{
            color: #e94560;
            margin: 25px 0 15px;
        }}
        .module {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border-left: 3px solid #e94560;
        }}
        .module-title {{
            color: #fff;
            font-size: 1.2em;
            margin-bottom: 15px;
        }}
        .module ol {{
            padding-left: 25px;
        }}
        .module li {{
            margin: 8px 0;
            color: #ccc;
        }}
        .lesson {{
            background: rgba(88, 166, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .lesson-title {{
            color: #58a6ff;
            font-size: 1.1em;
            margin-bottom: 10px;
        }}
        .duration {{
            color: #888;
            font-size: 0.9em;
            margin-bottom: 15px;
        }}
        .section {{
            background: rgba(233, 69, 96, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }}
        .section-title {{
            color: #e94560;
            margin-bottom: 10px;
        }}
        ul {{
            padding-left: 25px;
        }}
        li {{
            margin: 5px 0;
        }}
        a {{
            color: #58a6ff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .cheatsheet {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .cheat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 15px;
        }}
        .cheat-card h4 {{
            color: #e94560;
            margin-bottom: 10px;
        }}
        footer {{
            text-align: center;
            padding: 40px;
            color: #555;
            border-top: 1px solid #333;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{outline['title']}</h1>
            <p class="subtitle">{outline['description']}</p>
        </header>

        <main>
            <h2>Course Outline</h2>
'''

        for module in outline['modules']:
            html += f'''
            <div class="module">
                <div class="module-title">Module {module['number']}: {module['title']}</div>
                <ol>
'''
            for lesson in module['lessons']:
                html += f"                    <li>{lesson}</li>\n"
            html += '''                </ol>
            </div>
'''

        # Lessons
        if t in lessons and lessons[t]['lessons']:
            html += "\n            <h2>Lesson Details</h2>\n"
            for lesson in lessons[t]['lessons'][:5]:
                html += f'''
            <div class="lesson">
                <div class="lesson-title">{lesson['title']}</div>
                <div class="duration">Duration: {lesson['duration']}</div>
                <div class="section">
                    <div class="section-title">Objectives</div>
                    <ul>
'''
                for obj in lesson['objectives']:
                    html += f"                        <li>{obj}</li>\n"
                html += '''                    </ul>
                </div>
'''
                if lesson['content']:
                    html += '''                <div class="section">
                    <div class="section-title">Content</div>
                    <ul>
'''
                    for item in lesson['content']:
                        html += f"                        <li>{item}</li>\n"
                    html += '''                    </ul>
                </div>
'''
                html += "            </div>\n"

        # Cheatsheet
        if t in cheatsheets and cheatsheets[t]['sections']:
            html += "\n            <h2>Quick Reference</h2>\n"
            html += '            <div class="cheatsheet">\n'
            for section in cheatsheets[t]['sections']:
                html += f'''                <div class="cheat-card">
                    <h4>{section['title']}</h4>
                    <ul>
'''
                for item in section['items'][:8]:
                    html += f"                        <li>{item}</li>\n"
                html += '''                    </ul>
                </div>
'''
            html += "            </div>\n"

        html += f'''
        </main>

        <footer>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p>AI Knowledge Base - Course Materials</p>
        </footer>
    </div>
</body>
</html>
'''

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        exported_files.append(filename)
        print(f"Exported: {filename}")

    return exported_files


def show_stats():
    """Show content statistics for course materials."""
    db = load_database()
    data = load_extracted_data()
    categorized = categorize_content_by_topic(data, db)

    print("\n=== COURSE MATERIALS STATISTICS ===")
    print("="*50)

    for topic, config in COURSE_TOPICS.items():
        content = categorized[topic]
        total = (len(content['tutorials']) + len(content['tips']) +
                len(content['techniques']) + len(content['tools']) +
                len(content['repositories']))

        if total > 0:
            print(f"\n{config['title']}:")
            print(f"  Tutorials: {len(content['tutorials'])}")
            print(f"  Tips: {len(content['tips'])}")
            print(f"  Techniques: {len(content['techniques'])}")
            print(f"  Tools: {len(content['tools'])}")
            print(f"  Repositories: {len(content['repositories'])}")

    # Total extracted content
    print(f"\n{'='*50}")
    print("TOTAL EXTRACTED CONTENT:")
    print(f"  Tips: {len(data['tips'])}")
    print(f"  Tutorials analyzed: {len(db.get('tutorials', []))}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate course materials from AI knowledge base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Topics:
  claude-code       Claude Code mastery
  midjourney        Midjourney art creation
  image-generation  AI image generation (Flux, SDXL)
  prompt-engineering Prompt crafting techniques
  ai-coding         AI-assisted coding tools
  tts-voice         Text-to-speech models

Examples:
  python course_materials.py                        # Generate all materials
  python course_materials.py --topic claude-code    # Single topic
  python course_materials.py outline                # Course outlines only
  python course_materials.py lessons                # Lesson plans only
  python course_materials.py cheatsheet             # Quick reference only
  python course_materials.py export --format html   # Export as HTML
  python course_materials.py export --format md     # Export as Markdown
  python course_materials.py stats                  # Show statistics
        '''
    )

    parser.add_argument('--topic', '-t', choices=COURSE_TOPICS.keys(),
                       help='Generate for specific topic')

    subparsers = parser.add_subparsers(dest='command')

    # Outline command
    outline_parser = subparsers.add_parser('outline', help='Generate course outlines')
    outline_parser.add_argument('--topic', '-t', choices=COURSE_TOPICS.keys())

    # Lessons command
    lessons_parser = subparsers.add_parser('lessons', help='Generate lesson plans')
    lessons_parser.add_argument('--topic', '-t', choices=COURSE_TOPICS.keys())

    # Cheatsheet command
    cheat_parser = subparsers.add_parser('cheatsheet', help='Generate quick reference')
    cheat_parser.add_argument('--topic', '-t', choices=COURSE_TOPICS.keys())

    # Export command
    export_parser = subparsers.add_parser('export', help='Export course materials')
    export_parser.add_argument('--format', '-f', choices=['md', 'html'], default='html')
    export_parser.add_argument('--topic', '-t', choices=COURSE_TOPICS.keys())

    # Stats command
    subparsers.add_parser('stats', help='Show content statistics')

    args = parser.parse_args()

    topic = getattr(args, 'topic', None)

    if args.command == 'outline':
        outlines = generate_course_outline(topic)
        for t, outline in outlines.items():
            print(f"\n{'='*60}")
            print(f"{outline['title']}")
            print(f"{'='*60}")
            for module in outline['modules']:
                print(f"\nModule {module['number']}: {module['title']}")
                for i, lesson in enumerate(module['lessons'], 1):
                    print(f"  {i}. {lesson}")

    elif args.command == 'lessons':
        lessons = generate_lesson_plans(topic)
        for t, data in lessons.items():
            print(f"\n{'='*60}")
            print(f"{data['topic']} - Lessons")
            print(f"{'='*60}")
            for lesson in data['lessons']:
                print(f"\n{lesson['title']}")
                print(f"  Duration: {lesson['duration']}")

    elif args.command == 'cheatsheet':
        sheets = generate_cheatsheet(topic)
        for t, sheet in sheets.items():
            print(f"\n{'='*60}")
            print(f"{sheet['title']}")
            print(f"{'='*60}")
            for section in sheet['sections']:
                print(f"\n{section['title']}:")
                for item in section['items'][:5]:
                    print(f"  - {item}")

    elif args.command == 'export':
        if args.format == 'html':
            export_html(topic)
        else:
            export_markdown(topic)

    elif args.command == 'stats':
        show_stats()

    else:
        # Default: generate and export all
        print("Generating course materials...")
        export_html(topic)
        export_markdown(topic)
        print("\nDone! Course materials exported to:")
        print(f"  {COURSE_DIR}")


if __name__ == '__main__':
    main()
