from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import yaml
import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional
from fastapi.staticfiles import StaticFiles

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AmbroseServer")

app = FastAPI(title="Ambrose API")

# CORS for Dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "null"], # Vite Dev Server + static files
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'rules', 'scott_config.yaml')
LOG_PATH = os.path.join(BASE_DIR, 'orchestrator.log')
DB_PATH = r'D:\AI-Knowledge-Base\chromadb'
EXPORTS_PATH = r'D:\AI-Knowledge-Base\exports'
SEARCH_INDEX_PATH = r'D:\AI-Knowledge-Base\tutorials\search_index.db'

# Global State
ORCHESTRATOR_PROCESS = None

class ConfigUpdate(BaseModel):
    dry_run: bool

@app.get("/")
def read_root():
    return {"status": "Ambrose System Online", "version": "1.0"}

# Mount reports directory
if os.path.exists(EXPORTS_PATH):
    app.mount("/reports-static", StaticFiles(directory=EXPORTS_PATH), name="reports")

@app.get("/reports/list")
def list_reports():
    """List all available HTML reports."""
    reports = []
    report_metadata = {
        'index.html': {'name': 'Main Index', 'description': 'Overview of all Knowledge Base content', 'icon': '🏠'},
        'universal_insights.html': {'name': 'Universal Insights', 'description': 'Top content ranked by impact', 'icon': '📊'},
        'github_repos.html': {'name': 'GitHub Repos', 'description': 'Discovered GitHub repositories', 'icon': '🐙'},
        'huggingface.html': {'name': 'HuggingFace', 'description': 'ML models and datasets', 'icon': '🤗'},
        'tutorials.html': {'name': 'Tutorials', 'description': 'Video tutorials with transcripts', 'icon': '🎬'},
        'tips_by_topic.html': {'name': 'Tips by Topic', 'description': 'Actionable tips organized by category', 'icon': '💡'},
        'workflows.html': {'name': 'Workflows', 'description': 'Step-by-step guides with diagrams', 'icon': '🔄'},
        'tool_mentions.html': {'name': 'Tool Mentions', 'description': 'Tools mentioned across tutorials', 'icon': '🛠️'},
        'styles.html': {'name': 'Style Codes', 'description': 'Midjourney --sref codes', 'icon': '🎨'},
        'search.html': {'name': 'Search', 'description': 'Search across transcripts', 'icon': '🔍'},
        'url_cache.html': {'name': 'URL Cache', 'description': 'Expanded t.co links', 'icon': '🔗'},
        'models_report.html': {'name': 'AI Models', 'description': 'Tracked AI models and tools', 'icon': '🤖'},
    }

    if os.path.exists(EXPORTS_PATH):
        for filename in os.listdir(EXPORTS_PATH):
            if filename.endswith('.html'):
                filepath = os.path.join(EXPORTS_PATH, filename)
                stat = os.stat(filepath)
                meta = report_metadata.get(filename, {
                    'name': filename.replace('.html', '').replace('_', ' ').title(),
                    'description': 'Report',
                    'icon': '📄'
                })
                reports.append({
                    'filename': filename,
                    'name': meta['name'],
                    'description': meta['description'],
                    'icon': meta['icon'],
                    'url': f'/reports-static/{filename}',
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })

    # Sort by predefined order
    order = list(report_metadata.keys())
    reports.sort(key=lambda x: order.index(x['filename']) if x['filename'] in order else 999)

    return {'reports': reports, 'base_url': '/reports-static'}

@app.get("/search")
def search_transcripts(
    q: str,
    channel: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 20
):
    """
    Search YouTube transcripts using FTS5 full-text search.
    Returns timestamped results with links to video moments.
    """
    if not os.path.exists(SEARCH_INDEX_PATH):
        raise HTTPException(status_code=404, detail="Search index not found. Run transcript_search.py --index first.")

    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")

    try:
        conn = sqlite3.connect(SEARCH_INDEX_PATH)
        cursor = conn.cursor()

        # Escape special FTS5 characters
        def escape_fts_query(query):
            words = query.split()
            escaped = []
            for word in words:
                if any(c in word for c in '.+-^$()[]{}|\\:') and not word.startswith('"'):
                    escaped.append(f'"{word}"')
                else:
                    escaped.append(word)
            return ' '.join(escaped)

        fts_query = escape_fts_query(q.strip())

        # Build query
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

        if channel:
            sql += ' AND t.channel LIKE ?'
            params.append(f'%{channel}%')

        if topic:
            sql += ' AND t.topics LIKE ?'
            params.append(f'%{topic}%')

        sql += ' ORDER BY score LIMIT ?'
        params.append(min(limit, 100))  # Cap at 100

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Format results
        results = []
        for video_id, title, channel_name, topics_json, timestamp, text, score in rows:
            # Format timestamp
            ts = int(timestamp)
            if ts >= 3600:
                timestamp_str = f"{ts // 3600}:{(ts % 3600) // 60:02d}:{ts % 60:02d}"
            else:
                timestamp_str = f"{ts // 60}:{ts % 60:02d}"

            results.append({
                'video_id': video_id,
                'title': title or 'Unknown',
                'channel': channel_name or 'Unknown',
                'topics': json.loads(topics_json) if topics_json else [],
                'timestamp': timestamp_str,
                'timestamp_seconds': ts,
                'text': text,
                'url': f"https://youtube.com/watch?v={video_id}&t={ts}s",
                'score': round(score, 3)
            })

        # Get stats
        cursor.execute('SELECT COUNT(DISTINCT video_id) FROM transcript_fts')
        total_videos = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM transcript_fts')
        total_segments = cursor.fetchone()[0]

        conn.close()

        return {
            'query': q,
            'results': results,
            'count': len(results),
            'stats': {
                'total_videos': total_videos,
                'total_segments': total_segments
            }
        }

    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Search error: {str(e)}. Try using quotes for exact phrases.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search/stats")
