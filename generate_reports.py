"""
Generate Reports - Creates HTML reports from the AI Knowledge Base
Generates category-specific reports and a main index page.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
from datetime import datetime

# Paths
MASTER_DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'
URL_CACHE_PATH = r'D:\AI-Knowledge-Base\url_cache.json'
EXPORTS_PATH = r'D:\AI-Knowledge-Base\exports'
EXTRACTED_PATH = r'D:\AI-Knowledge-Base\extracted'
SEARCH_INDEX_PATH = r'D:\AI-Knowledge-Base\tutorials\search_index.db'

# =============================================================================
# HTML TEMPLATES
# =============================================================================

HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-card: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --accent: #e94560;
            --accent-hover: #ff6b6b;
            --link: #4da8da;
            --link-hover: #7ec8e3;
            --border: #2a2a4a;
            --success: #4ade80;
            --warning: #fbbf24;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        header {{
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-card));
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            border: 1px solid var(--border);
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, var(--accent), var(--link));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}

        .stats {{
            display: flex;
            gap: 2rem;
            margin-top: 1.5rem;
            flex-wrap: wrap;
        }}

        .stat {{
            background: var(--bg-primary);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}

        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent);
        }}

        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}

        .card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }}

        .card {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }}

        .card-title {{
            font-size: 1.2rem;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }}

        .card-title a {{
            color: var(--link);
            text-decoration: none;
        }}

        .card-title a:hover {{
            color: var(--link-hover);
            text-decoration: underline;
        }}

        .card-meta {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 0.75rem;
        }}

        .card-source {{
            background: var(--bg-primary);
            padding: 0.75rem;
            border-radius: 6px;
            font-size: 0.85rem;
            margin-top: 0.75rem;
        }}

        .tag {{
            display: inline-block;
            background: var(--bg-card);
            color: var(--text-secondary);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            margin-right: 0.5rem;
            margin-top: 0.5rem;
        }}

        .tag.github {{
            background: #238636;
            color: white;
        }}

        .tag.huggingface {{
            background: #ff9d00;
            color: black;
        }}

        .tag.youtube {{
            background: #ff0000;
            color: white;
        }}

        .tag.sref {{
            background: #5865f2;
            color: white;
        }}

        section {{
            margin-bottom: 3rem;
        }}

        section h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--accent);
            display: inline-block;
        }}

        .nav-links {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }}

        .nav-link {{
            background: var(--bg-card);
            color: var(--text-primary);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            text-decoration: none;
            transition: background 0.2s;
        }}

        .nav-link:hover {{
            background: var(--accent);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}

        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: var(--bg-card);
            font-weight: 600;
        }}

        tr:hover {{
            background: var(--bg-secondary);
        }}

        a {{
            color: var(--link);
        }}

        a:hover {{
            color: var(--link-hover);
        }}

        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--text-secondary);
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
            border-top: 1px solid var(--border);
            margin-top: 3rem;
        }}

        .url-list {{
            list-style: none;
            padding: 0;
        }}

        .url-list li {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
        }}

        .url-list li:hover {{
            background: var(--bg-secondary);
        }}

        .url-short {{
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}

        .url-expanded {{
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
"""

