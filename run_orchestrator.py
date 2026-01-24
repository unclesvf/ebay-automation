import sys
import yaml
import logging
import os
from typing import Dict
from actions.folder_automator import FolderAutomator

# Add current directory to path dynamically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(BASE_DIR, 'orchestrator.log'))
        ]
    )

def load_config(path: str) -> Dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def run_main():
    setup_logging()
    logger = logging.getLogger("Orchestrator")
    
    # Allow config override via CLI
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = os.path.join(BASE_DIR, 'rules', 'scott_config.yaml')
    
    try:
        logger.info(f"Loading configuration from {config_path}")
        full_config = load_config(config_path)
        
        global_settings = full_config.get('global', {})
        profiles = full_config.get('profiles', [])
        
        dry_run = global_settings.get('dry_run', True)
        if dry_run:
            logger.info("--- DRY RUN MODE ENABLED (No changes will be made) ---")

        for profile in profiles:
            if not profile.get('active', False):
                logger.info(f"Skipping inactive profile: {profile.get('id')}")
                continue
                
            logger.info(f"Initializing profile: {profile.get('id')}")
            
            automator = FolderAutomator(profile, dry_run=dry_run)
            automator.run()
            
        logger.info("Orchestration complete.")
        
    except Exception as e:
        logger.error(f"Orchestration failed: {e}", exc_info=True)

if __name__ == "__main__":
    run_main()
