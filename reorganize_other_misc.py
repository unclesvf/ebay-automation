"""
Reorganize Other-Misc folder into new categories
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict

def categorize_other_misc(subject, body):
    """Categorize emails from Other-Misc into new categories"""
    text = (subject + ' ' + body[:2000]).lower()
    subject_lower = subject.lower()

    # IMI / Mint Asset Sale related
    if any(x in text for x in ['imi ', 'imi invoice', 'independence mint',
                                'used equipment', 'equipment sale', 'lsm',
                                'local silver mint', 'silver dave', 'dave engle']):
        return 'Mint Asset Sale'

    # Fadal related
    if 'fadal' in text:
        return 'Fadal'

    # Personal/Family
    if any(x in text for x in ['micah', 'lina', 'mandy', 'guardianship',
                                'adrian', 'thanksgiving', 'christmas',
                                'jonah', 'family', 'birthday']):
        return 'Personal-Family'

    # eBay/Auction Photos - lot numbers, SL references
    if any(x in text for x in ['sl#', 'sl3', 'sl4', 'kl2', 'lot number',
                                'no photos', 'missing photo', 'auction item',
                                'nugget earring', 'bracelet', 'ring photo',
                                'whitman album', 'medals', 'cabbage patch']):
        return 'eBay-Auction Photos'

    # Software/Apps
    if any(x in text for x in ['teamviewer', 'affinity', 'millwrite',
                                'archivinci', 'relief maker', 'capcup',
                                'malwarebytes', 'stripe', 'notion',
                                'lightroom', 'easeus']):
        return 'Software-Apps'

    # Engraving/Laser
    if any(x in text for x in ['jpt', 'laser', 'engrav', 'xtool', 'f1',
                                'gun engrav', 'relief maker', 'press photo']):
        return 'Engraving-Laser'

    # Business Docs
    if any(x in text for x in ['lease', 'invoice', 'budget', 'contract',
                                'bill of sale', 'permit', 'business card',
                                'bank statement', 'utility bill']):
        return 'Business Docs'

    # Medical/Personal docs
    if any(x in text for x in ['prescription', 'medical', 'bennet medical',
                                'passport', 'eye glass', 'fafsa', 'adapthealth']):
        return 'Medical-Personal'

    # History Project
    if any(x in text for x in ['american history', 'auntsvaluefarm',
                                '1565', '1914', 'history']):
        return 'History Project'

    return None  # Keep in Other-Misc


def reorganize():
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

    print("Found Scott folder")

    # Get or create all needed folders
    new_folders = [
        'Fadal',
        'Personal-Family',
        'eBay-Auction Photos',
        'Software-Apps',
        'Engraving-Laser',
        'Business Docs',
        'Medical-Personal',
        'History Project'
    ]

    folder_map = {}

    # First, map existing folders
    for subfolder in scott_folder.Folders:
        folder_map[subfolder.Name] = subfolder

    # Create new folders if needed
    print("\nCreating/finding folders...")
    for folder_name in new_folders:
        if folder_name not in folder_map:
            try:
                new_folder = scott_folder.Folders.Add(folder_name)
                folder_map[folder_name] = new_folder
                print(f"  [CREATED] {folder_name}")
            except Exception as e:
                print(f"  [ERROR] {folder_name}: {e}")
        else:
            print(f"  [EXISTS] {folder_name}")

    # Ensure Mint Asset Sale exists
    if 'Mint Asset Sale' not in folder_map:
        folder_map['Mint Asset Sale'] = scott_folder.Folders.Add('Mint Asset Sale')
        print("  [CREATED] Mint Asset Sale")

    # Find Other-Misc folder
    other_misc = folder_map.get('Other-Misc')
    if not other_misc:
        print("Could not find Other-Misc folder")
        return

    # Categorize and collect emails to move
    print("\nScanning Other-Misc folder...")

    items = other_misc.Items
    items.Sort("[ReceivedTime]", True)

    moves = defaultdict(list)

    for item in items:
        if item.Class != 43:
            continue

        subject = item.Subject or '(no subject)'
        body = item.Body or ''

        category = categorize_other_misc(subject, body)

        if category:
            moves[category].append({
                'item': item,
                'subject': subject
            })

    # Print summary
    print("\n" + "=" * 60)
    print("EMAILS TO MOVE:")
    print("=" * 60)

    for category, emails in sorted(moves.items(), key=lambda x: -len(x[1])):
        print(f"\n### {category} ({len(emails)} emails) ###")
        for email in emails:
            subj = email['subject'][:55].encode('ascii', 'replace').decode('ascii')
            print(f"  - {subj}")

    # Move the emails
    print("\n" + "=" * 60)
    print("Moving emails...")
    print("=" * 60)

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

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: Moved {total_moved} emails")
    print(f"{'=' * 60}")

    # Show remaining Other-Misc
    print("\nRemaining in Other-Misc:")
    items = other_misc.Items
    items.Sort("[ReceivedTime]", True)

    count = 0
    for item in items:
        if item.Class != 43:
            continue
        count += 1
        subj = (item.Subject or '(no subject)')[:55]
        subj = subj.encode('ascii', 'replace').decode('ascii')
        received = str(item.ReceivedTime)[:10]
        print(f"  {count:3}. [{received}] {subj}")

    print(f"\nTotal remaining: {count}")


if __name__ == "__main__":
    reorganize()
