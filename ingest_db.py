import json
import os
import sys

# Add current dir to path to import actions
sys.path.append(os.getcwd())

from actions.knowledge_base import KnowledgeBase

MASTER_DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'

def ingest_data():
    if not os.path.exists(MASTER_DB_PATH):
        print(f"Master DB not found at {MASTER_DB_PATH}")
        return

    print("Loading Master DB...")
    with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # Store ChromaDB on D: drive to save SSD space
    db_path = r'D:\AI-Knowledge-Base\chromadb'
    print(f"Connecting to Cortex at: {db_path}")
    
    kb = KnowledgeBase(db_path=db_path)
    
    documents = []
    metadatas = []
    ids = []

    print("Preparing documents...")

    # Process GitHub Repos
    for repo in db['repositories']['github']:
        content = f"GitHub Repository: {repo['name']}\nURL: {repo['url']}\nOwner: {repo.get('owner', 'Unknown')}\nDescription: A GitHub repository relevant to AI."
        meta = {
            "source": f"GitHub ({repo.get('owner', 'Unknown')})",
            "category": "Repository",
            "url": repo['url'],
            "timestamp": repo.get('date_found', '')
        }
        documents.append(content)
        metadatas.append(meta)
        ids.append(f"gh_{repo['name']}_{repo.get('owner', '')}")

    # Process YouTube Tutorials
    for vid in db['tutorials']:
        # Handle null/None title explicitly (get() returns None for null values)
        title = vid.get('title') or 'Unknown Title'
        content = f"YouTube Tutorial: {title}\nURL: {vid['url']}\nVideo ID: {vid['video_id']}"
        meta = {
            "source": "YouTube",
            "category": "Tutorial",
            "url": vid['url'],
            "timestamp": vid.get('date_found', '')
        }
        documents.append(content)
        metadatas.append(meta)
        ids.append(f"yt_{vid['video_id']}")
        
    # Process HF Models
    for model in db['repositories']['huggingface']:
         content = f"HuggingFace Model: {model['name']}\nURL: {model['url']}\nOwner: {model.get('owner', 'Unknown')}"
         meta = {
            "source": "HuggingFace",
            "category": "Model",
            "url": model['url'],
            "timestamp": model.get('date_found', '')
         }
         documents.append(content)
         metadatas.append(meta)
         ids.append(f"hf_{model['name']}")

    print(f"Ingesting {len(documents)} items into ChromaDB...")
    kb.add_documents(documents, metadatas, ids)
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_data()
