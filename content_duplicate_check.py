"""
Content-based duplicate check across all folders
Compares URLs and body content, not just subjects
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict
import re
import hashlib

def extract_urls(text):
    """Extract all URLs from text"""
    pattern = r'https?://[^\s<>"\')\]>]+'
    urls = re.findall(pattern, text)
    # Clean and dedupe
    cleaned = []
    for url in urls:
        url = url.rstrip('.,;:!')
        # Skip common tracking/image URLs
        if 'twimg.com' in url or 'spacer.png' in url:
            continue
        if url not in cleaned:
            cleaned.append(url)
    return cleaned

def get_content_hash(body):
    """Create a hash of the meaningful content"""
    # Normalize whitespace and get first 1000 chars
    text = ' '.join(body.split())[:1000].lower()
    return hashlib.md5(text.encode()).hexdigest()

def extract_x_status_id(text):
    """Extract X/Twitter status ID if present"""
    pattern = r'x\.com/\w+/status/(\d+)'
    match = re.search(pattern, text)
    return match.group(1) if match else None

def content_duplicate_check():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")
    if not scott_folder:
        print("Could not find 'scott' folder")
        return

    # Get all folders
    folder_map = {}
    for subfolder in scott_folder.Folders:
        folder_map[subfolder.Name] = subfolder

    print(f"Scanning {len(folder_map)} folders for content-based duplicates...\n")

    # Collect all emails with content signatures
    all_emails = []

    for folder_name, folder in folder_map.items():
        items = folder.Items

        for item in items:
            if item.Class != 43:
                continue

            subject = item.Subject or '(no subject)'
            body = item.Body or ''

            # Create content signature
            urls = extract_urls(body)
            x_status = extract_x_status_id(body)
            content_hash = get_content_hash(body)

            # Primary key for X posts is the status ID
            # For other emails, use content hash + primary URL
            if x_status:
                content_key = f"x_status:{x_status}"
            elif urls:
                content_key = f"url:{urls[0]}"
            else:
                content_key = f"hash:{content_hash}"

            all_emails.append({
                'item': item,
                'folder': folder_name,
                'subject': subject,
                'content_key': content_key,
                'x_status': x_status,
                'urls': urls,
                'received': str(item.ReceivedTime)[:19]
            })

    print(f"Scanned {len(all_emails)} total emails\n")

    # Group by content key to find duplicates
    by_content = defaultdict(list)
    for email in all_emails:
        by_content[email['content_key']].append(email)

    # Find duplicates (same content in multiple emails)
    duplicates_found = []

    for content_key, emails in by_content.items():
        if len(emails) > 1:
            # Sort by received date, keep oldest
            emails_sorted = sorted(emails, key=lambda x: x['received'])
            keep = emails_sorted[0]
            dupes = emails_sorted[1:]

            duplicates_found.append({
                'content_key': content_key,
                'keep': keep,
                'duplicates': dupes
            })

    # Report findings
    print("=" * 80)
    print("CONTENT-BASED DUPLICATE ANALYSIS")
    print("=" * 80)

    if not duplicates_found:
        print("\nNo content duplicates found across all folders!")
        return

    print(f"\nFound {len(duplicates_found)} sets of duplicates:\n")

    total_to_delete = 0

    for dup_set in duplicates_found:
        content_key = dup_set['content_key']
        keep = dup_set['keep']
        dupes = dup_set['duplicates']

        # Display info
        subj = keep['subject'][:45].encode('ascii', 'replace').decode('ascii')
        print(f"\n{'─' * 70}")
        print(f"Content: {content_key[:60]}")
        print(f"Subject: {subj}")
        print(f"  KEEP: [{keep['folder']}] {keep['received']}")

        for dup in dupes:
            print(f"  DELETE: [{dup['folder']}] {dup['received']}")
            total_to_delete += 1

    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {total_to_delete} duplicate emails can be deleted")
    print(f"{'=' * 80}")

    if total_to_delete == 0:
        return

    # Delete duplicates
    print("\nDeleting duplicates...")

    deleted = 0
    errors = 0

    for dup_set in duplicates_found:
        for dup in dup_set['duplicates']:
            try:
                dup['item'].Delete()
                deleted += 1
            except Exception as e:
                errors += 1
                subj = dup['subject'][:30].encode('ascii', 'replace').decode('ascii')
                print(f"  Error deleting '{subj}': {e}")

    print(f"\nDeleted {deleted} duplicate emails")
    if errors:
        print(f"Errors: {errors}")

    # Show updated folder counts
    print("\n" + "=" * 80)
    print("UPDATED FOLDER COUNTS:")
    print("=" * 80)

    for folder_name, folder in sorted(folder_map.items()):
        print(f"  {folder_name}: {folder.Items.Count}")


if __name__ == "__main__":
    content_duplicate_check()
