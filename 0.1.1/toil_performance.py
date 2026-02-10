"""
Performance enhancements for Toil Tracker
Caching, parallel processing, and optimization utilities
"""

import sqlite3
import json
import hashlib
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import concurrent.futures
import pickle
from functools import wraps

class ToilCache:
    """Simple file-based caching system for toil scan results"""
    
    def __init__(self, cache_dir: str = ".toil_cache", ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl  # Time to live in seconds
        
    def _get_cache_key(self, repo_path, days_back: int) -> str:
        """Generate cache key based on repo path and parameters"""
        if isinstance(repo_path, str):
            resolved_path = Path(repo_path).resolve()
        else:
            resolved_path = repo_path
        key_data = f"{resolved_path}:{days_back}:{self._get_last_commit_date(repo_path)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_last_commit_date(self, repo_path) -> str:
        """Get the date of the last commit to invalidate cache"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cd"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except:
            return ""
    
    def get(self, repo_path, days_back: int) -> Optional[List[Dict]]:
        """Get cached scan results if valid"""
        cache_key = self._get_cache_key(repo_path, days_back)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check if cache is still valid
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > self.ttl:
            cache_file.unlink()  # Remove expired cache
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            cache_file.unlink()  # Remove corrupted cache
            return None
    
    def set(self, repo_path: str, days_back: int, data: List[Dict]):
        """Cache scan results"""
        cache_key = self._get_cache_key(repo_path, days_back)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"⚠️ Cache write failed: {e}")
    
    def clear(self):
        """Clear all cached data"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except:
                pass

class ToilPerformanceOptimizer:
    """Performance optimization utilities for toil scanning"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cache = ToilCache(
            cache_dir=config.get('performance', {}).get('cache_dir', '.toil_cache'),
            ttl=config.get('performance', {}).get('cache_ttl', 3600)
        )
    
    def scan_with_caching(self, detector, repo_path: str, days_back: int) -> List[Dict]:
        """Scan repository with caching support"""
        # Try cache first
        cached_result = self.cache.get(repo_path, days_back)
        if cached_result is not None:
            print(f"📋 Using cached results for {repo_path}")
            return cached_result
        
        # Perform scan
        print(f"🔍 Scanning {repo_path}...")
        result = detector.scan_git_history(repo_path, days_back)
        
        # Cache the result
        self.cache.set(repo_path, days_back, result)
        
        return result
    
    def parallel_scan_multiple_repos(self, detector, repo_paths: List[str], days_back: int) -> Dict[str, List[Dict]]:
        """Enhanced parallel scanning with batch processing"""
        max_workers = self.config.get('performance', {}).get('max_workers', 4)
        batch_size = self.config.get('performance', {}).get('batch_size', 50)
        
        def scan_repo(repo_path):
            try:
                # Use caching for individual repos
                return repo_path, self.scan_with_caching(detector, repo_path, days_back)
            except Exception as e:
                print(f"❌ Error scanning {repo_path}: {e}")
                return repo_path, []
        
        # Process repos in parallel
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_repo = {
                executor.submit(scan_repo, repo): repo 
                for repo in repo_paths
            }
            
            for future in concurrent.futures.as_completed(future_to_repo):
                repo_path, toil_events = future.result()
                results[repo_path] = toil_events
        
        return results
    
    def optimize_git_commands(self, repo_path: str) -> bool:
        """Apply git performance optimizations"""
        try:
            # Configure git for better performance
            optimizations = [
                ["git", "config", "core.preloadindex", "true"],
                ["git", "config", "core.fscache", "true"],
                ["git", "config", "gc.auto", "256"],
            ]
            
            for cmd in optimizations:
                subprocess.run(cmd, cwd=repo_path, capture_output=True)
            
            return True
        except:
            return False
    
    def batch_process_commits(self, commits: List[Dict], batch_size: int = 50) -> List[List[Dict]]:
        """Batch commits for processing"""
        batches = []
        for i in range(0, len(commits), batch_size):
            batches.append(commits[i:i + batch_size])
        return batches
    
    def estimate_scan_time(self, repo_path: str, days_back: int) -> float:
        """Estimate scan time based on historical data"""
        cache_key = f"time_estimate:{hashlib.md5(f'{repo_path}:{days_back}'.encode()).hexdigest()}"
        
        # This would be enhanced with actual timing data in production
        base_time = 2.0  # Base time in seconds
        repo_complexity_factor = 1.0
        days_factor = min(days_back / 30, 2.0)  # Cap at 2x for long periods
        
        return base_time * repo_complexity_factor * days_factor

def performance_monitor(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            print(f"⏱️ {func.__name__}: {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ {func.__name__}: {execution_time:.2f}s (failed: {e})")
            raise
    
    return wrapper

class DatabaseOptimizer:
    """Database performance optimizations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def optimize_database(self):
        """Apply database optimizations"""
        conn = sqlite3.connect(self.db_path)
        try:
            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_toil_date ON toil_events(date)",
                "CREATE INDEX IF NOT EXISTS idx_toil_severity ON toil_events(severity)",
                "CREATE INDEX IF NOT EXISTS idx_toil_task_type ON toil_events(task_type)",
                "CREATE INDEX IF NOT EXISTS idx_toil_author ON toil_events(author)",
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            # Vacuum and analyze for better performance
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            
            conn.commit()
            print("✅ Database optimized")
            
        except Exception as e:
            print(f"❌ Database optimization failed: {e}")
        finally:
            conn.close()
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data to maintain performance"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute('''
                DELETE FROM toil_events 
                WHERE date < date('now', '-{} days')
            '''.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old records")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
        finally:
            conn.close()

def main():
    """Test performance optimizations"""
    print("🚀 Testing Toil Tracker Performance Optimizations")
    
    # Test cache
    cache = ToilCache()
    test_data = [{"test": "data", "timestamp": time.time()}]
    
    cache.set(".", 30, test_data)
    cached_data = cache.get(".", 30)
    
    if cached_data:
        print("✅ Cache test successful")
    else:
        print("❌ Cache test failed")
    
    # Test performance monitor
    @performance_monitor
    def slow_function():
        time.sleep(0.5)
        return "done"
    
    result = slow_function()
    
    # Test database optimizer
    db_optimizer = DatabaseOptimizer("test_toil.db")
    db_optimizer.optimize_database()
    db_optimizer.cleanup_old_data(30)

if __name__ == "__main__":
    main()