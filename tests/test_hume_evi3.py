"""
Test script for Hume EVI3 implementation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import tts module
sys.path.append(str(Path(__file__).parent.parent))

from tts.providers.hume_evi3 import HumeEVI3Provider
from tts.providers.hume_evi3.emotional import EmotionalContext
from tts.providers.hume_evi3.clm import HumeCLMWrapper

async def test_basic_synthesis():
    """Test basic text-to-speech synthesis"""
    print("\n🔍 Testing basic synthesis...")
    
    # Create provider instance
    provider = HumeEVI3Provider(api_key=os.getenv('HUME_API_KEY'))
    
    # Test text
    test_text = "Hello! This is a test of the Hume EVI3 system. How does this sound?"
    
    try:
        # Test synthesis
        audio_data = await provider.synthesize(
            text=test_text,
            voice_id='ee966436-01ab-4810-a880-9e0a532e03b8',
            speed=1.0,
            temperature=0.7
        )
        
        print("✅ Basic synthesis successful!")
        print(f"📊 Audio data size: {len(audio_data)} bytes")
        
        # Save test audio
        with open('test_output.mp3', 'wb') as f:
            f.write(audio_data)
        print("💾 Saved test audio to test_output.mp3")
        
    except Exception as e:
        print(f"❌ Basic synthesis failed: {e}")
        return False
    
    return True

async def test_emotional_context():
    """Test emotional context processing"""
    print("\n🔍 Testing emotional context...")
    
    # Create emotional context
    context = EmotionalContext()
    
    # Test emotional data
    test_data = {
        'emotions': {
            'frustration': 0.7,
            'excitement': 0.3
        },
        'prosody': {
            'pitch': 1.2,
            'speech_rate': 0.9
        },
        'confidence': 0.85
    }
    
    try:
        # Process emotional data
        state = context.process_emotional_data(test_data)
        
        # Get summary
        summary = context.get_emotional_summary()
        
        print("✅ Emotional context processing successful!")
        print(f"📊 Emotional summary: {summary}")
        
        # Test adaptation
        should_adapt = context.should_adapt_response()
        guidance = context.get_adaptation_guidance()
        
        print(f"📊 Should adapt: {should_adapt}")
        print(f"📊 Adaptation guidance: {guidance}")
        
    except Exception as e:
        print(f"❌ Emotional context test failed: {e}")
        return False
    
    return True

async def test_connection():
    """Test connection to Hume EVI3"""
    print("\n🔍 Testing connection...")
    
    # Create provider instance
    provider = HumeEVI3Provider(api_key=os.getenv('HUME_API_KEY'))
    
    try:
        # Test connection
        is_connected = await provider.test_connection()
        
        if is_connected:
            print("✅ Connection test successful!")
        else:
            print("❌ Connection test failed")
            return False
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting Hume EVI3 tests...")
    
    # Check for API key
    if not os.getenv('HUME_API_KEY'):
        print("❌ HUME_API_KEY environment variable not set")
        return
    
    # Run tests
    tests = [
        test_connection,
        test_basic_synthesis,
        test_emotional_context
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"✅ Passed: {sum(results)}/{len(tests)}")
    print(f"❌ Failed: {len(tests) - sum(results)}/{len(tests)}")

if __name__ == "__main__":
    asyncio.run(main()) 