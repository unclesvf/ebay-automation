import json
import os
import re

DB_PATH = r'D:\AI-Knowledge-Base\master_db.json'

def clean_db():
    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    with open(DB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Clean GitHub Repos
    new_repos = []
    removed_count = 0
    
    # Regex for a valid-looking hash (hex string, long)
    hash_pattern = re.compile(r'^[0-9a-f]{10,}$', re.IGNORECASE)
    
    # Known full repo names (to prefer over truncated versions)
    full_names = set()
    for repo in data['repositories']['github']:
        name = repo.get('name', '')
        if len(name) > 10:  # Likely a full name
            full_names.add(name)

    for repo in data['repositories']['github']:
        name = repo.get('name', '')
        url = repo.get('url', '')
        author = repo.get('source', {}).get('author', '')
        
        # Filter 1: Commit hashes as names
        if hash_pattern.match(name):
            print(f"Removing hash-like repo: {name}")
            removed_count += 1
            continue

        # Filter 2: Specific bad author "P" (likely truncation)
        if author == 'P':
            print(f"Removing bad author entry: {name} (Author: P)")
            removed_count += 1
            continue

        # Filter 3: Truncated names - short names that are prefixes of full names
        is_truncated = False
        if len(name) < 10:
            for full in full_names:
                if full.startswith(name) and full != name:
                    print(f"Removing truncated repo: {name} (full version exists: {full})")
                    is_truncated = True
                    removed_count += 1
                    break
        
        if is_truncated:
            continue
            
        # Filter 4: Names ending with ellipsis-like patterns
        if name.endswith('...') or name.endswith('..'):
            print(f"Removing ellipsis repo: {name}")
            removed_count += 1
            continue

        new_repos.append(repo)

    data['repositories']['github'] = new_repos
    print(f"Removed {removed_count} bad repositories. Remaining: {len(new_repos)}")

    # 2. Clean HuggingFace entries
    hf_entries = data['repositories'].get('huggingface', [])
    new_hf = []
    hf_removed = 0
    
    # Find full HF names
    hf_full_names = set()
    for entry in hf_entries:
        name = entry.get('name', '')
        if len(name) > 10:  # Likely a full name
            hf_full_names.add(name)
    
    for entry in hf_entries:
        name = entry.get('name', '')
        url = entry.get('url', '')
        
        # Filter: Truncated names - short names that are prefixes of full names
        is_truncated = False
        if len(name) < 15:
            for full in hf_full_names:
                if full.startswith(name) and full != name:
                    print(f"Removing truncated HuggingFace: {name} (full version exists: {full})")
                    is_truncated = True
                    hf_removed += 1
                    break
        
        if is_truncated:
            continue
            
        # Filter: Names ending with ellipsis-like patterns
        if name.endswith('...') or name.endswith('..'):
            print(f"Removing ellipsis HuggingFace: {name}")
            hf_removed += 1
            continue

        new_hf.append(entry)

    data['repositories']['huggingface'] = new_hf
    print(f"Removed {hf_removed} bad HuggingFace entries. Remaining: {len(new_hf)}")

    # Save
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Database saved.")

if __name__ == "__main__":
    clean_db()
