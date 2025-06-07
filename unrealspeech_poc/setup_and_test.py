#!/usr/bin/env python3
"""
Quick Setup and Test Script for Unreal Speech
This script helps you get started testing immediately
"""

import os
import sys
import subprocess
import requests
import tempfile
import time

def check_environment():
    """Check if everything is set up correctly"""
    print("🔍 Checking Environment Setup")
    print("="*40)
    
    # Check Python version
    python_version = sys.version_info
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("❌ Python 3.7+ required")
        return False
    else:
        print("✅ Python version OK")
    
    # Check for API key
    api_key = os.getenv("UNREALSPEECH_API_KEY", "")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("⚠️  API key not set")
        print("\nTo get your API key:")
        print("1. Visit: https://unrealspeech.com")
        print("2. Sign up (free 250K characters)")
        print("3. Copy your API key")
        print("4. Run: export UNREALSPEECH_API_KEY='your_key'")
        print("5. Then run this script again")
        return False
    else:
        print(f"✅ API key found: {api_key[:8]}...")
    
    # Check requirements
    try:
        import flask
        import requests
        import flask_cors
        print("✅ Required packages installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip3 install -r requirements.txt")
        return False
    
    return True

def test_api_connection():
    """Test basic API connectivity"""
    print("\n🌐 Testing API Connection")
    print("="*40)
    
    api_key = os.getenv("UNREALSPEECH_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test with minimal text
    test_payload = {
        "Text": "Hello, testing API connection.",
        "VoiceId": "af_sky",
        "Bitrate": "192k",
        "Speed": "0",
        "Pitch": "1",
        "Codec": "libmp3lame"
    }
    
    try:
        print("Making test request...")
        start_time = time.time()
        
        response = requests.post(
            "https://api.v8.unrealspeech.com/stream",
            headers=headers,
            json=test_payload,
            timeout=10
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ API connection successful!")
            print(f"⏱️  Response time: {response_time:.2f}s")
            print(f"📦 Audio size: {len(response.content)} bytes")
            
            # Save and play audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp.write(response.content)
                temp_path = tmp.name
            
            print(f"🔊 Playing test audio...")
            if os.path.exists('/usr/bin/afplay'):  # macOS
                subprocess.run(['afplay', temp_path])
            elif os.path.exists('/usr/bin/aplay'):  # Linux
                subprocess.run(['aplay', temp_path])
            else:
                print(f"Audio saved to: {temp_path}")
            
            return True
            
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def start_streaming_demo():
    """Start the streaming demo on port 5003"""
    print("\n🚀 Starting Streaming Demo")
    print("="*40)
    
    print("Starting server on http://localhost:5003")
    print("Press Ctrl+C to stop")
    print("\nFeatures to test:")
    print("- Basic synthesis")
    print("- Streaming audio")
    print("- Different voices")
    print("- Speed/pitch controls")
    print("- Latency metrics")
    
    try:
        # Import and run the streaming demo
        from streaming_demo import app
        app.run(debug=False, host='0.0.0.0', port=5003)
    except KeyboardInterrupt:
        print("\n👋 Demo stopped")
    except Exception as e:
        print(f"❌ Error starting demo: {str(e)}")

def quick_voice_test():
    """Test different voices quickly"""
    print("\n🎭 Quick Voice Test")
    print("="*40)
    
    api_key = os.getenv("UNREALSPEECH_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    voices_to_test = [
        ("af_sky", "Female - Sky"),
        ("af_bella", "Female - Bella"),
        ("am_adam", "Male - Adam"),
        ("bm_george", "Male - George (British)")
    ]
    
    test_text = "Hello! I'm testing different voice options."
    
    for voice_id, description in voices_to_test:
        print(f"\nTesting {description}...")
        
        try:
            response = requests.post(
                "https://api.v8.unrealspeech.com/stream",
                headers=headers,
                json={
                    "Text": test_text,
                    "VoiceId": voice_id,
                    "Bitrate": "192k",
                    "Speed": "0",
                    "Pitch": "1",
                    "Codec": "libmp3lame"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ {description} - {len(response.content)} bytes")
                
                # Play audio
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(response.content)
                    if os.path.exists('/usr/bin/afplay'):
                        subprocess.run(['afplay', tmp.name])
                    time.sleep(0.5)  # Brief pause between voices
            else:
                print(f"❌ {description} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description} error: {str(e)}")

def main():
    """Main testing flow"""
    print("🎯 Unreal Speech Quick Setup & Test")
    print("="*50)
    
    # Step 1: Check environment
    if not check_environment():
        return
    
    # Step 2: Test API connection
    if not test_api_connection():
        return
    
    # Step 3: Quick voice test
    quick_voice_test()
    
    # Step 4: Ask what to do next
    print("\n" + "="*50)
    print("🎉 Basic tests completed successfully!")
    print("\nWhat would you like to do next?")
    print("1. Start streaming demo (port 5003)")
    print("2. Run comprehensive tests")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        start_streaming_demo()
    elif choice == "2":
        print("\nRunning comprehensive tests...")
        os.system("python3 test_unrealspeech.py")
    else:
        print("👋 Done! You can run the streaming demo anytime with:")
        print("   python3 streaming_demo.py")

if __name__ == "__main__":
    main()