HTML_FOOTER = """
        <footer>
            Generated on {date} | AI Knowledge Base
        </footer>
    </div>
</body>
</html>
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_master_db():
    """Load the master database."""
    if os.path.exists(MASTER_DB_PATH):
        with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_url_cache():
    """Load the URL cache."""
    if os.path.exists(URL_CACHE_PATH):
        with open(URL_CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_extracted_knowledge():
    """Load all extracted knowledge files."""
    data = {
        'tips': [],
        'workflows': [],
        'prompts': [],
        'insights': [],
        'tools': []
    }

    # Load from individual knowledge files
    if os.path.exists(EXTRACTED_PATH):
        for filename in os.listdir(EXTRACTED_PATH):
            if filename.endswith('_knowledge.json'):
                filepath = os.path.join(EXTRACTED_PATH, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    video_id = knowledge.get('video_id', '')
                    video_title = knowledge.get('video_title', 'Unknown')

                    for tip in knowledge.get('tips', []):
                        tip['source_video'] = video_id
                        tip['source_title'] = video_title
                        data['tips'].append(tip)

                    for workflow in knowledge.get('workflows', []):
                        workflow['source_video'] = video_id
                        workflow['source_title'] = video_title
                        data['workflows'].append(workflow)

                    for prompt in knowledge.get('prompts', []):
                        prompt['source_video'] = video_id
                        prompt['source_title'] = video_title
                        data['prompts'].append(prompt)

                    for insight in knowledge.get('insights', []):
                        insight['source_video'] = video_id
                        insight['source_title'] = video_title
                        data['insights'].append(insight)

                    for tool in knowledge.get('tools_mentioned', []):
                        tool['source_video'] = video_id
                        tool['source_title'] = video_title
                        data['tools'].append(tool)

    return data

def load_tool_mentions():
    """Load tool mentions from extracted data."""
    filepath = os.path.join(EXTRACTED_PATH, 'tool_mentions.json')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def ensure_exports_dir():
    """Ensure the exports directory exists."""
    os.makedirs(EXPORTS_PATH, exist_ok=True)

def make_url(path):
    """Convert a path to a full URL."""
    if path.startswith('http'):
        return path
    return f"https://{path}"

def format_source(source):
    """Format source information for display."""
    if not source:
        return "Unknown source"

    parts = []
    if source.get('author'):
        parts.append(f"<strong>{source['author']}</strong>")
    if source.get('date'):
        parts.append(source['date'])
    if source.get('type'):
        parts.append(f"({source['type']})")

    return " | ".join(parts) if parts else "Unknown source"

# =============================================================================
# REPORT GENERATORS
# =============================================================================

def generate_index_report(db, url_cache):
    """Generate the main index page."""
    github_count = len(db['repositories']['github'])
    hf_count = len(db['repositories']['huggingface'])
    tutorial_count = len(db['tutorials'])
    sref_count = len(db['styles']['midjourney_sref'])
    cache_count = len(url_cache)

    # Count extracted knowledge
    extracted_data = load_extracted_knowledge()
    tips_count = len(extracted_data.get('tips', []))
    workflows_count = len(extracted_data.get('workflows', []))

    html = HTML_HEAD.format(title="AI Knowledge Base")

    html += """
        <header>
            <h1>AI Knowledge Base</h1>
            <p class="subtitle">Curated AI resources extracted from X/Twitter posts</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{github}</div>
                    <div class="stat-label">GitHub Repos</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{hf}</div>
                    <div class="stat-label">HuggingFace Models</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{tutorials}</div>
                    <div class="stat-label">Tutorials</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{tips}</div>
                    <div class="stat-label">Tips Extracted</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{workflows}</div>
                    <div class="stat-label">Workflows</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{sref}</div>
                    <div class="stat-label">Style Codes</div>
                </div>
            </div>
            <div class="nav-links">
                <a href="github_repos.html" class="nav-link">GitHub Repos</a>
                <a href="huggingface.html" class="nav-link">HuggingFace</a>
                <a href="tutorials.html" class="nav-link">Tutorials</a>
                <a href="styles.html" class="nav-link">Style Codes</a>
                <a href="tips_by_topic.html" class="nav-link">Tips</a>
                <a href="workflows.html" class="nav-link">Workflows</a>
                <a href="tool_mentions.html" class="nav-link">Tools</a>
                <a href="search.html" class="nav-link">Search</a>
                <a href="url_cache.html" class="nav-link">URL Cache</a>
            </div>
        </header>
    """.format(
        github=github_count,
        hf=hf_count,
        tutorials=tutorial_count,
        tips=tips_count,
        workflows=workflows_count,
        sref=sref_count
    )

    # Recent additions section
    html += """
        <section>
            <h2>Recent GitHub Repos</h2>
            <div class="card-grid">
    """

    for repo in db['repositories']['github'][:6]:
        url = make_url(repo['url'])
        html += f"""
                <div class="card">
                    <div class="card-title">
                        <a href="{url}" target="_blank">{repo.get('name', 'Unknown')}</a>
                    </div>
                    <div class="card-meta">
                        <span class="tag github">GitHub</span>
                        Owner: {repo.get('owner', 'Unknown')}
                    </div>
                    <div class="card-source">
                        {format_source(repo.get('source', {}))}
                    </div>
                </div>
        """

    html += """
            </div>
        </section>
    """

    # Recent HuggingFace
    if db['repositories']['huggingface']:
        html += """
        <section>
            <h2>HuggingFace Models</h2>
            <div class="card-grid">
        """

        for ref in db['repositories']['huggingface'][:6]:
            url = make_url(ref['url'])
            html += f"""
                <div class="card">
                    <div class="card-title">
                        <a href="{url}" target="_blank">{ref.get('name', 'Unknown')}</a>
                    </div>
                    <div class="card-meta">
                        <span class="tag huggingface">HuggingFace</span>
                        Owner: {ref.get('owner', 'Unknown')}
                    </div>
                    <div class="card-source">
                        {format_source(ref.get('source', {}))}
                    </div>
                </div>
            """

        html += """
            </div>
        </section>
        """

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_github_report(db):
    """Generate GitHub repositories report."""
    html = HTML_HEAD.format(title="GitHub Repositories - AI Knowledge Base")

    html += """
        <header>
            <h1>GitHub Repositories</h1>
            <p class="subtitle">{count} repositories discovered from AI-related posts</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
            </div>
        </header>
    """.format(count=len(db['repositories']['github']))

    html += """
        <section>
            <div class="card-grid">
    """

    for repo in db['repositories']['github']:
        url = make_url(repo['url'])
        html += f"""
                <div class="card">
                    <div class="card-title">
                        <a href="{url}" target="_blank">{repo.get('owner', '')}/{repo.get('name', 'Unknown')}</a>
                    </div>
                    <div class="card-meta">
                        <span class="tag github">GitHub</span>
                        Found: {repo.get('date_found', 'Unknown')}
                    </div>
                    <div class="card-source">
                        {format_source(repo.get('source', {}))}
                    </div>
                </div>
        """

    if not db['repositories']['github']:
        html += '<div class="empty-state">No GitHub repositories found yet.</div>'

    html += """
            </div>
        </section>
    """

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_huggingface_report(db):
    """Generate HuggingFace models report."""
    html = HTML_HEAD.format(title="HuggingFace Models - AI Knowledge Base")

    html += """
        <header>
            <h1>HuggingFace Models</h1>
            <p class="subtitle">{count} models and datasets discovered</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
            </div>
        </header>
    """.format(count=len(db['repositories']['huggingface']))

    html += """
        <section>
            <div class="card-grid">
    """

    for ref in db['repositories']['huggingface']:
        url = make_url(ref['url'])
        html += f"""
                <div class="card">
                    <div class="card-title">
                        <a href="{url}" target="_blank">{ref.get('owner', '')}/{ref.get('name', 'Unknown')}</a>
                    </div>
                    <div class="card-meta">
                        <span class="tag huggingface">HuggingFace</span>
                        Found: {ref.get('date_found', 'Unknown')}
                    </div>
                    <div class="card-source">
                        {format_source(ref.get('source', {}))}
                    </div>
                </div>
        """

    if not db['repositories']['huggingface']:
        html += '<div class="empty-state">No HuggingFace models found yet.</div>'

    html += """
            </div>
        </section>
    """

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_tutorials_report(db):
    """Generate tutorials report."""
    html = HTML_HEAD.format(title="Tutorials - AI Knowledge Base")

    html += """
        <header>
            <h1>Video Tutorials</h1>
            <p class="subtitle">{count} tutorials discovered</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
            </div>
        </header>
    """.format(count=len(db['tutorials']))

    html += """
        <section>
            <div class="card-grid">
    """

    for tutorial in db['tutorials']:
        url = make_url(tutorial['url'])
        video_id = tutorial.get('video_id', '')
        thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else ""

        html += f"""
                <div class="card">
                    <div class="card-title">
                        <a href="{url}" target="_blank">
                            {tutorial.get('title') or f'Video: {video_id}'}
                        </a>
                    </div>
                    <div class="card-meta">
                        <span class="tag youtube">YouTube</span>
                        Found: {tutorial.get('date_found', 'Unknown')}
                    </div>
                    <div class="card-source">
                        {format_source(tutorial.get('source', {}))}
                    </div>
                </div>
        """

    if not db['tutorials']:
        html += '<div class="empty-state">No tutorials found yet.</div>'

    html += """
            </div>
        </section>
    """

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_styles_report(db):
    """Generate Midjourney style codes report."""
    html = HTML_HEAD.format(title="Style Codes - AI Knowledge Base")

    html += """
        <header>
            <h1>Midjourney Style Codes</h1>
            <p class="subtitle">{count} --sref codes discovered</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
            </div>
        </header>
    """.format(count=len(db['styles']['midjourney_sref']))

    html += """
        <section>
            <div class="card-grid">
    """

    for style in db['styles']['midjourney_sref']:
        html += f"""
                <div class="card">
                    <div class="card-title">
                        <span class="tag sref">--sref {style.get('code', 'Unknown')}</span>
                    </div>
                    <div class="card-meta">
                        Found: {style.get('date_found', 'Unknown')}
                    </div>
                    {f'<p>{style["description"]}</p>' if style.get('description') else ''}
                    <div class="card-source">
                        {format_source(style.get('source', {}))}
                    </div>
                </div>
        """

    if not db['styles']['midjourney_sref']:
        html += '<div class="empty-state">No style codes found yet.</div>'

    html += """
            </div>
        </section>
    """

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_url_cache_report(url_cache):
    """Generate URL cache report showing all expanded t.co links."""
    html = HTML_HEAD.format(title="URL Cache - AI Knowledge Base")

    html += """
        <header>
            <h1>Expanded URL Cache</h1>
            <p class="subtitle">{count} t.co links expanded</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
            </div>
        </header>
    """.format(count=len(url_cache))

    html += """
        <section>
            <table>
                <thead>
                    <tr>
                        <th>Short URL</th>
                        <th>Expanded URL</th>
                    </tr>
                </thead>
                <tbody>
    """

    for short_url, expanded_url in sorted(url_cache.items()):
        if expanded_url:
            # Truncate long URLs for display
            display_url = expanded_url[:80] + '...' if len(expanded_url) > 80 else expanded_url
            html += f"""
                    <tr>
                        <td><a href="{short_url}" target="_blank">{short_url}</a></td>
                        <td><a href="{expanded_url}" target="_blank" title="{expanded_url}">{display_url}</a></td>
                    </tr>
            """

    html += """
                </tbody>
            </table>
        </section>
    """

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_tips_by_topic_report(extracted_data):
    """Generate tips grouped by topic/category report."""
    html = HTML_HEAD.format(title="Tips by Topic - AI Knowledge Base")

    tips = extracted_data.get('tips', [])

    # Group tips by category
    tips_by_category = {}
    for tip in tips:
        category = tip.get('category', 'general')
        if category not in tips_by_category:
            tips_by_category[category] = []
        tips_by_category[category].append(tip)

    html += """
        <header>
            <h1>Tips by Topic</h1>
            <p class="subtitle">{count} actionable tips extracted from tutorials</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{categories}</div>
                    <div class="stat-label">Categories</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{tips}</div>
                    <div class="stat-label">Total Tips</div>
                </div>
            </div>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
                <a href="workflows.html" class="nav-link">Workflows</a>
                <a href="tool_mentions.html" class="nav-link">Tools</a>
            </div>
        </header>
    """.format(
        count=len(tips),
        categories=len(tips_by_category),
        tips=len(tips)
    )

    # Generate category sections
    for category in sorted(tips_by_category.keys()):
        category_tips = tips_by_category[category]
        display_category = category.replace('-', ' ').replace('_', ' ').title()

        html += f"""
        <section>
            <h2>{display_category} ({len(category_tips)} tips)</h2>
            <div class="card-grid">
        """

        for tip in category_tips:
            video_id = tip.get('source_video', '')
            video_title = tip.get('source_title', 'Unknown')
            timestamp = tip.get('timestamp_approx', '')
            video_url = f"https://youtube.com/watch?v={video_id}" if video_id else '#'

            html += f"""
                <div class="card">
                    <p style="margin-bottom: 1rem;">{tip.get('text', '')}</p>
                    <div class="card-meta">
                        {f'<span class="tag">~{timestamp}</span>' if timestamp else ''}
                    </div>
                    <div class="card-source">
                        <a href="{video_url}" target="_blank">{video_title}</a>
                    </div>
                </div>
            """

        html += """
            </div>
        </section>
        """

    if not tips:
        html += '<div class="empty-state">No tips extracted yet. Run extract_knowledge.py to extract tips from transcripts.</div>'

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_workflows_report(extracted_data):
    """Generate step-by-step workflows report."""
    html = HTML_HEAD.format(title="Workflows - AI Knowledge Base")

    workflows = extracted_data.get('workflows', [])

    html += """
        <header>
            <h1>Step-by-Step Workflows</h1>
            <p class="subtitle">{count} workflows extracted from tutorials</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
                <a href="tips_by_topic.html" class="nav-link">Tips</a>
                <a href="tool_mentions.html" class="nav-link">Tools</a>
            </div>
        </header>
    """.format(count=len(workflows))

    html += "<section>"

    for workflow in workflows:
        video_id = workflow.get('source_video', '')
        video_title = workflow.get('source_title', 'Unknown')
        video_url = f"https://youtube.com/watch?v={video_id}" if video_id else '#'

        html += f"""
            <div class="card" style="margin-bottom: 1.5rem;">
                <div class="card-title" style="font-size: 1.4rem; color: var(--accent);">
                    {workflow.get('name', 'Unnamed Workflow')}
                </div>
        """

        # Prerequisites
        if workflow.get('prerequisites'):
            html += """
                <div style="margin: 1rem 0;">
                    <strong>Prerequisites:</strong>
                    <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
            """
            for prereq in workflow['prerequisites']:
                html += f"<li>{prereq}</li>"
            html += "</ul></div>"

        # Steps
        if workflow.get('steps'):
            html += """
                <div style="margin: 1rem 0;">
                    <strong>Steps:</strong>
                    <ol style="margin-top: 0.5rem; padding-left: 1.5rem;">
            """
            for step in workflow['steps']:
                html += f"<li style='margin: 0.5rem 0;'>{step}</li>"
            html += "</ol></div>"

        html += f"""
                <div class="card-source">
                    Source: <a href="{video_url}" target="_blank">{video_title}</a>
                </div>
            </div>
        """

    if not workflows:
        html += '<div class="empty-state">No workflows extracted yet. Run extract_knowledge.py to extract workflows from transcripts.</div>'

    html += "</section>"
    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_tool_mentions_report(extracted_data, db):
    """Generate tool mentions report showing which videos mention which tools."""
    html = HTML_HEAD.format(title="Tool Mentions - AI Knowledge Base")

    # Collect tool mentions from extracted data
    tools_data = extracted_data.get('tools', [])

    # Also get from transcript analyzer data
    tool_mentions_file = os.path.join(EXTRACTED_PATH, 'tool_mentions.json')
    analyzer_tools = {}
    if os.path.exists(tool_mentions_file):
        with open(tool_mentions_file, 'r', encoding='utf-8') as f:
            analyzer_tools = json.load(f)

    # Build tool -> videos mapping
    tool_videos = {}

    # From LLM extraction
    for tool in tools_data:
        tool_name = tool.get('name', '').lower()
        if tool_name:
            if tool_name not in tool_videos:
                tool_videos[tool_name] = {
                    'name': tool.get('name', ''),
                    'videos': [],
                    'contexts': []
                }
            video_id = tool.get('source_video', '')
            video_title = tool.get('source_title', '')
            if video_id and video_id not in [v['id'] for v in tool_videos[tool_name]['videos']]:
                tool_videos[tool_name]['videos'].append({
                    'id': video_id,
                    'title': video_title
                })
            if tool.get('context'):
                tool_videos[tool_name]['contexts'].append(tool['context'])

    # From transcript analyzer
    for video_id, tools in analyzer_tools.items():
        # Find video title
        video_title = 'Unknown'
        for tutorial in db.get('tutorials', []):
            if tutorial.get('video_id') == video_id:
                video_title = tutorial.get('title', 'Unknown')
                break

        for tool_name in tools:
            tool_lower = tool_name.lower()
            if tool_lower not in tool_videos:
                tool_videos[tool_lower] = {
                    'name': tool_name,
                    'videos': [],
                    'contexts': []
                }
            if video_id not in [v['id'] for v in tool_videos[tool_lower]['videos']]:
                tool_videos[tool_lower]['videos'].append({
                    'id': video_id,
                    'title': video_title
                })

    html += """
        <header>
            <h1>Tool Mentions</h1>
            <p class="subtitle">{count} tools mentioned across tutorials</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
                <a href="tips_by_topic.html" class="nav-link">Tips</a>
                <a href="workflows.html" class="nav-link">Workflows</a>
            </div>
        </header>
    """.format(count=len(tool_videos))

    html += """
        <section>
            <table>
                <thead>
                    <tr>
                        <th>Tool</th>
                        <th>Mentioned In</th>
                        <th>Context</th>
                    </tr>
                </thead>
                <tbody>
    """

    # Sort by number of mentions
    for tool_key in sorted(tool_videos.keys(), key=lambda x: -len(tool_videos[x]['videos'])):
        tool_info = tool_videos[tool_key]
        video_links = []
        for video in tool_info['videos'][:3]:
            url = f"https://youtube.com/watch?v={video['id']}"
            video_links.append(f'<a href="{url}" target="_blank">{video["title"][:30]}...</a>')

        contexts = tool_info['contexts'][:2] if tool_info['contexts'] else ['']
        context_text = '; '.join(contexts)[:100]

        html += f"""
                    <tr>
                        <td><strong>{tool_info['name']}</strong></td>
                        <td>{', '.join(video_links)}</td>
                        <td style="color: var(--text-secondary); font-size: 0.9rem;">{context_text}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </section>
    """

    if not tool_videos:
        html += '<div class="empty-state">No tool mentions found yet.</div>'

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_search_page():
    """Generate interactive transcript search page."""
    html = HTML_HEAD.format(title="Transcript Search - AI Knowledge Base")

    # Add search-specific styles
    html = html.replace('</style>', """
        .search-container {
            background: var(--bg-secondary);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }

        .search-input {
            width: 100%;
            padding: 1rem;
            font-size: 1.1rem;
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            margin-bottom: 1rem;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--accent);
        }

        .search-btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 1rem 2rem;
            font-size: 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .search-btn:hover {
            background: var(--accent-hover);
        }

        .search-results {
            margin-top: 2rem;
        }

        .result-item {
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 3px solid var(--accent);
        }

        .result-timestamp {
            display: inline-block;
            background: var(--accent);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
            margin-right: 0.5rem;
        }

        .result-text {
            margin: 1rem 0;
            line-height: 1.8;
        }

        .result-video {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .search-tips {
            background: var(--bg-card);
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-size: 0.9rem;
        }

        .search-tips code {
            background: var(--bg-primary);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }

        #loading {
            display: none;
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }

        .cli-command {
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 8px;
            font-family: monospace;
            margin-top: 1rem;
        }
    </style>""")

    html += """
        <header>
            <h1>Transcript Search</h1>
            <p class="subtitle">Search across all tutorial transcripts with timestamps</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
                <a href="tips_by_topic.html" class="nav-link">Tips</a>
                <a href="workflows.html" class="nav-link">Workflows</a>
            </div>
        </header>

        <div class="search-container">
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">
                This page provides instructions for using the CLI search tool.
                For real-time search, use the command-line interface.
            </p>

            <div class="cli-command">
                <strong>Quick Search Commands:</strong><br><br>
                <code>python transcript_search.py "your search query"</code><br><br>
                <code>python transcript_search.py "claude.md" --limit 10</code><br><br>
                <code>python transcript_search.py "plan mode" --topic claude-code</code>
            </div>

            <div class="search-tips">
                <strong>Search Tips:</strong>
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    <li>Use quotes for exact phrases: <code>"plan mode"</code></li>
                    <li>Use OR for alternatives: <code>cursor OR vscode</code></li>
                    <li>Filter by topic: <code>--topic claude-code</code></li>
                    <li>Filter by channel: <code>--channel "AI with Avthar"</code></li>
                    <li>Export results: <code>--export results.json</code></li>
                </ul>
            </div>
        </div>

        <section>
            <h2>Indexed Content</h2>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">
                The search index contains transcripts from tutorial videos.
                Each result includes a clickable timestamp link to jump directly to that moment in the video.
            </p>

            <div class="card-grid">
                <div class="card">
                    <div class="card-title">Full-Text Search</div>
                    <p>Search across all transcript text using SQLite FTS5 for fast, accurate results.</p>
                </div>
                <div class="card">
                    <div class="card-title">Timestamp Links</div>
                    <p>Every result includes a YouTube link with timestamp to jump directly to that moment.</p>
                </div>
                <div class="card">
                    <div class="card-title">Topic Filtering</div>
                    <p>Filter results by topic (claude-code, prompting, etc.) or channel name.</p>
                </div>
                <div class="card">
                    <div class="card-title">JSON Export</div>
                    <p>Export search results to JSON for further processing or integration.</p>
                </div>
            </div>
        </section>

        <section>
            <h2>Example Searches</h2>
            <div class="cli-command">
                # Find all mentions of CLAUDE.md<br>
                <code>python transcript_search.py "claude.md"</code><br><br>

                # Find best practices tips<br>
                <code>python transcript_search.py "best practice" --limit 20</code><br><br>

                # Search for MCP server setup<br>
                <code>python transcript_search.py "MCP server"</code><br><br>

                # Show search index statistics<br>
                <code>python transcript_search.py --stats</code><br><br>

                # Rebuild the search index<br>
                <code>python transcript_search.py --index</code>
            </div>
        </section>
    """

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

# =============================================================================
# MAIN
# =============================================================================

def generate_all_reports():
    """Generate all HTML reports."""
    print("=" * 80)
    print("GENERATING HTML REPORTS")
    print("=" * 80)

    # Load data
    db = load_master_db()
    if not db:
        print("ERROR: Could not load master_db.json")
        return

    url_cache = load_url_cache()
    extracted_data = load_extracted_knowledge()

    # Ensure exports directory exists
    ensure_exports_dir()

    # Core reports
    reports = [
        ('index.html', generate_index_report(db, url_cache)),
        ('github_repos.html', generate_github_report(db)),
        ('huggingface.html', generate_huggingface_report(db)),
        ('tutorials.html', generate_tutorials_report(db)),
        ('styles.html', generate_styles_report(db)),
        ('url_cache.html', generate_url_cache_report(url_cache)),
    ]

    # Knowledge extraction reports
    reports.extend([
        ('tips_by_topic.html', generate_tips_by_topic_report(extracted_data)),
        ('workflows.html', generate_workflows_report(extracted_data)),
        ('tool_mentions.html', generate_tool_mentions_report(extracted_data, db)),
        ('search.html', generate_search_page()),
    ])

    for filename, html_content in reports:
        filepath = os.path.join(EXPORTS_PATH, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"  Generated: {filename}")

    print("\n" + "-" * 80)
    print(f"Reports saved to: {EXPORTS_PATH}")
    print("-" * 80)
    print("\nTo view reports, open in browser:")
    print(f'  start chrome "{os.path.join(EXPORTS_PATH, "index.html")}"')

def main():
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage:")
        print("  python generate_reports.py          Generate all HTML reports")
        print("  python generate_reports.py --help   Show this help")
    else:
        generate_all_reports()

if __name__ == "__main__":
    main()
