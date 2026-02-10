"""
Enhanced CLI for Toil Tracker with multiple subcommands
"""

import argparse
import json
import sys
from pathlib import Path
from enhanced_toil_detector import ToilDetector

def scan_command(args):
    """Handle scan subcommand"""
    detector = ToilDetector(args.db, args.config)
    
    if args.multiple:
        # Multiple repos
        repo_paths = [line.strip() for line in args.repos.read().splitlines() if line.strip()]
        results = detector.scan_multiple_repos(repo_paths, args.days)
        
        total_events = 0
        for repo, events in results.items():
            print(f"📁 {repo}: {len(events)} toil events found")
            total_events += len(events)
            if events:
                detector.save_toil_events(events)
        
        print(f"✅ Total: {total_events} toil events across {len(repo_paths)} repositories")
    
    else:
        # Single repo
        events = detector.scan_git_history(args.repos, args.days)
        detector.save_toil_events(events)
        print(f"✅ Found {len(events)} toil events in {args.repos}")
        
        if args.verbose:
            for event in events:
                print(f"  📋 {event['date']} - {event['task_type']} ({event['severity']}) - {event['description'][:50]}...")

def report_command(args):
    """Handle report subcommand"""
    detector = ToilDetector(args.db, args.config)
    
    if args.export:
        try:
            data = detector.export_data(args.format, args.days)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(data)
                print(f"📊 Report exported to {args.output}")
            else:
                print(data)
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return
    else:
        summary = detector.get_toil_summary(args.days)
        
        print(f"📊 Toil Report (last {args.days} days)")
        print("=" * 50)
        
        # Group by task type
        task_summary = {}
        for task_type, severity, count, date, author in summary:
            if task_type not in task_summary:
                task_summary[task_type] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            task_summary[task_type][severity] += count
        
        for task_type, severities in task_summary.items():
            total = sum(severities.values())
            print(f"🔧 {task_type}: {total} total")
            for severity, count in severities.items():
                if count > 0:
                    print(f"   {severity}: {count}")
            print()

def benchmark_command(args):
    """Handle benchmark subcommand - compare time periods"""
    detector = ToilDetector(args.db, args.config)
    
    current_period = args.days
    previous_period = args.days * 2  # Double the period for comparison
    
    current_data = detector.get_toil_summary(current_period)
    previous_data = detector.get_toil_summary(previous_period - current_period)
    
    # Aggregate data
    def aggregate_summary(data):
        task_counts = {}
        for task_type, severity, count, date, author in data:
            if task_type not in task_counts:
                task_counts[task_type] = 0
            task_counts[task_type] += count
        return task_counts
    
    current_counts = aggregate_summary(current_data)
    previous_counts = aggregate_summary(previous_data)
    
    print(f"📈 Toil Benchmark: Last {current_period} days vs Previous {current_period} days")
    print("=" * 70)
    
    for task_type in set(list(current_counts.keys()) + list(previous_counts.keys())):
        current = current_counts.get(task_type, 0)
        previous = previous_counts.get(task_type, 0)
        change = current - previous
        percent_change = (change / previous * 100) if previous > 0 else 0
        
        trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        print(f"{trend} {task_type}: {current} vs {previous} ({change:+d}, {percent_change:+.1f}%)")

def init_command(args):
    """Handle init subcommand - create config"""
    if args.config and not Path(args.config).exists():
        default_config = {
            "patterns": {
                "manual_deploy": {
                    "keywords": ["deploy", "deployment", "production deploy"],
                    "regex": ["deploy.*production", "prod.*deploy"],
                    "file_patterns": ["deploy*.sh", "docker-compose.*.yml"],
                    "exclude": ["test", "staging"]
                }
            },
            "severity": {
                "high": ["emergency", "critical", "urgent"],
                "medium": ["hotfix", "production", "manual"],
                "low": ["update", "config", "restart"]
            }
        }
        
        import yaml
        with open(args.config, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        print(f"📝 Configuration file created: {args.config}")
    else:
        print("Using default configuration")

def main():
    parser = argparse.ArgumentParser(
        description="Toil Tracker - Detect, visualize, and reduce DevOps toil",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  toil-tracker scan ./my-repo --days 30 --verbose
  toil-tracker scan --multiple --repos repos.txt
  toil-tracker report --days 60 --export json --output report.json
  toil-tracker benchmark --days 30
        """
    )
    
    parser.add_argument('--db', default='toil.db', help='Database file path')
    parser.add_argument('--config', default=None, help='Configuration YAML file')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan repositories for toil')
    scan_parser.add_argument('repos', help='Repository path or file with repo paths (with --multiple)')
    scan_parser.add_argument('--days', type=int, default=30, help='Days to look back')
    scan_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    scan_parser.add_argument('--multiple', action='store_true', help='Scan multiple repos from file')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate toil reports')
    report_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    report_parser.add_argument('--export', action='store_true', help='Export data')
    report_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    report_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Benchmark toil over time')
    benchmark_parser.add_argument('--days', type=int, default=30, help='Period length in days')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize configuration')
    init_parser.add_argument('--config', default='toil-config.yaml', help='Config file path')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch web dashboard')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'scan':
        scan_command(args)
    elif args.command == 'report':
        report_command(args)
    elif args.command == 'benchmark':
        benchmark_command(args)
    elif args.command == 'init':
        init_command(args)
    elif args.command == 'dashboard':
        try:
            from dashboard import main as dashboard_main
            dashboard_main()
        except ImportError:
            print("❌ Dashboard module not found. Please ensure dashboard.py is in the same directory.")
            print("   You can also run: python dashboard.py")

if __name__ == "__main__":
    main()