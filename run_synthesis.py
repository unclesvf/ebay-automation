import sys
import logging
import os
from actions.synthesizer import Synthesizer

# Add current directory to path dynamically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(BASE_DIR, 'synthesis.log'))
        ]
    )

if __name__ == "__main__":
    setup_logging()
    
    print("Initializing Idea Generator...")
    synth = Synthesizer()
    
    print("Running cross-pollination algorithms...")
    synth.run_daily_synthesis()
    
    print("Done! Check 'idea_synthesis.txt' for new possibilities.")