def search_stats():
    """Get search index statistics."""
    if not os.path.exists(SEARCH_INDEX_PATH):
        return {'indexed': False, 'message': 'Search index not found'}

    try:
        conn = sqlite3.connect(SEARCH_INDEX_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM transcripts')
        total_transcripts = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM transcript_fts')
        total_segments = cursor.fetchone()[0]

        cursor.execute('SELECT channel, COUNT(*) as count FROM transcripts GROUP BY channel ORDER BY count DESC')
        channels = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            'indexed': True,
            'total_transcripts': total_transcripts,
            'total_segments': total_segments,
            'channels': channels,
            'db_path': SEARCH_INDEX_PATH
        }
    except Exception as e:
        return {'indexed': False, 'error': str(e)}

@app.get("/status")
def get_status():
    """Check system health and running status."""
    global ORCHESTRATOR_PROCESS
    is_running = ORCHESTRATOR_PROCESS is not None and ORCHESTRATOR_PROCESS.poll() is None
    
    # Check Ollama
    ollama_status = "Unknown"
    try:
        import requests
        resp = requests.get("http://localhost:11434")
        if resp.status_code == 200:
            ollama_status = "Online"
    except:
        ollama_status = "Offline"

    return {
        "orchestrator_running": is_running,
        "ollama_status": ollama_status,
        "model": "qwen2.5:32b" # hardcoded for now or read from config
    }

@app.get("/config")
def get_config():
    """Read current config."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    return {}

@app.post("/config/dry_run")
def update_dry_run(update: ConfigUpdate):
    """Toggle dry_run in config."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        config['global']['dry_run'] = update.dry_run
        
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(config, f)
            
        return {"status": "updated", "dry_run": update.dry_run}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
