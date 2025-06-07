"""
Unreal Speech TTS Provider
High-performance streaming TTS with low latency
"""

import requests
import asyncio
import aiohttp
from typing import AsyncGenerator, Dict, List, Tuple
from ..base import TTSProvider

class UnrealSpeechProvider(TTSProvider):
    """Unreal Speech TTS provider with streaming support"""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = "https://api.v8.unrealspeech.com"
        self.default_voice = kwargs.get('default_voice', 'af_sky')
        self.default_bitrate = kwargs.get('bitrate', '192k')
        
        # Voice mapping from provider format to internal format
        self._voice_map = {
            'friendly_casual': 'af_sky',
            'professional': 'am_adam', 
            'warm_natural': 'af_bella',
            # Add more mappings as needed
            # Mappings based on allowed voices from error message:
            'Eleanor': 'Eleanor',
            'Melody': 'Melody',
            'Javier': 'Javier',
            'Amelia': 'Amelia',
            'Sheng': 'Sheng',
            'Lian': 'Lian',
            'Jasper': 'Jasper',
            'Lauren': 'Lauren',
            'Luna': 'Luna',
            'Sierra': 'Sierra',
            'af': 'af',
            'Edward': 'Edward',
            'Charlotte': 'Charlotte',
            'Caleb': 'Caleb',
            'Priya': 'Priya',
            'Wei': 'Wei',
            'Ting': 'Ting',
            'Sakura': 'Sakura',
            'Chloe': 'Chloe',
            'Noah': 'Noah',
            'Rina': 'Rina',
            'Kaitlyn': 'Kaitlyn',
            'Luca': 'Luca',
            'Emily': 'Emily',
            'Jing': 'Jing',
            'Rowan': 'Rowan',
            'Hana': 'Hana',
            'Benjamin': 'Benjamin',
            'Maddie': 'Maddie',
            'Ronan': 'Ronan',
            'Mateo': 'Mateo',
            'Autumn': 'Autumn',
            'Arthur': 'Arthur',
            'Willow': 'Willow',
            'Daniel': 'Daniel',
            'Lucía': 'Lucía',
            'Rafael': 'Rafael',
            'Oliver': 'Oliver',
            'Yuki': 'Yuki',
            'Rohan': 'Rohan',
            'Jian': 'Jian',
            'Arjun': 'Arjun',
            'Élodie': 'Élodie',
            'Thiago': 'Thiago',
            'Giulia': 'Giulia',
            'Ananya': 'Ananya',
            'Camila': 'Camila',
            'Zane': 'Zane',
            'Ethan': 'Ethan',
            'Hao': 'Hao',
            'Mei': 'Mei',
            'Ivy': 'Ivy',
            'Hannah': 'Hannah',
            'Haruto': 'Haruto',
        }
    
    async def synthesize(self, text: str, voice_id: str, **options) -> bytes:
        """
        Synthesize text to audio (non-streaming)
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            **options: speed, pitch, bitrate, etc.
            
        Returns:
            Complete audio data as bytes
        """
        is_valid, error_msg = self.validate_text(text)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Map voice ID if needed
        actual_voice_id = self._voice_map.get(voice_id, voice_id)
        
        # Prepare request
        payload = {
            'Text': text,
            'VoiceId': actual_voice_id,
            'Bitrate': options.get('bitrate', self.default_bitrate),
            'Speed': str(options.get('speed', '0')),
            'Pitch': str(options.get('pitch', '1')),
            'Codec': 'libmp3lame',
            'Temperature': float(options.get('temperature', 0.25))  # UnrealSpeech DOES support temperature (0.1 to 0.8)
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/stream",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Unreal Speech API error: {error_text}")
                
                return await response.read()
    
    async def stream(self, text: str, voice_id: str, **options) -> AsyncGenerator[bytes, None]:
        """
        Stream audio chunks as they're generated
        
        Args:
            text: Text to synthesize  
            voice_id: Voice identifier
            **options: speed, pitch, bitrate, etc.
            
        Yields:
            Audio data chunks as bytes
        """
        is_valid, error_msg = self.validate_text(text)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Map voice ID if needed
        actual_voice_id = self._voice_map.get(voice_id, voice_id)
        
        # Prepare request
        payload = {
            'Text': text,
            'VoiceId': actual_voice_id,
            'Bitrate': options.get('bitrate', self.default_bitrate),
            'Speed': str(options.get('speed', '0')),
            'Pitch': str(options.get('pitch', '1')),
            'Codec': 'libmp3lame',
            'Temperature': float(options.get('temperature', 0.25))  # UnrealSpeech DOES support temperature (0.1 to 0.8)
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/stream",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Unreal Speech API error: {error_text}")
                
                # Stream chunks as they arrive
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        yield chunk
    
    def get_voices(self) -> List[Dict]:
        """Get available Unreal Speech voices"""
        return [
            {
                "id": "af_sky",
                "name": "Sky (Female)",
                "description": "Friendly and warm female voice",
                "gender": "female",
                "language": "en-US"
            },
            {
                "id": "af_bella", 
                "name": "Bella (Female)",
                "description": "Clear and professional female voice",
                "gender": "female",
                "language": "en-US"
            },
            {
                "id": "af_sarah",
                "name": "Sarah (Female)", 
                "description": "Natural and conversational female voice",
                "gender": "female",
                "language": "en-US"
            },
            {
                "id": "af_nicole",
                "name": "Nicole (Female)",
                "description": "Energetic and expressive female voice",
                "gender": "female", 
                "language": "en-US"
            },
            {
                "id": "am_adam",
                "name": "Adam (Male)",
                "description": "Professional and authoritative male voice",
                "gender": "male",
                "language": "en-US"
            },
            {
                "id": "am_michael",
                "name": "Michael (Male)",
                "description": "Warm and friendly male voice", 
                "gender": "male",
                "language": "en-US"
            },
            {
                "id": "bf_emma",
                "name": "Emma (British Female)",
                "description": "Elegant British female voice",
                "gender": "female",
                "language": "en-GB"
            },
            {
                "id": "bf_isabella",
                "name": "Isabella (British Female)",
                "description": "Sophisticated British female voice",
                "gender": "female",
                "language": "en-GB"
            },
            {
                "id": "bm_george",
                "name": "George (British Male)", 
                "description": "Distinguished British male voice",
                "gender": "male",
                "language": "en-GB"
            },
            {
                "id": "bm_lewis",
                "name": "Lewis (British Male)",
                "description": "Contemporary British male voice",
                "gender": "male",
                "language": "en-GB"
            }
        ]
    
    def validate_text(self, text: str) -> Tuple[bool, str]:
        """
        Validate text for Unreal Speech
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Text cannot be empty"
        
        if len(text) > 1000:
            return False, f"Text too long ({len(text)} chars). Maximum is 1000 characters for streaming."
        
        return True, ""
    
    # Synchronous methods for compatibility with Flask
    def synthesize_sync(self, text: str, voice_id: str, **options) -> bytes:
        """Synchronous synthesis"""
        return asyncio.run(self.synthesize(text, voice_id, **options))
    
    def stream_sync_generator(self, text: str, voice_id: str, **options):
        """
        Optimized synchronous streaming generator for Flask compatibility
        Uses larger chunks for better performance and reduced latency
        """
        is_valid, error_msg = self.validate_text(text)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Map voice ID if needed
        actual_voice_id = self._voice_map.get(voice_id, voice_id)
        
        # Prepare request
        payload = {
            'Text': text,
            'VoiceId': actual_voice_id,
            'Bitrate': options.get('bitrate', self.default_bitrate),
            'Speed': str(options.get('speed', '0')),
            'Pitch': str(options.get('pitch', '1')),
            'Codec': 'libmp3lame',
            'Temperature': float(options.get('temperature', 0.25))  # UnrealSpeech DOES support temperature (0.1 to 0.8)
        }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"🌊 Optimized Streaming: '{text[:50]}...' with voice {actual_voice_id}")
        
        try:
            import time
            start_time = time.time()
            
            # Use requests with streaming enabled
            response = requests.post(
                f"{self.base_url}/stream",
                json=payload,
                headers=headers,
                stream=True,  # Enable streaming
                timeout=(5, 30)  # 5s connect, 30s read timeout
            )
            
            if response.status_code != 200:
                error_text = response.text
                print(f"❌ Sync Streaming Error {response.status_code}: {error_text}")
                raise Exception(f"Unreal Speech streaming error ({response.status_code}): {error_text}")
            
            total_bytes = 0
            chunk_count = 0
            first_chunk = True
            
            # Use much larger chunks for better performance (16KB instead of 1KB)
            OPTIMIZED_CHUNK_SIZE = 16384  # 16KB chunks
            
            # Stream chunks as they arrive
            for chunk in response.iter_content(chunk_size=OPTIMIZED_CHUNK_SIZE):
                if chunk:
                    chunk_count += 1
                    total_bytes += len(chunk)
                    
                    if first_chunk:
                        latency = (time.time() - start_time) * 1000
                        print(f"⚡ First chunk in {latency:.0f}ms")
                        first_chunk = False
                    
                    yield chunk
            
            total_time = (time.time() - start_time) * 1000
            print(f"✅ Optimized stream: {chunk_count} chunks, {total_bytes} bytes in {total_time:.0f}ms")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            raise
