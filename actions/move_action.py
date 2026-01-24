from typing import Dict, List, Any
from actions.base_action import Action

class MoveAction(Action):
    """
    Action: Move emails to subfolders based on keyword matching.
    """
    
    def execute(self):
        rules = self.params.get('rules', {})
        default_folder = self.params.get('default_folder', 'Other-Misc')
        create_missing_folders = self.params.get('create_missing_folders', False)

        # Cache valid subfolders
        valid_subfolders = {}
        for sf in self.automator.folder.Folders:
            valid_subfolders[sf.Name] = sf

        items = self.automator.folder.Items
        items.Sort("[ReceivedTime]", True)
        
        move_count = 0
        
        # Iterate backwards? No, standard iteration is fine if we aren't deleting 
        # (Moving modifies the collection, so typically safer to loop carefully, 
        # but COM objects usually handle this specific Move case okay-ish, or we use a list copy)
        # For safety, let's collect items first.
        
        items_to_process = []
        # Limit processing to prevent hanging on huge folders during dev
        limit = self.params.get('limit', 100) 
        
        for i, item in enumerate(items):
            if i >= limit: break
            if item.Class == 43: # MailItem
                items_to_process.append(item)

        for item in items_to_process:
            subject = getattr(item, 'Subject', '') or ''
            try:
                body = getattr(item, 'Body', '') or ''
                # Truncate body for performance regarding regex/search
                body = body[:2000]
            except:
                body = ''

            # Check exclusion categories (Safety Mechanism)
            categories = getattr(item, 'Categories', '') or ''
            exclude_cats = self.params.get('exclude_categories', [])
            if any(cat in categories for cat in exclude_cats):
                self.logger.info(f"  Skipping '{subject[:30]}' (Excluded Category found)")
                continue

            target = self._categorize(subject, body, rules, default_folder)
            
            if not target:
                continue
                
            # Perform Move
            if target in valid_subfolders:
                dest = valid_subfolders[target]
                if self.automator.dry_run:
                    self.logger.info(f"[DRY RUN] Would move '{subject[:30]}...' -> '{target}'")
                else:
                    try:
                        item.Move(dest)
                        self.logger.info(f"Moved '{subject[:30]}...' -> '{target}'")
                        move_count += 1
                    except Exception as e:
                        self.logger.error(f"Error moving item: {e}")
            else:
            else:
                if create_missing_folders and not self.automator.dry_run:
                    try:
                        self.logger.info(f"Creating new folder: '{target}'")
                        new_folder = self.automator.folder.Folders.Add(target)
                        valid_subfolders[target] = new_folder  # Add to cache
                        
                        # Now retry move
                        item.Move(new_folder)
                        self.logger.info(f"Moved '{subject[:30]}...' -> '{target}' (Created new folder)")
                        move_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to create folder '{target}': {e}")
                elif create_missing_folders and self.automator.dry_run:
                    self.logger.info(f"[DRY RUN] Would create folder '{target}' and move '{subject[:30]}...'")
                else:
                    self.logger.debug(f"Target folder '{target}' not found. Skipping (create_missing=False).")

        self.logger.info(f"MoveAction Completed. Moved {move_count} items.")

    def _categorize(self, subject: str, body: str, rules: Dict[str, List[str]], default: str) -> str:
        text = f"{subject} {body}".lower()
        for category, keywords in rules.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category
        return default
