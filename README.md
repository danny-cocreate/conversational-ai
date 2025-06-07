# Conversational AI with Integrated TTS and Simplified Slide Control

A modular voice chat application that combines OpenAI's GPT-4 with high-quality text-to-speech providers and simplified slide control capabilities. Features easy switching between TTS providers with significant cost savings and streamlined presentation control.

## 🎯 Key Features

- **Modular TTS Architecture**: Easy switching between providers
- **Multiple TTS Providers**: Unreal Speech (primary) & Hume AI (fallback)
- **Cost Optimization**: 30x cheaper TTS with Unreal Speech
- **Real-time Streaming**: Low-latency audio streaming
- **Voice Chat Interface**: Complete web-based conversation system
- **Knowledge Base**: Upload documents for context-aware responses
- **Provider Management**: Runtime switching between TTS providers
- **Simplified Slide Control**: Voice commands for presentation navigation
- **Streamlined Implementation**: Optimized for performance and simplicity
- **Integrated Conversation**: Seamless handling of both chat and slide commands

## 💰 Cost Comparison

| Provider | Cost per 1M chars | Features | Latency |
|----------|-------------------|----------|---------|
| **Unreal Speech** | $8 | 48 voices, streaming, timestamps | ~300ms |
| Hume AI | ~$240 | Emotional synthesis | ~500ms+ |

**Savings: 30x cheaper with Unreal Speech!**

## 🚀 Quick Start

### 1. Setup
```bash
# Clone and navigate to project
cd "conversational AI"

# Install dependencies
pip install -r requirements.txt

# Run interactive setup
python setup.py
```

### 2. Configure API Keys
Get your API keys:
- **OpenAI**: https://platform.openai.com/api-keys (Required)
- **Unreal Speech**: https://unrealspeech.com (Recommended - 250k free chars)
- **Hume AI**: https://hume.ai (Fallback)

Set environment variables:
```bash
export OPENAI_API_KEY="your_openai_key"
export UNREALSPEECH_API_KEY="your_unrealspeech_key"
export HUME_API_KEY="your_hume_key"
```

### 3. Test Integration
```bash
python test_integration.py
```

### 4. Start the Server
```bash
python app.py
```

### 5. Open Web Interface
Navigate to: http://localhost:5001

## 🎙️ TTS Provider Architecture

### Modular Design
```python
# Easy provider switching
tts_provider = TTSFactory.create_provider("unrealspeech", config)
# or
tts_provider = TTSFactory.create_provider("hume", config)

# Same interface for all providers
audio = await tts_provider.synthesize(text, voice_id)
```

### Provider Features

#### Unreal Speech (Recommended)
- ✅ 48 voices across 8 languages
- ✅ True HTTP streaming (300ms latency)
- ✅ WebSocket support with word timestamps
- ✅ Multiple audio formats
- ✅ Speed and pitch control
- ✅ 11x cheaper than competitors

#### Hume AI (Fallback)
- ✅ Emotionally expressive synthesis
- ✅ Custom voice descriptions
- ⚠️ Limited streaming support
- ⚠️ Higher latency and cost

## 🎮 Simplified Slide Control

### Key Components

- **SimplifiedConversationManager**: Handles both regular conversation and slide commands
- **SimplifiedCommandHandler**: Streamlined execution of slide navigation commands
- **SimplifiedVoiceParser**: Efficient parsing of voice input for slide control

### Supported Slide Commands

| Command Type | Example Phrases |
|--------------|----------------|
| **Next** | "next slide", "forward", "advance" |
| **Previous** | "previous slide", "back", "go back" |
| **Go To** | "go to slide 3", "slide 5" |
| **First** | "first slide", "beginning", "start" |
| **Last** | "last slide", "final slide", "end" |
| **Reset** | "reset presentation", "restart", "start over" |
| **Status** | "what slide", "slide status", "where am I" |

### API Endpoints

```
# Execute a slide command
POST /slide/command
{"command": "next slide"}

# Get current slide status
GET /slide/status
```

## 🔧 Configuration

