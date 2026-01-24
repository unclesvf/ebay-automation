import sys
import os
import requests

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from actions.youtube_action import YouTubeAction

class MockAutomator:
    def __init__(self):
        self.config = {'vector_db_path': 'start_test'}
        self.folder_name = "TEST_FOLDER"
        self.dry_run = False

def run_verification():
    print("--- 1. Testing Ollama Connection ---")
    url = "http://localhost:11434/api/generate"
    try:
        resp = requests.get("http://localhost:11434")
        print(f"Ollama Server Status: {resp.status_code} (OK)")
    except Exception as e:
        print(f"Ollama Connection Failed: {e}")
        return

    print("\n--- 2. Testing Qwen 2.5 32B Inference ---")
    automator = MockAutomator()
    # Initialize Action
    action = YouTubeAction(automator, {'model': 'qwen2.5:32b'})
    
    # Mock Transcript (Short one for speed)
    mock_transcript = (
        "Hello everyone, welcome to this tutorial on Python. "
        "Today we will use the 'pandas' library to analyze data. "
        "First, install it using 'pip install pandas'. "
        "Then, import it with 'import pandas as pd'. "
        "A pro tip: always check your data types with df.dtypes to avoid errors. "
        "That is it for today."
    )
    
    print("Sending Mock Transcript to Model...")
    summary = action._summarize_with_ollama(mock_transcript)
    
    if summary:
        print("\nSUCCESS! Model Output:")
        print("="*40)
        print(summary)
        print("="*40)
        
        with open("verification_result.txt", "w", encoding='utf-8') as f:
            f.write(summary)
    else:
        print("FAILURE: Model returned no output.")

if __name__ == "__main__":
    run_verification()
