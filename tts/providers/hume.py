"""
Hume AI TTS Provider
Wrapper for existing Hume AI implementation
"""

import base64
import asyncio
from typing import AsyncGenerator, Dict, List, Tuple
from ..base import TTSProvider

class HumeProvider(TTSProvider):
    """Hume AI TTS provider wrapper"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        
        # Import Hume client
        from hume import HumeClient
        from hume.tts import PostedUtterance, FormatMp3
        
        self.client = HumeClient(api_key=api_key)
        self.PostedUtterance = PostedUtterance
        self.FormatMp3 = FormatMp3
    
    async def synthesize(self, text: str, voice_id: str, **options) -> bytes:
        """
        Synthesize text to audio using Hume AI
        
        Args:
            text: Text to synthesize
            voice_id: Voice description for Hume AI
            **options: speed, voice_description, etc.
            
        Returns:
            Audio data as bytes
        """
        is_valid, error_msg = self.validate_text(text)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Use voice_id as description for Hume
        voice_description = options.get('voice_description', voice_id)
        if voice_id in ['friendly_casual', 'warm_natural']:
            voice_description = "friendly casual female voice"
        elif voice_id == 'professional':
            voice_description = "clear and professional male voice"
        
        speed = float(options.get('speed', '1.0'))
        
        # Run Hume synthesis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.tts.synthesize_json(
                utterances=[self.PostedUtterance(
                    text=text,
                    description=voice_description,
                    speed=speed
                )],
                format=self.FormatMp3()
            )
        )
        
        if not result.generations or not result.generations[0].audio:
            raise Exception("No audio data received from Hume AI")
        
        # Decode base64 audio
        audio_data = result.generations[0].audio
        return base64.b64decode(audio_data)
    
    async def stream(self, text: str, voice_id: str, **options) -> AsyncGenerator[bytes, None]:
        """
        Stream audio (Hume doesn't support true streaming, so return all at once)
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            **options: synthesis options
            
        Yields:
            Audio data as bytes (single chunk)
        """
        # Hume doesn't support streaming, so synthesize and yield as one chunk
        audio_data = await self.synthesize(text, voice_id, **options)
        yield audio_data
    
    def get_voices(self) -> List[Dict]:
        """Get available Hume AI voices (descriptions)"""
        return [
            {
                "id": "friendly_casual",
                "name": "Friendly Casual",
                "description": "A friendly and casual female voice",
                "gender": "female",
                "language": "en-US"
            },
            {
                "id": "professional", 
                "name": "Professional",
                "description": "A clear and professional male voice",
                "gender": "male",
                "language": "en-US"
            },
            {
                "id": "warm_natural",
                "name": "Warm Natural",
                "description": "A warm and natural-sounding female voice",
                "gender": "female",
                "language": "en-US"
            }
        ]
    
    def validate_text(self, text: str) -> Tuple[bool, str]:
        """
        Validate text for Hume AI
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Text cannot be empty"
        
        # Hume AI has more generous limits
        if len(text) > 5000:
            return False, f"Text too long ({len(text)} chars). Maximum is 5000 characters."
        
        return True, ""
    
    # Synchronous methods for compatibility with Flask
    def synthesize_sync(self, text: str, voice_id: str, **options) -> bytes:
        """Synchronous synthesis"""
        return asyncio.run(self.synthesize(text, voice_id, **options))
    
    # Remove custom stream_sync_generator to use the improved base class implementation
