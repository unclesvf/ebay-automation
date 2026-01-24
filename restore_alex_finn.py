"""
Restore incorrectly deleted Alex Finn email
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
import re

def restore_email():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    # Find folders
    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    claude_folder = None
    for subfolder in scott_folder.Folders:
        if subfolder.Name == 'Claude-Anthropic':
            claude_folder = subfolder
            break

    # Find Deleted Items
    for account in reader.namespace.Accounts:
        if "unclesvf" in account.SmtpAddress.lower():
            store = account.DeliveryStore
            root = store.GetRootFolder()

            deleted_folder = None
            for folder in root.Folders:
                if "deleted" in folder.Name.lower():
                    deleted_folder = folder
                    break

            if not deleted_folder or not claude_folder:
                print("Could not find required folders")
                return

            # Find and restore the Alex Finn emails with different URLs
            items = deleted_folder.Items

            restored = 0
            for item in items:
                if item.Class != 43:
                    continue

                subject = item.Subject or ''
                if 'post by alex finn on x' in subject.lower():
                    body = item.Body or ''

                    # Extract URL
                    match = re.search(r'https://x\.com/(\w+)/status/(\d+)', body)
                    url = match.group(0) if match else 'unknown'

                    print(f"Restoring: {subject[:50]}")
                    print(f"  URL: {url}")

                    # Move back to Claude-Anthropic
                    item.Move(claude_folder)
                    restored += 1

            print(f"\nRestored {restored} Alex Finn email(s) to Claude-Anthropic")
            print(f"Claude-Anthropic now has {claude_folder.Items.Count} items")
            return


if __name__ == "__main__":
    restore_email()