def run_orchestrator(background_tasks: BackgroundTasks):
    """Trigger the orchestrator."""
    global ORCHESTRATOR_PROCESS
    if ORCHESTRATOR_PROCESS is not None and ORCHESTRATOR_PROCESS.poll() is None:
        return {"status": "already_running"}
    
    cmd = ["python", os.path.join(BASE_DIR, "run_orchestrator.py"), CONFIG_PATH]
    
    # We run it as a subprocess
    try:
        # Open in new window or capture output? 
        # For server, we usually capture logs to file (which orchestrator does anyway)
        ORCHESTRATOR_PROCESS = subprocess.Popen(
            cmd, 
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return {"status": "started", "pid": ORCHESTRATOR_PROCESS.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
def get_logs(lines: int = 50):
    """Get last N lines of logs."""
    if not os.path.exists(LOG_PATH):
        return {"logs": []}
    
    try:
        # Simple tail implementation
        with open(LOG_PATH, 'r') as f:
            all_lines = f.readlines()
            return {"logs": all_lines[-lines:]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/knowledge")
def search_knowledge(query: str = "", limit: int = 20, threshold: float = 1.3):
    """Search or list knowledge base items."""
    # We need to load ChromaDB here
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        client = chromadb.PersistentClient(path=DB_PATH)
        # Must match the collection name used in ingest_db.py / KnowledgeBase class
        ef = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(name="uncles_wisdom", embedding_function=ef)
        
        if query:
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                include=["documents", "metadatas", "distances"]  # Include distance scores
            )
            # Flatten results structure
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            ids = results['ids'][0]
            distances = results.get('distances', [[]])[0]  # Lower = more similar
            
            items = []
            # Distance threshold - filter out low-similarity results
            # ChromaDB uses L2 distance: 0 = exact match, higher = less similar
            # Use the threshold parameter passed from frontend
            MAX_DISTANCE = threshold
            
            for i in range(len(ids)):
                # Only include results within similarity threshold
                if distances and i < len(distances) and distances[i] > MAX_DISTANCE:
                    continue  # Skip irrelevant results
                    
                items.append({
                    "id": ids[i],
                    "content": documents[i],
                    "metadata": metadatas[i],
                    "distance": distances[i] if distances and i < len(distances) else None
                })
            return {"items": items}
        else:
            # List recent (peek)
            results = collection.peek(limit=limit)
            # Similar structure but peek returns directly
            items = []
            if results['ids']:
                for i in range(len(results['ids'])):
                     items.append({
                        "id": results['ids'][i],
                        "content": results['documents'][i] if 'documents' in results and results['documents'] else "",
                        "metadata": results['metadatas'][i]
                    })
            # Start/Peek might behave differently depending on chromadb version, 
            # safe fallback: return raw or empty if complex
            return {"items": [], "raw_peek": str(results)} 

    except Exception as e:
        return {"error": str(e)}

@app.get("/insights")
def get_insights(limit: int = 50, sort_by: str = "impact"):
    """
    Get unified insights across all sources, sorted by impact score.
    Returns: { items: [...], timeline: {...}, top_authors: [...] }
    """
    try:
        # Load master database
        master_db_path = r'D:\AI-Knowledge-Base\master_db.json'
        if not os.path.exists(master_db_path):
            return {"items": [], "timeline": {}, "top_authors": []}
        
        with open(master_db_path, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        all_items = []
        author_scores = {}  # Track author contributions
        timeline_data = {}  # Track items by date
        
        def add_items(source_list, item_type, icon):
            for item in source_list:
                source = item.get('source', {})
                metrics = source.get('metrics', {})
                impact = source.get('impact_score', 0)
                date_found = item.get('date_found', '')
                author = source.get('author') or source.get('sender') or 'Unknown'
                
                # Boost recent items with no impact score
                if impact == 0 and date_found:
                    from datetime import datetime
                    try:
                        if date_found == datetime.now().strftime('%Y-%m-%d'):
                            impact = 10
                    except:
                        pass
                
                entry = {
                    'id': item.get('url') or item.get('video_id') or item.get('code', ''),
                    'title': item.get('name') or item.get('title') or item.get('code') or 'Unknown',
                    'url': item.get('url') or '',
                    'type': item_type,
                    'icon': icon,
                    'impact': impact,
                    'metrics': metrics,
                    'date': date_found,
                    'author': author,
                    'owner': item.get('owner', ''),
                    'confidence': source.get('confidence', 0.5),
                    'relevance_tags': source.get('relevance_tags', [])
                }
                all_items.append(entry)
                
                # Track author contributions
                if author not in author_scores:
                    author_scores[author] = {'count': 0, 'total_impact': 0}
                author_scores[author]['count'] += 1
                author_scores[author]['total_impact'] += impact
                
                # Track timeline
                if date_found:
                    if date_found not in timeline_data:
                        timeline_data[date_found] = {'count': 0, 'items': []}
                    timeline_data[date_found]['count'] += 1
                    if len(timeline_data[date_found]['items']) < 3:
                        timeline_data[date_found]['items'].append(entry['title'][:50])
        
        # Process all sources
        add_items(db.get('repositories', {}).get('github', []), 'GitHub', 'github')
        add_items(db.get('repositories', {}).get('huggingface', []), 'HuggingFace', 'huggingface')
        add_items(db.get('tutorials', []), 'Tutorial', 'youtube')
        add_items(db.get('styles', {}).get('midjourney_sref', []), 'Style', 'sref')
        add_items(db.get('coding_tools', []), 'Tool', 'tool')
        
        # Sort by impact or date
        if sort_by == 'date':
            all_items.sort(key=lambda x: x['date'], reverse=True)
        else:
            all_items.sort(key=lambda x: x['impact'], reverse=True)
        
        # Limit results
        top_items = all_items[:limit]
        
        # Build top authors list
        top_authors = [
            {'author': author, 'count': data['count'], 'impact': data['total_impact']}
            for author, data in author_scores.items()
        ]
        top_authors.sort(key=lambda x: x['impact'], reverse=True)
        top_authors = top_authors[:10]  # Top 10 authors
        
        # Sort timeline by date
        sorted_timeline = dict(sorted(timeline_data.items(), reverse=True)[:14])  # Last 14 days
        
        return {
            "items": top_items,
            "timeline": sorted_timeline,
            "top_authors": top_authors,
            "total_count": len(all_items)
        }
        
    except Exception as e:
        return {"error": str(e), "items": [], "timeline": {}, "top_authors": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
