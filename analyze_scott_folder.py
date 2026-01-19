"""
Analyze emails in Scott's folder in Outlook
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')

from outlook_reader import OutlookReader
from collections import defaultdict
import re

def analyze_scott_folder():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    # Find the scott folder in scott@unclesvf.com
    folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    if not folder:
        print("Could not find 'scott' folder. Let me list available folders...")
        folders = reader.get_folders("scott@unclesvf.com")
        print_folders(folders)
        return

    print(f"Found folder: {folder.Name} with {folder.Items.Count} items")

    # Read emails (get more to have a good sample)
    emails = reader.read_emails(folder, limit=200)

    print(f"\nRead {len(emails)} emails from the folder\n")

    # Analyze by sender
    sender_counts = defaultdict(int)
    # Analyze by subject keywords
    subject_keywords = defaultdict(int)
    # Store sample subjects per sender
    sender_subjects = defaultdict(list)

    ai_keywords = ['AI', 'Claude', 'GPT', 'ChatGPT', 'Anthropic', 'OpenAI', 'LLM',
                   'artificial intelligence', 'machine learning', 'ML', 'neural',
                   'deep learning', 'Gemini', 'Copilot', 'Midjourney', 'DALL-E',
                   'language model', 'transformer', 'Llama', 'Mistral', 'AGI',
                   'automation', 'robot', 'bot']

    for email in emails:
        sender = email.get('sender', 'Unknown')
        subject = email.get('subject', '(no subject)')

        sender_counts[sender] += 1

        if len(sender_subjects[sender]) < 3:  # Keep up to 3 sample subjects
            sender_subjects[sender].append(subject[:60])

        # Check for AI keywords
        text = (subject + ' ' + email.get('body', '')[:500]).lower()
        for keyword in ai_keywords:
            if keyword.lower() in text:
                subject_keywords[keyword] += 1

    # Print results
    print("=" * 80)
    print("EMAIL ANALYSIS - Scott Folder")
    print("=" * 80)

    print("\n### Emails by Sender ###\n")
    print(f"{'Sender':<40} {'Count':>6}  Sample Subjects")
    print("-" * 80)

    for sender, count in sorted(sender_counts.items(), key=lambda x: -x[1]):
        samples = sender_subjects[sender]
        sample_str = samples[0] if samples else ''
        print(f"{sender[:40]:<40} {count:>6}  {sample_str[:30]}")
        for s in samples[1:]:
            print(f"{'':<48} {s[:30]}")

    print("\n\n### AI-Related Keyword Matches ###\n")
    print(f"{'Keyword':<25} {'Count':>6}")
    print("-" * 35)
    for keyword, count in sorted(subject_keywords.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"{keyword:<25} {count:>6}")

    # Also print some raw email details
    print("\n\n### Sample Email Details (first 20) ###\n")
    for i, email in enumerate(emails[:20]):
        print(f"{i+1:2}. From: {email.get('sender', 'Unknown')[:30]}")
        print(f"    Subject: {email.get('subject', '(no subject)')[:60]}")
        print(f"    Date: {email.get('received')}")
        print()

def print_folders(folder_dict, indent=0):
    """Pretty print folder structure."""
    prefix = "  " * indent
    name = folder_dict.get('name', 'Unknown')
    count = folder_dict.get('count', 0)
    print(f"{prefix}- {name} ({count} items)")
    for sub in folder_dict.get('subfolders', []):
        print_folders(sub, indent + 1)

if __name__ == "__main__":
    analyze_scott_folder()
