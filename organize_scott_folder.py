"""
Organize emails in Scott's folder into subfolders by category
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')

from outlook_reader import OutlookReader
from collections import defaultdict

def categorize_email(subject, body):
    """Categorize email by content type"""
    text = (subject + ' ' + body[:1000]).lower()
    subject_lower = subject.lower()

    # Check various categories
    if 'post by' in subject_lower and 'on x' in subject_lower:
        return 'X-Twitter Posts'
    if 'github' in subject_lower or 'github.com' in text:
        return 'GitHub Projects'
    if 'youtube' in text or 'youtu.be' in text:
        return 'YouTube Videos'
    if 'reddit' in text or 'r/' in subject_lower:
        return 'Reddit Posts'
    if any(x in text for x in ['claude', 'anthropic']):
        return 'Claude-Anthropic'
    if any(x in text for x in ['chatgpt', 'openai', 'gpt-4', 'gpt4']):
        return 'ChatGPT-OpenAI'
    if 'gemini' in text or 'google ai' in text:
        return 'Google-Gemini'
    if any(x in text for x in ['pricing', 'plans', 'subscription', 'tier']):
        return 'Pricing-Plans'
    if 'ebay' in text or 'listing' in text:
        return 'eBay Related'
    if any(x in text for x in ['coin', 'silver', 'gold', 'peso', 'centavo', 'numismatic']):
        return 'Coins-Numismatics'
    if any(x in text for x in ['ai agent', 'autonomous', 'agentic']):
        return 'AI Agents'
    if any(x in text for x in ['music', 'audio', 'song']):
        return 'AI Music-Audio'
    if any(x in text for x in ['image', 'art', 'midjourney', 'dall-e', 'stable diffusion']):
        return 'AI Art-Images'
    if any(x in text for x in ['code', 'coding', 'programming', 'developer', 'dev']):
        return 'Coding-Development'
    if 'outlook' in text:
        return 'Outlook-Email'
    if len(subject) <= 3:
        return 'Short Notes'

    # If has AI keywords but not categorized above
    if any(x in text for x in ['ai', 'artificial intelligence', 'machine learning', 'llm', 'neural']):
        return 'General AI'

    return 'Other-Misc'


def organize_scott_folder():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    # Find the scott folder
    folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    if not folder:
        print("Could not find 'scott' folder")
        return

    print(f"Found folder: {folder.Name} with {folder.Items.Count} items")

    # First, categorize all emails
    print("\nCategorizing emails...")

    items = folder.Items
    items.Sort("[ReceivedTime]", True)

    # Collect emails by category
    email_categories = defaultdict(list)

    for item in items:
        if item.Class != 43:  # Only mail items
            continue

        subject = item.Subject or '(no subject)'
        body = item.Body or ''
        category = categorize_email(subject, body)
        email_categories[category].append(item)

    # Print summary
    print("\nCategories to create:")
    for cat, emails in sorted(email_categories.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(emails)} emails")

    # Create subfolders
    print("\n" + "=" * 50)
    print("Creating subfolders...")
    print("=" * 50)

    created_folders = {}

    for category in email_categories.keys():
        try:
            # Check if folder already exists
            existing = None
            for subfolder in folder.Folders:
                if subfolder.Name.lower() == category.lower():
                    existing = subfolder
                    break

            if existing:
                print(f"  [EXISTS] {category}")
                created_folders[category] = existing
            else:
                new_folder = folder.Folders.Add(category)
                print(f"  [CREATED] {category}")
                created_folders[category] = new_folder
        except Exception as e:
            print(f"  [ERROR] Could not create '{category}': {e}")

    # Move emails to subfolders
    print("\n" + "=" * 50)
    print("Moving emails to subfolders...")
    print("=" * 50)

    moved_count = 0
    error_count = 0

    for category, emails in email_categories.items():
        if category not in created_folders:
            print(f"  Skipping {category} - folder not available")
            continue

        dest_folder = created_folders[category]
        cat_moved = 0

        for email in emails:
            try:
                email.Move(dest_folder)
                cat_moved += 1
                moved_count += 1
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"  Error moving email: {e}")

        print(f"  {category}: moved {cat_moved} emails")

    print("\n" + "=" * 50)
    print(f"COMPLETE: Moved {moved_count} emails into {len(created_folders)} subfolders")
    if error_count > 0:
        print(f"Errors: {error_count}")
    print("=" * 50)


if __name__ == "__main__":
    organize_scott_folder()
