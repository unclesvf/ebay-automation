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

        .impact-badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}

        .impact-high {{
            background: #ff4757;
            color: white;
        }}

        .impact-medium {{
            background: #ffa502;
            color: black;
        }}

        .metrics-row {{
            display: flex;
            gap: 1rem;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}

        .metric {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        .back-to-top {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--accent);
            color: white;
            padding: 0.75rem;
            border-radius: 50%;
            text-decoration: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: none;
            z-index: 100;
            font-size: 1.2rem;
        }}

        .back-to-top:hover {{
            background: var(--accent-hover);
        }}

        /* Collapsible Deep Dive sections */
        details {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin: 1rem 0;
            padding: 0;
        }}

        details summary {{
            padding: 1rem;
            cursor: pointer;
            font-weight: 600;
            color: var(--accent);
            list-style: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        details summary::-webkit-details-marker {{
            display: none;
        }}

        details summary::before {{
            content: '▶';
            font-size: 0.8rem;
            transition: transform 0.2s;
        }}

        details[open] summary::before {{
            transform: rotate(90deg);
        }}

        details .deep-dive-content {{
            padding: 0 1rem 1rem 1rem;
            border-top: 1px solid var(--border);
        }}

        /* Mermaid diagram container */
        .mermaid-container {{
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            overflow-x: auto;
        }}

        .mermaid {{
            text-align: center;
        }}

        /* Timestamp link styling */
        .timestamp-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: var(--accent);
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.8rem;
            text-decoration: none;
            transition: background 0.2s;
        }}

        .timestamp-link:hover {{
            background: var(--accent-hover);
            color: white;
        }}

        /* Workflow step styling */
        .workflow-step {{
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            margin: 0.75rem 0;
            padding: 0.5rem;
            border-radius: 6px;
            background: rgba(255,255,255,0.02);
        }}

        .step-number {{
            background: var(--accent);
            color: white;
            min-width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.85rem;
        }}

        .step-content {{
            flex: 1;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Persistent Nav -->
        <nav style="background: var(--bg-card); padding: 1rem; border-radius: 8px; margin-bottom: 2rem; display: flex; gap: 1rem; align-items: center; justify-content: space-between;">
            <div style="font-weight: bold; font-size: 1.1rem; color: var(--accent);">
                <a href="universal_insights.html" style="text-decoration: none; color: inherit;">AMBROSE Insights</a>
            </div>
            <div style="display: flex; gap: 1rem;">
                <a href="universal_insights.html" class="tag" style="text-decoration: none;">Dashboard</a>
                <a href="index.html" class="tag" style="text-decoration: none;">Index</a>
                <a href="tutorials.html" class="tag" style="text-decoration: none;">Tutorials</a>
                <a href="tips_by_topic.html" class="tag" style="text-decoration: none;">Tips</a>
                <a href="tool_mentions.html" class="tag" style="text-decoration: none;">Tools</a>
            </div>
        </nav>
"""

HTML_FOOTER = """
        <a href="#" class="back-to-top" id="backToTop">⬆️</a>
        <footer>
            Generated on {date} | AI Knowledge Base
        </footer>
        <!-- Mermaid.js for workflow diagrams -->
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            // Initialize Mermaid with dark theme
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'dark',
                themeVariables: {{
                    primaryColor: '#e94560',
                    primaryTextColor: '#eaeaea',
                    primaryBorderColor: '#4da8da',
                    lineColor: '#4da8da',
                    secondaryColor: '#16213e',
                    tertiaryColor: '#0f3460'
                }}
            }});

            // Back to top capability
            window.addEventListener('scroll', () => {{
                const btn = document.getElementById('backToTop');
                if (window.scrollY > 300) {{
                    btn.style.display = 'block';
                }} else {{
                    btn.style.display = 'none';
                }}
            }});
        </script>
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
    if not path:
        return "#"
    path = path.strip()
    if path.startswith('http'):
        return path
    return f"https://{path}"

def format_source(source):
    """Format source information for display."""
    if not source:
        return "Unknown source"

    parts = []
    author = source.get('author') or source.get('sender') or 'Unknown'
    parts.append(f"<strong>{author}</strong>")
    if source.get('date'):
        parts.append(source['date'])
    if source.get('type'):
        parts.append(f"({source['type']})")

    return " | ".join(parts) if parts else "Unknown source"

