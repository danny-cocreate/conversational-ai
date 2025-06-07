#!/usr/bin/env python3
"""
Test Unreal Speech using their public demo
This doesn't require an API key and helps validate basic functionality
"""

import requests
import json
import tempfile
import subprocess
import os
import time

def test_public_demo():
    """Test using Unreal Speech's public demo endpoint"""
    print("🔬 Testing Unreal Speech Public Demo")
    print("="*40)
    
    # This is based on their website demo - may not require API key
    demo_url = "https://api.v8.unrealspeech.com/demo"
    
    test_texts = [
        "Hello! This is a test of Unreal Speech.",
        "The quick brown fox jumps over the lazy dog.",
        "I'm excited to help you with your project today!"
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        
        try:
            # First, let's try their main endpoint without auth to see the error
            response = requests.post(
                "https://api.v8.unrealspeech.com/stream",
                headers={
                    "Content-Type": "application/json"
                },
                json={
                    "Text": text,
                    "VoiceId": "af_sky",
                    "Bitrate": "192k",
                    "Speed": "0",
                    "Pitch": "1",
                    "Codec": "libmp3lame"
                }
            )
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 401:
                print("  ❌ Authentication required (expected)")
                print(f"  Response: {response.text[:100]}...")
            elif response.status_code == 200:
                print("  ✅ Success (unexpected without API key)")
                # Save audio if successful
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp.write(response.content)
                    print(f"  📁 Saved to: {tmp.name}")
                    if os.path.exists('/usr/bin/afplay'):
                        subprocess.run(['afplay', tmp.name])
            else:
                print(f"  ⚠️  Unexpected response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "="*40)
    print("To use Unreal Speech, you need to:")
    print("1. Sign up at https://unrealspeech.com")
    print("2. Get your API key (250K characters free)")
    print("3. Set: export UNREALSPEECH_API_KEY='your_key'")
    print("4. Run the full test suite")

def check_pricing():
    """Display Unreal Speech pricing information"""
    print("\n💰 Unreal Speech Pricing")
    print("="*40)
    print("Free Tier: 250,000 characters")
    print("Paid: $8 per 1M characters")
    print("\nComparison:")
    print("- 11Labs: ~$88 per 1M chars (11x more expensive)")
    print("- Google TTS: ~$16 per 1M chars (2x more expensive)")
    print("- Amazon Polly: ~$4 per 1M chars (0.5x cheaper)")
    print("\nFor 10M chars/month:")
    print("- Unreal Speech: $80")
    print("- 11Labs: $880")
    print("- Your savings: $800/month or $9,600/year")

def test_latency_check():
    """Test connection latency to Unreal Speech servers"""
    print("\n🌐 Testing Connection Latency")
    print("="*40)
    
    endpoints = [
        "https://api.v8.unrealspeech.com",
        "https://unrealspeech.com"
    ]
    
    for endpoint in endpoints:
        try:
            start = time.time()
            response = requests.get(endpoint, timeout=5)
            latency = (time.time() - start) * 1000
            print(f"{endpoint}: {latency:.0f}ms")
        except Exception as e:
            print(f"{endpoint}: Failed - {str(e)}")

if __name__ == "__main__":
    test_public_demo()
    check_pricing()
    test_latency_check()
