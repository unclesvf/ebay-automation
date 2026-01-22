"""
Detailed analysis of emails in Scott's folder - categorize by type
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict
import re

def categorize_email(subject, body):
    """Categorize email by content type"""
    text = (subject + ' ' + body[:1000]).lower()
    subject_lower = subject.lower()

    # Check various categories
    if 'post by' in subject_lower and 'on x' in subject_lower:
        return 'X/Twitter Posts'
    if 'github' in subject_lower or 'github.com' in text:
        return 'GitHub Projects'
    if 'youtube' in text or 'youtu.be' in text:
        return 'YouTube Videos'
    if 'reddit' in text or 'r/' in subject_lower:
        return 'Reddit Posts'
    if any(x in text for x in ['claude', 'anthropic']):
        return 'Claude/Anthropic'
    if any(x in text for x in ['chatgpt', 'openai', 'gpt-4', 'gpt4']):
        return 'ChatGPT/OpenAI'
    if 'gemini' in text or 'google ai' in text:
        return 'Google/Gemini'
    if any(x in text for x in ['pricing', 'plans', 'subscription', 'tier']):
        return 'Pricing/Plans'
    if 'ebay' in text or 'listing' in text:
        return 'eBay Related'
    if any(x in text for x in ['coin', 'silver', 'gold', 'peso', 'centavo', 'numismatic']):
        return 'Coins/Numismatics'
    if any(x in text for x in ['ai agent', 'autonomous', 'agentic']):
        return 'AI Agents'
    if any(x in text for x in ['music', 'audio', 'song']):
        return 'AI Music/Audio'
    if any(x in text for x in ['image', 'art', 'midjourney', 'dall-e', 'stable diffusion']):
        return 'AI Art/Images'
    if any(x in text for x in ['code', 'coding', 'programming', 'developer', 'dev']):
        return 'Coding/Development'
    if 'outlook' in text:
        return 'Outlook/Email'
    if len(subject) <= 3:
        return 'Short Notes'

    # If has AI keywords but not categorized above
    if any(x in text for x in ['ai', 'artificial intelligence', 'machine learning', 'llm', 'neural']):
        return 'General AI'

    return 'Other/Misc'


def analyze_scott_folder():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    if not folder:
        print("Could not find 'scott' folder")
        return

    total_items = folder.Items.Count
    print(f"Found folder: {folder.Name} with {total_items} items")

    # Read all emails
    emails = reader.read_emails(folder, limit=500)
    print(f"Read {len(emails)} emails\n")

    # Categorize
    categories = defaultdict(list)

    for email in emails:
        subject = email.get('subject', '(no subject)')
        body = email.get('body', '')
        received = email.get('received')

        category = categorize_email(subject, body)
        categories[category].append({
            'subject': subject,
            'date': received
        })

    # Print summary table
    print("=" * 80)
    print("EMAIL CATEGORIES SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Category':<30} {'Count':>6}  {'% of Total':>10}")
    print("-" * 50)

    total = len(emails)
    for category, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        count = len(items)
        pct = (count / total) * 100 if total > 0 else 0
        print(f"{category:<30} {count:>6}  {pct:>9.1f}%")

    print("-" * 50)
    print(f"{'TOTAL':<30} {total:>6}  {'100.0%':>10}")

    # Print sample subjects for each category
    print("\n\n" + "=" * 80)
    print("SAMPLE EMAILS BY CATEGORY")
    print("=" * 80)

    for category, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"\n### {category} ({len(items)} emails) ###\n")
        for item in items[:5]:  # Show 5 samples per category
            date_str = str(item['date'])[:10] if item['date'] else 'Unknown'
            print(f"  [{date_str}] {item['subject'][:65]}")

if __name__ == "__main__":
    analyze_scott_folder()
