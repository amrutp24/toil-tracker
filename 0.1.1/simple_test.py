#!/usr/bin/env python3
"""
Simple test for Toil Tracker v0.1.1
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=== Toil Tracker v0.1.1 Quick Test ===\n")
    
    # Test 1: Import detector
    try:
        from enhanced_toil_detector import ToilDetector
            print("PASS: Enhanced detector imports")
    except Exception as e:
        print(f"FAIL: Enhanced detector failed: {e}")
        return 1
    
    # Test 2: Import analytics
    try:
        from toil_analytics_simple import ToilAnalyticsSimple
        print("PASS: Analytics imports")
    except Exception as e:
        print(f"FAIL: Analytics failed: {e}")
        return 1
    
    # Test 3: Test YAML
    try:
        import yaml
        print("PASS: PyYAML available")
    except ImportError:
        print("FAIL: PyYAML missing")
        return 1
    
    # Test 4: Test requests
    try:
        import requests
        print("PASS: Requests available")
    except ImportError:
        print("FAIL: Requests missing")
        return 1
    
    # Test 5: Initialize detector
    try:
        detector = ToilDetector()
        print("PASS: Detector initializes")
    except Exception as e:
        print(f"FAIL: Detector init failed: {e}")
        return 1
    
    print("\n=== All basic tests passed! ===")
    print("Toil Tracker v0.1.1 is functional.")
    return 0

if __name__ == "__main__":
    sys.exit(main())