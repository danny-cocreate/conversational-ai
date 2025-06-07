from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, send_file, jsonify, Response
import os
import base64
import tempfile
import json
import time
import requests

from flask_cors import CORS
from config import Config
from tts import TTSFactory, TTSProvider
from tts.text_chunker import SmartTextChunker
# Import core components and helpers from the simplified slide module
from slide_module_simplified import (
    setup_slide_system,
    UserAuthManager, get_user_auth_manager, get_slide_content, LessonManager, LessonCoachingManager,
    get_slide_controller, get_voice_interaction,
    DATABASE_AVAILABLE # Import DATABASE_AVAILABLE as it's used in app.py
)
import logging
from database import db, init_db
from models import TTSSettings, TokenSettings

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Flask app for admin
app.secret_key = 'your-secret-key-change-in-production'  # Needed for flash messages
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Initialize the guidance-based slide system with database enabled
setup_slide_system(app, enable_database=True)

# Register admin interface
try:
    from admin import init_admin_routes
    admin_success = init_admin_routes(app)
    if admin_success:
        print("🔧 Admin interface registered successfully")
        print("    📊 Access admin: http://localhost:5001/admin")
        print("    🔑 Default password: admin123")
    else:
        print("⚠️ Admin interface registration failed")
except Exception as admin_error:
    print(f"⚠️ Admin interface not available: {admin_error}")
    print("    💡 Admin features require database to be enabled")

# Set up environment variables from config
os.environ["HUME_API_KEY"] = Config.HUME_API_KEY
os.environ["OPENAI_API_KEY"] = Config.OPENAI_API_KEY
if Config.UNREALSPEECH_API_KEY:
    os.environ["UNREALSPEECH_API_KEY"] = Config.UNREALSPEECH_API_KEY

# Initialize TTS provider and other components
tts_provider: TTSProvider = None


# Initialize global instances
slide_controller = get_slide_controller()
voice_interaction = get_voice_interaction()
slide_content = get_slide_content()



# Dictionary to store lesson managers by lesson ID
lesson_managers = {}

def get_lesson_manager(lesson_id: str) -> LessonCoachingManager:
    """Get or create a LessonCoachingManager instance for a lesson"""
    if lesson_id not in lesson_managers:
        lesson_managers[lesson_id] = LessonCoachingManager(lesson_id)
    return lesson_managers[lesson_id]

