#!/usr/bin/env python3
"""
Simple Unreal Speech Test - No pip dependency check
"""

import os
import sys

def print_header():
    print("🎯 Unreal Speech Streaming Test (Simple Version)")
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

def check_imports():
    """Check if required modules are available"""
    missing = []
    
    try:
        import flask
        print("✅ Flask available")
    except ImportError:
        missing.append("flask")
    
    try:
        import requests
        print("✅ Requests available")
    except ImportError:
        missing.append("requests")
    
    try:
        import flask_cors
        print("✅ Flask-CORS available")
    except ImportError:
        missing.append("flask-cors")
    
    if missing:
        print(f"❌ Missing modules: {', '.join(missing)}")
        print()
        print("Install them manually:")
        print(f"pip3 install {' '.join(missing)}")
        print("OR")
        print(f"python3 -m pip install {' '.join(missing)}")
        return False
    
    return True

def start_streaming_demo():
    """Start the streaming demo"""
    print()
    print("🚀 Starting Unreal Speech Streaming Demo")
    print("-" * 50)
    print("Server URL: http://localhost:5003")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Import here to avoid issues if modules aren't installed
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        print("Loading streaming demo...")
        exec(open('streaming_demo.py').read())
        
    except FileNotFoundError:
        print("❌ streaming_demo.py not found")
        print("Make sure you're in the unrealspeech_poc directory")
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print()
        print("Try running directly:")
        print("python3 streaming_demo.py")

def main():
    print_header()
    
    # Check API key
    if not check_api_key():
        return
    
    # Check imports
    if not check_imports():
        return
    
    # Start demo
    start_streaming_demo()

if __name__ == "__main__":
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    main()
