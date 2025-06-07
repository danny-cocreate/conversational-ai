# Unreal Speech API Testing Plan

## Phase 1: Get Your API Key

1. **Visit unrealspeech.com**
   - Sign up for a free account
   - You get 250,000 characters FREE (worth $2 in paid usage)
   - No credit card required for free tier

2. **Get Your API Key**
   - Go to your dashboard after signup
   - Copy your API key
   - Keep it secure (don't share it publicly)

## Phase 2: Set Up Environment

```bash
# Navigate to the POC directory
cd unrealspeech_poc

# Set your API key (replace with your actual key)
export UNREALSPEECH_API_KEY='your_actual_api_key_here'

# Install requirements
pip3 install -r requirements.txt
```

## Phase 3: Test Basic Functionality

### Test 1: Basic API Connection
```bash
python3 test_unrealspeech.py
```
This will test:
- ✅ API authentication
- ✅ Basic synthesis
- ✅ Streaming capabilities 
- ✅ Different voices
- ✅ Speed/pitch parameters
- ✅ Latency measurements

### Test 2: Streaming Demo (Port 5003)
```bash
python3 streaming_demo.py
```
Then open: http://localhost:5003

This provides:
- 🎯 Web interface for testing
- 📊 Real-time metrics (latency, file size)
- 🎛️ Voice/speed/pitch controls
- 🔄 Compare standard vs streaming

## Phase 4: Advanced Testing

### Test 3: WebSocket with Word Timestamps
```bash
python3 websocket_demo.py
```
Features:
- Word-level synchronization
- Real-time text highlighting
- Advanced streaming capabilities

### Test 4: Direct Comparison with Hume AI
```bash
python3 comparison_tool.py
```
Side-by-side comparison:
- Audio quality
- Response time
- Cost analysis
- Feature comparison

## Expected Results

### Latency Benchmarks
- **Time to First Byte**: ~300ms
- **Total Generation**: <1 second for 100 words
- **Streaming Start**: Nearly instant

### Cost Comparison
Current monthly cost (estimated):
- Hume AI: ~$240 per 1M characters
- Unreal Speech: $8 per 1M characters
- **Savings**: $232 per 1M characters (96% reduction)

### Quality Metrics
- 48 voices available
- 8 languages supported
- 192k bitrate MP3 output
- Natural speech patterns

## Troubleshooting

### Common Issues

1. **"Authentication required" error**
   - Solution: Check that UNREALSPEECH_API_KEY is set correctly
   - Verify: `echo $UNREALSPEECH_API_KEY`

2. **"Text too long" error**
   - Stream endpoint: 1,000 character limit
   - Speech endpoint: 3,000 character limit
   - Solution: Break text into smaller chunks

3. **Import errors**
   - Solution: `pip3 install -r requirements.txt`

4. **Port 5003 already in use**
   - Solution: Kill existing process or change port in streaming_demo.py

### Testing Without API Key

If you want to test the concept first:
```bash
python3 quick_test.py        # Tests connection, shows pricing
python3 simulate_behavior.py # Simulates expected performance
python3 offline_demo.py      # Runs demo UI (port 5004)
```

## Next Steps After Validation

Once you confirm Unreal Speech meets your needs:

1. **Implement Modular TTS System**
   - Create abstract TTS interface
   - Implement provider switching
   - Add fallback mechanisms

2. **Integration with Existing App**
   - Replace Hume TTS calls
   - Update frontend for streaming
   - Add configuration management

3. **Production Deployment**
   - Set up production API key
   - Configure rate limiting
   - Monitor usage and costs

## Success Criteria

✅ **Audio Quality**: Comparable to Hume AI
✅ **Latency**: <500ms time to first byte
✅ **Streaming**: Chunks arrive progressively
✅ **Voice Options**: Multiple suitable voices
✅ **Cost**: Significant savings confirmed
✅ **Reliability**: Consistent API responses

Run all tests and confirm each criterion before proceeding with full integration.