def initialize_tts_provider():
    """
    Robust TTS provider initialization with comprehensive error handling
    """
    global tts_provider
    
    # Clear any existing provider
    tts_provider = None
    
    print("🔧 Initializing TTS provider...")
    
    # Step 1: Check and import dependencies
    try:
        import requests
        import aiohttp
        import asyncio
        print("   ✅ Dependencies available")
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        print("   💡 Install with: pip install requests aiohttp")
        return False
    
    # Step 2: Import TTS modules with specific error handling
    try:
        from config import Config
        print("   ✅ Config imported")
    except Exception as e:
        print(f"   ❌ Config import failed: {e}")
        return False
    
    try:
        from tts.factory import TTSFactory
        print("   ✅ TTSFactory imported")
    except Exception as e:
        print(f"   ❌ TTSFactory import failed: {e}")
        return False
    
    # Step 3: Get TTS configuration
    try:
        tts_config = Config.get_tts_config()
        provider_name = tts_config.get("provider", "unknown")
        has_api_key = bool(tts_config.get("api_key"))
        
        print(f"   📋 Provider: {provider_name}")
        print(f"   🔑 API Key: {'SET' if has_api_key else 'NOT SET'}")
        
        if not has_api_key:
            print("   ❌ No API key found in configuration")
            return False
            
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False
    
    # Step 4: Create TTS provider with retry logic
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"   🔄 Attempt {attempt + 1}/{max_retries} to create {provider_name} provider...")
            
            tts_provider = TTSFactory.create_provider(
                tts_config["provider"], 
                tts_config
            )
            
            # Validate the provider works
            try:
                voices = tts_provider.get_voices()
                voice_count = len(voices) if voices else 0
                print(f"   ✅ Provider created successfully with {voice_count} voices")
                
                # Quick validation test
                is_valid, msg = tts_provider.validate_text("Test")
                if is_valid:
                    print("   ✅ Provider validation passed")
                    return True
                else:
                    print(f"   ⚠️  Provider validation warning: {msg}")
                    return True  # Still usable
                    
            except Exception as validation_error:
                print(f"   ⚠️  Provider created but validation failed: {validation_error}")
                return True  # Provider exists, validation issues can be handled later
                
        except ImportError as e:
            missing_dep = str(e).split("'")[1] if "'" in str(e) else str(e)
            print(f"   ❌ Import error on attempt {attempt + 1}: Missing {missing_dep}")
            if attempt == max_retries - 1:
                print(f"   💡 Install missing dependency: pip install {missing_dep}")
                return False
                
        except Exception as e:
            print(f"   ❌ Provider creation failed on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                print("   💥 All attempts failed")
                import traceback
                traceback.print_exc()
                return False
    
    return False

# Initialize TTS provider on startup
if not initialize_tts_provider():
    print("⚠️  TTS provider initialization failed, some features may not work")

# Create demo user for testing
try:
    auth_manager = get_user_auth_manager()
    demo_result = auth_manager.register_user(
        email="demo@example.com",
        password="demo123",
        first_name="Demo",
        last_name="User"
    )
    if demo_result['success']:
        print("📝 Demo user created: demo@example.com / demo123")
    else:
        print("📝 Demo user already exists")
except Exception as e:
    print(f"⚠️ Demo user creation failed: {e}")

@app.route('/login')
def login_page():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/')
def index():
    # Fetch only published lessons
    lesson_manager = LessonManager()
    lessons = lesson_manager.list_lessons(published_only=True)
    return render_template('index.html', lessons=lessons)

@app.route('/test-chunking')
def test_chunking_page():
    """Serve the auto-chunking test page"""
    return send_file('test_auto_chunking.html')

@app.route('/test-progressive')
def test_progressive_page():
    """Serve the progressive audio test page"""
    return send_file('test_progressive_audio.html')

@app.route('/system-prompt', methods=['POST'])
def set_system_prompt():
    """Set the system prompt for the lesson manager"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        # lesson_id is still needed for context in the frontend, but not for setting the base prompt here
        # lesson_id = data.get('lesson_id')

        if not prompt:
            return jsonify({'error': 'Missing prompt'}), 400

        # Get the centralized SystemPromptManager
        from slide_module_simplified.system_prompt_manager import get_system_prompt_manager
        prompt_manager = get_system_prompt_manager()

        # Set the base prompt using the SystemPromptManager
        prompt_manager.set_base_prompt(prompt)

        return jsonify({'success': True, 'prompt_length': len(prompt)})
    except Exception as e:
        logger.error(f"Error setting system prompt: {e}")
        return jsonify({'error': str(e)}), 500

# Document upload endpoints removed - using only database lessons as knowledge base



def get_authenticated_user_id(request):
    """Get authenticated user ID from request headers"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        auth_manager = get_user_auth_manager()
        return auth_manager.verify_token(token)
    except Exception:
        return None

@app.route('/stream', methods=['POST', 'OPTIONS'])
def stream_synthesize():
    """Ultra-robust streaming TTS endpoint with comprehensive error handling"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    print("🎙️ === STREAM TTS REQUEST RECEIVED ===")
    
    if not tts_provider:
        print("❌ ERROR: TTS provider not initialized")
        return jsonify({'error': 'TTS provider not initialized'}), 500

    try:
        # Step 1: Parse request data with fallbacks
        print("📥 Step 1: Parsing request data...")
        
        if request.is_json:
            data = request.json or {}
        else:
            data = request.form.to_dict()
        
        print(f"   Raw data: {data}")
        
        # Extract parameters with robust defaults
        text = str(data.get('text', '')).strip()
        voice_id = str(data.get('voice_id', '')).strip()
        speed = str(data.get('speed', '1.0')).strip()
        temperature = str(data.get('temperature', '0.25')).strip()
        pitch = str(data.get('pitch', '1.0')).strip()
        
        print(f"   Parsed - Text: '{text[:50]}...', Voice: '{voice_id}', Speed: '{speed}', Temperature: '{temperature}', Pitch: '{pitch}'")
        
        # Step 2: Validate required parameters
        print("✅ Step 2: Validating parameters...")
        
        if not text:
            print("❌ ERROR: Missing or empty text")
            return jsonify({'error': 'Text is required and cannot be empty'}), 400
        
        if not voice_id:
            print("❌ ERROR: Missing or empty voice_id")
            # Try to use a default voice as fallback
            voices = tts_provider.get_voices()
            if voices:
                voice_id = voices[0]['id']
                print(f"🔄 Using default voice: {voice_id}")
            else:
                return jsonify({'error': 'Voice ID is required and no default available'}), 400
        
        # Step 3: Validate text with provider
        print("📝 Step 3: Validating text with TTS provider...")
        is_valid, error_msg = tts_provider.validate_text(text)
        if not is_valid:
            print(f"❌ Text validation failed: {error_msg}")
            return jsonify({'error': f'Text validation failed: {error_msg}'}), 400
        
        print("✅ Text validation passed")
        
        # Step 4: Handle speed conversion for UnrealSpeech
        print("🔢 Step 4: Processing speed parameter...")
        original_speed = speed
        
        try:
            speed_float = float(speed)
            if Config.TTS_PROVIDER == "unrealspeech":
                # Convert frontend speed (0.5-2.0) to UnrealSpeech range (-0.5 to 1.0)
                converted_speed = speed_float - 1.0
                speed = str(converted_speed)
                print(f"   UnrealSpeech speed conversion: {original_speed} -> {speed}")
            else:
                print(f"   Using original speed: {speed}")
        except ValueError:
            print(f"❌ Invalid speed value: {speed}, using default 1.0")
            speed = "0.0" if Config.TTS_PROVIDER == "unrealspeech" else "1.0"
        
        # Step 5: Generate streaming audio
        print("🌊 Step 5: Starting audio generation...")
        
        def generate_audio_stream():
            """Robust audio generation with error handling"""
            try:
                print(f"🎵 Calling TTS provider stream_sync_generator...")
                print(f"   Provider: {type(tts_provider).__name__}")
                print(f"   Text length: {len(text)} chars")
                print(f"   Voice: {voice_id}")
                print(f"   Speed: {speed}")
                
                chunk_count = 0
                total_bytes = 0
                
                for chunk in tts_provider.stream_sync_generator(
                    text=text,
                    voice_id=voice_id,
                    speed=speed,
                    temperature=temperature,
                    pitch=pitch
                ):
                    if chunk:
                        chunk_count += 1
                        total_bytes += len(chunk)
                        if chunk_count == 1:
                            print(f"⚡ First chunk received: {len(chunk)} bytes")
                        # Reduced logging - only log every 20 chunks instead of every 10
                        elif chunk_count % 20 == 0 and chunk_count <= 100:
                            print(f"📊 Progress: {chunk_count} chunks, {total_bytes} bytes")
                        yield chunk
                
                print(f"✅ Audio generation complete: {chunk_count} chunks, {total_bytes} total bytes")
                
            except Exception as stream_error:
                print(f"❌ STREAMING ERROR: {stream_error}")
                import traceback
                traceback.print_exc()
                
                # Try to yield at least some error indication
                error_message = f"Audio generation failed: {str(stream_error)}"
                print(f"🔄 Attempting fallback for: {error_message}")
                yield b''  # Empty chunk to indicate end
        
        # Step 6: Create and return streaming response
        print("📤 Step 6: Creating streaming response...")
        
        response = Response(
            generate_audio_stream(),
            mimetype='audio/mpeg',
            direct_passthrough=True
        )
        
        # Set comprehensive headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Transfer-Encoding'] = 'chunked'
        response.headers['X-Accel-Buffering'] = 'no'
        response.headers['X-TTS-Provider'] = Config.TTS_PROVIDER
        response.headers['X-Original-Speed'] = original_speed
        response.headers['X-Converted-Speed'] = speed
        response.headers['X-Voice-ID'] = voice_id
        response.headers['X-Text-Length'] = str(len(text))
        response.headers['X-Temperature'] = temperature
        response.headers['X-Pitch'] = pitch
        
        print("🚀 Returning streaming response with all headers set")
        return response
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR in stream_synthesize: {e}")
        import traceback
        traceback.print_exc()
        
        # Return detailed error for debugging
        error_info = {
            'error': str(e),
            'type': type(e).__name__,
            'provider': Config.TTS_PROVIDER if tts_provider else 'None',
            'request_data': str(request.get_json() if request.is_json else request.form.to_dict())
        }
        
        return jsonify(error_info), 500

@app.route('/stream-chunked', methods=['POST', 'OPTIONS'])
def stream_chunked_synthesize():
    """Chunked streaming TTS endpoint for long texts"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        text = data.get('text', '')
        # Enforce consistent voice - use custom ID as default
        DEFAULT_CUSTOM_VOICE_ID = 'ee966436-01ab-4810-a880-9e0a532e03b8'
        voice_id = data.get('voice_id', DEFAULT_CUSTOM_VOICE_ID)
        
        # Get TTS provider to check valid voices
        # Initialize TTS provider
        # Use the globally initialized tts_provider
        global tts_provider
        if not tts_provider:
            print("❌ ERROR: TTS provider not initialized for /stream-chunked")
            return jsonify({'error': 'TTS provider not initialized'}), 500

        # Check if the provided voice_id is in the list of known voices OR is the new default custom voice
        # Only check if tts_provider is successfully initialized
        valid_voices = [v['id'] for v in tts_provider.get_voices()] + [DEFAULT_CUSTOM_VOICE_ID]
        
        if voice_id not in valid_voices:
            voice_id = DEFAULT_CUSTOM_VOICE_ID
            print(f"⚠️ Using default custom voice: {voice_id}")
            
        speed = data.get('speed', '1.0')
        temperature = data.get('temperature', '0.75')
        pitch = data.get('pitch', '1.0')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Get text chunks
        chunker = SmartTextChunker(max_chunk_size=995) # Ensure chunker is initialized if needed
        text_chunks = chunker.chunk_text(text)
        chunk_info = {
            'total_chunks': len(text_chunks),
            'original_length': len(text),
            'chunks': [{
                'index': chunk.index,
                'length': len(chunk.text),
                'is_final': chunk.is_final
            } for chunk in text_chunks]
        }
        
        print(f"📊 Chunking info: {json.dumps(chunk_info, indent=2)}")
        
        # Convert speed for Unreal Speech (keep this logic)
        if Config.TTS_PROVIDER == "unrealspeech":
            speed_float = float(speed)
            # Unreal Speech uses -1 to 1 scale, where 0 is normal speed
            # Frontend sends 0.5-2.0, we need to convert to -0.5 to 1.0
            speed = str(speed_float - 1.0)  # 1.0 -> 0, 1.5 -> 0.5, 0.5 -> -0.5
        
        def generate_chunked():
            """Generator that yields audio from all chunks sequentially"""
            try:
                for i, chunk in enumerate(text_chunks):
                    print(f"🎵 Processing chunk {i+1}/{len(text_chunks)}: '{chunk.text[:30]}...'")
                    
                    # Generate audio for this chunk
                    # Pass emotional_parameters from the request if available
                    emotional_parameters = data.get('emotional_parameters', {})
                    
                    chunk_generator = tts_provider.stream_sync_generator(
                        text=chunk.text,
                        voice_id=voice_id,  # Use consistent voice
                        speed=speed,
                        temperature=temperature,
                        pitch=pitch,
                        emotional_parameters=emotional_parameters # Pass emotional parameters
                    )
                    
                    # Yield all audio data from this chunk
                    for audio_chunk in chunk_generator:
                        if audio_chunk:
                            # Add logging for chunk size
                            print(f"      -> Yielding audio chunk: {len(audio_chunk)} bytes")
                            yield audio_chunk
                    
                    print(f"✅ Completed chunk {i+1}/{len(text_chunks)}")
                    
            except Exception as e:
                print(f"❌ Chunked streaming error: {e}")
                yield b''
        
        # Return streaming response with proper headers
        return Response(
            generate_chunked(),
            mimetype='audio/mpeg',
            headers={
                'Content-Type': 'audio/mpeg',
                'Cache-Control': 'no-cache, no-transform',
                'Transfer-Encoding': 'chunked',
                'X-Accel-Buffering': 'no',  # Disable nginx buffering
                'X-Content-Type-Options': 'nosniff',
                'Connection': 'keep-alive',
                'Keep-Alive': 'timeout=60',
                'X-Voice-ID': voice_id,  # Add voice ID to headers for tracking
                'Accept-Ranges': 'none' # Explicitly disable range requests
            }
        )
        
    except Exception as e:
        print(f"❌ Error in stream_chunked_synthesize: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug-current-audio', methods=['POST', 'OPTIONS'])
def debug_current_audio():
    """Debug endpoint for TTS testing"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if not tts_provider:
        return jsonify({'error': 'TTS provider not initialized'}), 500

    try:
        # Parse request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        text = request.json.get('text', 'Debug test')
        voice_id = request.json.get('voice_id', 'af_sky')
        speed = request.json.get('speed', '1.0')
        
        print(f'🔍 Debug TTS request: {text[:50]}...')
        
        # Validate and synthesize
        is_valid, error_msg = tts_provider.validate_text(text)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Synthesize audio
        audio_bytes = tts_provider.synthesize_sync(
            text=text,
            voice_id=voice_id,
            speed=speed
        )
        
        # Return debug info and audio
        debug_info = {
            'provider': Config.TTS_PROVIDER,
            'text_length': len(text),
            'audio_size': len(audio_bytes),
            'voice_id': voice_id,
            'speed': speed
        }
        
        response = Response(
            audio_bytes,
            mimetype='audio/mpeg'
        )
        response.headers['X-Debug-Info'] = str(debug_info)
        response.headers['Content-Disposition'] = 'attachment; filename="debug-audio.mp3"'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['X-TTS-Provider'] = Config.TTS_PROVIDER
        
        return response

    except Exception as e:
        print(f'❌ Debug Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/voices', methods=['GET'])
def get_voices():
    try:
        if not tts_provider:
            return jsonify({"error": "TTS provider not initialized"}), 500
        
        voices = tts_provider.get_voices()
        return jsonify({"voices_page": voices})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/synthesize', methods=['POST', 'OPTIONS'])
def synthesize():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    if not tts_provider:
        return jsonify({'error': 'TTS provider not initialized'}), 500

    try:
        # Get parameters from request (support both form and JSON)
        if request.is_json:
            data = request.json
            text = data.get('text', '')
            voice_id = data.get('voice_id', '')
            speed = data.get('speed', '1.0')
            temperature = data.get('temperature', '0.25')
            pitch = data.get('pitch', '1.0')
        else:
            text = request.form.get('text', '')
            voice_id = request.form.get('voice_id', '')
            speed = request.form.get('speed', '1.0')
            temperature = request.form.get('temperature', '0.25')
            pitch = request.form.get('pitch', '1.0')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        if not voice_id:
            return jsonify({'error': 'No voice specified'}), 400

        print(f"🎙️ Synthesizing with {Config.TTS_PROVIDER}: '{text[:50]}...'")
        
        # Validate text
        is_valid, error_msg = tts_provider.validate_text(text)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Convert speed for different providers
        if Config.TTS_PROVIDER == "unrealspeech":
            # Unreal Speech uses -1 to 1 scale
            speed_float = float(speed)
            if speed_float >= 1.0:
                speed = str(speed_float - 1.0)  # 1.0 -> 0, 1.5 -> 0.5
            else:
                speed = str(speed_float - 1.0)  # 0.8 -> -0.2
        
        # Synthesize audio
        audio_data = tts_provider.synthesize_sync(
            text=text,
            voice_id=voice_id,
            speed=speed,
            temperature=temperature,
            pitch=pitch
        )
        
        print(f"✅ Generated {len(audio_data)} bytes of audio")
        
        # Create response
        response = Response(
            audio_data,
            mimetype='audio/mpeg'
        )
        
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['X-TTS-Provider'] = Config.TTS_PROVIDER
        
        return response

    except Exception as e:
        print(f"❌ TTS Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# New TTS Management Endpoints
@app.route('/tts/providers', methods=['GET'])
def get_tts_providers():
    """Get information about available TTS providers"""
    try:
        providers = {}
        for provider_name in TTSFactory.get_available_providers():
            providers[provider_name] = TTSFactory.get_provider_info(provider_name)
        
        status = Config.get_provider_status()
        
        return jsonify({
            'current_provider': status['current_provider'],
            'providers': providers,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/provider', methods=['POST'])
def switch_tts_provider():
    """Switch TTS provider"""
    try:
        data = request.json
        provider_name = data.get('provider')
        
        if not provider_name:
            return jsonify({'error': 'Provider name required'}), 400
        
        # Switch provider in config
        Config.switch_tts_provider(provider_name)
        
        # Reinitialize TTS provider
        if initialize_tts_provider():
            return jsonify({
                'status': 'success',
                'provider': provider_name,
                'message': f'Switched to {provider_name}'
            })
        else:
            return jsonify({
                'error': f'Failed to initialize {provider_name} provider'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/test', methods=['POST'])
def test_tts_provider():
    """Test current TTS provider with sample text"""
    try:
        if not tts_provider:
            return jsonify({'error': 'TTS provider not initialized'}), 500
        
        data = request.json or {}
        test_text = data.get('text', 'Hello, this is a test of the TTS system.')
        voice_id = data.get('voice_id', tts_provider.get_voices()[0]['id'])
        
        # Validate and synthesize
        is_valid, error_msg = tts_provider.validate_text(test_text)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        audio_bytes = tts_provider.synthesize_sync(
            text=test_text,
            voice_id=voice_id
        )
        
        return jsonify({
            'status': 'success',
            'provider': Config.TTS_PROVIDER,
            'audio_size': len(audio_bytes),
            'test_text': test_text,
            'voice_id': voice_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chunk-preview', methods=['POST'])
def preview_text_chunking():
    """Preview how text would be chunked for TTS"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        text = request.json.get('text', '')
        max_chunk_size = request.json.get('max_chunk_size', 995)
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Initialize chunker and get preview
        chunker = SmartTextChunker(max_chunk_size=max_chunk_size)
        chunking_info = chunker.get_chunking_info(text)
        
        return jsonify({
            'status': 'success',
            'needs_chunking': len(text) > max_chunk_size,
            'chunking_info': chunking_info
        })
        
    except Exception as e:
        print(f'❌ Chunk Preview Error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/slide-changed', methods=['POST'])
def slide_changed():
    """Handle slide change notification"""
    try:
        data = request.get_json()
        new_slide = data.get('slide_number', 0)
        lesson_id = data.get('lesson_id', 'ai-ux-design')
        
        # Update lesson manager with new slide
        lesson_manager = get_lesson_manager(lesson_id)
        lesson_manager.coaching_context.slide_number = new_slide
        
        return jsonify({
            'success': True,
            'message': f'Slide changed to {new_slide}',
            'slide_info': slide_controller.get_navigation_info()
        })
    except Exception as e:
        print(f"❌ Slide change error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/slides/manual-navigation', methods=['POST'])
def manual_slide_navigation():
    """
    Handle manual slide navigation when user clicks UI buttons
    This updates the guidance system's slide state
    """
    try:
        from slide_module_simplified import get_slide_controller
        
        data = request.get_json()
        action = data.get('action')
        slide_number = data.get('slide_number')
        
        slide_controller = get_slide_controller()
        
        # Execute the manual navigation
        if action == 'next':
            result = slide_controller.manual_next()
        elif action == 'previous':
            result = slide_controller.manual_previous()
        elif action == 'goto' and slide_number is not None:
            result = slide_controller.manual_goto(slide_number)
        else:
            return jsonify({
                "error": "Invalid navigation action",
                "valid_actions": ["next", "previous", "goto"]
            }), 400
        
        # Update coaching context and get response with enhanced memory
        if result['success']:
            if DATABASE_AVAILABLE:
                coaching_result = on_manual_navigation_enhanced(result['current_slide'])
                print("🧠 Enhanced manual navigation with persistent memory")
            else:
                coaching_result = on_manual_navigation(result['current_slide'])
                print("📚 Basic manual navigation")
            result['coaching_response'] = coaching_result['coaching_response']
            result['guidance_system'] = True
            result['enhanced_memory'] = DATABASE_AVAILABLE
        
        return jsonify(result)
    
    except Exception as e:
        print(f"❌ Manual navigation error: {e}")
        return jsonify({
            "error": "Manual navigation failed",
            "details": str(e)
        }), 500

@app.route('/slides/guidance-status', methods=['GET'])
def get_guidance_status():
    """
    Get current status of the guidance-based slide system
    """
    try:
        from slide_module_simplified import get_slide_controller, get_coaching_context
        
        slide_controller = get_slide_controller()
        nav_info = slide_controller.get_navigation_info()
        coaching_context = get_coaching_context()
        
        return jsonify({
            'guidance_system': True,
            'slide_info': nav_info,
            'coaching_context': coaching_context,
            'system_type': 'guidance_based',
            'ai_controls_slides': False,
            'user_controls_slides': True,
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Guidance status error: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/slide-content/<int:slide_number>', methods=['GET'])
def get_slide_content_endpoint(slide_number):
    """
    Get content for a specific slide (for frontend display)
    """
    try:
        # Use the guidance system's slide content module
        from slide_module_simplified import get_slide_content
        
        slide_content_module = get_slide_content()
        content_data = slide_content_module.get_slide_content(slide_number)
        
        return jsonify({
            'slide_number': slide_number,
            'slide_number_human': slide_number + 1,
            'content_data': content_data,
            'guidance_system': True,
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Get slide content error: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

# ========================================
# AUTHENTICATION ENDPOINTS
# ========================================

@app.route('/auth/register', methods=['POST', 'OPTIONS'])
def register():
    """Register a new user"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Register user
        auth_manager = get_user_auth_manager()
        result = auth_manager.register_user(
            email=email,
            password=password,
            first_name=first_name or None,
            last_name=last_name or None
        )

        if result['success']:
            print(f"🎆 New user registered: {email}")
            return jsonify({
                'success': True,
                'message': 'Registration successful',
                'user_id': result['user_id']
            })
        else:
            return jsonify({'error': result['error']}), 400

    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Authenticate user login"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Authenticate user
        auth_manager = get_user_auth_manager()
        result = auth_manager.authenticate_user(email, password)

        if result['success']:
            print(f"✅ User authenticated: {email}")
            return jsonify({
                'success': True,
                'token': result['token'],
                'user': result['user'],
                'user_id': result['user_id']
            })
        else:
            return jsonify({'error': result['error']}), 401

    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/auth/profile', methods=['GET', 'OPTIONS'])
def get_profile():
    """Get user profile (requires authentication)"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401

        token = auth_header.split(' ')[1]
        auth_manager = get_user_auth_manager()
        user_id = auth_manager.verify_token(token)

        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get user profile
        profile = auth_manager.get_user_profile(user_id)
        if profile:
            return jsonify({
                'success': True,
                'profile': profile
            })
        else:
            return jsonify({'error': 'Profile not found'}), 404

    except Exception as e:
        print(f"❌ Profile error: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@app.route('/auth/profile', methods=['PUT', 'OPTIONS'])
def update_profile():
    """Update user profile (requires authentication)"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401

        token = auth_header.split(' ')[1]
        auth_manager = get_user_auth_manager()
        user_id = auth_manager.verify_token(token)

        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Get update data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No update data provided'}), 400

        # Update profile
        success = auth_manager.update_user_profile(user_id, data)
        if success:
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
        else:
            return jsonify({'error': 'Profile update failed'}), 500

    except Exception as e:
        print(f"❌ Profile update error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@app.route('/auth/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Logout user (invalidate token)"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    try:
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401

        token = auth_header.split(' ')[1]
        auth_manager = get_user_auth_manager()
        
        # Logout user (invalidate token)
        success = auth_manager.logout_user(token)
        if success:
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            })
        else:
            return jsonify({'error': 'Logout failed'}), 500

    except Exception as e:
        print(f"❌ Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/start-enhanced-session', methods=['POST', 'OPTIONS'])
def start_enhanced_session_endpoint():
    """Start an enhanced session with persistent memory (requires authentication)"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    try:
        # Enhanced coaching (persistent memory) requires the database
        if not DATABASE_AVAILABLE:
            return jsonify({
                'error': 'Enhanced coaching not available', # More specific error message
                'details': 'Database connection not established.'
            }), 500 # Changed to 500 as it's a server-side dependency issue

        # Import start_enhanced_session only if database is available
        try:
            from slide_module_simplified.database import start_enhanced_session
        except ImportError:
             return jsonify({
                'error': 'Enhanced coaching not available', # Should not happen if DATABASE_AVAILABLE is true, but as a safeguard
                'details': 'Required database functions not found.'
            }), 500

        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401

        token = auth_header.split(' ')[1]
        auth_manager = get_user_auth_manager()
        user_id = auth_manager.verify_token(token)

        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401

        data = request.get_json() or {}
        lesson_id = data.get('lesson_id', 'wireframing-wth-ai')
        existing_session_id = data.get('session_id')
        
        # Start enhanced session for authenticated user
        session_id = start_enhanced_session(
            user_id=user_id,
            lesson_id=lesson_id,
            session_id=existing_session_id
        )
        
        if session_id:
            # Get user profile for response
            profile = auth_manager.get_user_profile(user_id)
            user_name = profile.get('first_name') if profile else 'User'
            
            print(f"🎆 Enhanced session started: {session_id[:8]}... for {user_name} ({user_id[:8]}...) on lesson {lesson_id}")
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'user_id': user_id,
                'lesson_id': lesson_id,
                'enhanced_memory': True,
                'message': f'Enhanced session started for {user_name}!'
            })
        else:
            return jsonify({
                'error': 'Failed to start enhanced session',
                'details': 'Could not create or retrieve session from database.'
            }), 500 # Changed to 500 as it's a database/backend issue
            
    except Exception as e:
        print(f"❌ Enhanced session error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'enhanced_session': False,
            'details': 'An unexpected error occurred on the server.'
        }), 500 # Ensure server errors return 500

@app.route('/reset-conversation', methods=['POST', 'OPTIONS'])
def reset_conversation():
    """Reset conversation state to clear any stuck states after interruption"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        # Clear any potential stuck states
        # Note: Add any conversation state clearing logic here if needed
        
        print("🔄 Conversation state reset requested")
        
        return jsonify({
            'status': 'success',
            'message': 'Conversation state reset successfully'
        })
        
    except Exception as e:
        print(f"❌ Reset conversation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/tts/debug', methods=['GET'])
def debug_tts():
    """Debug endpoint to check TTS status"""
    try:
        if not tts_provider:
            return jsonify({
                'status': 'error',
                'message': 'TTS provider not initialized',
                'provider': None
            }), 500
        
        from config import Config
        voices = tts_provider.get_voices()
        
        return jsonify({
            'status': 'success',
            'provider': Config.TTS_PROVIDER,
            'provider_type': type(tts_provider).__name__,
            'voice_count': len(voices) if voices else 0,
            'api_key_set': bool(Config.UNREALSPEECH_API_KEY),
            'voices_sample': voices[:3] if voices else []
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'provider': type(tts_provider).__name__ if tts_provider else None
        }), 500


# NEW DEBUGGING ENDPOINTS FOR SYSTEM PROMPT & KNOWLEDGE BASE

@app.route('/knowledge-base/status', methods=['GET'])
def get_knowledge_base_status():
    """Get the status of the knowledge base for a specific lesson (database-based)"""
    try:
        lesson_id = request.args.get('lesson_id')
        if not lesson_id:
            return jsonify({'error': 'Missing lesson_id'}), 400

        # Use the lesson manager to get knowledge base status from database
        lesson_manager = get_lesson_manager(lesson_id)
        status = {
            'lesson_id': lesson_id,
            'content_source': 'database',
            'total_slides': len(lesson_manager.lesson_manager.get_lesson_slides(lesson_id)),
            'lesson_exists': lesson_manager.lesson_manager.get_lesson(lesson_id) is not None
        }
        logger.info(f"✅ Retrieved database-based knowledge base status for lesson {lesson_id}")

        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Error getting knowledge base status for lesson {lesson_id}: {e}")
        return jsonify({'error': f'Failed to get knowledge base status: {str(e)}'}), 500

@app.route('/knowledge-base/refresh', methods=['POST'])
def refresh_knowledge_base():
    """Refresh the knowledge base"""
    try:
        lesson_id = request.json.get('lesson_id')
        if not lesson_id:
            return jsonify({'error': 'Missing lesson_id'}), 400
            
        lesson_manager = get_lesson_manager(lesson_id)
        lesson_manager.refresh_knowledge_base()
        
        return jsonify({
            'success': True,
            'message': 'Knowledge base refreshed successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/conversation-state', methods=['GET'])
def debug_conversation_state():
    """Get the current state of the conversation"""
    try:
        lesson_id = request.args.get('lesson_id')
        if not lesson_id:
            return jsonify({'error': 'Missing lesson_id'}), 400
            
        lesson_manager = get_lesson_manager(lesson_id)
        state = lesson_manager.get_conversation_state()
        
        return jsonify({
            'success': True,
            'state': state
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/slides/notify-change', methods=['POST'])
def notify_slide_change():
    """Notify frontend that slides have changed (for immediate sync)"""
    try:
        from slide_module.slide_controller import get_slide_controller
        
        # Get current slide state
        controller = get_slide_controller()
        current_state = controller.get_navigation_info()
        
        # This endpoint will be called by the chat interface after processing slide commands
        # The frontend can poll this or use it to trigger immediate updates
        
        print(f"📡 SLIDE CHANGE NOTIFICATION: Current slide {current_state['current_slide']}")
        
        return jsonify({
            'success': True,
            'message': 'Slide change notification sent',
            'current_state': current_state,
            'timestamp': time.time()
        })
        
    except Exception as e:
        print(f"❌ Slide change notification error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========================================
# EMERGENCY FALLBACK & DEBUG ENDPOINTS
# ========================================

@app.route('/chat-ultra-simple', methods=['POST', 'OPTIONS'])
def chat_ultra_simple():
    """EMERGENCY ULTRA-SIMPLE CHAT - bypasses ALL complex logic for debugging"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        # Get input
        if request.is_json:
            user_input = request.json.get('text', '')
        else:
            user_input = request.form.get('text', '')
            
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400
        
        print(f"🔧 ULTRA-SIMPLE: '{user_input[:30]}...'")
        
        # Ultra-simple slide detection
        if any(cmd in user_input.lower() for cmd in ['next slide', 'previous slide', 'go to slide']):
            print("🎬 Ultra-simple slide response")
            return jsonify({
                'response': 'Slide navigation completed.',
                'slide_command': True,
                'ultra_simple': True
            })
        
        # Ultra-simple conversation
        print("💬 Ultra-simple conversation response")
        return jsonify({
            'response': f"I understand you said: '{user_input}'. How can I help you?",
            'slide_command': False,
            'ultra_simple': True
        })
    
    except Exception as e:
        print(f"❌ Ultra-simple error: {e}")
        return jsonify({
            'response': 'Simple response mode active.',
            'error': str(e),
            'ultra_simple': True
        }), 200 # Return 200 even on error to avoid hangs

@app.route('/chat-fallback', methods=['POST', 'OPTIONS'])
def chat_fallback():
    """Ultra-simple fallback chat that bypasses all slide complexity"""
    if request.method == 'OPTIONS':
        response = Response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        # Handle both form data and JSON data
        if request.is_json:
            user_input = request.json.get('text', '')
        else:
            user_input = request.form.get('text', '')
            
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400
        
        print(f"🔧 Fallback chat: '{user_input[:50]}...'")
        
        # Try to use basic conversation manager without slide system
        try:
            from conversation import ConversationManager
            basic_manager = ConversationManager()
            response = basic_manager.get_response(user_input)
            
            return jsonify({
                'response': response,
                'fallback_mode': True,
                'message': 'Using basic conversation mode'
            })
            
        except Exception as conv_error:
            print(f"❌ Basic conversation error: {conv_error}")
            import traceback
            traceback.print_exc()
            
            # Ultimate fallback - hardcoded responses
            fallback_responses = {
                'hello': 'Hello! I\'m in emergency fallback mode. The slide system is temporarily disabled.',
                'hi': 'Hi there! I\'m running in simplified mode right now.',
                'start presentation': 'Presentation features are temporarily unavailable. I\'m in basic chat mode.',
                'next slide': 'Slide navigation is currently disabled. I\'m in fallback mode.',
                'help': 'I\'m running in emergency mode with limited functionality. You can still chat with me!'
            }
            
            # Simple keyword matching
            response = fallback_responses.get(
                user_input.lower().strip(),
                f"I heard you say '{user_input}'. I'm currently in emergency fallback mode with limited functionality."
            )
            
            return jsonify({
                'response': response,
                'fallback_mode': True,
                'emergency_mode': True,
                'message': 'Using hardcoded fallback responses',
                'original_error': str(conv_error)
            })
    
    except Exception as e:
        print(f"❌ Fallback chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'response': 'I apologize, but I\'m experiencing technical difficulties. Please try refreshing the page.',
            'error': str(e),
            'fallback_mode': True,
            'critical_error': True
        }), 500

@app.route('/lesson/<lesson_id>')
def lesson_page(lesson_id):
    """Serve lesson page for students - dynamic lesson URLs"""
    try:
        from slide_module_simplified import DATABASE_AVAILABLE, LessonManager
        
        if not DATABASE_AVAILABLE:
            return render_template('lesson_error.html', 
                                 error="Database not available", 
                                 lesson_id=lesson_id), 404
        
        # Get lesson from database
        lesson_manager = LessonManager()
        lesson = lesson_manager.get_lesson(lesson_id)
        
        if not lesson:
            return render_template('lesson_error.html', 
                                 error="Lesson not found", 
                                 lesson_id=lesson_id), 404
        
        if not lesson['is_published']:
            return render_template('lesson_error.html', 
                                 error="Lesson not published", 
                                 lesson_id=lesson_id), 404
        
        # Load lesson content for the slide system
        lesson_slides = lesson_manager.get_lesson_slides(lesson_id)
        
        # 🎯 CRITICAL FIX: Set the current lesson in the slide content system
        from slide_module_simplified import get_slide_content
        slide_content_module = get_slide_content()
        slide_content_module.set_current_lesson(lesson_id)
        print(f"✅ Set slide content lesson to: {lesson_id} on page load")
        
        # Render the lesson page with voice-enhanced dynamic content
        return render_template('lesson_voice_enhanced.html', 
                             lesson=lesson,
                             lesson_id=lesson_id,
                             slides=lesson_slides,
                             total_slides=len(lesson_slides))
        
    except Exception as e:
        print(f"❌ Lesson page error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('lesson_error.html', 
                             error=str(e), 
                             lesson_id=lesson_id), 500

@app.route('/lesson/<lesson_id>/chat', methods=['POST'])
def lesson_chat(lesson_id):
    """
    🎓 LESSON-SPECIFIC CHAT: Enhanced AI coaching with slide content awareness
    """
    try:
        # Handle both form data and JSON data
        if request.is_json:
            user_input = request.json.get('text', '')
            current_slide = request.json.get('current_slide', 0)
            slide_title = request.json.get('slide_title', '')
            conversation_history = request.json.get('conversation_history', [])  # NEW: Get conversation history
        else:
            user_input = request.form.get('text', '')
            current_slide = int(request.form.get('current_slide', 0))
            slide_title = request.form.get('slide_title', '')
            # For form data, try to parse conversation history from JSON string
            try:
                conversation_history = json.loads(request.form.get('conversation_history', '[]'))
            except:
                conversation_history = []

        if not user_input:
            return jsonify({'error': 'No input provided'}), 400

        print(f"🎓 Lesson chat [{lesson_id}]: '{user_input[:50]}...' | Slide {current_slide + 1}")
        print(f"📚 Conversation history: {len(conversation_history)} messages")

        # 👋 SPECIAL HANDLING: Check for greeting trigger
        if user_input == "START_AI_COACH_GREETING" or request.json.get('is_greeting_trigger'):
            print("👋 Handling lesson greeting trigger")
            
            try:
                from slide_module_simplified import LessonCoachingManager
                lesson_manager = LessonCoachingManager(lesson_id)
                
                # Generate a personalized greeting for the lesson
                greeting_response = lesson_manager.generate_lesson_greeting(
                    current_slide=current_slide,
                    lesson_context=request.json.get('lesson_context', {})
                )
                
                return jsonify({
                    'response': greeting_response,
                    'slide_command': False,
                    'lesson_conversation': True,
                    'lesson_mode': True,
                    'lesson_id': lesson_id,
                    'current_slide': current_slide,
                    'greeting': True,
                    'coaching_used': True
                })
                
            except Exception as greeting_error:
                print(f"❌ Greeting generation error: {greeting_error}")
                # Fallback greeting
                fallback_greeting = f"Welcome to this lesson! I'm your AI coach and I'm here to help you learn. We're starting with slide {current_slide + 1}. Feel free to ask me questions about anything you see here!"
                
                return jsonify({
                    'response': fallback_greeting,
                    'slide_command': False,
                    'lesson_conversation': True,
                    'lesson_mode': True,
                    'lesson_id': lesson_id,
                    'current_slide': current_slide,
                    'greeting': True,
                    'fallback_greeting': True
                })

        try:
            # Use the new LessonCoachingManager
            from slide_module_simplified import LessonCoachingManager
            
            # Get or create a lesson manager for this lesson
            lesson_manager = LessonCoachingManager(lesson_id)
            
            # Process user input through lesson manager with conversation history
            result = lesson_manager.process_user_input(
                user_input, 
                current_slide,
                conversation_history=conversation_history  # NEW: Pass conversation history
            )
            
            return jsonify({
                'response': result['coaching_response'],
                'slide_command': False,
                'lesson_conversation': True,
                'lesson_mode': True,
                'lesson_id': lesson_id,
                'current_slide': current_slide,
                'slide_title': slide_title,
                'slide_aware': True,
                'coaching_used': True
            })
            
        except Exception as e:
            print(f"❌ Lesson chat error: {e}")
            import traceback
            traceback.print_exc()

            return jsonify({
                'response': 'I encountered an error while helping with this lesson. Please try again!',
                'slide_command': False,
                'lesson_conversation': True,
                'lesson_mode': True,
                'lesson_id': lesson_id,
                'current_slide': current_slide,
                'slide_title': slide_title,
                'error': str(e)
            }), 500

    except Exception as e:
        print(f"❌ Lesson chat route error: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'response': 'I encountered an error while helping with this lesson. Please try again!',
            'error': str(e),
            'lesson_mode': True,
            'lesson_id': lesson_id
        }), 500

@app.route('/lesson/<lesson_id>/api/content')
def lesson_api_content(lesson_id):
    """API endpoint to get lesson content for dynamic lessons"""
    try:
        from slide_module_simplified import DATABASE_AVAILABLE, LessonManager, get_slide_content
        
        if not DATABASE_AVAILABLE:
            return jsonify({'error': 'Database not available'}), 500
        
        lesson_manager = LessonManager()
        lesson = lesson_manager.get_lesson(lesson_id)
        
        if not lesson or not lesson['is_published']:
            return jsonify({'error': 'Lesson not found or not published'}), 404
        
        slides = lesson_manager.get_lesson_slides(lesson_id)
        
        # Set the lesson context for the slide content module
        slide_content = get_slide_content()
        slide_content.set_current_lesson(lesson_id)
        
        return jsonify({
            'success': True,
            'lesson': lesson,
            'slides': slides,
            'total_slides': len(slides)
        })
        
    except Exception as e:
        print(f"❌ Lesson API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/enhanced-status', methods=['GET'])
def enhanced_status():
    """Check status of enhanced coaching features"""
    try:
        # Enhanced coaching availability is tied to database availability in this simplified version
        enhanced_coaching_available = DATABASE_AVAILABLE
        
        status = {
            'enhanced_coaching_available': enhanced_coaching_available,
            'database_available': DATABASE_AVAILABLE,  # We know it's available since setup worked
            'persistent_memory': enhanced_coaching_available,
            'timestamp': str(time.time())
        }
        
        if enhanced_coaching_available:
            # Get enhanced coaching context if available (via a LessonCoachingManager instance)
            # We can't get a global enhanced coaching context easily here, 
            # but we can indicate that the capability is present.
            try:
                # Attempt to get a status from a dummy or existing lesson manager
                # This part might need refinement depending on how you want to expose context status
                # For now, just indicate that the capability exists.
                status['coaching_context_capability'] = 'Available via LessonCoachingManager'
            except Exception as e:
                 status['context_error'] = str(e)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'enhanced_coaching_available': False
        }), 500

@app.route('/debug-status', methods=['GET'])
def debug_status():
    """Get detailed system status"""
    try:
        status = {
            'slide_controller': 'available',
            'voice_interaction': 'available',
            'slide_content': 'available',
            'lesson_managers': {
                lesson_id: manager.get_status()
                for lesson_id, manager in lesson_managers.items()
            }
        }
        
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# New endpoint to test OpenAI connection
@app.route('/test-openai-connection')
def test_openai_connection():
    """Test the OpenAI API connection by listing models."""
    try:
        from openai import OpenAI
        from config import Config
        import logging

        logger = logging.getLogger(__name__)

        api_key = Config.OPENAI_API_KEY
        if not api_key:
            logger.error("OPENAI_API_KEY is not set in config.py")
            return jsonify({'status': 'error', 'message': 'OpenAI API key not configured.'}), 500

        client = OpenAI(api_key=api_key)

        logger.info("Attempting to list OpenAI models...")
        models = client.models.list()
        
        # Check if the call was successful and we got some models
        if models and models.data:
            logger.info(f"Successfully listed {len(models.data)} models.")
            # Return a success message with a sample of models
            return jsonify({
                'status': 'success',
                'message': 'Successfully connected to OpenAI API and listed models.',
                'model_count': len(models.data),
                'sample_models': [model.id for model in models.data[:5]] # Show first 5 model IDs
            })
        else:
            logger.warning("OpenAI API call succeeded, but no models were returned.")
            return jsonify({'status': 'warning', 'message': 'Connected to OpenAI API, but no models returned.'}), 200

    except Exception as e:
        logger.error(f"Failed to connect to OpenAI API: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to OpenAI API: {str(e)}',
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc() # Include traceback for detailed debugging
        }), 500

@app.route('/tts/settings', methods=['GET'])
def get_tts_settings():
    settings = TTSSettings.query.first()
    if not settings:
        # Return sensible defaults if not set
        return jsonify({
            'provider': 'hume_evi3',
            'voice_id': 'ee966436-01ab-4810-a880-9e0a532e03b8',
            'speed': '1.0',
            'temperature': '0.7'
        })
    return jsonify({
        'provider': settings.provider,
        'voice_id': settings.voice_id,
        'speed': settings.speed,
        'temperature': settings.temperature
    })

@app.route('/tts/settings', methods=['POST'])
def set_tts_settings():
    try:
        data = request.json
        settings = TTSSettings.query.first()
        if not settings:
            settings = TTSSettings()
            db.session.add(settings)
        
        # Update all settings
        settings.provider = data.get('provider', settings.provider)
        settings.voice_id = data.get('voice_id', settings.voice_id)
        settings.speed = data.get('speed', settings.speed)
        settings.temperature = data.get('temperature', settings.temperature)
        
        # Commit changes
        db.session.commit()
        
        # Update the TTS provider if it changed
        if data.get('provider'):
            from config import Config
            Config.switch_tts_provider(data['provider'])
            print(f"🔄 Switched TTS provider to: {data['provider']}")
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"❌ Error saving TTS settings: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Conversational AI Server - Guidance-Based System")
    print("=" * 60)
    
    # Fetch the actual provider from the database for the final log
    db_settings = None
    with app.app_context():
        db_settings = TTSSettings.query.first()
        
    logged_provider = db_settings.provider if db_settings else Config.TTS_PROVIDER # Use DB setting if available, else Config default
    logged_api_keys_status = Config.get_provider_status() # This already checks Config

    print(f"🎙️ TTS Provider (Loaded): {logged_provider}")
    print(f"🔑 API Keys: {logged_api_keys_status}")
    print(f"🧭 Slide System: GUIDANCE-BASED (AI guides, user controls)")
    print(f"✨ Architecture: AI provides navigation guidance")
    print(f"🖱️ Navigation: User clicks UI buttons")
    print(f"🎓 Coaching: Personalized and context-aware")
    
    app.run(debug=True, host='0.0.0.0', port=5001)