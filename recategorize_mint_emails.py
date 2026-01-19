"""
Recategorize emails related to Mint Asset Sale
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')

# Fix unicode output on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader

def is_mint_related(subject, body):
    """Check if email is related to Mint Asset Sale"""
    text = (subject + ' ' + body[:2000]).lower()

    keywords = [
        'silver dave',
        'local silver mint',
        'asset sale',
        'independence mint',
        'lsm',
        'dave engle',
        'jack engle',
        'alan engle',
        'equipment sale agreement',
        'used equipment sale',
    ]

    for keyword in keywords:
        if keyword in text:
            return True, keyword

    return False, None


def safe_print(text):
    """Print with unicode handling"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('ascii', 'replace').decode('ascii'))


def recategorize_mint_emails():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    # Find the Scott folder
    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    if not scott_folder:
        print("Could not find 'scott' folder")
        return

    print(f"Found Scott folder")

    # Create or find Mint Asset Sale folder
    mint_folder = None
    for subfolder in scott_folder.Folders:
        if subfolder.Name.lower() == "mint asset sale":
            mint_folder = subfolder
            print("Found existing 'Mint Asset Sale' folder")
            break

    if not mint_folder:
        mint_folder = scott_folder.Folders.Add("Mint Asset Sale")
        print("Created 'Mint Asset Sale' folder")

    # Scan all subfolders for mint-related emails
    print("\nScanning subfolders for Mint Asset Sale related emails...")
    print("=" * 60)

    emails_to_move = []

    for subfolder in scott_folder.Folders:
        if subfolder.Name == "Mint Asset Sale":
            continue

        folder_name = subfolder.Name
        items = subfolder.Items

        for item in items:
            if item.Class != 43:  # Only mail items
                continue

            subject = item.Subject or '(no subject)'
            body = item.Body or ''

            is_mint, matched_keyword = is_mint_related(subject, body)

            if is_mint:
                emails_to_move.append({
                    'item': item,
                    'subject': subject,
                    'from_folder': folder_name,
                    'keyword': matched_keyword
                })

    # Print what we found
    print(f"\nFound {len(emails_to_move)} emails to move to 'Mint Asset Sale':\n")

    for email in emails_to_move:
        subj = email['subject'][:50].encode('ascii', 'replace').decode('ascii')
        safe_print(f"  [{email['from_folder']}] {subj}")
        safe_print(f"      Matched: '{email['keyword']}'")

    # Move the emails
    print("\n" + "=" * 60)
    print("Moving emails...")
    print("=" * 60)

    moved = 0
    for email in emails_to_move:
        try:
            email['item'].Move(mint_folder)
            moved += 1
        except Exception as e:
            subj = email['subject'][:40].encode('ascii', 'replace').decode('ascii')
            print(f"  Error moving: {subj} - {e}")

    print(f"\nMoved {moved} emails to 'Mint Asset Sale' folder")

    # Now let's also look at Other-Misc and show what's there
    print("\n" + "=" * 60)
    print("Reviewing Other-Misc folder contents...")
    print("=" * 60)

    other_misc = None
    for subfolder in scott_folder.Folders:
        if subfolder.Name == "Other-Misc":
            other_misc = subfolder
            break

    if other_misc:
        items = other_misc.Items
        items.Sort("[ReceivedTime]", True)

        print(f"\nOther-Misc has {items.Count} emails remaining:\n")

        count = 0
        for item in items:
            if item.Class != 43:
                continue
            count += 1
            subject = (item.Subject or '(no subject)')[:60]
            subject = subject.encode('ascii', 'replace').decode('ascii')
            received = str(item.ReceivedTime)[:10]
            safe_print(f"  {count:3}. [{received}] {subject}")

            if count >= 116:  # Show all
                break


if __name__ == "__main__":
    recategorize_mint_emails()
