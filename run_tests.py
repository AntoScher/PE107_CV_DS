#!/usr/bin/env python3
"""
Test runner script for the AI Resume Analyzer application.
"""
import sys
import os
import subprocess
import unittest
from pathlib import Path

def run_unit_tests():
    """Run all unit tests."""
    print("🧪 Running unit tests...")
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = project_root
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_with_coverage():
    """Run tests with coverage reporting."""
    print("📊 Running tests with coverage...")
    
    try:
        # Install coverage if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "coverage"], 
                      check=True, capture_output=True)
        
        # Run tests with coverage
        cmd = [
            sys.executable, "-m", "coverage", "run", 
            "--source=.", "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Generate coverage report
            subprocess.run([sys.executable, "-m", "coverage", "report"], check=True)
            subprocess.run([sys.executable, "-m", "coverage", "html"], check=True)
            print("✅ Coverage report generated in htmlcov/")
            return True
        else:
            print(f"❌ Tests failed: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests with coverage: {e}")
        return False

def run_linting():
    """Run code linting checks."""
    print("🔍 Running code linting...")
    
    try:
        # Install flake8 if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "flake8"], 
                      check=True, capture_output=True)
        
        # Run flake8
        cmd = [sys.executable, "-m", "flake8", ".", "--max-line-length=100", "--ignore=E501,W503"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Code linting passed")
            return True
        else:
            print(f"⚠️  Linting issues found:\n{result.stdout}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running linting: {e}")
        return False

def run_type_checking():
    """Run type checking with mypy."""
    print("🔍 Running type checking...")
    
    try:
        # Install mypy if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "mypy"], 
                      check=True, capture_output=True)
        
        # Run mypy
        cmd = [sys.executable, "-m", "mypy", ".", "--ignore-missing-imports"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Type checking passed")
            return True
        else:
            print(f"⚠️  Type checking issues found:\n{result.stdout}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running type checking: {e}")
        return False

def main():
    """Main test runner function."""
    print("🚀 Starting test suite for AI Resume Analyzer")
    print("=" * 50)
    
    success = True
    
    # Run different types of tests
    if not run_linting():
        success = False
    
    if not run_type_checking():
        success = False
    
    if not run_unit_tests():
        success = False
    
    if not run_with_coverage():
        success = False
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