def timestamp_to_seconds(timestamp):
    """Convert timestamp string (e.g., '5:30' or '1:23:45') to seconds."""
    if not timestamp:
        return 0

    # Clean the timestamp - remove non-numeric/colon characters
    timestamp = ''.join(c for c in str(timestamp) if c.isdigit() or c == ':')
    if not timestamp:
        return 0

    parts = timestamp.split(':')
    try:
        if len(parts) == 3:  # H:M:S
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:  # M:S
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:  # Just seconds
            return int(parts[0])
    except (ValueError, IndexError):
        return 0
    return 0

def make_timestamped_url(video_id, timestamp):
    """Create a YouTube URL with timestamp parameter."""
    if not video_id:
        return '#'

    base_url = f"https://youtube.com/watch?v={video_id}"

    if timestamp:
        seconds = timestamp_to_seconds(timestamp)
        if seconds > 0:
            return f"{base_url}&t={seconds}s"

    return base_url

def generate_mermaid_workflow(steps):
    """Generate a Mermaid flowchart from workflow steps."""
    if not steps or len(steps) < 2:
        return None

    # Limit to first 8 steps to keep diagram readable
    display_steps = steps[:8]

    lines = ['graph TD']
    for i, step in enumerate(display_steps):
        # Sanitize step text for Mermaid (remove special chars, limit length)
        safe_text = step.replace('"', "'").replace('\n', ' ')[:50]
        if len(step) > 50:
            safe_text += '...'

        node_id = f"S{i+1}"
        lines.append(f'    {node_id}["{i+1}. {safe_text}"]')

        if i > 0:
            prev_id = f"S{i}"
            lines.append(f'    {prev_id} --> {node_id}')

    # Add styling
    lines.append('    style S1 fill:#e94560,color:#fff')
    if len(display_steps) > 1:
        lines.append(f'    style S{len(display_steps)} fill:#4ade80,color:#000')

    return '\n'.join(lines)

# =============================================================================
# REPORT GENERATORS
# =============================================================================

