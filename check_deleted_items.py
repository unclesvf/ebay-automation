"""
Check Deleted Items folder to verify if deleted emails were true duplicates
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
import re

def extract_x_url(text):
    """Extract the main X.com post URL from email body"""
    # Look for x.com status URLs
    pattern = r'https://x\.com/(\w+)/status/(\d+)'
    match = re.search(pattern, text)
    if match:
        return f"https://x.com/{match.group(1)}/status/{match.group(2)}"
    return None

def check_deleted():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    # Find Deleted Items folder for the account
    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    # Get the store/account root to find Deleted Items
    for account in reader.namespace.Accounts:
        if "unclesvf" in account.SmtpAddress.lower():
            store = account.DeliveryStore
            root = store.GetRootFolder()

            # Find Deleted Items
            deleted_folder = None
            for folder in root.Folders:
                if "deleted" in folder.Name.lower():
                    deleted_folder = folder
                    break

            if not deleted_folder:
                print("Could not find Deleted Items folder")
                return

            print(f"Found Deleted Items folder with {deleted_folder.Items.Count} items")

            # Look for recently deleted X post emails
            items = deleted_folder.Items
            items.Sort("[ReceivedTime]", True)

            print("\n" + "=" * 80)
            print("RECENTLY DELETED X POST EMAILS - CHECKING FOR TRUE DUPLICATES")
            print("=" * 80)

            # Collect X posts we deleted
            x_posts = []
            for item in items:
                if item.Class != 43:
                    continue

                subject = item.Subject or ''
                if 'post by' in subject.lower() and 'on x' in subject.lower():
                    body = item.Body or ''
                    x_url = extract_x_url(body)

                    x_posts.append({
                        'item': item,
                        'subject': subject,
                        'url': x_url,
                        'received': str(item.ReceivedTime)[:19]
                    })

                # Also check for login emails
                if 'secure link to log in to claude.ai' in subject.lower():
                    x_posts.append({
                        'item': item,
                        'subject': subject,
                        'url': 'LOGIN EMAIL',
                        'received': str(item.ReceivedTime)[:19]
                    })

            # Group by subject to check
            from collections import defaultdict
            by_subject = defaultdict(list)
            for post in x_posts:
                by_subject[post['subject']].append(post)

            print("\nAnalyzing deleted emails by subject:\n")

            needs_restore = []

            for subject, posts in sorted(by_subject.items()):
                subj = subject[:50].encode('ascii', 'replace').decode('ascii')
                print(f"\n'{subj}' ({len(posts)} deleted)")

                # Check if URLs are different
                urls = [p['url'] for p in posts]
                unique_urls = set(urls)

                if len(unique_urls) == 1:
                    print(f"  STATUS: TRUE DUPLICATES - same URL")
                    print(f"  URL: {urls[0]}")
                else:
                    print(f"  STATUS: *** DIFFERENT CONTENT - SHOULD RESTORE ***")
                    for post in posts:
                        print(f"    [{post['received']}] {post['url']}")
                    needs_restore.extend(posts[:-1])  # All but one need restoring

                for post in posts:
                    print(f"    - {post['received']}")

            # Summary
            print("\n" + "=" * 80)
            if needs_restore:
                print(f"WARNING: {len(needs_restore)} emails may need to be restored!")
                print("These had the same subject but DIFFERENT content.")
            else:
                print("All deleted duplicates were TRUE duplicates (same URL/content)")
            print("=" * 80)

            return needs_restore


if __name__ == "__main__":
    check_deleted()
