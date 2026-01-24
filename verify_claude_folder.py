"""
Verify Claude-Anthropic folder has no true duplicates
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict
import re

def extract_x_url(text):
    """Extract the main X.com post URL from email body"""
    pattern = r'https://x\.com/(\w+)/status/(\d+)'
    match = re.search(pattern, text)
    if match:
        return f"https://x.com/{match.group(1)}/status/{match.group(2)}"
    return None

def verify():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    claude_folder = None
    for subfolder in scott_folder.Folders:
        if subfolder.Name == 'Claude-Anthropic':
            claude_folder = subfolder
            break

    print(f"Claude-Anthropic has {claude_folder.Items.Count} items")

    items = claude_folder.Items
    items.Sort("[ReceivedTime]", True)

    # Collect all emails with their URLs
    emails = []
    for item in items:
        if item.Class != 43:
            continue

        subject = item.Subject or '(no subject)'
        body = item.Body or ''
        url = extract_x_url(body)

        emails.append({
            'subject': subject,
            'url': url,
            'received': str(item.ReceivedTime)[:19]
        })

    # Check for duplicate URLs
    by_url = defaultdict(list)
    for email in emails:
        if email['url']:
            by_url[email['url']].append(email)

    print("\n" + "=" * 70)
    print("CHECKING FOR DUPLICATE URLs:")
    print("=" * 70)

    has_duplicates = False
    for url, url_emails in by_url.items():
        if len(url_emails) > 1:
            has_duplicates = True
            print(f"\nDUPLICATE URL: {url}")
            for e in url_emails:
                subj = e['subject'][:40].encode('ascii', 'replace').decode('ascii')
                print(f"  [{e['received']}] {subj}")

    if not has_duplicates:
        print("\nNo duplicate URLs found - all emails are unique!")

    # Show Alex Finn emails specifically
    print("\n" + "=" * 70)
    print("ALEX FINN EMAILS IN FOLDER:")
    print("=" * 70)

    for email in emails:
        if 'alex finn' in email['subject'].lower():
            subj = email['subject'][:50].encode('ascii', 'replace').decode('ascii')
            print(f"\n  [{email['received']}] {subj}")
            print(f"  URL: {email['url']}")


if __name__ == "__main__":
    verify()
