"""
Test with a DevOps-focused repository
"""

import subprocess
import os
from pathlib import Path
from toil_detector import ToilDetector

def test_devops_repo():
    repo_url = "https://github.com/traefik/traefik"
    temp_dir = Path("temp_devops_repo")
    
    try:
        # Clone repo
        print("Cloning DevOps test repo (traefik)...")
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
            
        subprocess.run(["git", "clone", repo_url, str(temp_dir)], 
                     check=True, capture_output=True)
        
        # Test detection with more days
        print("Running toil detection (last 30 days)...")
        detector = ToilDetector("devops_test.db")
        events = detector.scan_git_history(str(temp_dir), days_back=30)
        
        print(f"\nFound {len(events)} toil events in last 30 days:")
        
        # Group by type
        by_type = {}
        for event in events:
            task_type = event['task_type']
            if task_type not in by_type:
                by_type[task_type] = []
            by_type[task_type].append(event)
        
        for task_type, task_events in by_type.items():
            print(f"\n{task_type.upper()} ({len(task_events)} events):")
            for event in task_events[:3]:  # Show first 3 of each type
                print(f"  {event['date']} ({event['severity']})")
                print(f"    {event['description']}")
            if len(task_events) > 3:
                print(f"    ... and {len(task_events) - 3} more")
        
        return events
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    test_devops_repo()