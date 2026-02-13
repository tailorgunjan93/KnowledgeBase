"""Automation script to run tests and verification."""
import os
import sys
import subprocess
import time

def run_tests():
    """Run the pytest suite."""
    print("🧪 Running Automated Tests...")
    try:
        # Run pytest using uv run to ensure environment
        result = subprocess.run(
            ["uv", "run", "pytest", "-v"], 
            capture_output=True, 
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print("❌ Tests Failed!")
            print(result.stderr)
            return False
        print("✅ All Tests Passed!")
        return True
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def check_structure():
    """Verify key files exist."""
    required = [
        "app_v2.py",
        "ui/styles/main.css",
        "data/db_context.py",
        "data/schema.sql"
    ]
    missing = []
    for f in required:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    print("✅ File Structure Verified.")
    return True

if __name__ == "__main__":
    print("🚀 Starting Automation Suite")
    print("===========================")
    
    if not check_structure():
        sys.exit(1)
        
    if not run_tests():
        sys.exit(1)
        
    print("\n✨ Automation Complete. System is ready.")
    print("Run: uv run streamlit run app_v2.py")
