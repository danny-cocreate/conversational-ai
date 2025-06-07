#!/usr/bin/env python3
"""
Unreal Speech Test Runner
Runs all available tests and demos
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    required = ['flask', 'requests', 'flask_cors']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("Installing requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed")
    else:
        print("✅ All requirements satisfied")

def run_test(script_name, description):
    """Run a test script"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    script_path = Path(__file__).parent / script_name
    if script_path.exists():
        subprocess.run([sys.executable, str(script_path)])
    else:
        print(f"❌ Script not found: {script_name}")

def start_server(script_name, port, description):
    """Start a Flask server in the background"""
    print(f"\n🌐 Starting {description} on port {port}...")
    script_path = Path(__file__).parent / script_name
    
    if script_path.exists():
        proc = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)  # Give server time to start
        
        # Open in browser
        url = f"http://localhost:{port}"
        print(f"✅ Server started at {url}")
        try:
            webbrowser.open(url)
            print("🌐 Opened in browser")
        except:
            print("ℹ️  Please open your browser and navigate to:", url)
        
        return proc
    else:
        print(f"❌ Script not found: {script_name}")
        return None

def main():
    """Main test runner"""
    print("🚀 Unreal Speech Test Suite")
    print("="*60)
    
    # Check for API key
    api_key = os.getenv("UNREALSPEECH_API_KEY", "")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("⚠️  No API key found!")
        print("\nTo use Unreal Speech:")
        print("1. Sign up at https://unrealspeech.com")
        print("2. Get your API key (250K characters free)")
        print("3. Set environment variable:")
        print("   export UNREALSPEECH_API_KEY='your_key_here'")
        print("\nFor now, running demos in offline/simulation mode...")
        has_api_key = False
    else:
        print("✅ API key found")
        has_api_key = True
    
    # Check requirements
    check_requirements()
    
    # Menu
    while True:
        print("\n" + "="*60)
        print("📋 Available Tests:")
        print("="*60)
        print("1. Quick Connection Test")
        print("2. Behavior Simulation (No API key required)")
        print("3. Offline Demo UI (No API key required)")
        if has_api_key:
            print("4. Full API Test Suite")
            print("5. Web Streaming Demo")
            print("6. Comparison Tool")
        print("0. Exit")
        
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            run_test("quick_test.py", "Quick Connection Test")
        elif choice == "2":
            run_test("simulate_behavior.py", "API Behavior Simulation")
        elif choice == "3":
            proc = start_server("offline_demo.py", 5004, "Offline Demo UI")
            if proc:
                input("\nPress Enter to stop the server...")
                proc.terminate()
                print("✅ Server stopped")
        elif choice == "4" and has_api_key:
            run_test("test_unrealspeech.py", "Full API Test Suite")
        elif choice == "5" and has_api_key:
            proc = start_server("streaming_demo.py", 5003, "Web Streaming Demo")
            if proc:
                input("\nPress Enter to stop the server...")
                proc.terminate()
                print("✅ Server stopped")
        elif choice == "6" and has_api_key:
            run_test("comparison_tool.py", "TTS Comparison Tool")
        else:
            print("❌ Invalid option or API key required")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