### Environment Variables
```bash
# Provider selection (default: unrealspeech)
export TTS_PROVIDER="unrealspeech"  # or "hume"

# API Keys
export OPENAI_API_KEY="your_key"
export UNREALSPEECH_API_KEY="your_key"
export HUME_API_KEY="your_key"
```

### Runtime Provider Switching
The web interface allows switching between providers without restarting:

1. Open Settings in the web interface
2. Select different TTS Provider
3. Click "Switch"
4. Test with new provider

## 📁 Project Structure

```
conversational AI/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── conversation.py       # OpenAI GPT integration
├── document_processor.py # Knowledge base management
├── setup.py             # Interactive setup script
├── test_integration.py  # Integration tests
├── requirements.txt     # Dependencies
├── tts/                 # TTS module
│   ├── __init__.py
│   ├── base.py          # Abstract TTS interface
│   ├── factory.py       # Provider factory
│   └── providers/       # TTS provider implementations
│       ├── unrealspeech.py
│       └── hume.py
├── templates/
│   └── index.html       # Web interface
└── unrealspeech_poc/    # Original Unreal Speech POC
```

## 🛠️ API Endpoints

### TTS Endpoints
- `GET /voices` - Get available voices for current provider
- `POST /synthesize` - Synthesize text to speech
- `POST /stream` - Stream TTS audio in real-time

### Provider Management
- `GET /tts/providers` - List all TTS providers and status
- `POST /tts/provider` - Switch TTS provider
- `POST /tts/test` - Test current TTS provider

### Chat & Documents
- `POST /chat` - Send message to GPT
- `POST /system-prompt` - Set system prompt
- `POST /documents` - Upload knowledge base document
- `GET /documents` - List uploaded documents
- `DELETE /documents/<name>` - Delete document

## 🧪 Testing

### Integration Tests
```bash
python test_integration.py
```

Tests:
- ✅ Provider configuration
- ✅ TTS provider creation
- ✅ Audio synthesis
- ✅ Voice availability

### Manual Testing
1. Open web interface
2. Try different voices
3. Switch between providers
4. Test conversation flow
5. Upload documents and test knowledge integration

## 🔄 Migration from Original System

The new modular system maintains backward compatibility while adding:

### What's New
- ✅ Provider switching without restart
- ✅ Streaming TTS with Unreal Speech
- ✅ 30x cost reduction option
- ✅ Better error handling
- ✅ Provider status monitoring

### What's Preserved
- ✅ All existing conversation features
- ✅ Document upload functionality
- ✅ Speech recognition
- ✅ Same web interface
- ✅ System prompt management

## 📊 Performance Metrics

### Unreal Speech Benefits
- **Latency**: 300ms vs 500ms+ (Hume)
- **Cost**: $8/1M chars vs $240/1M chars
- **Voices**: 48 professional voices
- **Languages**: 8 languages supported
- **Streaming**: True chunked streaming

### Expected Monthly Savings
For 10M characters/month:
- **Unreal Speech**: $80
- **Hume AI**: $2,400
- **Monthly Savings**: $2,320
- **Annual Savings**: $27,840

## 🐛 Troubleshooting

### Common Issues

#### TTS Provider Not Initialized
```
Error: TTS provider not initialized
```
**Solution**: Check API keys and run `python test_integration.py`

#### Voice Not Available
```
Error: No voice specified
```
**Solution**: Select a voice in the web interface settings

#### Streaming Issues
```
Error: Streaming failed
```
**Solution**: Ensure provider supports streaming (Unreal Speech recommended)

### Debug Commands
```bash
# Test provider status
python -c "from config import Config; print(Config.get_provider_status())"

# Test voice loading
python -c "from tts import TTSFactory; from config import Config; provider = TTSFactory.create_provider(**Config.get_tts_config()); print(len(provider.get_voices()))"

# Check API connectivity
python test_integration.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section
2. Run `python test_integration.py`
3. Review API key configuration
4. Check server logs for detailed errors

For Unreal Speech API issues, refer to their documentation: https://docs.unrealspeech.com