def generate_universal_insights_report(db):
    """Generate the 'Universal Insights' dashboard ranking all content by impact."""
    html = HTML_HEAD.format(title="Universal AI Insights - Dashboard")
    
    # Collect all items
    all_items = []
    
    # helper to normalize items
    def add_items(source_list, type_label, icon_class):
        for item in source_list:
            source = item.get('source', {})
            impact = source.get('impact_score', 0)
            metrics = source.get('metrics', {})
            
            # Boost score for recent items if impact is 0
            date_found = item.get('date_found', '')
            is_recent = date_found == datetime.now().strftime('%Y-%m-%d')
            if impact == 0 and is_recent:
                impact = 10 # Baseline for new items
                
            all_items.append({
                'title': item.get('name') or item.get('title') or item.get('code') or 'Unknown',
                'url': item.get('url') or '#',
                'type': type_label,
                'icon_class': icon_class,
                'impact': impact,
                'metrics': metrics,
                'date': date_found,
                'author': source.get('author', 'Unknown'),
                'owner': item.get('owner'), # specific for repos
                'source_obj': source
            })

    # Add from all sources
    add_items(db['repositories']['github'], 'GitHub Repo', 'github')
    add_items(db['repositories']['huggingface'], 'HF Model', 'huggingface')
    add_items(db['tutorials'], 'Tutorial', 'youtube')
    add_items(db['styles']['midjourney_sref'], 'Style Code', 'sref')
    
    # Sort by impact score descending
    all_items.sort(key=lambda x: x['impact'], reverse=True)
    
    # Top 50 items only for the dashboard
    top_items = all_items[:50]
    
    html += """
        <header>
            <h1>Universal AI Insights</h1>
            <p class="subtitle">Unified view of top-tier AI content ranking by impact & engagement</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Main Index</a>
                <a href="tutorials.html" class="nav-link">Tutorials</a>
                <a href="tips_by_topic.html" class="nav-link">Tips</a>
            </div>
        </header>

        <section>
            <h2>🔥 Trending Now (Top 50)</h2>
            <div class="card-grid">
    """
    
    for item in top_items:
        impact_class = 'impact-high' if item['impact'] > 50 else 'impact-medium'
        metrics_html = ""
        m = item['metrics']
        if m:
            parts = []
            if m.get('views'): parts.append(f"👁️ {m['views']:,}")
            if m.get('likes'): parts.append(f"❤️ {m['likes']:,}")
            if m.get('reposts'): parts.append(f"🔁 {m['reposts']:,}")
            metrics_html = f'<div class="metrics-row">{" ".join(parts)}</div>'
            
        html += f"""
            <div class="card">
                <div class="impact-badge {impact_class}">Impact Score: {item['impact']}</div>
                <div class="card-title">
                    <a href="{make_url(item['url'])}" target="_blank">{item['title']}</a>
                </div>
                <div class="card-meta">
                    <span class="tag {item['icon_class']}">{item['type']}</span>
                    {item['date']}
                </div>
                <div class="card-source">
                    Author: <strong>{item['author']}</strong>
                </div>
                {metrics_html}
            </div>
        """
        
    html += """
            </div>
        </section>
    """
    
    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))
    return html

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

    # Quick Access TOC
    html += """
        <div class="toc-container" style="background: var(--bg-secondary); padding: 1.5rem; border-radius: 8px; margin-bottom: 2rem;">
            <h3 style="margin-bottom: 1rem; color: var(--text-primary);">Quick Access</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
    """
    for category in sorted(tips_by_category.keys()):
        count = len(tips_by_category[category])
        display_name = category.replace('-', ' ').replace('_', ' ').title()
        html += f'<a href="#{category}" class="tag" style="text-decoration: none; color: var(--text-primary); cursor: pointer;">{display_name} ({count})</a>'
    
    html += """
            </div>
        </div>
    """

    # Generate category sections
    for category in sorted(tips_by_category.keys()):
        category_tips = tips_by_category[category]
        display_category = category.replace('-', ' ').replace('_', ' ').title()

        html += f"""
        <section id="{category}">
            <h2>{display_category} ({len(category_tips)} tips)</h2>
            <div class="card-grid">
        """

        for tip in category_tips:
            video_id = tip.get('source_video', '')
            video_title = tip.get('source_title', 'Unknown')
            timestamp = tip.get('timestamp_approx', '')

            # Create timestamped URL for direct jump to video moment
            video_url = make_timestamped_url(video_id, timestamp)

            # Timestamp link that jumps directly to that moment
            timestamp_html = ''
            if timestamp and video_id:
                timestamp_html = f'<a href="{video_url}" target="_blank" class="timestamp-link">⏱️ {timestamp}</a>'
            elif timestamp:
                timestamp_html = f'<span class="tag">~{timestamp}</span>'

            html += f"""
                <div class="card">
                    <p style="margin-bottom: 1rem;">{tip.get('text', '')}</p>
                    <div class="card-meta">
                        {timestamp_html}
                    </div>
                    <div class="card-source">
                        <a href="{make_timestamped_url(video_id, None)}" target="_blank">{video_title}</a>
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
    """Generate step-by-step workflows report with category grouping."""
    html = HTML_HEAD.format(title="Workflows - AI Knowledge Base")

    workflows = extracted_data.get('workflows', [])
    
    # Categorize workflows by first significant word in name
    categories = {}
    for workflow in workflows:
        name = workflow.get('name', 'Unnamed Workflow')
        # Extract category from name (first word or common patterns)
        words = name.split()
        if words:
            first_word = words[0].lower()
            # Normalize common categories
            if first_word in ['how', 'step', 'steps']:
                first_word = words[1].lower() if len(words) > 1 else 'general'
            elif first_word in ['setting', 'set']:
                first_word = 'setup'
            elif first_word in ['creating', 'create']:
                first_word = 'creation'
            elif first_word in ['using', 'use']:
                first_word = 'usage'
            elif first_word in ['building', 'build']:
                first_word = 'building'
            
            # Capitalize for display
            category = first_word.capitalize()
        else:
            category = 'General'
            
        if category not in categories:
            categories[category] = []
        categories[category].append(workflow)
    
    # Sort categories alphabetically
    sorted_categories = sorted(categories.keys())

    html += """
        <header>
            <h1>Step-by-Step Workflows</h1>
            <p class="subtitle">{count} workflows in {cat_count} categories</p>
            <div class="nav-links">
                <a href="index.html" class="nav-link">Back to Index</a>
                <a href="tips_by_topic.html" class="nav-link">Tips</a>
                <a href="tool_mentions.html" class="nav-link">Tools</a>
            </div>
        </header>
    """.format(count=len(workflows), cat_count=len(categories))

    # Table of Contents
    html += """
        <section>
            <h2>📑 Quick Navigation</h2>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 2rem;">
    """
    for cat in sorted_categories:
        count = len(categories[cat])
        html += f'<a href="#{cat.lower()}" class="tag" style="text-decoration: none;">{cat} ({count})</a>'
    html += "</div></section>"

    # Grouped workflows
    for category in sorted_categories:
        cat_workflows = categories[category]
        html += f"""
            <section id="{category.lower()}">
                <h2 style="border-left: 4px solid var(--accent); padding-left: 1rem;">{category} ({len(cat_workflows)})</h2>
        """
        
        for workflow in cat_workflows:
            video_id = workflow.get('source_video', '')
            video_title = workflow.get('source_title', 'Unknown')
            video_url = f"https://youtube.com/watch?v={video_id}" if video_id else '#'
            steps = workflow.get('steps', [])
            prereqs = workflow.get('prerequisites', [])

            # Determine if this is a complex workflow (many steps/prereqs)
            is_complex = len(steps) >= 5 or len(prereqs) >= 3

            html += f"""
                <div class="card" style="margin-bottom: 1.5rem;">
                    <div class="card-title" style="font-size: 1.4rem; color: var(--accent);">
                        {workflow.get('name', 'Unnamed Workflow')}
                    </div>
            """

            # Generate Mermaid diagram for workflows with multiple steps
            mermaid_code = generate_mermaid_workflow(steps)
            if mermaid_code and len(steps) >= 3:
                html += f"""
                    <div class="mermaid-container">
                        <div class="mermaid">
{mermaid_code}
                        </div>
                    </div>
                """

            # For complex workflows, use collapsible Deep Dive section
            if is_complex:
                html += """
                    <details>
                        <summary>🔍 Deep Dive - Full Details</summary>
                        <div class="deep-dive-content">
                """

            # Prerequisites
            if prereqs:
                html += """
                    <div style="margin: 1rem 0;">
                        <strong>📋 Prerequisites:</strong>
                        <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                """
                for prereq in prereqs:
                    html += f"<li>{prereq}</li>"
                html += "</ul></div>"

            # Steps with enhanced styling
            if steps:
                html += """
                    <div style="margin: 1rem 0;">
                        <strong>📝 Steps:</strong>
                        <div style="margin-top: 0.5rem;">
                """
                for i, step in enumerate(steps, 1):
                    html += f"""
                        <div class="workflow-step">
                            <span class="step-number">{i}</span>
                            <span class="step-content">{step}</span>
                        </div>
                    """
                html += "</div></div>"

            # Close Deep Dive section if complex
            if is_complex:
                html += """
                        </div>
                    </details>
                """

            html += f"""
                    <div class="card-source">
                        Source: <a href="{video_url}" target="_blank">{video_title}</a>
                    </div>
                </div>
            """
        
        html += "</section>"

    if not workflows:
        html += '<div class="empty-state">No workflows extracted yet. Run extract_knowledge.py to extract workflows from transcripts.</div>'

    html += HTML_FOOTER.format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))

    return html

def generate_tool_mentions_report(extracted_data, db):
    """Generate tool mentions report showing which videos mention which tools."""
    html = HTML_HEAD.format(title="Tool Mentions - AI Knowledge Base")

    # Collect tool mentions from extracted data
    tools_data = extracted_data.get('tools', [])

    # Build tool -> videos mapping
    tool_videos = {}

    def is_valid_tool_name(name):
        """Filter out garbage tool names like numbers, single chars, etc."""
        if not name or len(name) < 2:
            return False
        # Reject pure numbers
        if name.isdigit():
            return False
        # Reject single special characters
        if name in ['-', '.', ':', ';', ',', '/', '\\', '|', '_']:
            return False
        # Reject very short names that are just punctuation/numbers
        if len(name) <= 2 and not name.isalpha():
            return False
        return True

    # From LLM extraction
    for tool in tools_data:
        tool_name = tool.get('name', '').lower()
        if tool_name and is_valid_tool_name(tool_name):
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

    # From tutorial database (populated by transcript_analyzer.py)
    for tutorial in db.get('tutorials', []):
        video_id = tutorial.get('video_id')
        video_title = tutorial.get('title')
        tools_mentioned = tutorial.get('tools_mentioned', [])

        # Skip if video title is unknown/missing
        if not video_title or video_title in ['Unknown', 'Unknown Title']:
            continue

        for tool_name in tools_mentioned:
            tool_lower = tool_name.lower()
            if not is_valid_tool_name(tool_lower):
                continue
            if tool_lower not in tool_videos:
                tool_videos[tool_lower] = {
                    'name': tool_name,
                    'videos': [],
                    'contexts': []
                }
            if video_id and video_id not in [v['id'] for v in tool_videos[tool_lower]['videos']]:
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

    # Sort alphabetically by tool name
    for tool_key in sorted(tool_videos.keys()):
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
    """Generate interactive transcript search page with live API search."""
    html = HTML_HEAD.format(title="Transcript Search - AI Knowledge Base")

    # Add search-specific styles
    html = html.replace('</style>', """
        .search-container {
            background: var(--bg-secondary);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }

        .search-form {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: flex-end;
        }

        .search-field {
            flex: 1;
            min-width: 300px;
        }

        .search-field label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .search-input {
            width: 100%;
            padding: 1rem;
            font-size: 1.1rem;
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
        }

        .search-input:focus {
            outline: none;
            border-color: var(--accent);
        }

        .search-input::placeholder {
            color: var(--text-secondary);
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
            height: fit-content;
        }

        .search-btn:hover {
            background: var(--accent-hover);
        }

        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .search-stats {
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        .search-results {
            margin-top: 2rem;
        }

        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .results-count {
            color: var(--text-secondary);
        }

        .result-item {
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            border-left: 3px solid var(--accent);
            transition: transform 0.2s;
        }

        .result-item:hover {
            transform: translateX(4px);
        }

        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }

        .result-video-title {
            font-weight: 600;
            color: var(--link);
            text-decoration: none;
        }

        .result-video-title:hover {
            color: var(--link-hover);
        }

        .result-timestamp {
            display: inline-block;
            background: var(--accent);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
            text-decoration: none;
            transition: background 0.2s;
        }

        .result-timestamp:hover {
            background: var(--accent-hover);
        }

        .result-text {
            margin: 1rem 0;
            line-height: 1.8;
            color: var(--text-primary);
        }

        .result-meta {
            display: flex;
            gap: 1rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        .search-tips {
            background: var(--bg-card);
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1.5rem;
            font-size: 0.9rem;
        }

        .search-tips code {
            background: var(--bg-primary);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }

        #loading {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }

        #error-message {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #ef4444;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            display: none;
        }

        .highlight {
            background: rgba(233, 69, 96, 0.3);
            padding: 0.1rem 0.2rem;
            border-radius: 2px;
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
            <form class="search-form" id="searchForm" onsubmit="performSearch(event)">
                <div class="search-field">
                    <label for="query">Search Query</label>
                    <input type="text" id="query" class="search-input" placeholder="e.g., CLAUDE.md setup, MCP server, best practices..." autofocus>
                </div>
                <div class="search-field" style="min-width: 150px; flex: 0.3;">
                    <label for="limit">Results</label>
                    <select id="limit" class="search-input" style="padding: 0.9rem 1rem;">
                        <option value="10">10</option>
                        <option value="20" selected>20</option>
                        <option value="50">50</option>
                    </select>
                </div>
                <button type="submit" class="search-btn" id="searchBtn">Search</button>
            </form>

            <div class="search-stats" id="indexStats">
                Loading index stats...
            </div>

            <div class="search-tips">
                <strong>Search Tips:</strong>
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    <li>Use quotes for exact phrases: <code>"plan mode"</code></li>
                    <li>Use OR for alternatives: <code>cursor OR vscode</code></li>
                    <li>Use * for prefix matching: <code>config*</code></li>
                </ul>
            </div>
        </div>

        <div id="error-message"></div>

        <div id="loading" style="display: none;">
            <p>Searching transcripts...</p>
        </div>

        <div class="search-results" id="results" style="display: none;">
            <div class="results-header">
                <h2>Results</h2>
                <span class="results-count" id="resultsCount"></span>
            </div>
            <div id="resultsList"></div>
        </div>

        <script>
            const API_BASE = window.location.port === '5173' || window.location.port === '5174'
                ? 'http://localhost:8001'  // FastAPI server port (vLLM uses 8000)
                : '';

            // Load index stats on page load
            async function loadStats() {
                try {
                    const resp = await fetch(`${API_BASE}/search/stats`);
                    const data = await resp.json();
                    if (data.indexed) {
                        document.getElementById('indexStats').innerHTML = `
                            <span><strong>${data.total_transcripts}</strong> videos indexed</span>
                            <span><strong>${data.total_segments.toLocaleString()}</strong> searchable segments</span>
                            <span><strong>${data.channels?.length || 0}</strong> channels</span>
                        `;
                    } else {
                        document.getElementById('indexStats').innerHTML = 'Search index not available. Run transcript_search.py --index to build it.';
                    }
                } catch (e) {
                    document.getElementById('indexStats').innerHTML = 'Could not load index stats';
                }
            }

            async function performSearch(event) {
                event.preventDefault();

                const query = document.getElementById('query').value.trim();
                const limit = document.getElementById('limit').value;

                if (!query) {
                    showError('Please enter a search query');
                    return;
                }

                const searchBtn = document.getElementById('searchBtn');
                const loading = document.getElementById('loading');
                const results = document.getElementById('results');
                const errorMsg = document.getElementById('error-message');

                searchBtn.disabled = true;
                loading.style.display = 'block';
                results.style.display = 'none';
                errorMsg.style.display = 'none';

                try {
                    const resp = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=${limit}`);

                    if (!resp.ok) {
                        const err = await resp.json();
                        throw new Error(err.detail || 'Search failed');
                    }

                    const data = await resp.json();
                    displayResults(data, query);

                } catch (e) {
                    showError(e.message);
                } finally {
                    searchBtn.disabled = false;
                    loading.style.display = 'none';
                }
            }

            function showError(message) {
                const errorMsg = document.getElementById('error-message');
                errorMsg.textContent = message;
                errorMsg.style.display = 'block';
            }

            function highlightText(text, query) {
                const words = query.replace(/["*]/g, '').split(/\\s+OR\\s+|\\s+/i).filter(w => w.length > 2);
                let highlighted = text;
                words.forEach(word => {
                    const regex = new RegExp(`(${word})`, 'gi');
                    highlighted = highlighted.replace(regex, '<span class="highlight">$1</span>');
                });
                return highlighted;
            }

            function displayResults(data, query) {
                const results = document.getElementById('results');
                const resultsList = document.getElementById('resultsList');
                const resultsCount = document.getElementById('resultsCount');

                resultsCount.textContent = `${data.count} results found`;

                if (data.results.length === 0) {
                    resultsList.innerHTML = '<p style="color: var(--text-secondary); padding: 2rem; text-align: center;">No results found. Try different keywords or check spelling.</p>';
                } else {
                    resultsList.innerHTML = data.results.map(r => `
                        <div class="result-item">
                            <div class="result-header">
                                <a href="https://youtube.com/watch?v=${r.video_id}" target="_blank" class="result-video-title">
                                    ${r.title}
                                </a>
                                <a href="${r.url}" target="_blank" class="result-timestamp">
                                    ⏱️ ${r.timestamp}
                                </a>
                            </div>
                            <div class="result-text">${highlightText(r.text, query)}</div>
                            <div class="result-meta">
                                <span>📺 ${r.channel}</span>
                                ${r.topics.length ? `<span>🏷️ ${r.topics.join(', ')}</span>` : ''}
                            </div>
                        </div>
                    `).join('');
                }

                results.style.display = 'block';
            }

            // Initialize
            loadStats();

            // Allow Enter key to search
            document.getElementById('query').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    performSearch(e);
                }
            });
        </script>
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
        ('universal_insights.html', generate_universal_insights_report(db)),
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
