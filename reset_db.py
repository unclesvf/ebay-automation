import json
import os

DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'

def reset_db():
    """Reset the database to empty state while preserving structure."""
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    with open(DB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Clear all extracted content
    data['repositories']['github'] = []
    data['repositories']['huggingface'] = []
    data['tutorials'] = []
    data['styles']['midjourney_sref'] = []
    data['metadata']['total_entries'] = 0
    
    print("Cleared all repositories, tutorials, and styles.")

    # Save
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Database reset complete.")

if __name__ == "__main__":
    reset_db()
