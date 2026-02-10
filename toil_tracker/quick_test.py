"""
Quick test with one public repository
"""

import subprocess
import os
from pathlib import Path
from toil_detector import ToilDetector

def test_single_repo():
    repo_url = "https://github.com/dwmkerr/hacker-laws"
    repo_name = "hacker-laws"
    temp_dir = Path("temp_repo")
    
    try:
        # Clone repo
        print("Cloning test repo...")
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
            
        subprocess.run(["git", "clone", repo_url, str(temp_dir)], 
                     check=True, capture_output=True)
        
        # Test detection
        print("Running toil detection...")
        detector = ToilDetector("test.db")
        events = detector.scan_git_history(str(temp_dir), days_back=90)
        
        print(f"Found {len(events)} toil events:")
        for event in events:
            print(f"  {event['date']} - {event['task_type']} ({event['severity']})")
            print(f"    {event['description']}")
        
        return events
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    test_single_repo()