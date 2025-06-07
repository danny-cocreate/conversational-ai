"""
Configuration management for conversational AI application
Handles TTS provider settings and easy switching
"""

import os
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    # API Keys - Load from environment variables
    HUME_API_KEY = os.getenv("HUME_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    UNREALSPEECH_API_KEY = os.getenv("UNREALSPEECH_API_KEY")
    
    # TTS Configuration
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "unrealspeech")  # Default to Unreal Speech
    
    @classmethod
    def get_tts_config(cls) -> Dict[str, Any]:
        """Get TTS configuration for the current provider"""
        if cls.TTS_PROVIDER.lower() == "unrealspeech":
            if not cls.UNREALSPEECH_API_KEY:
                print("⚠️  Unreal Speech API key not found, falling back to Hume AI")
                return cls._get_hume_config()
            return {
                "provider": "unrealspeech",
                "api_key": cls.UNREALSPEECH_API_KEY,
                "options": {
                    "default_voice": "af_sky",
                    "bitrate": "192k"
                }
            }
        elif cls.TTS_PROVIDER.lower() == "hume":
            return cls._get_hume_config()
        elif cls.TTS_PROVIDER.lower() == "hume_evi3":
            return cls._get_hume_evi3_config()
        else:
            raise ValueError(f"Unknown TTS provider: {cls.TTS_PROVIDER}")
    
    @classmethod
    def _get_hume_config(cls) -> Dict[str, Any]:
        """Get Hume AI configuration"""
        return {
            "provider": "hume",
            "api_key": cls.HUME_API_KEY,
            "options": {
                "default_voice": "friendly_casual"
            }
        }
    
    @classmethod
    def _get_hume_evi3_config(cls) -> Dict[str, Any]:
        """Get Hume EVI3 configuration"""
        return {
            "provider": "hume_evi3",
            "api_key": cls.HUME_API_KEY,
            "options": {
                "default_voice": "friendly_casual"
            }
        }
    
    @classmethod
    def switch_tts_provider(cls, provider_name: str):
        """Switch TTS provider at runtime"""
        cls.TTS_PROVIDER = provider_name
        print(f"🔄 Switched TTS provider to: {provider_name}")
    
    @classmethod
    def get_provider_status(cls) -> Dict[str, Any]:
        """Get status of all TTS providers"""
        return {
            "current_provider": cls.TTS_PROVIDER,
            "available_providers": {
                "unrealspeech": {
                    "available": bool(cls.UNREALSPEECH_API_KEY),
                    "api_key_set": bool(cls.UNREALSPEECH_API_KEY)
                },
                "hume": {
                    "available": bool(cls.HUME_API_KEY),
                    "api_key_set": bool(cls.HUME_API_KEY)
                }
            }
        }
