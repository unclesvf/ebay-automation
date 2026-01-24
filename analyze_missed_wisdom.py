import sys
import os
import yaml
import re

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from outlook_reader import OutlookReader

def load_config():
    config_path = os.path.join(BASE_DIR, 'rules', 'scott_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def is_currently_captured(text, config):
    # Extract the ingestion rules from the config
    ingest_action = None
    for profile in config['profiles']:
        if profile['id'] == 'scott_organizer': # matches yaml id
            for action in profile['actions']:
                if action['name'] == 'ingest_wisdom':
                    ingest_action = action
                    break
    
    if not ingest_action:
        return False
        
    params = ingest_action['params']
    required_keywords = params.get('required_keywords', [])
    min_length = params.get('min_body_length', 100)
    
    if len(text) < min_length:
        return True # Considered "captured" in the sense that we deliberately skip it (not missed wisdom, just usage)
        
    text_lower = text.lower()
    for kw in required_keywords:
        if kw.lower() in text_lower:
            return True
            
    return False

def has_potential_value(subject, body):
    text = (subject + " " + body).lower()
    
    # Heuristics for value that we might be missing
    value_indicators = [
        "idea", "thought", "considering", "maybe we should", # Brainstorming
        "script", "code", "python", "function", "api",       # Technical
        "researched", "found this", "check out",             # Research
        "summary", "notes", "update on",                     # Project updates
        "prompt", "llm", "model", "token"                    # AI specifics
    ]
    
    # Check for code blocks
    if "```" in body or "def " in body or "import " in body:
        return "Contains Code"
        
    for ind in value_indicators:
        if ind in text:
            return f"Contains '{ind}'"
            
    # Long thoughtful email?
    if len(body) > 1000:
        return "Long Content (>1000 chars)"
        
    return None

def run_analysis():
    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect")
        return

    folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")
    if not folder:
        # Fallback to default if not found (for dry run testing)
        print("Could not find 'Scott' folder, using Default Inbox for test")
        folder = reader.namespace.GetDefaultFolder(6)

    print(f"Scanning '{folder.Name}' for missed opportunities...")
    
    config = load_config()
    items = folder.Items
    items.Sort("[ReceivedTime]", True)
    
    missed_ops = []
    scanned = 0
    limit = 200
    
    for item in items:
        if scanned >= limit: break
        if item.Class != 43: continue
        
        scanned += 1
        subject = getattr(item, 'Subject', '') or ''
        try:
            body = getattr(item, 'Body', '') or ''
        except:
            body = ''
            
        full_text = f"{subject}\n{body}"
        
        # 1. Is it currently captured?
        if is_currently_captured(full_text, config):
            continue
            
        # 2. If NOT captured, does it look valuable?
        reason = has_potential_value(subject, body)
        if reason:
            missed_ops.append({
                "subject": subject,
                "reason": reason,
                "snippet": body[:100].replace('\n', ' ')
            })

    # Report
    print(f"\nAnalysis Complete. Scanned {scanned} emails.")
    print(f"Found {len(missed_ops)} potential knowledge opportunities currently MISSED.\n")
    
    print(f"{'Reason':<25} | {'Subject'}")
    print("-" * 60)
    for op in missed_ops[:30]: # Print top 30
        print(f"{op['reason']:<25} | {op['subject'][:50]}")
        
    # Write to file for user
    with open("missed_knowledge_report.txt", "w", encoding='utf-8') as f:
        f.write("MISSED KNOWLEDGE OPPORTUNITIES REPORT\n")
        f.write("=======================================\n")
        f.write("These emails contain indicators of value but fail current 'Wisdom' filters.\n\n")
        for op in missed_ops:
            f.write(f"Reason: {op['reason']}\n")
            f.write(f"Subject: {op['subject']}\n")
            f.write(f"Snippet: {op['snippet']}...\n")
            f.write("-" * 40 + "\n")

if __name__ == "__main__":
    run_analysis()
