"""
Move the Local Silver Miknt (typo) email to Mint Asset Sale
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader

def move_typo_email():
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
    coins_folder = None
    mint_folder = None
    for subfolder in scott_folder.Folders:
        if subfolder.Name == 'Coins-Numismatics':
            coins_folder = subfolder
        if subfolder.Name == 'Mint Asset Sale':
            mint_folder = subfolder

    if not coins_folder or not mint_folder:
        print("Could not find required folders")
        return

    # Find and move the email
    items = coins_folder.Items
    moved = 0

    for item in items:
        if item.Class != 43:
            continue
        subject = item.Subject or ''
        if 'local silver miknt' in subject.lower() or 'local silver mint' in subject.lower():
            print(f"Moving: {subject}")
            item.Move(mint_folder)
            moved += 1

    print(f"\nMoved {moved} email(s) to Mint Asset Sale")

if __name__ == "__main__":
    move_typo_email()
