"""
Test Toil Detector against public repositories
Validate patterns and see real-world DevOps toil
"""

import subprocess
import os
from pathlib import Path
from toil_detector import ToilDetector

def clone_and_test_repo(repo_url, repo_name):
    """Clone a repo temporarily and test for toil"""
    temp_dir = Path("temp_repos") / repo_name.replace("/", "_")
    
    try:
        # Clone if not exists
        if not temp_dir.exists():
            print(f"Cloning {repo_name}...")
            temp_dir.parent.mkdir(exist_ok=True)
            subprocess.run(["git", "clone", repo_url, str(temp_dir)], 
                         check=True, capture_output=True)
        
        # Test toil detection
        print(f"\nAnalyzing {repo_name}...")
        detector = ToilDetector(f"test_{repo_name.replace('/', '_')}.db")
        events = detector.scan_git_history(str(temp_dir), days_back=60)
        
        if events:
            print(f"Found {len(events)} toil events:")
            for event in events[:5]:  # Show first 5
                print(f"  {event['date']} - {event['task_type']} ({event['severity']})")
                print(f"    {event['description'][:80]}...")
            if len(events) > 5:
                print(f"  ... and {len(events) - 5} more")
        else:
            print("  No toil patterns detected")
            
        return events
        
    except Exception as e:
        print(f"Error with {repo_name}: {e}")
        return []

def main():
    print("Testing Toil Detector on Public Repositories\n")
    
    # Test diverse repos
    test_repos = [
        # DevOps/Infrastructure
        ("https://github.com/hashicorp/terraform", "terraform"),
        ("https://github.com/kubernetes/kubernetes", "kubernetes"),
        ("https://github.com/microsoft/vscode", "vscode"),
        
        # Smaller projects (more realistic patterns)
        ("https://github.com/dwmkerr/hacker-laws", "hacker-laws"),
        ("https://github.com/public-apis/public-apis", "public-apis"),
        
        # DevOps focused
        ("https://github.com/grafana/grafana", "grafana"),
        ("https://github.com/traefik/traefik", "traefik")
    ]
    
    total_events = 0
    successful_repos = 0
    
    for repo_url, repo_name in test_repos:
        events = clone_and_test_repo(repo_url, repo_name)
        if events is not None:
            total_events += len(events)
            successful_repos += 1
    
    print(f"\nSummary:")
    print(f"  Analyzed: {successful_repos}/{len(test_repos)} repos")
    print(f"  Total toil events: {total_events}")
    print(f"  Average per repo: {total_events/successful_repos:.1f}")
    
    # Clean up
    print(f"\nCleaning up temporary files...")
    import shutil
    if Path("temp_repos").exists():
        shutil.rmtree("temp_repos")

if __name__ == "__main__":
    main()