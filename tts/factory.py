"""
TTS Provider Factory
Handles creation and configuration of TTS providers
"""

from typing import Dict, Any, List
from .base import TTSProvider

class TTSFactory:
    """Factory for creating TTS provider instances"""
    
    @staticmethod
    def create_provider(provider_name: str, config: Dict[str, Any]) -> TTSProvider:
        """
        Create a TTS provider instance
        
        Args:
            provider_name: Name of the provider ('unrealspeech', 'hume', 'hume_evi3')
            config: Configuration dictionary with provider-specific settings
            
        Returns:
            TTSProvider instance
            
        Raises:
            ValueError: If provider_name is not supported
            KeyError: If required config keys are missing
        """
        provider_name = provider_name.lower()
        
        if provider_name == "unrealspeech":
            try:
                # Check for required dependencies first
                import requests
                import aiohttp
                import asyncio
                
                # Use the original provider implementation
                from .providers.unrealspeech import UnrealSpeechProvider
                return UnrealSpeechProvider(
                    api_key=config['api_key'],
                    **config.get('options', {})
                )
            except ImportError as e:
                missing_dep = str(e).split("'")[1] if "'" in str(e) else str(e)
                raise ImportError(f"Cannot create UnrealSpeech provider: Missing dependency '{missing_dep}'. Install with: pip install {missing_dep}")
            except Exception as e:
                raise Exception(f"Failed to create UnrealSpeech provider: {e}")
        
        elif provider_name == "hume":
            try:
                # Check for required hume dependency
                import hume
                
                # Check if EVI3 is enabled
                if config.get('use_evi3', False):
                    from .providers.hume_evi3 import HumeEVI3Provider
                    return HumeEVI3Provider(
                        api_key=config['api_key'],
                        **config.get('options', {})
                    )
                else:
                    # Use regular Hume provider
                    from .providers.hume import HumeProvider
                    return HumeProvider(
                        api_key=config['api_key'],
                        **config.get('options', {})
                    )
            except ImportError as e:
                missing_dep = str(e).split("'")[1] if "'" in str(e) else str(e)
                raise ImportError(f"Cannot create Hume provider: Missing dependency '{missing_dep}'. Install with: pip install {missing_dep}")
            except Exception as e:
                raise Exception(f"Failed to create Hume provider: {e}")
        
        elif provider_name == "hume_evi3":
            from .providers.hume_evi3 import HumeEVI3Provider
            return HumeEVI3Provider(
                api_key=config['api_key'],
                **config.get('options', {})
            )
        
        else:
            available_providers = ['unrealspeech', 'hume', 'hume_evi3']
            raise ValueError(f"Unknown provider '{provider_name}'. Available providers: {available_providers}")
    
    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available TTS providers"""
        return ['unrealspeech', 'hume', 'hume_evi3']
    
    @staticmethod
    def get_provider_info(provider_name: str) -> Dict[str, Any]:
        """Get information about a specific provider"""
        provider_info = {
            'unrealspeech': {
                'name': 'Unreal Speech',
                'description': 'High-quality, low-latency streaming TTS',
                'features': ['streaming', 'word_timestamps', 'low_latency'],
                'cost_per_million_chars': 8,
                'max_text_length': 1000,
                'languages': 8,
                'voices': 48
            },
            'hume': {
                'name': 'Hume AI',
                'description': 'Emotionally expressive TTS',
                'features': ['emotional_synthesis', 'custom_voices'],
                'cost_per_million_chars': 240,  # Estimated
                'max_text_length': 5000,  # Estimated
                'languages': 1,
                'voices': 'custom',
                'evi3_enabled': False  # New flag for EVI3 support
            },
            'hume_evi3': {
                'name': 'Hume EVI3',
                'description': 'Advanced emotional TTS (EVI3)',
                'features': ['emotional_synthesis', 'evi3', 'custom_voices'],
                'cost_per_million_chars': 240,  # Estimated
                'max_text_length': 5000,  # Estimated
                'languages': 1,
                'voices': 'custom',
                'evi3_enabled': True
            }
        }
        
        if provider_name.lower() not in provider_info:
            raise ValueError(f"Unknown provider '{provider_name}'")
        
        return provider_info[provider_name.lower()]
