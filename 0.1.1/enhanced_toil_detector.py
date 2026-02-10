"""
Enhanced Toil Detector with advanced pattern matching
Detect DevOps toil from Git history with regex patterns and file analysis
"""

import subprocess
import json
import sqlite3
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import concurrent.futures
from typing import Dict, List, Tuple, Optional

class ToilDetector:
    def __init__(self, db_path="toil.db", config_path=None):
        self.db_path = db_path
        self.config = self._load_config(config_path)
        self.init_db()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from YAML file or use defaults"""
        default_config = {
            "patterns": {
                "manual_deploy": {
                    "keywords": ["deploy", "deployment", "production deploy", "prod deploy"],
                    "regex": [
                        r"deploy.*production",
                        r"prod.*deploy",
                        r"release.*v\d+\.\d+",
                        r"pipeline.*run"
                    ],
                    "file_patterns": ["deploy*.sh", "docker-compose.*.yml", "k8s/*.yaml"],
                    "exclude": ["test", "staging", "dev"]
                },
                "manual_fix": {
                    "keywords": ["fix", "hotfix", "emergency", "manual", "patch"],
                    "regex": [
                        r"emergency.*fix",
                        r"critical.*bug",
                        r"manual.*intervention",
                        r"hotfix.*\d+"
                    ],
                    "file_patterns": ["*.patch", "hotfix*"],
                    "exclude": ["test", "unit test"]
                },
                "revert": {
                    "keywords": ["revert", "rollback", "backed out"],
                    "regex": [
                        r"revert.*[a-f0-9]{7,}",
                        r"rollback.*version",
                        r"backed out.*changes"
                    ],
                    "file_patterns": [],
                    "exclude": []
                },
                "env_setup": {
                    "keywords": ["env", "environment", "setup", "config", "configuration"],
                    "regex": [
                        r"environment.*setup",
                        r"config.*change",
                        r"infrastructure.*update",
                        r"terraform.*apply"
                    ],
                    "file_patterns": ["*.tf", "ansible/*", "puppet/*", "chef/*", "Dockerfile"],
                    "exclude": []
                },
                "restart": {
                    "keywords": ["restart", "reboot", "restart service"],
                    "regex": [
                        r"service.*restart",
                        r"server.*reboot",
                        r"container.*restart"
                    ],
                    "file_patterns": [],
                    "exclude": []
                },
                "pipeline_issue": {
                    "keywords": ["pipeline", "ci", "cd", "build"],
                    "regex": [
                        r"pipeline.*failed",
                        r"ci.*fix",
                        r"build.*broken",
                        r"jenkins.*issue"
                    ],
                    "file_patterns": ["*.yml", "Jenkinsfile", ".github/workflows/*"],
                    "exclude": []
                },
                "kubernetes": {
                    "keywords": ["k8s", "kubernetes", "kubectl", "pod"],
                    "regex": [
                        r"kubectl.*apply",
                        r"k8s.*restart",
                        r"pod.*crash",
                        r"deployment.*rollback"
                    ],
                    "file_patterns": ["k8s/*.yaml", "kubernetes/*.yaml"],
                    "exclude": []
                }
            },
            "severity": {
                "high": ["emergency", "critical", "urgent", "outage", "downtime", "security"],
                "medium": ["hotfix", "production", "manual", "ci", "pipeline"],
                "low": ["update", "config", "restart", "env"]
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                default_config.update(user_config)
        
        return default_config
        
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS toil_events (
                id INTEGER PRIMARY KEY,
                date TEXT,
                repo_path TEXT,
                task_type TEXT,
                description TEXT,
                severity TEXT,
                author TEXT,
                files_changed TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def scan_git_history(self, repo_path, days_back: int = 30, include_file_analysis: bool = True) -> List[Dict]:
        """Enhanced git history scanning with file analysis"""
        try:
            repo_path = Path(repo_path).resolve()
            
            # Get commit data
            result = subprocess.run(
                ["git", "log", f"--since={days_back} days ago", 
                 "--pretty=format:%h|%s|%ad|%an", "--date=short", "--name-only"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"Git command failed: {result.stderr}")
            
            toil_found = []
            commits = self._parse_git_output(result.stdout)
            
            for commit in commits:
                # Analyze commit message
                detected_type = self._analyze_commit_message(commit['message'])
                
                if detected_type:
                    # File-based detection if enabled
                    file_based_type = None
                    if include_file_analysis and commit.get('files'):
                        file_based_type = self._analyze_files_changed(commit['files'])
                    
                    # Use most specific match
                    final_type = file_based_type or detected_type
                    
                    severity = self._assess_severity(commit['message'], final_type)
                    
                    toil_found.append({
                        'date': commit['date'],
                        'repo_path': str(repo_path),
                        'task_type': final_type,
                        'description': commit['message'],
                        'severity': severity,
                        'author': commit['author'],
                        'files_changed': ','.join(commit.get('files', []))
                    })
                        
            return toil_found
            
        except Exception as e:
            print(f"Error scanning {repo_path}: {e}")
            return []
    
    def _parse_git_output(self, output: str) -> List[Dict]:
        """Parse git log output into structured commits"""
        commits = []
        current_commit = {}
        
        for line in output.split('\n'):
            if not line.strip():
                if current_commit:
                    commits.append(current_commit)
                    current_commit = {}
                continue
            
            if '|' in line:
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    current_commit = {
                        'hash': parts[0],
                        'message': parts[1],
                        'date': parts[2],
                        'author': parts[3],
                        'files': []
                    }
            elif current_commit and line.strip():
                current_commit['files'].append(line.strip())
        
        if current_commit:
            commits.append(current_commit)
            
        return commits
    
    def _analyze_commit_message(self, message: str) -> Optional[str]:
        """Enhanced commit message analysis with regex"""
        message_lower = message.lower()
        
        for task_type, config in self.config['patterns'].items():
            # Check keywords first (fast path)
            keywords = config.get('keywords', [])
            if any(keyword in message_lower for keyword in keywords):
                # Verify with regex for precision
                regex_patterns = config.get('regex', [])
                if not regex_patterns or any(re.search(pattern, message_lower) for pattern in regex_patterns):
                    # Check exclusions
                    exclusions = config.get('exclude', [])
                    if not any(exclusion in message_lower for exclusion in exclusions):
                        return task_type
        
        return None
    
    def _analyze_files_changed(self, files: List[str]) -> Optional[str]:
        """File-based toil detection"""
        for task_type, config in self.config['patterns'].items():
            file_patterns = config.get('file_patterns', [])
            if not file_patterns:
                continue
                
            for pattern in file_patterns:
                if any(Path(file).match(pattern) for file in files):
                    return task_type
        
        return None
    
    def _assess_severity(self, message: str, task_type: str) -> str:
        """Enhanced severity assessment"""
        message_lower = message.lower()
        
        # Check severity keywords from config
        for level, keywords in self.config['severity'].items():
            if any(keyword in message_lower for keyword in keywords):
                return level.upper()
        
        # Default severity based on task type
        high_severity_types = ['manual_fix', 'revert', 'pipeline_issue']
        medium_severity_types = ['manual_deploy', 'restart']
        
        if task_type in high_severity_types:
            return "HIGH"
        elif task_type in medium_severity_types:
            return "MEDIUM"
        else:
            return "LOW"
    
    def scan_multiple_repos(self, repo_paths: List[str], days_back: int = 30) -> Dict[str, List[Dict]]:
        """Parallel scanning of multiple repositories"""
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_repo = {
                executor.submit(self.scan_git_history, repo, days_back): repo 
                for repo in repo_paths
            }
            
            for future in concurrent.futures.as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    results[repo] = future.result()
                except Exception as e:
                    print(f"Error scanning {repo}: {e}")
                    results[repo] = []
        
        return results
    
    def save_toil_events(self, events: List[Dict]):
        """Save detected toil events to database"""
        conn = sqlite3.connect(self.db_path)
        for event in events:
            conn.execute('''
                INSERT INTO toil_events (date, repo_path, task_type, description, severity, author, files_changed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (event['date'], event['repo_path'], event['task_type'], 
                  event['description'], event['severity'], event['author'], event.get('files_changed', '')))
        conn.commit()
        conn.close()
    
    def get_toil_summary(self, days_back: int = 30) -> List[Tuple]:
        """Get summary of toil events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT task_type, severity, COUNT(*) as count, date, author
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY task_type, severity, author
            ORDER BY count DESC
        '''.format(days_back))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def export_data(self, format_type: str = 'json', days_back: int = 30) -> str:
        """Export toil data in various formats"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT date, repo_path, task_type, description, severity, author
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            ORDER BY date DESC
        '''.format(days_back))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        if format_type.lower() == 'json':
            data = [dict(zip(columns, row)) for row in rows]
            return json.dumps(data, indent=2)
        elif format_type.lower() == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            writer.writerows(rows)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format_type}")

def main():
    detector = ToilDetector()
    
    # Example: Scan current directory
    print("🔍 Scanning for DevOps toil patterns...")
    
    if Path(".git").exists():
        events = detector.scan_git_history(".", days_back=30)
        detector.save_toil_events(events)
        print(f"✅ Found {len(events)} toil events")
        
        summary = detector.get_toil_summary()
        print("\n📊 Toil Summary (last 30 days):")
        for task_type, severity, count, date, author in summary:
            print(f"  {task_type}: {count} ({severity}) by {author}")
    else:
        print("❌ Not a git repository. Run from a git repo directory.")

if __name__ == "__main__":
    main()