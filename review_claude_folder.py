"""
Review Claude-Anthropic folder contents in detail
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
import re

def extract_urls(text):
    """Extract URLs from text"""
    url_pattern = r'https?://[^\s<>"\')\]>]+'
    urls = re.findall(url_pattern, text)
    # Clean up URLs
    cleaned = []
    for url in urls:
        # Remove trailing punctuation
        url = url.rstrip('.,;:!')
        if url not in cleaned:
            cleaned.append(url)
    return cleaned

def review_claude_folder():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")
    if not scott_folder:
        print("Could not find 'scott' folder")
        return

    # Find Claude-Anthropic folder
    claude_folder = None
    for subfolder in scott_folder.Folders:
        if subfolder.Name == 'Claude-Anthropic':
            claude_folder = subfolder
            break

    if not claude_folder:
        print("Could not find Claude-Anthropic folder")
        return

    print(f"Found Claude-Anthropic folder with {claude_folder.Items.Count} items")

    # Read all emails with details
    items = claude_folder.Items
    items.Sort("[ReceivedTime]", True)

    print("\n" + "=" * 80)
    print("CLAUDE-ANTHROPIC FOLDER CONTENTS")
    print("=" * 80)

    emails_data = []

    count = 0
    for item in items:
        if item.Class != 43:
            continue
        count += 1

        subject = item.Subject or '(no subject)'
        body = item.Body or ''
        received = str(item.ReceivedTime)[:10]

        # Extract URLs
        urls = extract_urls(body)

        # Get first 200 chars of body as preview
        preview = body[:300].replace('\n', ' ').replace('\r', ' ')
        preview = ' '.join(preview.split())  # Normalize whitespace

        emails_data.append({
            'num': count,
            'date': received,
            'subject': subject,
            'preview': preview,
            'urls': urls,
            'body': body
        })

    # Print detailed view
    for email in emails_data:
        subj = email['subject'][:70].encode('ascii', 'replace').decode('ascii')
        print(f"\n{email['num']:2}. [{email['date']}] {subj}")

        # Show preview
        preview = email['preview'][:150].encode('ascii', 'replace').decode('ascii')
        if preview:
            print(f"    Preview: {preview}...")

        # Show URLs
        if email['urls']:
            print(f"    URLs ({len(email['urls'])}):")
            for url in email['urls'][:3]:  # Show first 3 URLs
                print(f"      - {url[:80]}")
            if len(email['urls']) > 3:
                print(f"      ... and {len(email['urls']) - 3} more")

    # Summary by type
    print("\n" + "=" * 80)
    print("SUMMARY BY TYPE")
    print("=" * 80)

    # Categorize
    twitter_posts = []
    github_links = []
    youtube_links = []
    reddit_posts = []
    other = []

    for email in emails_data:
        subj_lower = email['subject'].lower()
        urls_str = ' '.join(email['urls']).lower()

        if 'post by' in subj_lower and 'on x' in subj_lower:
            twitter_posts.append(email)
        elif 'github.com' in urls_str or 'github' in subj_lower:
            github_links.append(email)
        elif 'youtube.com' in urls_str or 'youtu.be' in urls_str:
            youtube_links.append(email)
        elif 'reddit.com' in urls_str:
            reddit_posts.append(email)
        else:
            other.append(email)

    print(f"\nTwitter/X Posts about Claude: {len(twitter_posts)}")
    print(f"GitHub Projects: {len(github_links)}")
    print(f"YouTube Videos: {len(youtube_links)}")
    print(f"Reddit Posts: {len(reddit_posts)}")
    print(f"Other: {len(other)}")

    # List the "other" ones
    if other:
        print("\n### Other/Direct Claude Content ###")
        for email in other:
            subj = email['subject'][:60].encode('ascii', 'replace').decode('ascii')
            print(f"  [{email['date']}] {subj}")

    print(f"\nTotal emails: {len(emails_data)}")


if __name__ == "__main__":
    review_claude_folder()
