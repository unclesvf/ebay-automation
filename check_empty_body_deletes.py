"""
Check emails deleted due to empty body hash - may need restoration
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from collections import defaultdict

def check_empty_deletes():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("Connected to Outlook")

    scott_folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

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

            if not deleted_folder:
                print("Could not find Deleted Items folder")
                return

            print(f"Checking Deleted Items ({deleted_folder.Items.Count} items)...\n")

            # Find recently deleted emails with empty bodies
            items = deleted_folder.Items
            items.Sort("[ReceivedTime]", True)

            empty_body_emails = []

            for item in items:
                if item.Class != 43:
                    continue

                subject = item.Subject or '(no subject)'
                body = item.Body or ''

                # Check if body is essentially empty
                if len(body.strip()) < 50:  # Very short or empty body
                    empty_body_emails.append({
                        'item': item,
                        'subject': subject,
                        'body_len': len(body.strip()),
                        'received': str(item.ReceivedTime)[:19],
                        'has_attachments': item.Attachments.Count > 0
                    })

            print("=" * 80)
            print("RECENTLY DELETED EMAILS WITH EMPTY/SHORT BODIES:")
            print("=" * 80)

            # Group by subject to see what's what
            by_subject = defaultdict(list)
            for email in empty_body_emails:
                by_subject[email['subject']].append(email)

            unique_subjects = []
            duplicate_subjects = []

            for subject, emails in by_subject.items():
                if len(emails) == 1:
                    unique_subjects.append(emails[0])
                else:
                    duplicate_subjects.append((subject, emails))

            # Show unique subjects that should be restored
            print(f"\n### UNIQUE EMAILS TO RESTORE ({len(unique_subjects)}) ###\n")
            for email in unique_subjects[:30]:  # Show first 30
                subj = email['subject'][:55].encode('ascii', 'replace').decode('ascii')
                att = " [+ATT]" if email['has_attachments'] else ""
                print(f"  [{email['received']}] {subj}{att}")

            if len(unique_subjects) > 30:
                print(f"  ... and {len(unique_subjects) - 30} more")

            # Show true duplicates (same subject, empty body)
            print(f"\n### TRUE DUPLICATES - OK TO DELETE ({len(duplicate_subjects)} sets) ###\n")
            for subject, emails in duplicate_subjects[:10]:
                subj = subject[:50].encode('ascii', 'replace').decode('ascii')
                print(f"  '{subj}' - {len(emails)} copies")

            if len(duplicate_subjects) > 10:
                print(f"  ... and {len(duplicate_subjects) - 10} more sets")

            # Restore unique emails
            print("\n" + "=" * 80)
            print("RESTORING UNIQUE EMAILS...")
            print("=" * 80)

            # We need to figure out which folder to restore to
            # For now, restore all unique ones to Other-Misc and user can re-sort
            other_misc = None
            for subfolder in scott_folder.Folders:
                if subfolder.Name == 'Other-Misc':
                    other_misc = subfolder
                    break

            if not other_misc:
                print("Could not find Other-Misc folder")
                return

            restored = 0
            for email in unique_subjects:
                try:
                    email['item'].Move(other_misc)
                    restored += 1
                except Exception as e:
                    print(f"  Error restoring: {e}")

            print(f"\nRestored {restored} unique emails to Other-Misc")
            print(f"Other-Misc now has {other_misc.Items.Count} items")

            return


if __name__ == "__main__":
    check_empty_deletes()
