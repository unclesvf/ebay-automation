import subprocess
import json

try:
    # Run ollama list
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True, encoding='utf-8')
    
    print("Ollama Models Found:\n")
    print(result.stdout)
    
    with open("ollama_models.txt", "w", encoding='utf-8') as f:
        f.write(result.stdout)
        
except Exception as e:
    print(f"Error: {e}")
