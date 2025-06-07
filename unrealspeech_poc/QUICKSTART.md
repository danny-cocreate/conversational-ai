# Unreal Speech POC - Quick Start Guide

## 🚀 Quick Start (No API Key Required)

You can test Unreal Speech functionality without an API key:

```bash
# Make the start script executable
chmod +x start.sh

# Run the launcher
./start.sh
```

Or run individual tests:

```bash
# 1. Quick connection test
python3 quick_test.py

# 2. Behavior simulation (shows expected performance)
python3 simulate_behavior.py

# 3. Interactive UI demo (no API key needed)
python3 offline_demo.py
# Then open http://localhost:5004
```

## 🔑 Full Testing (With API Key)

1. **Get your API key**:
   - Sign up at [unrealspeech.com](https://unrealspeech.com)
   - 250,000 characters free
   - Then $8 per 1M characters

2. **Set your API key**:
   ```bash
   export UNREALSPEECH_API_KEY='your_key_here'
   ```

3. **Run full test suite**:
   ```bash
   python3 run_tests.py
   ```

## 📊 Test Results Summary

Based on Unreal Speech documentation:

### Performance Metrics
- **Latency**: ~300ms (vs ~500ms+ for Hume AI)
- **Streaming**: True HTTP chunked streaming
- **Cost**: $8/1M chars (vs ~$240/1M for Hume AI)

### Key Features
- ✅ 48 voices in 8 languages
- ✅ WebSocket streaming with word timestamps
- ✅ Real-time audio streaming
- ✅ Multiple audio formats (MP3, μ-law)
- ✅ Speed and pitch control

### Expected Savings
For 10M characters/month:
- Unreal Speech: $80
- Hume AI: ~$2,400
- **Monthly savings: $2,320**
- **Annual savings: $27,840**

## 🧪 What Each Test Does

1. **quick_test.py**: Tests connection and displays pricing
2. **simulate_behavior.py**: Shows expected API behavior
3. **offline_demo.py**: Interactive UI without API calls
4. **test_unrealspeech.py**: Full API test suite (requires key)
5. **streaming_demo.py**: Web-based streaming demo (requires key)
6. **comparison_tool.py**: Side-by-side comparison with Hume

## 📝 Next Steps

1. Run the offline demo to see the UI
2. Get an API key from Unreal Speech
3. Test with your actual conversation content
4. Compare audio quality with Hume samples
5. Measure actual latency in your network environment

## 🔧 Troubleshooting

If you get import errors:
```bash
pip install -r requirements.txt
```

If ports are in use:
- Main app: 5001
- Streaming demo: 5003
- Offline demo: 5004

## 💡 Integration Preview

Once validated, we'll create a modular TTS system:

```python
# Easy provider switching
tts = TTSFactory.create_provider("unrealspeech", config)
# or
tts = TTSFactory.create_provider("hume", config)

# Same interface for all providers
audio = await tts.synthesize(text, voice_id)
```

Ready to test? Run `./start.sh` to begin!
