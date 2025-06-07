"""
Voice Interaction for AI Coaching
Provides navigation guidance based on voice input - user controls via UI buttons
"""

import re
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from .slide_controller import get_slide_controller

logger = logging.getLogger(__name__)

class NavigationIntent(Enum):
    NEXT = "next"
    PREVIOUS = "previous"
    GOTO = "goto"
    FIRST = "first"
    LAST = "last"
    STATUS = "status"
    GENERAL_NAV = "general_nav"
    UNKNOWN = "unknown"

@dataclass
class VoiceIntent:
    """Represents detected navigation intent from voice input"""
    intent: NavigationIntent
    confidence: float
    slide_number: Optional[int] = None
    original_text: str = ""

@dataclass
class GuidanceResult:
    """Result containing navigation guidance for the user"""
    has_navigation_intent: bool
    guidance_message: str
    intent_type: str
    slide_info: Optional[Dict[str, Any]] = None
    confidence: float = 0.0

class VoiceInteraction:
    """
    Voice interaction for AI coaching with navigation guidance
    
    Features:
    - Detects navigation intent from voice input
    - Provides guidance messages instead of controlling slides
    - Gives contextual navigation help
    
    Note: AI provides guidance, user clicks UI buttons to navigate
    """
    
    def __init__(self):
        self.slide_controller = get_slide_controller()
        
        # Patterns for detecting navigation intent
        self.patterns = {
            NavigationIntent.NEXT: [
                r'\b(next|forward|advance|continue|go forward|move forward)\b',
                r'\bnext slide\b'
            ],
            NavigationIntent.PREVIOUS: [
                r'\b(previous|back|backward|go back|move back)\b',
                r'\bprevious slide\b'
            ],
            NavigationIntent.GOTO: [
                r'\b(go to|jump to|show|take me to) slide (\d+)\b',
                r'\bslide (\d+)\b'
            ],
            NavigationIntent.FIRST: [
                r'\b(first|beginning|start|go to first)\b',
                r'\bback to (the )?beginning\b'
            ],
            NavigationIntent.LAST: [
                r'\b(last|final|end|go to last)\b',
                r'\bgo to (the )?end\b'
            ],
            NavigationIntent.STATUS: [
                r'\b(status|where|current|what slide|which slide)\b',
                r'\bwhere are we\b'
            ],
            NavigationIntent.GENERAL_NAV: [
                r'\b(navigate|navigation|move|go)\b',
                r'\bhow to (navigate|move)\b'
            ]
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for intent, patterns in self.patterns.items():
            self.compiled_patterns[intent] = [re.compile(p, re.IGNORECASE) for p in patterns]
        
        logger.info("🎤 VoiceInteraction initialized for guidance")
    
    def process_voice_input(self, text: str) -> GuidanceResult:
        """
        Process voice input and provide navigation guidance
        
        Args:
            text: Voice input text
            
        Returns:
            GuidanceResult with navigation guidance instead of control
        """
        # Parse the voice input for navigation intent
        intent = self._parse_navigation_intent(text)
        
        # Provide guidance if navigation intent detected
        if intent.intent != NavigationIntent.UNKNOWN and intent.confidence > 0.6:
            guidance_message = self._get_navigation_guidance(intent)
            
            return GuidanceResult(
                has_navigation_intent=True,
                guidance_message=guidance_message,
                intent_type=intent.intent.value,
                slide_info=self.slide_controller.get_navigation_info(),
                confidence=intent.confidence
            )
        else:
            return GuidanceResult(
                has_navigation_intent=False,
                guidance_message="I'm here to help with any questions about the content.",
                intent_type="unknown",
                slide_info=self.slide_controller.get_navigation_info(),
                confidence=intent.confidence
            )
    
    def _parse_navigation_intent(self, text: str) -> VoiceIntent:
        """Parse text for navigation intent"""
        if not text:
            return VoiceIntent(NavigationIntent.UNKNOWN, 0.0, original_text=text)
        
        text_lower = text.lower().strip()
        best_intent = NavigationIntent.UNKNOWN
        best_confidence = 0.0
        slide_number = None
        
        # Check each intent pattern
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text_lower)
                if match:
                    confidence = self._calculate_confidence(text_lower, match, intent)
                    
                    # Extract slide number for GOTO intent
                    if intent == NavigationIntent.GOTO and match.groups():
                        try:
                            slide_number = int(match.group(1)) if len(match.groups()) > 0 else None
                        except ValueError:
                            slide_number = None
                    
                    # Keep the best match
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        return VoiceIntent(
            intent=best_intent,
            confidence=best_confidence,
            slide_number=slide_number,
            original_text=text
        )
    
    def _calculate_confidence(self, text: str, match: re.Match, intent: NavigationIntent) -> float:
        """Calculate confidence score for a match"""
        base_confidence = 0.8  # Base confidence for any match
        
        # Boost confidence for complete matches
        match_ratio = len(match.group(0)) / len(text)
        if match_ratio > 0.7:
            base_confidence += 0.15
        
        # Boost confidence for specific intents
        if intent == NavigationIntent.GOTO and match.groups():
            base_confidence += 0.1  # GOTO with number is very specific
        elif intent in [NavigationIntent.NEXT, NavigationIntent.PREVIOUS]:
            base_confidence += 0.05  # Common navigation intents
        
        return min(1.0, base_confidence)
    
    def _get_navigation_guidance(self, intent: VoiceIntent) -> str:
        """Generate navigation guidance based on detected intent"""
        try:
            if intent.intent == NavigationIntent.NEXT:
                return self.slide_controller.get_navigation_guidance("next")
                
            elif intent.intent == NavigationIntent.PREVIOUS:
                return self.slide_controller.get_navigation_guidance("previous")
                
            elif intent.intent == NavigationIntent.GOTO:
                if intent.slide_number is None:
                    return "I heard you want to go to a specific slide. Could you tell me which slide number? Then you can click the navigation buttons to get there."
                
                current = self.slide_controller.get_current_slide() + 1
                target = intent.slide_number
                total = self.slide_controller.get_total_slides()
                
                if target == current:
                    return f"We're already on slide {target}!"
                elif target < 1 or target > total:
                    return f"Slide {target} doesn't exist. We have slides 1 through {total}."
                elif target > current:
                    clicks_needed = target - current
                    return f"To get to slide {target}, click the 'Next' button {clicks_needed} times."
                else:
                    clicks_needed = current - target
                    return f"To get to slide {target}, click the 'Previous' button {clicks_needed} times."
                
            elif intent.intent == NavigationIntent.FIRST:
                return self.slide_controller.get_navigation_guidance("first")
                
            elif intent.intent == NavigationIntent.LAST:
                return self.slide_controller.get_navigation_guidance("last")
                
            elif intent.intent == NavigationIntent.STATUS:
                return self.slide_controller.get_contextual_guidance()
                
            elif intent.intent == NavigationIntent.GENERAL_NAV:
                return self.slide_controller.get_navigation_guidance("general")
            
            else:
                return "I'm here to help! You can ask me questions about the content or ask me where we are in the presentation."
                
        except Exception as e:
            logger.error(f"Error generating guidance: {e}")
            return "I can help you navigate. Use the buttons at the top of the screen to move between slides."
    
    def has_navigation_intent(self, text: str) -> bool:
        """Check if text contains navigation intent"""
        intent = self._parse_navigation_intent(text)
        return intent.intent != NavigationIntent.UNKNOWN or intent.confidence > 0.3
    
    def get_current_slide_info(self) -> Dict[str, Any]:
        """Get current slide information for AI coaching context"""
        return self.slide_controller.get_navigation_info()

# Global instance
voice_interaction = VoiceInteraction()

def get_voice_interaction() -> VoiceInteraction:
    """Get the global voice interaction instance"""
    return voice_interaction

def process_voice_input(text: str) -> GuidanceResult:
    """Process voice input using global instance - returns guidance instead of control"""
    return voice_interaction.process_voice_input(text)

def has_navigation_intent(text: str) -> bool:
    """Check if text has navigation intent using global instance"""
    return voice_interaction.has_navigation_intent(text)
