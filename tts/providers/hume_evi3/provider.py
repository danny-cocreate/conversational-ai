"""
Hume EVI3 Provider
=================
Advanced TTS provider with emotional intelligence
"""

import base64
import asyncio
import time
import json
import httpx
from typing import AsyncGenerator, Dict, List, Tuple, Optional
from hume import HumeClient
from hume.tts import PostedUtterance, FormatMp3

from ...base import TTSProvider
from .emotional import EmotionalContext
from .clm import HumeCLMWrapper

class HumeEVI3Provider(TTSProvider):
    """Hume EVI3 TTS provider with emotional intelligence"""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize Hume EVI3 provider
        
        Args:
            api_key: Hume API key
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        
        # Initialize Hume client
        self.client = HumeClient(api_key=api_key)
        self.PostedUtterance = PostedUtterance
        self.FormatMp3 = FormatMp3
        
        # HTTP streaming configuration
        self.stream_url = "https://api.hume.ai/v0/tts/stream/json"
        self.api_key = api_key
        
        # Initialize emotional context
        self.emotional_context = EmotionalContext()
        
        # Initialize CLM wrapper if coaching system provided
        self.clm_wrapper = None
        if 'coaching_system' in kwargs:
            self.clm_wrapper = HumeCLMWrapper(
                coaching_system=kwargs['coaching_system'],
                emotional_context=self.emotional_context
            )
        
        # Performance monitoring
        self.last_synthesis_time = 0
        self.last_chunk_count = 0
        self.last_total_bytes = 0
    
    async def synthesize(self, text: str, voice_id: str, **options) -> bytes:
        """
        Synthesize text to audio using Hume EVI3
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            **options: Additional options including emotional context and emotional parameters
            
        Returns:
            Audio data as bytes
        """
        is_valid, error_msg = self.validate_text(text)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Get emotional context if available (from previous interactions)
        emotional_context_state = self.emotional_context.current_state # Use state from previous turns
        if emotional_context_state:
            print("🧠 Incorporating emotional context state from previous turns...")
        
        # Get explicit emotional/prosody parameters from options (from current request)
        explicit_parameters = options.get('emotional_parameters', {})
        explicit_emotions = explicit_parameters.get('emotions', {})
        explicit_prosody = explicit_parameters.get('prosody', {})
        
        # Get voice description
        voice_description = self._get_voice_description(voice_id, options)
        
        # Get synthesis parameters (speed, temperature, pitch)
        speed = float(options.get('speed', '1.0'))
        temperature = float(options.get('temperature', '0.75')) 
        pitch = float(options.get('pitch', '1.0'))       
        
        # --- Build Final Emotional and Prosody Parameters with explicit dictionary creation ---
        # Start with fresh mutable dictionaries
        final_emotions_dict = {}
        final_prosody_dict = {}

        # Copy emotional state from previous turns if available and is a dictionary
        if emotional_context_state and isinstance(emotional_context_state.emotions, dict):
             final_emotions_dict.update(emotional_context_state.emotions)
        if emotional_context_state and isinstance(emotional_context_state.prosody, dict):
             final_prosody_dict.update(emotional_context_state.prosody)
             
        # Override/merge with explicit parameters from the current request if they are dictionaries
        if explicit_emotions and isinstance(explicit_emotions, dict):
            print(f"🎭 Overriding/merging with explicit emotions: {explicit_emotions}")
            final_emotions_dict.update(explicit_emotions)
            
        if explicit_prosody and isinstance(explicit_prosody, dict):
            print(f"🎭 Overriding/merging with explicit prosody: {explicit_prosody}")
            final_prosody_dict.update(explicit_prosody)
            
        # Prepare synthesis request - Pass explicitly created dictionaries
        # Conditionally include emotions and prosody only if they are not empty
        utterance_args = {
            'text': text,
            'description': voice_description,
            'speed': speed,
        }
        
        if final_emotions_dict:
            utterance_args['emotions'] = dict(final_emotions_dict)
            
        if final_prosody_dict:
            utterance_args['prosody'] = dict(final_prosody_dict)

        # Hume library might not directly support temperature/pitch in PostedUtterance
        # If it does, uncomment these lines and add to utterance_args:
        # 'temperature': temperature,
        # 'pitch': pitch,
        
        utterance = self.PostedUtterance(**utterance_args)
        
        # Log the final utterance structure being sent to Hume
        print("✨ Final Utterance for Hume:")
        print(f"  Text: '{utterance.text[:50]}...'")
        print(f"  Description: {utterance.description}")
        print(f"  Speed: {utterance.speed}")
        print(f"  Emotions: {getattr(utterance, 'emotions', 'Omitted (empty)')}") # Log if omitted
        print(f"  Prosody: {getattr(utterance, 'prosody', 'Omitted (empty)')}")   # Log if omitted
        # print(f"  Temperature: {temperature}") # Uncomment if temperature/pitch supported
        # print(f"  Pitch: {pitch}")         # Uncomment if temperature/pitch supported
        
        # Run synthesis in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.tts.synthesize_json(
                utterances=[utterance],
                format=self.FormatMp3()
            )
        )
        
        if not result.generations or not result.generations[0].audio:
            # Log detailed response for debugging
            print(f"❌ Hume EVI3 Synthesis Error: No audio data. Full result: {result}")
            raise Exception("No audio data received from Hume EVI3")
        
        # Decode base64 audio
        audio_data = result.generations[0].audio
        return base64.b64decode(audio_data)
    
    async def stream(self, text: str, voice_id: str, **options) -> AsyncGenerator[bytes, None]:
        """
        Stream audio using HTTP streaming with instant mode
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            **options: Additional options
            
        Yields:
            Audio data as bytes in chunks
        """
        start_time = time.time()
        chunk_count = 0
        total_bytes = 0
        first_chunk_time = None
        
        try:
            # Validate text
            is_valid, error_msg = self.validate_text(text)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Ensure consistent voice - use custom ID as default
            DEFAULT_CUSTOM_VOICE_ID = 'ee966436-01ab-4810-a880-9e0a532e03b8'
            
            # For instant_mode, a predefined voice must be specified. Using the default if none provided.
            if not voice_id or voice_id not in [DEFAULT_CUSTOM_VOICE_ID]:
                voice_id = DEFAULT_CUSTOM_VOICE_ID
                print(f"⚠️ Using default voice: {voice_id} (required for instant_mode)")
            
            # Get synthesis parameters
            speed = float(options.get('speed', '1.0'))
            
            # Prepare HTTP streaming request
            headers = {
                "X-Hume-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Re-enabling instant_mode with predefined voice
            payload = {
                "utterances": [{
                    "text": text,
                    "voice": {
                        "id": voice_id  # Re-adding voice ID as required for instant_mode
                    },
                    "speed": speed
                }],
                "format": {
                    "type": "mp3"
                },
                "instant_mode": True,        # 🔥 Re-enabled for ~200ms response
                "strip_headers": True,       # Remove audio artifacts (recommended for instant_mode)
                "num_generations": 1         # Required for instant_mode
            }
            
            print(f"🎵 Sending HTTP streaming request:")
            print(f"  Text: '{text[:50]}...'")
            print(f"  Voice ID: {voice_id}")
            print(f"  Speed: {speed}")
            print(f"  Headers: {json.dumps(headers, indent=2)}")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            
            # Use httpx for streaming with proper configuration
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    async with client.stream(
                        "POST",
                        "https://api.hume.ai/v0/tts/stream/file",
                        headers=headers,
                        json=payload,
                        follow_redirects=True
                    ) as response:
                        print(f"📋 Status: {response.status_code}")
                        print(f"📋 Content-Type: {response.headers.get('content-type')}")
                        print(f"📋 Content-Length: {response.headers.get('content-length')}")
                        
                        if response.status_code != 200:
                            error_body = await response.aread()
                            try:
                                error_json = json.loads(error_body)
                                error_msg = f"HTTP error {response.status_code}: {json.dumps(error_json, indent=2)}"
                            except json.JSONDecodeError:
                                error_msg = f"HTTP error {response.status_code}: {error_body.decode()}"
                            print(f"❌ {error_msg}")
                            raise Exception(error_msg)
                        
                        print("🎵 Starting to receive audio chunks...")
                        
                        # Only iterate once through the response
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            if chunk:  # Non-empty chunk
                                chunk_count += 1
                                total_bytes += len(chunk)
                                
                                if first_chunk_time is None:
                                    first_chunk_time = (time.time() - start_time) * 1000
                                    print(f"⚡ First chunk in {first_chunk_time:.0f}ms")
                                    print(f"📦 First chunk size: {len(chunk)} bytes")
                                else:
                                    print(f"🎵 Chunk {chunk_count}: {len(chunk)} bytes")
                                
                                yield chunk
                        
                        print(f"✅ Received {chunk_count} chunks, {total_bytes} total bytes")
                        
                        if chunk_count == 0:
                            print("⚠️ Warning: No audio chunks were received!")
                except httpx.RequestError as e:
                    print(f"❌ Request error: {e}")
                    raise
            
            # Update performance metrics
            self.last_synthesis_time = time.time() - start_time
            self.last_chunk_count = chunk_count
            self.last_total_bytes = total_bytes
            
            total_time = (time.time() - start_time) * 1000
            print(f"✅ Stream complete: {chunk_count} chunks, {total_bytes} bytes in {total_time:.0f}ms")
            
            if chunk_count == 0:
                print("⚠️ Warning: No audio chunks were received!")
            
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            raise
    
    def get_voices(self) -> List[Dict]:
        """Get available Hume EVI3 voices"""
        return [
            {
                "id": "358105e3-807d-4f0a-9b17-c35751a1040b",
                "name": "UX Coach EVI",
                "description": "A warm, friendly female voice with clear pronunciation. Great for educational content.",
                "gender": "female",
                "language": "en-US",
                "features": ["emotional", "natural"]
            }
        ]
    
    def validate_text(self, text: str) -> Tuple[bool, str]:
        """
        Validate text for Hume EVI3
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Text cannot be empty"
        
        # Hume EVI3 has more generous limits
        if len(text) > 5000:
            return False, f"Text too long ({len(text)} chars). Maximum is 5000 characters."
        
        return True, ""
    
    def _get_voice_description(self, voice_id: str, options: Dict) -> str:
        """
        Get voice description for Hume EVI3
        
        Args:
            voice_id: Voice identifier
            options: Additional options
            
        Returns:
            Voice description string
        """
        # Use provided description if available
        if 'voice_description' in options:
            return options['voice_description']
        
        # Map voice IDs to descriptions
        voice_descriptions = {
            '358105e3-807d-4f0a-9b17-c35751a1040b': "UX Coach EVI - A warm, friendly female voice with clear pronunciation. Great for educational content.",
            'friendly_casual': "friendly casual female voice with emotional intelligence",
            'professional': "clear and professional male voice with emotional intelligence",
            'warm_natural': "warm and natural-sounding female voice with emotional intelligence"
        }
        
        # Return the mapped description or use the voice_id as fallback
        return voice_descriptions.get(voice_id, voice_id)
    
    async def test_connection(self) -> bool:
        """
        Test connection to Hume EVI3
        
        Returns:
            True if connection is working
        """
        try:
            # Test basic synthesis
            test_text = "Hello, this is a test of the Hume EVI3 system."
            await self.synthesize(test_text, 'friendly_casual')
            
            # Test CLM if available
            if self.clm_wrapper:
                clm_working = await self.clm_wrapper.test_connection()
                if not clm_working:
                    print("Warning: CLM connection test failed")
            
            return True
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False 