"""
Simplified Analytics for Toil Tracker
Time-based analysis, team insights, and cost estimation (without pandas)
"""

import sqlite3
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class ToilAnalyticsSimple:
    def __init__(self, db_path="toil_v2.db"):
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
        
        hourly_data = conn.execute(hourly_query).fetchall()
        daily_data = conn.execute(daily_query).fetchall()
        trend_data = conn.execute(trend_query).fetchall()
        
        conn.close()
        
        # Find peak hour
        peak_hour = max(hourly_data, key=lambda x: x[1]) if hourly_data else (0, 0)
        
        # Find busiest day
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        daily_with_names = [(day_names[int(day)], count) for day, count in daily_data]
        busiest_day = max(daily_with_names, key=lambda x: x[1]) if daily_with_names else ('Unknown', 0)
        
        # Calculate trend
        if len(trend_data) >= 14:
            recent_avg = statistics.mean([row[1] for row in trend_data[-7:]])
            earlier_avg = statistics.mean([row[1] for row in trend_data[-14:-7]])
            trend_direction = "increasing" if recent_avg > earlier_avg else "decreasing"
            trend_percent = abs((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        else:
            trend_direction = "insufficient_data"
            trend_percent = 0
        
        return {
            'peak_hour': {'hour': peak_hour[0], 'count': peak_hour[1]},
            'busiest_day': {'day': busiest_day[0], 'count': busiest_day[1]},
            'trend': {'direction': trend_direction, 'percent_change': round(trend_percent, 1)},
            'hourly_distribution': [{'hour': h, 'count': c} for h, c in hourly_data],
            'daily_distribution': [{'day': day_names[int(d)], 'count': c} for d, c in daily_data]
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
        
        author_data = conn.execute(author_query).fetchall()
        repo_data = conn.execute(repo_query).fetchall()
        
        conn.close()
        
        # Top contributors
        author_totals = defaultdict(int)
        for author, task_type, severity, count in author_data:
            author_totals[author] += count
        
        # Task specialization
        task_specialization = defaultdict(dict)
        for author, task_type, severity, count in author_data:
            if author not in task_specialization:
                task_specialization[author] = defaultdict(int)
            task_specialization[author][task_type] += count
        
        # Calculate percentages for specialization
        for author in task_specialization:
            total = sum(task_specialization[author].values())
            for task_type in task_specialization[author]:
                task_specialization[author][task_type] = round((task_specialization[author][task_type] / total) * 100, 1)
        
        # Cross-team collaboration (repos with multiple authors)
        repo_authors = defaultdict(set)
        for repo_path, author, count in repo_data:
            repo_authors[repo_path].add(author)
        
        collaborative_repos = {repo: len(authors) for repo, authors in repo_authors.items() if len(authors) > 1}
        collaborative_repos_sorted = sorted(collaborative_repos.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'top_contributors': dict(sorted(author_totals.items(), key=lambda x: x[1], reverse=True)[:10]),
            'task_specialization': dict(task_specialization),
            'collaborative_repos': dict(collaborative_repos_sorted),
            'total_authors': len(author_totals),
            'author_details': [{'author': a, 'task_type': t, 'severity': s, 'count': c} 
                           for a, t, s, c in author_data]
        }
    
    def estimate_cost_impact(self, days_back: int = 30, hourly_rate: float = 100.0) -> Dict:
        """Estimate financial impact of toil"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT task_type, severity, COUNT(*) as count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY task_type, severity
        '''.format(days_back)
        
        data = conn.execute(query).fetchall()
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
        
        for task_type, severity, count in data:
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
        
        query = '''
            SELECT date, COUNT(*) as daily_count
            FROM toil_events 
            WHERE date >= date('now', '-{} days')
            GROUP BY date
            ORDER BY date
        '''.format(days_back)
        
        data = conn.execute(query).fetchall()
        conn.close()
        
        if len(data) < 7:
            return {'error': 'Insufficient data for velocity analysis'}
        
        # Calculate velocity (events per day)
        daily_counts = [row[1] for row in data]
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
        anomaly_days = [{'date': row[0], 'count': row[1]} for row in data if row[1] > threshold]
        
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
        top_contributors = team_insights['top_contributors']
        if top_contributors:
            top_contributor_name = list(top_contributors.keys())[0]
            if top_contributors[top_contributor_name] > 10:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'workload',
                    'title': 'Workload Imbalance Detected',
                    'description': f"{top_contributor_name} handles {top_contributors[top_contributor_name]} toil events",
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
                'estimated_impact': f"ROI: {cost_impact['total_cost'] * 3:.0f} annual savings"
            })
        
        return recommendations

def main():
    analytics = ToilAnalyticsSimple()
    
    print("📊 Toil Analytics Report v2.0")
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