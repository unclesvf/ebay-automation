"""
Mark emails as read after batch processing
"""
import os
from outlook_reader import OutlookReader

def mark_all_read():
    if not os.path.exists('pending_entries.txt'):
        print("No pending_entries.txt found. Run batch_urls.py first.")
        return

    with open('pending_entries.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        print("No entries to mark as read.")
        return

    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print(f"Marking {len(lines)} emails as read...")

    success = 0
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) >= 1:
            entry_id = parts[0]
            item_id = parts[1] if len(parts) > 1 else "unknown"
            if reader.mark_as_read(entry_id):
                print(f"  Marked as read: {item_id}")
                success += 1
            else:
                print(f"  FAILED: {item_id}")

    print(f"\nDone! {success}/{len(lines)} emails marked as read.")

    # Remove the pending file
    os.remove('pending_entries.txt')
    print("Cleared pending_entries.txt")

def mark_specific(item_ids):
    """Mark only specific item IDs as read."""
    if not os.path.exists('pending_entries.txt'):
        print("No pending_entries.txt found.")
        return

    with open('pending_entries.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    remaining = []
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) >= 2:
            entry_id = parts[0]
            item_id = parts[1]
            if item_id in item_ids:
                if reader.mark_as_read(entry_id):
                    print(f"Marked as read: {item_id}")
                else:
                    print(f"FAILED: {item_id}")
                    remaining.append(line)
            else:
                remaining.append(line)

    # Update pending file with remaining entries
    with open('pending_entries.txt', 'w', encoding='utf-8') as f:
        f.writelines(remaining)

    print(f"\n{len(remaining)} entries remaining in pending_entries.txt")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Mark specific item IDs
        mark_specific(sys.argv[1:])
    else:
        # Mark all as read
        confirm = input("Mark ALL pending emails as read? (y/n): ").strip().lower()
        if confirm == 'y':
            mark_all_read()
        else:
            print("Cancelled.")
