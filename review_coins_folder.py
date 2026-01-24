"""
Review Coins-Numismatics folder and recategorize emails
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict

def categorize_coin_email(subject, body):
    """Recategorize emails from Coins-Numismatics"""
    text = (subject + ' ' + body[:2000]).lower()
    subject_lower = subject.lower()

    # Mint Asset Sale related
    if any(x in text for x in ['imi ', 'imi invoice', 'independence mint',
                                'used equipment', 'equipment sale', 'lsm',
                                'local silver mint', 'silver dave', 'dave engle',
                                'jack engle', 'alan engle', 'asset sale']):
        return 'Mint Asset Sale'

    # JSON/Image prompts
    if any(x in text for x in ['json', 'mermaid', 'prompt', 'image json']):
        return 'General AI'

    # eBay-Auction Photos - specific item photos, lot numbers, SL references
    if any(x in text for x in ['sl#', 'sl3', 'sl4', 'kl2', 'lot number',
                                'no photos', 'missing photo', 'photo for',
                                'photos have no', 'ring photo', 'which one',
                                'first or the second']):
        return 'eBay-Auction Photos'

    # eBay Related - listings, prices, selling
    if any(x in text for x in ['ebay', 'listing', 'sell similar', 'list new',
                                'relist', 'price change', 'item number']):
        return 'eBay Related'

    return None  # Keep in Coins-Numismatics


def review_coins_folder():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")
    if not scott_folder:
        print("Could not find 'scott' folder")
        return

    # Get folder references
    folder_map = {}
    for subfolder in scott_folder.Folders:
        folder_map[subfolder.Name] = subfolder

    coins_folder = folder_map.get('Coins-Numismatics')
    if not coins_folder:
        print("Could not find Coins-Numismatics folder")
        return

    print(f"Found Coins-Numismatics folder with {coins_folder.Items.Count} items")

    # First, show all emails in the folder
    print("\n" + "=" * 70)
    print("CURRENT CONTENTS OF COINS-NUMISMATICS:")
    print("=" * 70)

    items = coins_folder.Items
    items.Sort("[ReceivedTime]", True)

    all_emails = []
    for item in items:
        if item.Class != 43:
            continue
        subject = item.Subject or '(no subject)'
        body = item.Body or ''
        received = str(item.ReceivedTime)[:10]

        category = categorize_coin_email(subject, body)

        all_emails.append({
            'item': item,
            'subject': subject,
            'body': body,
            'received': received,
            'new_category': category
        })

    # Print all with suggested recategorization
    for i, email in enumerate(all_emails):
        subj = email['subject'][:50].encode('ascii', 'replace').decode('ascii')
        cat = email['new_category'] or '(keep)'
        marker = f"-> {cat}" if email['new_category'] else ""
        print(f"  {i+1:2}. [{email['received']}] {subj}")
        if marker:
            print(f"      {marker}")

    # Collect moves
    moves = defaultdict(list)
    for email in all_emails:
        if email['new_category']:
            moves[email['new_category']].append(email)

    # Summary
    print("\n" + "=" * 70)
    print("EMAILS TO MOVE:")
    print("=" * 70)

    for category, emails in sorted(moves.items(), key=lambda x: -len(x[1])):
        print(f"\n### {category} ({len(emails)} emails) ###")
        for email in emails:
            subj = email['subject'][:55].encode('ascii', 'replace').decode('ascii')
            print(f"  - {subj}")

    if not moves:
        print("\nNo emails to move.")
        return

    # Move the emails
    print("\n" + "=" * 70)
    print("Moving emails...")
    print("=" * 70)

    total_moved = 0
    for category, emails in moves.items():
        dest_folder = folder_map.get(category)
        if not dest_folder:
            print(f"  Skipping {category} - folder not found")
            continue

        moved = 0
        for email in emails:
            try:
                email['item'].Move(dest_folder)
                moved += 1
            except Exception as e:
                print(f"  Error: {e}")

        print(f"  {category}: moved {moved} emails")
        total_moved += moved

    print(f"\nTotal moved: {total_moved}")

    # Show remaining
    print("\n" + "=" * 70)
    print("REMAINING IN COINS-NUMISMATICS:")
    print("=" * 70)

    items = coins_folder.Items
    items.Sort("[ReceivedTime]", True)

    count = 0
    for item in items:
        if item.Class != 43:
            continue
        count += 1
        subj = (item.Subject or '(no subject)')[:55]
        subj = subj.encode('ascii', 'replace').decode('ascii')
        received = str(item.ReceivedTime)[:10]
        print(f"  {count:2}. [{received}] {subj}")

    print(f"\nTotal remaining: {count}")


if __name__ == "__main__":
    review_coins_folder()
