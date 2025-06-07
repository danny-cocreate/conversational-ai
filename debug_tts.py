#!/usr/bin/env python3
"""
Debug script to test TTS streaming functionality
"""

import requests
import time
import sys
import os

# Add the project root to path
sys.path.append('/Users/dSetia/Dropbox/projects/conversational AI')

from config import Config

def test_unrealspeech_api():
    """Test UnrealSpeech API directly"""
    
    print("🔍 DEBUGGING TTS STREAMING ISSUE")
    print("=" * 50)
    
    # Check configuration
    api_key = Config.UNREALSPEECH_API_KEY
    provider = Config.TTS_PROVIDER
    
    print(f"🔑 API Key present: {bool(api_key)}")
    print(f"🔑 API Key (first 10 chars): {api_key[:10] if api_key else 'None'}...")
    print(f"🎙️ Provider: {provider}")
    
    if not api_key:
        print("❌ No API key found!")
        return False
    
    # Test payload
    payload = {
        'Text': 'Hello, this is a test of the streaming system.',
        'VoiceId': 'af_sky',
        'Bitrate': '128k',
        'Speed': '0',
        'Pitch': '1',
        'Codec': 'libmp3lame'
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    url = "https://api.v8.unrealspeech.com/stream"
    
    print(f"\n📡 Testing request to: {url}")
    print(f"📦 Payload: {payload}")
    print(f"🔑 Headers (auth hidden): {dict((k, '***' if 'auth' in k.lower() else v) for k, v in headers.items())}")
    
    try:
        print("\n🚀 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            stream=True,
            timeout=(5, 30)
        )
        
        request_time = (time.time() - start_time) * 1000
        print(f"📡 Request completed in {request_time:.0f}ms")
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            error_text = response.text
            print(f"❌ ERROR RESPONSE: {error_text}")
            return False
        
        print("\n🌊 Testing streaming...")
        chunk_count = 0
        total_bytes = 0
        first_chunk_time = None
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                if chunk_count == 0:
                    first_chunk_time = (time.time() - start_time) * 1000
                    print(f"⚡ First chunk received in {first_chunk_time:.0f}ms")
                    print(f"📦 First chunk size: {len(chunk)} bytes")
                    print(f"🎵 First chunk preview: {chunk[:50]}...")
                
                chunk_count += 1
                total_bytes += len(chunk)
                
                if chunk_count <= 5:
                    print(f"📦 Chunk {chunk_count}: {len(chunk)} bytes")
                elif chunk_count % 10 == 0:
                    print(f"📊 Progress: {chunk_count} chunks, {total_bytes} bytes")
        
        total_time = (time.time() - start_time) * 1000
        print(f"\n✅ STREAMING COMPLETED:")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Total bytes: {total_bytes}")
        print(f"   Total time: {total_time:.0f}ms")
        print(f"   First chunk latency: {first_chunk_time:.0f}ms" if first_chunk_time else "   First chunk: NEVER RECEIVED")
        
        if chunk_count == 0:
            print("❌ CRITICAL ISSUE: No chunks received!")
            print("🔍 This explains the frontend streaming issue")
            return False
        elif total_bytes == 0:
            print("❌ CRITICAL ISSUE: Zero bytes received!")
            return False
        else:
            print("✅ Streaming appears to work correctly")
            return True
            
    except requests.exceptions.Timeout as e:
        print(f"⏰ Timeout error: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")
        return False
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_endpoint():
    """Test the Flask /stream endpoint"""
    
    print("\n🌐 TESTING FLASK ENDPOINT")
    print("=" * 30)
    
    url = "http://localhost:5001/stream"
    payload = {
        'text': 'Hello, this is a test of the Flask streaming endpoint.',
        'voice_id': 'af_sky',
        'speed': '1.0',
        'temperature': '0.25'
    }
    
    print(f"📡 Testing: {url}")
    print(f"📦 Payload: {payload}")
    
    try:
        response = requests.post(
            url,
            json=payload,
            stream=True,
            timeout=(5, 30)
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Flask endpoint error: {error_data}")
            return False
        
        chunk_count = 0
        total_bytes = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                if chunk_count == 0:
                    print(f"⚡ First chunk from Flask: {len(chunk)} bytes")
                chunk_count += 1
                total_bytes += len(chunk)
        
        print(f"✅ Flask endpoint results:")
        print(f"   Chunks: {chunk_count}")
        print(f"   Bytes: {total_bytes}")
        
        return chunk_count > 0 and total_bytes > 0
        
    except Exception as e:
        print(f"❌ Flask endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TTS DEBUG SUITE")
    print("==================")
    
    # Test 1: Direct API
    api_works = test_unrealspeech_api()
    
    # Test 2: Flask endpoint (only if server is running)
    flask_works = test_flask_endpoint()
    
    print("\n📊 SUMMARY")
    print("=" * 20)
    print(f"✅ Direct API: {'PASS' if api_works else 'FAIL'}")
    print(f"✅ Flask endpoint: {'PASS' if flask_works else 'FAIL'}")
    
    if not api_works:
        print("\n🔍 ROOT CAUSE: Direct API communication failing")
        print("💡 RECOMMENDATION: Check API key, network, and UnrealSpeech service status")
    elif not flask_works:
        print("\n🔍 ROOT CAUSE: Flask streaming wrapper issue") 
        print("💡 RECOMMENDATION: Check Flask streaming implementation")
    else:
        print("\n🤔 Both tests passed - issue may be frontend-specific")
        print("💡 RECOMMENDATION: Check frontend audio processing logic")
