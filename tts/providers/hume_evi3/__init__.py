"""
Hume EVI3 TTS Provider Module
=============================
Advanced emotional voice synthesis with CLM integration
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__description__ = "Hume EVI3 TTS provider with emotional intelligence and CLM integration"

from .provider import HumeEVI3Provider
from .clm import HumeCLMWrapper
from .emotional import EmotionalContext

__all__ = ['HumeEVI3Provider', 'HumeCLMWrapper', 'EmotionalContext'] 