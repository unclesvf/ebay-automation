"""
Clean up Claude-Anthropic folder - delete login emails and duplicates
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict

def cleanup_claude_folder():
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

    # Collect all emails
    items = claude_folder.Items
    items.Sort("[ReceivedTime]", True)

    all_emails = []
    for item in items:
        if item.Class != 43:
            continue

        subject = item.Subject or '(no subject)'
        body = item.Body or ''
        received = str(item.ReceivedTime)

        all_emails.append({
            'item': item,
            'subject': subject,
            'body': body[:500],  # First 500 chars for comparison
            'received': received
        })

    print(f"Found {len(all_emails)} emails")

    # Find login emails to delete
    print("\n" + "=" * 60)
    print("LOGIN EMAILS TO DELETE:")
    print("=" * 60)

    login_emails = []
    for email in all_emails:
        if 'secure link to log in to claude.ai' in email['subject'].lower():
            login_emails.append(email)
            subj = email['subject'][:55].encode('ascii', 'replace').decode('ascii')
            print(f"  - {subj}")

    # Find duplicates (same subject)
    print("\n" + "=" * 60)
    print("CHECKING FOR DUPLICATES:")
    print("=" * 60)

    # Group by subject
    by_subject = defaultdict(list)
    for email in all_emails:
        by_subject[email['subject']].append(email)

    duplicates_to_delete = []
    for subject, emails in by_subject.items():
        if len(emails) > 1:
            subj = subject[:55].encode('ascii', 'replace').decode('ascii')
            print(f"\n  '{subj}' - {len(emails)} copies")

            # Keep the oldest one, delete the rest
            emails_sorted = sorted(emails, key=lambda x: x['received'])
            keep = emails_sorted[0]
            delete = emails_sorted[1:]

            print(f"    KEEP: {keep['received'][:19]}")
            for dup in delete:
                print(f"    DELETE: {dup['received'][:19]}")
                duplicates_to_delete.append(dup)

    # Summary before deletion
    total_to_delete = len(login_emails) + len(duplicates_to_delete)
    print("\n" + "=" * 60)
    print(f"SUMMARY: Deleting {total_to_delete} emails")
    print(f"  - Login emails: {len(login_emails)}")
    print(f"  - Duplicates: {len(duplicates_to_delete)}")
    print("=" * 60)

    # Delete the emails
    deleted = 0

    # Delete login emails
    for email in login_emails:
        try:
            email['item'].Delete()
            deleted += 1
        except Exception as e:
            print(f"  Error deleting login email: {e}")

    # Delete duplicates
    for email in duplicates_to_delete:
        try:
            email['item'].Delete()
            deleted += 1
        except Exception as e:
            print(f"  Error deleting duplicate: {e}")

    print(f"\nDeleted {deleted} emails")
    print(f"Remaining in Claude-Anthropic: {claude_folder.Items.Count}")


if __name__ == "__main__":
    cleanup_claude_folder()
