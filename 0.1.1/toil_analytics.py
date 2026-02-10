"""
Enhanced Analytics for Toil Tracker
Time-based analysis, team insights, and cost estimation
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
from collections import defaultdict

class ToilAnalytics:
    def __init__(self, db_path="toil.db"):
        self.db_path = db_path
        
    def get_time_based_insights(self, days_back: int = 30) -> Dict:
        """Analyze toil patterns over time"""
        conn = sqlite3.connect(self.db_path)
        
        # Hourly distribution
        hourly_query = '''
            SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY hour
            ORDER BY hour
        '''.format(days_back)
        
        # Daily distribution  
        daily_query = '''
            SELECT strftime('%w', date) as day_of_week, COUNT(*) as count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY day_of_week
            ORDER BY day_of_week
        '''.format(days_back)
        
        # Trend analysis
        trend_query = '''
            SELECT date, COUNT(*) as daily_count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY date
            ORDER BY date
        '''.format(days_back)
        
        hourly_data = pd.read_sql_query(hourly_query, conn)
        daily_data = pd.read_sql_query(daily_query, conn)
        trend_data = pd.read_sql_query(trend_query, conn)
        
        conn.close()
        
        # Find peak hours
        peak_hour = hourly_data.loc[hourly_data['count'].idxmax()]
        
        # Find busiest day
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        daily_data['day_name'] = daily_data['day_of_week'].astype(int).map(lambda x: day_names[x])
        busiest_day = daily_data.loc[daily_data['count'].idxmax()]
        
        # Calculate trend
        if len(trend_data) >= 7:
            recent_avg = trend_data['daily_count'].tail(7).mean()
            earlier_avg = trend_data['daily_count'].head(7).mean()
            trend_direction = "increasing" if recent_avg > earlier_avg else "decreasing"
            trend_percent = abs((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        else:
            trend_direction = "insufficient_data"
            trend_percent = 0
        
        return {
            'peak_hour': {'hour': int(peak_hour['hour']), 'count': int(peak_hour['count'])},
            'busiest_day': {'day': busiest_day['day_name'], 'count': int(busiest_day['count'])},
            'trend': {'direction': trend_direction, 'percent_change': round(trend_percent, 1)},
            'hourly_distribution': hourly_data.to_dict('records'),
            'daily_distribution': daily_data.to_dict('records')
        }
    
    def get_team_insights(self, days_back: int = 30) -> Dict:
        """Analyze team-based toil patterns"""
        conn = sqlite3.connect(self.db_path)
        
        # Author-based analysis
        author_query = '''
            SELECT author, task_type, severity, COUNT(*) as count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY author, task_type, severity
            ORDER BY count DESC
        '''.format(days_back)
        
        # Repository-based analysis
        repo_query = '''
            SELECT repo_path, author, COUNT(*) as count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY repo_path, author
            ORDER BY count DESC
        '''.format(days_back)
        
        author_data = pd.read_sql_query(author_query, conn)
        repo_data = pd.read_sql_query(repo_query, conn)
        
        conn.close()
        
        # Top contributors
        author_totals = author_data.groupby('author')['count'].sum().sort_values()
        
        # Task specialization
        task_specialization = {}
        for author in author_data['author'].unique():
            author_tasks = author_data[author_data['author'] == author]
            total_tasks = author_tasks['count'].sum()
            task_dist = author_tasks.groupby('task_type')['count'].apply(lambda x: x/total_tasks * 100).to_dict()
            task_specialization[author] = task_dist
        
        # Cross-team collaboration (repos with multiple authors)
        repo_authors = repo_data.groupby('repo_path')['author'].nunique()
        collaborative_repos = repo_authors[repo_authors > 1].sort_values(ascending=False)
        
        return {
            'top_contributors': author_totals.head(10).to_dict(),
            'task_specialization': task_specialization,
            'collaborative_repos': collaborative_repos.head(5).to_dict(),
            'total_authors': len(author_totals),
            'author_details': author_data.to_dict('records')
        }
    
    def estimate_cost_impact(self, days_back: int = 30, hourly_rate: float = 100.0) -> Dict:
        """Estimate financial impact of toil"""
        conn = sqlite3.connect(self.db_path)
        
        # Get all toil events
        query = '''
            SELECT task_type, severity, COUNT(*) as count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY task_type, severity
        '''.format(days_back)
        
        data = pd.read_sql_query(query, conn)
        conn.close()
        
        # Time estimates per toil type (in hours)
        time_estimates = {
            'manual_deploy': {'HIGH': 4.0, 'MEDIUM': 2.0, 'LOW': 1.0},
            'manual_fix': {'HIGH': 6.0, 'MEDIUM': 3.0, 'LOW': 1.5},
            'revert': {'HIGH': 3.0, 'MEDIUM': 2.0, 'LOW': 1.0},
            'env_setup': {'HIGH': 3.0, 'MEDIUM': 2.0, 'LOW': 1.0},
            'restart': {'HIGH': 2.0, 'MEDIUM': 1.0, 'LOW': 0.5},
            'pipeline_issue': {'HIGH': 3.0, 'MEDIUM': 2.0, 'LOW': 1.0},
            'kubernetes': {'HIGH': 4.0, 'MEDIUM': 2.0, 'LOW': 1.0}
        }
        
        total_hours = 0
        total_cost = 0
        cost_breakdown = {}
        
        for _, row in data.iterrows():
            task_type = row['task_type']
            severity = row['severity']
            count = row['count']
            
            if task_type in time_estimates and severity in time_estimates[task_type]:
                hours_per_event = time_estimates[task_type][severity]
                event_hours = hours_per_event * count
                event_cost = event_hours * hourly_rate
                
                total_hours += event_hours
                total_cost += event_cost
                
                key = f"{task_type}_{severity}"
                cost_breakdown[key] = {
                    'hours': event_hours,
                    'cost': event_cost,
                    'events': count
                }
        
        # Calculate automation ROI potential
        automation_potential = {
            'high_automation': ['manual_deploy', 'manual_fix', 'pipeline_issue'],
            'medium_automation': ['env_setup', 'kubernetes'],
            'low_automation': ['restart', 'revert']
        }
        
        roi_breakdown = {}
        for category, task_types in automation_potential.items():
            category_hours = 0
            category_cost = 0
            
            for task_type in task_types:
                for severity in ['HIGH', 'MEDIUM', 'LOW']:
                    key = f"{task_type}_{severity}"
                    if key in cost_breakdown:
                        category_hours += cost_breakdown[key]['hours']
                        category_cost += cost_breakdown[key]['cost']
            
            roi_breakdown[category] = {
                'hours': category_hours,
                'cost': category_cost,
                'potential_savings': category_cost * 0.8  # 80% automation efficiency
            }
        
        return {
            'total_hours': round(total_hours, 1),
            'total_cost': round(total_cost, 2),
            'daily_average_hours': round(total_hours / days_back, 1),
            'daily_average_cost': round(total_cost / days_back, 2),
            'cost_breakdown': cost_breakdown,
            'automation_roi': roi_breakdown,
            'hourly_rate_used': hourly_rate
        }
    
    def get_toil_velocity_metrics(self, days_back: int = 30) -> Dict:
        """Calculate toil velocity and acceleration metrics"""
        conn = sqlite3.connect(self.db_path)
        
        # Daily counts for velocity calculation
        query = '''
            SELECT date, COUNT(*) as daily_count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY date
            ORDER BY date
        '''.format(days_back)
        
        data = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(data) < 7:
            return {'error': 'Insufficient data for velocity analysis'}
        
        # Calculate velocity (events per day)
        daily_counts = data['daily_count'].tolist()
        mean_velocity = statistics.mean(daily_counts)
        velocity_std = statistics.stdev(daily_counts) if len(daily_counts) > 1 else 0
        
        # Calculate acceleration (change in velocity)
        if len(daily_counts) >= 14:
            recent_velocity = statistics.mean(daily_counts[-7:])
            earlier_velocity = statistics.mean(daily_counts[-14:-7])
            acceleration = (recent_velocity - earlier_velocity) / 7  # events per day²
        else:
            acceleration = 0
        
        # Predict next week's toil
        predicted_next_week = mean_velocity + (acceleration * 7)
        
        # Detect anomalies (days with unusually high toil)
        threshold = mean_velocity + (1.5 * velocity_std)
        anomaly_days = data[data['daily_count'] > threshold].to_dict('records')
        
        return {
            'current_velocity': round(mean_velocity, 2),
            'velocity_std': round(velocity_std, 2),
            'acceleration': round(acceleration, 3),
            'predicted_next_week': max(0, round(predicted_next_week, 1)),
            'anomaly_days': anomaly_days,
            'trend_stability': 'stable' if velocity_std < mean_velocity * 0.3 else 'volatile'
        }
    
    def generate_recommendations(self, days_back: int = 30) -> List[Dict]:
        """Generate actionable recommendations based on analysis"""
        insights = self.get_time_based_insights(days_back)
        team_insights = self.get_team_insights(days_back)
        cost_impact = self.estimate_cost_impact(days_back)
        velocity = self.get_toil_velocity_metrics(days_back)
        
        recommendations = []
        
        # High-frequency toil recommendations
        if cost_impact['total_hours'] > 20:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'automation',
                'title': 'High Toil Volume Detected',
                'description': f"{cost_impact['total_hours']:.1f} hours spent on toil in last {days_back} days",
                'action': 'Focus automation on top 3 toil types',
                'estimated_impact': f"Potential savings: ${cost_impact['automation_roi']['high_automation']['potential_savings']:.0f}"
            })
        
        # Time-based recommendations
        peak_hour = insights['peak_hour']
        if peak_hour['count'] > cost_impact['daily_average_hours'] * 2:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'scheduling',
                'title': 'Peak Toil Hour Identified',
                'description': f"Hour {peak_hour['hour']}:00 has {peak_hour['count']} toil events",
                'action': 'Schedule proactive maintenance during off-peak hours',
                'estimated_impact': 'Reduce emergency toil by 30%'
            })
        
        # Team workload recommendations
        top_contributor = list(team_insights['top_contributors'].keys())[0] if team_insights['top_contributors'] else None
        if top_contributor and team_insights['top_contributors'][top_contributor] > 10:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'workload',
                'title': 'Workload Imbalance Detected',
                'description': f"{top_contributor} handles {team_insights['top_contributors'][top_contributor]} toil events",
                'action': 'Distribute operational tasks more evenly',
                'estimated_impact': 'Reduce burnout risk, improve team resilience'
            })
        
        # Velocity trend recommendations
        if velocity.get('acceleration', 0) > 0.5:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'trend',
                'title': 'Increasing Toil Velocity',
                'description': f"Toil is increasing by {velocity['acceleration']:.2f} events per day²",
                'action': 'Immediate investigation needed - system may be degrading',
                'estimated_impact': 'Prevent further operational overhead growth'
            })
        
        # Cost-based recommendations
        if cost_impact['total_cost'] > 5000:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'cost',
                'title': 'High Toil Cost Impact',
                'description': f"${cost_impact['total_cost']:.0f} spent on toil in last {days_back} days",
                'action': 'Present business case for automation investment',
                'estimated_impact': f"ROI: {cost_impact['total_cost'] * 3:.0f} annual savings'
            })
        
        return recommendations

def main():
    analytics = ToilAnalytics()
    
    print("📊 Toil Analytics Report")
    print("=" * 50)
    
    # Time insights
    time_insights = analytics.get_time_based_insights()
    print(f"⏰ Peak Hour: {time_insights['peak_hour']['hour']}:00 ({time_insights['peak_hour']['count']} events)")
    print(f"📅 Busiest Day: {time_insights['busiest_day']['day']} ({time_insights['busiest_day']['count']} events)")
    print(f"📈 Trend: {time_insights['trend']['direction']} ({time_insights['trend']['percent_change']}%)")
    print()
    
    # Cost impact
    cost_impact = analytics.estimate_cost_impact()
    print(f"💰 Total Cost: ${cost_impact['total_cost']:.0f}")
    print(f"⏱️ Total Hours: {cost_impact['total_hours']:.1f}")
    print(f"📊 Daily Average: {cost_impact['daily_average_hours']:.1f} hours (${cost_impact['daily_average_cost']:.0f})")
    print()
    
    # Recommendations
    recommendations = analytics.generate_recommendations()
    if recommendations:
        print("💡 Recommendations:")
        for rec in recommendations[:3]:  # Top 3
            print(f"  {rec['priority']}: {rec['title']}")
            print(f"     {rec['description']}")
            print(f"     Action: {rec['action']}")
            print()

if __name__ == "__main__":
    main()