import json
import os

DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'

if os.path.exists(DB_PATH):
    with open(DB_PATH, 'r', encoding='utf-8', errors='ignore') as f:
        data = json.load(f)
        
    print("--- SAMPLE GITHUB REPO ---")
    if data['repositories']['github']:
        print(json.dumps(data['repositories']['github'][0], indent=2))
        
    print("\n--- SAMPLE TUTORIAL ---")
    if data['tutorials']:
        print(json.dumps(data['tutorials'][0], indent=2))
else:
    print(f"File not found: {DB_PATH}")
