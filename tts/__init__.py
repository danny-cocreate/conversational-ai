"""
Text-to-Speech module for conversational AI
Provides a modular, provider-agnostic TTS interface
"""

from .base import TTSProvider
from .factory import TTSFactory
from .text_chunker import SmartTextChunker, chunk_text_for_tts

# Don't import providers here - let factory handle imports lazily
# This prevents import errors from breaking the entire module

__all__ = ['TTSProvider', 'TTSFactory', 'SmartTextChunker', 'chunk_text_for_tts']

# Providers are imported lazily by the factory when needed
