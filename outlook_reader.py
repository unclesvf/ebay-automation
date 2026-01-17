"""
Outlook Email Reader Module
Uses COM automation to read emails from Outlook Classic
"""

import win32com.client
from typing import List, Dict, Optional
from datetime import datetime


class OutlookReader:
    def __init__(self):
        self.outlook = None
        self.namespace = None

    def connect(self) -> bool:
        """Connect to Outlook application via COM."""
        try:
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook.GetNamespace("MAPI")
            return True
        except Exception as e:
            print(f"Failed to connect to Outlook: {e}")
            return False

    def get_accounts(self) -> List[str]:
        """Get list of email accounts configured in Outlook."""
        accounts = []
        try:
            for account in self.namespace.Accounts:
                accounts.append(account.SmtpAddress)
        except Exception as e:
            print(f"Error getting accounts: {e}")
        return accounts

    def get_folders(self, account_email: Optional[str] = None) -> Dict[str, any]:
        """Get folder structure for an account."""
        folders = {}
        try:
            if account_email:
                # Find the specific account's root folder
                for store in self.namespace.Stores:
                    if account_email.lower() in store.DisplayName.lower():
                        root = store.GetRootFolder()
                        folders = self._enumerate_folders(root)
                        break
            else:
                # Use default inbox's parent
                inbox = self.namespace.GetDefaultFolder(6)  # 6 = olFolderInbox
                root = inbox.Parent
                folders = self._enumerate_folders(root)
        except Exception as e:
            print(f"Error getting folders: {e}")
        return folders

    def _enumerate_folders(self, folder, level=0) -> Dict:
        """Recursively enumerate folders."""
        result = {
            'name': folder.Name,
            'path': folder.FolderPath,
            'count': getattr(folder, 'Items', {}).Count if hasattr(folder, 'Items') else 0,
            'subfolders': []
        }
        try:
            for subfolder in folder.Folders:
                result['subfolders'].append(self._enumerate_folders(subfolder, level + 1))
        except:
            pass
        return result

    def get_folder_by_name(self, folder_name: str, account_email: Optional[str] = None):
        """Find a folder by name within an account."""
        try:
            if account_email:
                # Use account's DeliveryStore for more reliable access
                for account in self.namespace.Accounts:
                    if account_email.lower() in account.SmtpAddress.lower():
                        store = account.DeliveryStore
                        root = store.GetRootFolder()
                        return self._find_folder(root, folder_name)
            else:
                inbox = self.namespace.GetDefaultFolder(6)
                root = inbox.Parent
                return self._find_folder(root, folder_name)
        except Exception as e:
            print(f"Error finding folder '{folder_name}': {e}")
        return None

    def _find_folder(self, parent_folder, target_name: str):
        """Recursively search for a folder by name."""
        try:
            if parent_folder.Name.lower() == target_name.lower():
                return parent_folder
            for subfolder in parent_folder.Folders:
                found = self._find_folder(subfolder, target_name)
                if found:
                    return found
        except:
            pass
        return None

    def read_emails(self, folder, limit: int = 50, unread_only: bool = False) -> List[Dict]:
        """
        Read emails from a folder.

        Args:
            folder: Outlook folder object
            limit: Maximum number of emails to retrieve
            unread_only: If True, only return unread emails

        Returns:
            List of email dictionaries
        """
        emails = []
        try:
            items = folder.Items
            items.Sort("[ReceivedTime]", True)  # Sort by newest first

            count = 0
            for item in items:
                if count >= limit:
                    break

                # Check if it's a mail item (not meeting request, etc.)
                if item.Class != 43:  # 43 = olMail
                    continue

                if unread_only and item.UnRead == False:
                    continue

                email_data = {
                    'subject': item.Subject,
                    'sender': item.SenderName,
                    'sender_email': self._get_sender_email(item),
                    'received': item.ReceivedTime,
                    'body': item.Body,
                    'html_body': getattr(item, 'HTMLBody', ''),
                    'unread': item.UnRead,
                    'entry_id': item.EntryID,
                    'attachments': [att.FileName for att in item.Attachments] if item.Attachments.Count > 0 else []
                }
                emails.append(email_data)
                count += 1

        except Exception as e:
            print(f"Error reading emails: {e}")

        return emails

    def _get_sender_email(self, item) -> str:
        """Extract sender email address."""
        try:
            if item.SenderEmailType == "EX":
                # Exchange address - need to resolve
                sender = item.Sender
                if sender:
                    return sender.GetExchangeUser().PrimarySmtpAddress
            return item.SenderEmailAddress
        except:
            return item.SenderEmailAddress or ""

    def mark_as_read(self, entry_id: str) -> bool:
        """Mark an email as read by its EntryID."""
        try:
            item = self.namespace.GetItemFromID(entry_id)
            item.UnRead = False
            item.Save()
            return True
        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False

    def mark_as_unread(self, entry_id: str) -> bool:
        """Mark an email as unread by its EntryID."""
        try:
            item = self.namespace.GetItemFromID(entry_id)
            item.UnRead = True
            item.Save()
            return True
        except Exception as e:
            print(f"Error marking email as unread: {e}")
            return False

    def move_email(self, entry_id: str, dest_folder) -> bool:
        """Move an email to a different folder."""
        try:
            item = self.namespace.GetItemFromID(entry_id)
            item.Move(dest_folder)
            return True
        except Exception as e:
            print(f"Error moving email: {e}")
            return False


def list_folders_for_account(account_email: str = None):
    """Utility function to list all folders."""
    reader = OutlookReader()
    if reader.connect():
        print("Connected to Outlook")
        print("\nAccounts:")
        for acc in reader.get_accounts():
            print(f"  - {acc}")

        print("\nFolders:")
        folders = reader.get_folders(account_email)
        _print_folders(folders)


def _print_folders(folder_dict, indent=0):
    """Pretty print folder structure."""
    prefix = "  " * indent
    name = folder_dict.get('name', 'Unknown')
    count = folder_dict.get('count', 0)
    print(f"{prefix}- {name} ({count} items)")
    for sub in folder_dict.get('subfolders', []):
        _print_folders(sub, indent + 1)


if __name__ == "__main__":
    # Test the module
    list_folders_for_account()
