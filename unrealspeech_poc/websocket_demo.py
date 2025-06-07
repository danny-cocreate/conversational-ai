"""
Unreal Speech WebSocket Streaming Demo
Shows real-time streaming with word-level timestamps
"""

import asyncio
import websockets
import json
import base64
import os

UNREALSPEECH_API_KEY = os.getenv("UNREALSPEECH_API_KEY", "YOUR_API_KEY_HERE")

async def test_websocket_streaming(text: str, voice_id: str = "af_sky"):
    """Test WebSocket streaming with word timestamps"""
    
    # WebSocket URL for streamWithTimestamps endpoint
    ws_url = "wss://api.v8.unrealspeech.com/streamWithTimestamps"
    
    audio_chunks = []
    timestamps = []
    
    print(f"Connecting to WebSocket...")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            # Send initial request with auth and parameters
            request = {
                "Text": text,
                "VoiceId": voice_id,
                "Bitrate": "192k",
                "Speed": "0",
                "Pitch": "1",
                "Codec": "libmp3lame",
                "Authorization": f"Bearer {UNREALSPEECH_API_KEY}"
            }
            
            await websocket.send(json.dumps(request))
            print("Request sent, waiting for response...")
            
            # Receive messages
            while True:
                try:
                    message = await websocket.recv()
                    
                    # Check if it's binary (audio) or text (JSON)
                    if isinstance(message, bytes):
                        # Audio chunk
                        audio_chunks.append(message)
                        print(f"Received audio chunk: {len(message)} bytes")
                    else:
                        # JSON message (timestamps or status)
                        data = json.loads(message)
                        
                        if data.get('type') == 'progress' and 'message' in data:
                            # Timestamp data
                            msg_val = data['message']
                            if isinstance(msg_val, list):
                                timestamps.extend(msg_val)
                                print(f"Received {len(msg_val)} word timestamps")
                                # Print first few timestamps as example
                                for ts in msg_val[:3]:
                                    if ts and 'word' in ts:
                                        print(f"  - '{ts['word']}' at {ts.get('start', 0)}ms")
                        
                        elif data.get('type') == 'complete':
                            print("Streaming complete!")
                            break
                        
                        elif data.get('type') == 'error':
                            print(f"Error: {data.get('message', 'Unknown error')}")
                            break
                        
                        else:
                            print(f"Received: {data}")
                
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        return None, None
    
    # Combine audio chunks
    if audio_chunks:
        print(f"\nTotal audio chunks: {len(audio_chunks)}")
        print(f"Total audio size: {sum(len(chunk) for chunk in audio_chunks)} bytes")
        
        # Save audio
        with open("websocket_output.mp3", "wb") as f:
            for chunk in audio_chunks:
                f.write(chunk)
        print("Audio saved to websocket_output.mp3")
    
    # Process timestamps
    if timestamps:
        print(f"\nTotal word timestamps: {len(timestamps)}")
        # Save timestamps
        with open("timestamps.json", "w") as f:
            json.dump(timestamps, f, indent=2)
        print("Timestamps saved to timestamps.json")
    
    return audio_chunks, timestamps


def create_subtitle_file(timestamps, output_file="subtitles.srt"):
    """Create an SRT subtitle file from word timestamps"""
    if not timestamps:
        return
    
    with open(output_file, "w") as f:
        for i, ts in enumerate(timestamps):
            if ts and 'word' in ts:
                start_ms = ts.get('start', 0)
                end_ms = ts.get('end', start_ms + 500)  # Default 500ms duration if no end
                
                # Convert to SRT timestamp format
                start_time = f"{int(start_ms//3600000):02d}:{int((start_ms%3600000)//60000):02d}:{int((start_ms%60000)//1000):02d},{int(start_ms%1000):03d}"
                end_time = f"{int(end_ms//3600000):02d}:{int((end_ms%3600000)//60000):02d}:{int((end_ms%60000)//1000):02d},{int(end_ms%1000):03d}"
                
                f.write(f"{i+1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{ts['word']}\n\n")
    
    print(f"Subtitles saved to {output_file}")


async def main():
    """Run WebSocket streaming test"""
    print("=== Unreal Speech WebSocket Streaming Test ===")
    
    if UNREALSPEECH_API_KEY == "YOUR_API_KEY_HERE":
        print("\n⚠️  Please set your API key:")
        print("export UNREALSPEECH_API_KEY='your_actual_key'")
        return
    
    # Test text
    test_text = """
    Welcome to the Unreal Speech WebSocket streaming demo. 
    This demonstrates real-time audio streaming with word-level timestamps. 
    You can use these timestamps to highlight words as they're spoken, 
    create subtitles, or build interactive experiences.
    """
    
    print(f"\nText to synthesize: {test_text[:100]}...")
    print("\nStarting WebSocket stream...")
    
    # Run the test
    audio_chunks, timestamps = await test_websocket_streaming(test_text, "af_bella")
    
    # Create subtitle file if we got timestamps
    if timestamps:
        create_subtitle_file(timestamps)
        
        # Show timing analysis
        print("\n=== Timing Analysis ===")
        if len(timestamps) > 0:
            first_word = timestamps[0].get('start', 0)
            last_word = timestamps[-1].get('end', timestamps[-1].get('start', 0))
            total_duration = last_word - first_word
            
            print(f"First word at: {first_word}ms")
            print(f"Last word at: {last_word}ms")
            print(f"Total duration: {total_duration/1000:.2f}s")
            print(f"Average word duration: {total_duration/len(timestamps):.0f}ms")


if __name__ == "__main__":
    asyncio.run(main())
