#!/usr/bin/env python3
"""
One-Click Unreal Speech Test Runner
Run this to quickly test everything
"""

import os
import subprocess
import sys

def print_header():
    print("🎯 Unreal Speech API Test - One Click Setup")
    print("="*60)
    print()

def check_api_key():
    """Check if API key is set"""
    api_key = os.getenv("UNREALSPEECH_API_KEY", "")
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("❌ API Key Required")
        print()
        print("To get your FREE API key (250K characters):")
        print("1. 🌐 Visit: https://unrealspeech.com")
        print("2. 📝 Sign up (no credit card needed)")
        print("3. 🔑 Copy your API key")
        print("4. 💻 Run: export UNREALSPEECH_API_KEY='your_key_here'")
        print("5. 🔄 Run this script again")
        print()
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...")
    return True

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Requirements installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def run_streaming_demo():
    """Start the streaming demo server"""
    print()
    print("🚀 Starting Streaming Demo Server")
    print("-" * 40)
    print("Server will start on: http://localhost:5003")
    print("Press Ctrl+C to stop the server")
    print()
    print("Test features:")
    print("- ⚡ Real-time streaming")
    print("- 🎭 Multiple voices")
    print("- 🎛️ Speed/pitch controls")
    print("- 📊 Performance metrics")
    print()
    
    try:
        # Run the streaming demo
        subprocess.run([sys.executable, "streaming_demo.py"])
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print_header()
    
    # Check API key
    if not check_api_key():
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Start streaming demo
    run_streaming_demo()

if __name__ == "__main__":
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
