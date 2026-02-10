#!/usr/bin/env python3
"""
Quick test script for Toil Tracker v0.1.1
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test all module imports"""
    print("Testing imports...")
    
    try:
        from enhanced_toil_detector import ToilDetector
        print("Enhanced detector imported")
    except Exception as e:
        print(f"✗ Enhanced detector failed: {e}")
        return False
    
    try:
        import yaml
        print("✓ PyYAML available")
    except ImportError:
        print("✗ PyYAML missing")
        return False
    
    try:
        import requests
        print("✓ Requests available")
    except ImportError:
        print("✗ Requests missing")
        return False
    
    return True

def test_detector():
    """Test detector functionality"""
    print("\nTesting detector...")
    
    try:
        from enhanced_toil_detector import ToilDetector
        
        # Test with default config
        detector = ToilDetector()
        print("✓ Detector initialized with default config")
        
        # Test with custom config
        if os.path.exists('toil-config.yaml'):
            detector_custom = ToilDetector(config_path='toil-config.yaml')
            print("✓ Detector initialized with custom config")
        
        return True
    except Exception as e:
        print(f"✗ Detector test failed: {e}")
        return False

def test_analytics():
    """Test analytics functionality"""
    print("\nTesting analytics...")
    
    try:
        from toil_analytics_simple import ToilAnalyticsSimple
        
        analytics = ToilAnalyticsSimple()
        print("✓ Analytics initialized")
        
        # Test basic functionality (no data expected)
        insights = analytics.get_time_based_insights(7)
        print("✓ Time insights method works")
        
        return True
    except Exception as e:
        print(f"✗ Analytics test failed: {e}")
        return False

def test_integrations():
    """Test integrations module"""
    print("\nTesting integrations...")
    
    try:
        from toil_integrations import ToilIntegrations
        import yaml
        
        # Test with empty config
        config = {"integrations": {"slack": {"enabled": False}}}
        integrations = ToilIntegrations(config)
        print("✓ Integrations initialized")
        
        return True
    except Exception as e:
        print(f"✗ Integrations test failed: {e}")
        return False

def test_performance():
    """Test performance module"""
    print("\nTesting performance...")
    
    try:
        from toil_performance import ToilCache
        
        cache = ToilCache()
        print("✓ Cache initialized")
        
        return True
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False

def test_cli():
    """Test CLI module"""
    print("\nTesting CLI...")
    
    try:
        import enhanced_cli
        print("✓ CLI module imports")
        
        return True
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False

def main():
    print("=== Toil Tracker v0.1.1 Test Suite ===\n")
    
    tests = [
        test_imports,
        test_detector,
        test_analytics,
        test_integrations,
        test_performance,
        test_cli
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All tests passed! v0.1.1 is ready for use.")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed. Review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())