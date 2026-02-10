"""
Demo output showing what the dashboard would display
"""

import sqlite3
import pandas as pd

def show_dashboard_demo():
    """Show what the dashboard would look like with our demo data"""
    
    # Load demo data
    conn = sqlite3.connect('demo.db')
    df = pd.read_sql_query('SELECT * FROM toil_events ORDER BY date DESC', conn)
    conn.close()
    
    print("DEVOPS TOIL DASHBOARD DEMO")
    print("=" * 50)
    
    # Key Metrics
    total_toil = len(df)
    high_severity = len(df[df['severity'] == 'HIGH'])
    unique_task_types = df['task_type'].nunique()
    
    print(f"\nKEY METRICS")
    print(f"Total Toil Events: {total_toil}")
    print(f"High Severity: {high_severity} ({high_severity/total_toil*100:.0f}%)")
    print(f"Task Types: {unique_task_types}")
    print(f"Daily Average: {total_toil/7:.1f} (last 7 days)")
    
    # Toil by Task Type
    print(f"\nTOIL BY TASK TYPE")
    task_counts = df['task_type'].value_counts()
    for task_type, count in task_counts.items():
        print(f"{task_type.upper()}: {count} events")
    
    # Recent Events
    print(f"\nRECENT TOIL EVENTS")
    for _, row in df.head(5).iterrows():
        severity_marker = "HIGH" if row['severity'] == 'HIGH' else "MED" if row['severity'] == 'MEDIUM' else "LOW"
        print(f"[{severity_marker}] {row['date']} - {row['task_type'].upper()}")
        print(f"   {row['description']}")
        print()
    
    # Recommendations
    print(f"RECOMMENDATIONS")
    
    high_count_tasks = task_counts[task_counts > 1]
    if not high_count_tasks.empty:
        print("HIGH-FREQUENCY TOIL DETECTED:")
        for task_type, count in high_count_tasks.items():
            print(f"   • {task_type}: {count} events - Consider automation")
    
    if high_severity > 0:
        high_events = df[df['severity'] == 'HIGH']
        print(f"\nHIGH SEVERITY TOIL ({high_severity} events):")
        for _, row in high_events.iterrows():
            print(f"   • {row['description']}")
    
    print(f"\nNEXT STEPS")
    print("1. Automate manual_deploy tasks")
    print("2. Fix root causes of high_severity issues") 
    print("3. Set up alerts for recurring patterns")
    print("4. Document and standardize procedures")

if __name__ == "__main__":
    show_dashboard_demo()