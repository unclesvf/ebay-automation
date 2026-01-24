import json
DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'
with open(DB_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total GitHub repos: {len(data['repositories']['github'])}")
for r in data['repositories']['github'][:10]:
    print(f" - {r['url']} (Owner: {r.get('owner')})")
