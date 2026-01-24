from youtube_transcript_api import YouTubeTranscriptApi
import sys

# Video: "Python in 100 Seconds" by Fireship (Known to have captions)
TEST_VIDEO_ID = "x7X9w_GIm1s" 

def test_api():
    print(f"Testing YouTube Transcript API connectivity...")
    print(f"Target Video ID: {TEST_VIDEO_ID}")
    
    try:
        # Try Static Method first (Standard Library)
        try:
            print("Attempting static method: YouTubeTranscriptApi.get_transcript...")
            transcript = YouTubeTranscriptApi.get_transcript(TEST_VIDEO_ID)
            print("Static method SUCCESS.")
        except AttributeError:
             print("Static method failed (AttributeError). Attempting Instance method...")
             # Try Instance Method (Legacy/Custom Wrapper?)
             api = YouTubeTranscriptApi()
             if hasattr(api, 'get_transcript'):
                 transcript = api.get_transcript(TEST_VIDEO_ID)
             elif hasattr(api, 'fetch'):
                 transcript = api.fetch(TEST_VIDEO_ID)
             else:
                 print("Could not find suitable method on YouTubeTranscriptApi instance.")
                 return False

        if transcript:
            print("\nSUCCESS: Transcript fetched.")
            # Handle different return types (list of dicts vs object)
            if isinstance(transcript, list):
                print(f"Sentence Count: {len(transcript)}")
                print(f"First line: {transcript[0]}")
            else:
                 print(f"Transcript Object: {transcript}")
            return True
        else:
            print("\nFAILURE: Returned empty transcript.")
            return False
            
    except Exception as e:
        print(f"\nCRITICAL FAILURE: API Error.")
        print(f"Error Details: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    if not success:
        sys.exit(1)
