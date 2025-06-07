#!/usr/bin/env python3
"""
Unreal Speech API Test Script
Tests basic functionality, streaming, and voice options
"""

import os
import requests
import json
import base64
import time
from typing import Optional
import subprocess
import tempfile

# You'll need to set this environment variable or replace with your API key
UNREALSPEECH_API_KEY = os.getenv("UNREALSPEECH_API_KEY", "YOUR_API_KEY_HERE")

class UnrealSpeechTester:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.v8.unrealspeech.com"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Available voices according to documentation
        self.voices = {
            "female": ["af", "af_bella", "af_sarah", "bf_emma", "bf_isabella", "af_nicole", "af_sky"],
            "male": ["am_adam", "am_michael", "bm_george", "bm_lewis"]
        }
    
    def test_basic_synthesis(self, text: str, voice_id: str = "af_sky"):
        """Test basic /stream endpoint (up to 1,000 chars, instant response)"""
        print(f"\n=== Testing Basic Synthesis ===")
        print(f"Text: {text[:50]}...")
        print(f"Voice: {voice_id}")
        
        try:
            response = requests.post(
                f"{self.base_url}/stream",
                headers=self.headers,
                json={
                    "Text": text,
                    "VoiceId": voice_id,
                    "Bitrate": "192k",
                    "Speed": "0",  # -1.0 to 1.0
                    "Pitch": "1",  # 0.5 to 1.5
                    "Codec": "libmp3lame"
                },
                stream=True  # Enable streaming
            )
            
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                return None
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        tmp_file.write(chunk)
                temp_path = tmp_file.name
            
            print(f"✓ Audio saved to: {temp_path}")
            print(f"✓ File size: {os.path.getsize(temp_path)} bytes")
            
            # Play audio on macOS
            if os.path.exists('/usr/bin/afplay'):
                print("Playing audio...")
                subprocess.run(['afplay', temp_path])
            
            return temp_path
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def test_streaming_response(self, text: str, voice_id: str = "af_sky"):
        """Test streaming with chunk processing"""
        print(f"\n=== Testing Streaming Response ===")
        print(f"Text length: {len(text)} chars")
        
        try:
            response = requests.post(
                f"{self.base_url}/stream",
                headers=self.headers,
                json={
                    "Text": text,
                    "VoiceId": voice_id,
                    "Bitrate": "192k",
                    "Speed": "0",
                    "Pitch": "1",
                    "Codec": "libmp3lame"
                },
                stream=True
            )
            
            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
                return
            
            # Process chunks as they arrive
            chunk_count = 0
            total_bytes = 0
            start_time = time.time()
            first_chunk_time = None
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        if first_chunk_time is None:
                            first_chunk_time = time.time() - start_time
                        
                        chunk_count += 1
                        total_bytes += len(chunk)
                        tmp_file.write(chunk)
                        
                        # Log chunk info
                        if chunk_count <= 5:  # Show first 5 chunks
                            print(f"  Chunk {chunk_count}: {len(chunk)} bytes")
                
                temp_path = tmp_file.name
            
            total_time = time.time() - start_time
            
            print(f"\n✓ Streaming complete!")
            print(f"  - Time to first chunk: {first_chunk_time:.3f}s")
            print(f"  - Total time: {total_time:.3f}s")
            print(f"  - Total chunks: {chunk_count}")
            print(f"  - Total size: {total_bytes} bytes")
            print(f"  - Average chunk size: {total_bytes/chunk_count:.0f} bytes")
            
            return temp_path
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
    def test_voice_comparison(self, text: str = "Hello, this is a test of different voices."):
        """Test different voice options"""
        print(f"\n=== Testing Voice Options ===")
        
        for gender, voices in self.voices.items():
            print(f"\n{gender.capitalize()} voices:")
            for voice in voices[:2]:  # Test first 2 of each gender
                print(f"\n  Testing {voice}...")
                result = self.test_basic_synthesis(text, voice)
                if result:
                    time.sleep(1)  # Brief pause between voices
    
    def test_speech_parameters(self, text: str = "This is a test of speech parameters."):
        """Test different speed and pitch settings"""
        print(f"\n=== Testing Speech Parameters ===")
        
        test_params = [
            {"Speed": "-0.5", "Pitch": "1", "desc": "Slower speech"},
            {"Speed": "0.5", "Pitch": "1", "desc": "Faster speech"},
            {"Speed": "0", "Pitch": "0.8", "desc": "Lower pitch"},
            {"Speed": "0", "Pitch": "1.2", "desc": "Higher pitch"},
        ]
        
        for params in test_params:
            print(f"\n  Testing: {params['desc']}")
            try:
                response = requests.post(
                    f"{self.base_url}/stream",
                    headers=self.headers,
                    json={
                        "Text": text,
                        "VoiceId": "af_sky",
                        "Bitrate": "192k",
                        "Speed": params["Speed"],
                        "Pitch": params["Pitch"],
                        "Codec": "libmp3lame"
                    }
                )
                
                if response.status_code == 200:
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                        tmp.write(response.content)
                        temp_path = tmp.name
                    
                    print(f"    ✓ Generated: {os.path.getsize(temp_path)} bytes")
                    
                    if os.path.exists('/usr/bin/afplay'):
                        subprocess.run(['afplay', temp_path])
                        time.sleep(0.5)
                    
                    os.unlink(temp_path)
                else:
                    print(f"    ✗ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
    
    def test_long_text_handling(self):
        """Test handling of longer texts"""
        print(f"\n=== Testing Long Text Handling ===")
        
        # Test different text lengths
        test_cases = [
            ("Short", "Hello world!", "af_sky"),
            ("Medium", "This is a medium length text that contains a few sentences. It should process quickly and demonstrate the streaming capability of the API.", "af_bella"),
            ("Long", "This is a much longer text that approaches the character limit. " * 20, "am_michael"),  # ~900 chars
        ]
        
        for name, text, voice in test_cases:
            print(f"\n  {name} text ({len(text)} chars) with {voice}:")
            start = time.time()
            result = self.test_streaming_response(text[:1000], voice)  # Ensure under 1000 char limit
            if result:
                print(f"    ✓ Completed in {time.time() - start:.2f}s")
                os.unlink(result)


def main():
    """Run all tests"""
    print("=== Unreal Speech API Test Suite ===")
    print(f"API Key: {'Set' if UNREALSPEECH_API_KEY != 'YOUR_API_KEY_HERE' else 'Not Set'}")
    
    if UNREALSPEECH_API_KEY == "YOUR_API_KEY_HERE":
        print("\n⚠️  Please set your Unreal Speech API key:")
        print("   export UNREALSPEECH_API_KEY='your_actual_key'")
        print("   or edit this script directly")
        return
    
    tester = UnrealSpeechTester(UNREALSPEECH_API_KEY)
    
    # Run tests
    print("\n1. Testing basic synthesis...")
    result = tester.test_basic_synthesis("Hello, this is a test of Unreal Speech text to speech API.")
    if result:
        os.unlink(result)
    
    print("\n2. Testing streaming capabilities...")
    result = tester.test_streaming_response("This text will be streamed from the API, allowing us to measure the time to first byte and overall latency.")
    if result:
        os.unlink(result)
    
    print("\n3. Testing different voices...")
    tester.test_voice_comparison()
    
    print("\n4. Testing speech parameters...")
    tester.test_speech_parameters()
    
    print("\n5. Testing long text handling...")
    tester.test_long_text_handling()
    
    print("\n=== Tests Complete ===")


if __name__ == "__main__":
    main()
