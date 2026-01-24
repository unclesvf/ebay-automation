import sys
import logging
from typing import Dict, List, Any
import yaml

# Add parent directory to path to import outlook_reader
# sys.path.insert(0, r'C:\Users\scott\ebay-automation') # Handled by orchestrator
from outlook_reader import OutlookReader

class FolderAutomator:
    """
    Core engine for folder-specific automation.
    Connects to a specific folder and executes a defined set of actions.
    """
    
    def __init__(self, config: Dict[str, Any], dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.account_email = config.get('account')
        self.folder_name = config.get('source_folder')
        self.actions = config.get('actions', [])
        
        self.reader = OutlookReader()
        self.folder = None
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger(f"Automator-{self.folder_name}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def connect(self) -> bool:
        """Establish connection to the target Outlook folder."""
        if not self.reader.connect():
            self.logger.error("Failed to connect to Outlook application")
            return False

        self.folder = self.reader.get_folder_by_name(self.folder_name, self.account_email)
        
        if not self.folder:
            self.logger.error(f"Could not find folder '{self.folder_name}' in account '{self.account_email}'")
            return False
            
        self.logger.info(f"Connected to '{self.folder.Name}' ({self.folder.Items.Count} items)")
        return True

    def run(self):
        """Execute all configured actions for this folder."""
        if not self.folder:
            if not self.connect():
                return

        self.logger.info(f"Starting automation for profile: {self.config.get('id', 'unknown')}")
        
        for action_config in self.actions:
            action_name = action_config.get('name', 'unnamed_action')
            action_type = action_config.get('type')
            params = action_config.get('params', {})
            
            self.logger.info(f"--- Running Action: {action_name} ({action_type}) ---")
            
            try:
                self._dispatch_action(action_type, params)
            except Exception as e:
                self.logger.error(f"Error executing action '{action_name}': {e}", exc_info=True)

    def _dispatch_action(self, action_type: str, params: Dict[str, Any]):
        """Route the action type to the correct handler class."""
        
        action_map = {
            'move_based_on_keywords': 'actions.move_action.MoveAction',
            'ingest_to_knowledge_base': 'actions.ingest_action.IngestAction',
            'discover_new_keywords': 'actions.discovery_action.DiscoveryAction',
            'process_youtube_videos': 'actions.youtube_action.YouTubeAction',
            # Future mappings:
            # 'save_attachments': 'actions.save_action.SaveAction',
        }
        
        if action_type in action_map:
            module_path, class_name = action_map[action_type].rsplit('.', 1)
            try:
                # Dynamic import
                module = __import__(module_path, fromlist=[class_name])
                action_class = getattr(module, class_name)
                
                # Instantiate and Execute
                action_instance = action_class(self, params)
                action_instance.execute()
                
            except ImportError as e:
                self.logger.error(f"Could not import action module '{module_path}': {e}")
            except AttributeError as e:
                self.logger.error(f"Could not find class '{class_name}' in '{module_path}': {e}")
            except Exception as e:
                self.logger.error(f"Error executing action class '{class_name}': {e}", exc_info=True)
        else:
            self.logger.warning(f"Unknown action type: {action_type}")
