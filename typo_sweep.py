"""
Sweep all folders for typos that may have caused miscategorization
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict
import re

# Typo patterns mapped to correct category
TYPO_PATTERNS = {
    'Mint Asset Sale': [
        # Local Silver Mint typos
        r'local\s*silv[ea]r\s*mi[nk][nt]',  # miknt, mikt, mint, etc.
        r'local\s*silvr\s*mint',
        r'local\s*sliver\s*mint',  # sliver vs silver
        r'lsm',
        # Independence Mint typos
        r'independ[ae]nc[ea]\s*mi[nk][nt]',
        r'indepedence\s*mint',  # missing n
        r'independance\s*mint',  # ance vs ence
        # IMI typos
        r'\bimi\b',
        # Dave/Engle typos
        r'silv[ea]r\s*dav[ea]',
        r'dave\s*engl[ea]',
        r'jack\s*engl[ea]',
        r'alan\s*engl[ea]',
        # Equipment sale
        r'equip?ment\s*sale',
        r'used\s*equip?ment',
        r'asset\s*sal[ea]',
    ],
    'eBay Related': [
        r'e-?bay',
        r'ebya',  # typo
        r'eaby',  # typo
        r'listin[gf]',
        r'relits',  # relist typo
        r'sel+\s*similar',
    ],
    'Claude-Anthropic': [
        r'claud[ea]',
        r'cluade',  # typo
        r'antropic',  # missing h
        r'anthrop[io]c',
    ],
    'ChatGPT-OpenAI': [
        r'chat\s*gp[ts]',
        r'chatgtp',  # typo
        r'opena[il]',
        r'gpt-?[34]',
    ],
    'GitHub Projects': [
        r'git\s*hub',
        r'github',
        r'guthub',  # typo
        r'githbu',  # typo
    ],
}


def check_typos(text):
    """Check text for typo patterns, return matching category"""
    text_lower = text.lower()

    for category, patterns in TYPO_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return category, pattern

    return None, None


def typo_sweep():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")
    if not scott_folder:
        print("Could not find 'scott' folder")
        return

    # Get all folder references
    folder_map = {}
    for subfolder in scott_folder.Folders:
        folder_map[subfolder.Name] = subfolder

    print(f"Found {len(folder_map)} subfolders")

    # Scan all folders for misplaced emails
    print("\n" + "=" * 70)
    print("SCANNING ALL FOLDERS FOR TYPOS/MISCATEGORIZATIONS...")
    print("=" * 70)

    emails_to_move = []

    for folder_name, folder in folder_map.items():
        items = folder.Items

        for item in items:
            if item.Class != 43:
                continue

            subject = item.Subject or '(no subject)'
            body = item.Body or ''
            text = subject + ' ' + body[:2000]

            correct_category, matched_pattern = check_typos(text)

            # Only flag if it's in the WRONG folder
            if correct_category and correct_category != folder_name:
                emails_to_move.append({
                    'item': item,
                    'subject': subject,
                    'from_folder': folder_name,
                    'to_folder': correct_category,
                    'matched': matched_pattern
                })

    # Group by destination
    moves_by_dest = defaultdict(list)
    for email in emails_to_move:
        moves_by_dest[email['to_folder']].append(email)

    # Print findings
    print(f"\nFound {len(emails_to_move)} potentially miscategorized emails:\n")

    for dest, emails in sorted(moves_by_dest.items()):
        print(f"\n### Should be in '{dest}' ({len(emails)} emails) ###")
        for email in emails:
            subj = email['subject'][:45].encode('ascii', 'replace').decode('ascii')
            print(f"  [{email['from_folder']}] {subj}")
            print(f"      Pattern: {email['matched']}")

    if not emails_to_move:
        print("No miscategorized emails found!")
        return

    # Move the emails
    print("\n" + "=" * 70)
    print("Moving emails to correct folders...")
    print("=" * 70)

    total_moved = 0
    for dest, emails in moves_by_dest.items():
        dest_folder = folder_map.get(dest)
        if not dest_folder:
            print(f"  Skipping {dest} - folder not found")
            continue

        moved = 0
        for email in emails:
            try:
                email['item'].Move(dest_folder)
                moved += 1
            except Exception as e:
                subj = email['subject'][:30].encode('ascii', 'replace').decode('ascii')
                print(f"  Error moving '{subj}': {e}")

        print(f"  {dest}: moved {moved} emails")
        total_moved += moved

    print(f"\n{'=' * 70}")
    print(f"COMPLETE: Moved {total_moved} emails")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    typo_sweep()
