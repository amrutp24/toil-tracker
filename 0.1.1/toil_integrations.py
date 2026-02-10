"""
Toil Tracker Integrations
Slack, JIRA, GitHub Actions, and Email notifications
"""

import json
import requests
import smtplib
import pandas as pd
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3

class ToilIntegrations:
    def __init__(self, config: Dict, db_path: str = "toil_v2.db"):
        self.config = config
        self.db_path = db_path
        
    def send_slack_notification(self, message: str, channel: Optional[str] = None) -> bool:
        """Send notification to Slack"""
        slack_config = self.config.get('integrations', {}).get('slack', {})
        
        if not slack_config.get('enabled', False):
            return False
            
        webhook_url = slack_config.get('webhook_url', '')
        if not webhook_url:
            print("❌ Slack webhook URL not configured")
            return False
        
        payload = {
            "channel": channel or slack_config.get('channel', '#devops-alerts'),
            "username": slack_config.get('username', 'ToilTracker'),
            "icon_emoji": slack_config.get('icon_emoji', ':warning:'),
            "text": message,
            "attachments": [
                {
                    "color": "danger" if "HIGH" in message else "warning" if "MEDIUM" in message else "good",
                    "footer": "Toil Tracker",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Slack notification failed: {e}")
            return False
    
    def create_jira_issue(self, toil_event: Dict) -> Optional[str]:
        """Create JIRA issue for toil event"""
        jira_config = self.config.get('integrations', {}).get('jira', {})
        
        if not jira_config.get('enabled', False):
            return None
        
        server_url = jira_config.get('server_url', '')
        username = jira_config.get('username', '')
        api_token = jira_config.get('api_token', '')
        
        if not all([server_url, username, api_token]):
            print("❌ JIRA configuration incomplete")
            return None
        
        # Map severity to JIRA priority
        priority_map = {
            'HIGH': jira_config.get('priority_mapping', {}).get('HIGH', 'Highest'),
            'MEDIUM': jira_config.get('priority_mapping', {}).get('MEDIUM', 'High'),
            'LOW': jira_config.get('priority_mapping', {}).get('LOW', 'Medium')
        }
        
        issue_data = {
            "fields": {
                "project": {"key": jira_config.get('project_key', 'DEV')},
                "summary": f"Toil Alert: {toil_event['task_type']} - {toil_event['description'][:50]}",
                "description": f"""
                *Toil Event Details:*
                
                *Type:* {toil_event['task_type']}
                *Severity:* {toil_event['severity']}
                *Author:* {toil_event['author']}
                *Date:* {toil_event['date']}
                *Repository:* {toil_event['repo_path']}
                
                *Description:* {toil_event['description']}
                
                *Files Changed:* {toil_event.get('files_changed', 'N/A')}
                
                ---
                *This issue was automatically created by Toil Tracker to highlight automation opportunities.*
                """,
                "issuetype": {"name": jira_config.get('default_issue_type', 'Task')},
                "priority": {"name": priority_map.get(toil_event['severity'], 'Medium')},
                "labels": ["toil", "automation-opportunity", "devops"]
            }
        }
        
        try:
            auth = (username, api_token)
            headers = {"Content-Type": "application/json"}
            url = f"{server_url}/rest/api/2/issue"
            
            response = requests.post(url, json=issue_data, auth=auth, headers=headers, timeout=15)
            
            if response.status_code == 201:
                issue_key = response.json().get('key')
                print(f"✅ JIRA issue created: {issue_key}")
                return issue_key
            else:
                print(f"❌ JIRA issue creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ JIRA integration error: {e}")
            return None
    
    def create_github_issue(self, toil_event: Dict) -> Optional[str]:
        """Create GitHub issue for toil event"""
        github_config = self.config.get('integrations', {}).get('github', {})
        
        if not github_config.get('enabled', False):
            return None
        
        token = github_config.get('token', '')
        if not token:
            print("❌ GitHub token not configured")
            return None
        
        # Get repo from path or use default
        repo_path = Path(toil_event['repo_path'])
        repo_name = github_config.get('default_repo', 'toil-tracker/issues')
        
        issue_data = {
            "title": f"Toil Alert: {toil_event['task_type']} - {toil_event['description'][:50]}",
            "body": f"""
## Toil Event Details

**Type:** {toil_event['task_type']}  
**Severity:** {toil_event['severity']}  
**Author:** {toil_event['author']}  
**Date:** {toil_event['date']}  
**Repository:** {toil_event['repo_path']}  

### Description
{toil_event['description']}

### Files Changed
{toil_event.get('files_changed', 'N/A')}

---
*This issue was automatically created by Toil Tracker to highlight automation opportunities.* 
""",
            "labels": github_config.get('labels', ['toil', 'automation-opportunity']),
            "assignees": github_config.get('assign_to', [])
        }
        
        try:
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            url = f"https://api.github.com/repos/{repo_name}/issues"
            
            response = requests.post(url, json=issue_data, headers=headers, timeout=15)
            
            if response.status_code == 201:
                issue_data = response.json()
                issue_url = issue_data.get('html_url')
                print(f"✅ GitHub issue created: {issue_url}")
                return issue_url
            else:
                print(f"❌ GitHub issue creation failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ GitHub integration error: {e}")
            return None
    
    def send_email_notification(self, subject: str, body: str, recipients: Optional[List[str]] = None) -> bool:
        """Send email notification"""
        email_config = self.config.get('integrations', {}).get('email', {})
        
        if not email_config.get('enabled', False):
            return False
        
        required_fields = ['smtp_server', 'username', 'password', 'from_address']
        if not all(email_config.get(field) for field in required_fields):
            print("❌ Email configuration incomplete")
            return False
        
        to_addresses = recipients or email_config.get('to_addresses', [])
        if not to_addresses:
            print("❌ No email recipients specified")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config.get('smtp_port', 587))
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            
            text = msg.as_string()
            server.sendmail(email_config['from_address'], to_addresses, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
            return False
    
    def check_and_trigger_integrations(self) -> Dict[str, int]:
        """Check conditions and trigger configured integrations"""
        conn = sqlite3.connect(self.db_path)
        
        # Get recent toil events (last 24 hours)
        query = '''
            SELECT * FROM toil_events 
            WHERE date >= date('now', '-1 day')
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {"slack": 0, "jira": 0, "github": 0, "email": 0}
        
        integration_stats = {"slack": 0, "jira": 0, "github": 0, "email": 0}
        
        # Check trigger conditions
        conditions = self.config.get('integrations', {}).get('slack', {}).get('trigger_conditions', {})
        
        high_severity_count = len(df[df['severity'] == 'HIGH'])
        daily_toil_count = len(df)
        
        # Calculate estimated cost
        hourly_rate = self.config.get('analytics', {}).get('cost_estimation', {}).get('default_hourly_rate', 100)
        estimated_cost = daily_toil_count * 2 * hourly_rate  # 2 hours avg per toil event
        
        # Prepare summary message
        summary = f"""
🔧 **Toil Tracker Alert - Last 24 Hours**

📊 **Summary:**
• Total Toil Events: {daily_toil_count}
• High Severity: {high_severity_count}
• Estimated Cost: ${estimated_cost:.0f}

🔥 **Top Issues:"""
        
        # Add top 3 issues
        for _, event in df.head(3).iterrows():
            summary += f"\n• {event['task_type']} ({event['severity']}) - {event['description'][:50]}..."
        
        # Send Slack notification if conditions met
        if (high_severity_count >= conditions.get('high_severity_count', 3) or
            daily_toil_count >= conditions.get('daily_toil_threshold', 10) or
            estimated_cost >= conditions.get('cost_threshold', 1000)):
            
            if self.send_slack_notification(summary):
                integration_stats["slack"] = 1
        
        # Create JIRA issues for high severity events
        jira_config = self.config.get('integrations', {}).get('jira', {})
        if jira_config.get('enabled', False):
            high_severity_df = df[df['severity'] == 'HIGH']
            for index, row in high_severity_df.iterrows():
                if integration_stats["jira"] >= 3:  # Limit to 3 issues
                    break
                event = {
                    'task_type': row['task_type'],
                    'severity': row['severity'],
                    'description': row['description'],
                    'author': row['author'],
                    'date': row['date'],
                    'repo_path': row['repo_path'],
                    'files_changed': row.get('files_changed', '')
                }
                if self.create_jira_issue(event):
                    integration_stats["jira"] += 1
        
        # Create GitHub issues if enabled
        github_config = self.config.get('integrations', {}).get('github', {})
        if github_config.get('enabled', False) and github_config.get('create_issues', False):
            high_severity_df = df[df['severity'] == 'HIGH']
            for index, row in high_severity_df.iterrows():
                if integration_stats["github"] >= 2:  # Limit to 2 issues
                    break
                event = {
                    'task_type': row['task_type'],
                    'severity': row['severity'],
                    'description': row['description'],
                    'author': row['author'],
                    'date': row['date'],
                    'repo_path': row['repo_path'],
                    'files_changed': row.get('files_changed', '')
                }
                if self.create_github_issue(event):
                    integration_stats["github"] += 1
        
        # Send email summary
        email_config = self.config.get('integrations', {}).get('email', {})
        if email_config.get('enabled', False):
            email_subject = f"Toil Tracker Alert - {daily_toil_count} events detected"
            if self.send_email_notification(email_subject, summary):
                integration_stats["email"] = 1
        
        return integration_stats

def test_integrations():
    """Test integration configurations"""
    # Load config
    with open('toil-config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    integrations = ToilIntegrations(config)
    
    # Test Slack
    if integrations.send_slack_notification("🧪 Test message from Toil Tracker"):
        print("✅ Slack test successful")
    
    # Test with sample toil event
    sample_event = {
        'task_type': 'manual_fix',
        'severity': 'HIGH',
        'description': 'Emergency production server restart due to memory leak',
        'author': 'test-user',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'repo_path': '/test/repo',
        'files_changed': 'server.py,docker-compose.yml'
    }
    
    # Test JIRA
    jira_result = integrations.create_jira_issue(sample_event)
    if jira_result:
        print(f"✅ JIRA test successful: {jira_result}")
    
    # Test GitHub
    github_result = integrations.create_github_issue(sample_event)
    if github_result:
        print(f"✅ GitHub test successful: {github_result}")
    
    print("🧪 Integration tests completed")

if __name__ == "__main__":
    test_integrations()