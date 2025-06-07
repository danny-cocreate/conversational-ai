# Unreal Speech TTS Proof of Concept

This POC demonstrates Unreal Speech's text-to-speech capabilities in isolation, allowing you to test and validate the service before integrating it into your main application.

## Setup

1. **Get an API Key**
   - Sign up at https://unrealspeech.com
   - Get your API key from the dashboard
   - They offer 250K characters free

2. **Set Environment Variable**
   ```bash
   export UNREALSPEECH_API_KEY='your_api_key_here'
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Test Scripts

### 1. Basic API Test (`test_unrealspeech.py`)
Tests core functionality including:
- ✅ Basic text synthesis
- ✅ Streaming response with timing metrics
- ✅ Voice comparison (10 different voices)
- ✅ Speech parameters (speed, pitch)
- ✅ Long text handling (up to 1000 chars)

**Run it:**
```bash
python test_unrealspeech.py
```

### 2. Web Streaming Demo (`streaming_demo.py`)
A Flask web app that demonstrates:
- ✅ Browser-based audio playback
- ✅ Real-time streaming to web clients
- ✅ Voice selection UI
- ✅ Speed and pitch controls
- ✅ Performance metrics (TTFB, total time, size)

**Run it:**
```bash
python streaming_demo.py
# Open http://localhost:5003 in your browser
```

### 3. WebSocket Demo (`websocket_demo.py`)
Advanced streaming with word-level timestamps:
- ✅ WebSocket-based streaming
- ✅ Word-by-word timestamps
- ✅ Subtitle generation (SRT format)
- ✅ Timing analysis

**Run it:**
```bash
python websocket_demo.py
```

## Key Features to Test

### 1. **Latency** 
- Unreal Speech promises 300ms latency
- Test with the web demo's "Test Streaming" button
- Check the "Time to First Byte" metric

### 2. **Voice Quality**
- Test different voices in the web demo
- Compare male vs female voices
- Test British vs American accents

### 3. **Streaming Performance**
- Monitor chunk delivery in console
- Test with different text lengths
- Check audio continuity

### 4. **Cost Effectiveness**
- Unreal Speech is 11x cheaper than 11Labs
- Monitor your usage in their dashboard
- Calculate cost per character

### 5. **API Limits**
- /stream endpoint: up to 1,000 characters
- Test text chunking for longer content

## Integration Considerations

### Advantages ✅
1. **Cost**: Significantly cheaper than Hume AI
2. **Latency**: Fast streaming response
3. **Flexibility**: Multiple endpoints for different use cases
4. **Features**: Word timestamps for advanced UX

### Potential Challenges ⚠️
1. **Character Limits**: 1000 chars for streaming endpoint
2. **Voice Selection**: Different voice IDs than Hume
3. **Audio Format**: Ensure MP3 compatibility
4. **Error Handling**: Different error response format

## Next Steps

After validating the POC:

1. **Compare Quality**: Record samples from both Hume and Unreal Speech
2. **Measure Performance**: Document actual latency numbers
3. **Test Edge Cases**: Empty text, special characters, long texts
4. **Validate Streaming**: Ensure smooth playback in your target browsers
5. **Check Reliability**: Test error scenarios and recovery

## Recommended Testing Sequence

1. Run `test_unrealspeech.py` first to verify API connectivity
2. Use `streaming_demo.py` to test in a browser environment
3. Try `websocket_demo.py` if you need word-level synchronization
4. Test with your actual conversation content
5. Compare results with current Hume AI implementation

## Sample Test Cases

```python
# Short conversational response
"Sure, I'd be happy to help you with that."

# Longer explanation
"The process involves three main steps. First, you'll need to gather all the required documents. Second, submit your application through the online portal. Finally, wait for confirmation which typically takes 3-5 business days."

# Technical content
"To implement the algorithm, use a recursive approach with memoization. The time complexity is O(n log n) with a space complexity of O(n)."

# Emotional/expressive content  
"Wow! That's absolutely fantastic news! I'm so excited to hear about your success. Congratulations on this amazing achievement!"
```

## Notes

- The web demo runs on port 5003 to avoid conflict with your main app (port 5001)
- Audio files are saved for offline analysis
- All demos include error handling and logging
- WebSocket demo requires `websockets` library (included in requirements)
