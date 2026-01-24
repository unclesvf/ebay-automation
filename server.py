from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import yaml
import json
import logging
from typing import Dict, Any, List
from fastapi.staticfiles import StaticFiles

# Setup Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AmbroseServer")

app = FastAPI(title="Ambrose API")

# CORS for Dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite Dev Server
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

# Global State
ORCHESTRATOR_PROCESS = None

class ConfigUpdate(BaseModel):
    dry_run: bool

@app.get("/")
def read_root():
    return {"status": "Ambrose System Online", "version": "1.0"}

# Mount reports directory
if os.path.exists(EXPORTS_PATH):
    app.mount("/reports", StaticFiles(directory=EXPORTS_PATH), name="reports")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
