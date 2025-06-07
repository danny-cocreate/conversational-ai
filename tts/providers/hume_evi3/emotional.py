"""
Emotional Context Handler
========================
Processes and manages emotional data from Hume EVI3
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import json

@dataclass
class EmotionalState:
    """Represents the emotional state of a voice input"""
    emotions: Dict[str, float]  # e.g. {"frustration": 0.7, "excitement": 0.3}
    prosody: Dict[str, float]   # e.g. {"pitch": 1.2, "speech_rate": 0.9}
    confidence: float           # Confidence score of emotional analysis

class EmotionalContext:
    """Handles emotional context processing and management"""
    
    def __init__(self):
        self.current_state: Optional[EmotionalState] = None
        self.history: List[EmotionalState] = []
        self.max_history = 10  # Keep last 10 emotional states
    
    def process_emotional_data(self, data: Dict) -> EmotionalState:
        """
        Process raw emotional data from Hume EVI3
        
        Args:
            data: Raw emotional data from Hume
            
        Returns:
            Processed EmotionalState
        """
        try:
            # Extract emotions and prosody from Hume data
            emotions = data.get('emotions', {})
            prosody = data.get('prosody', {})
            confidence = data.get('confidence', 0.0)
            
            # Create new emotional state
            state = EmotionalState(
                emotions=emotions,
                prosody=prosody,
                confidence=confidence
            )
            
            # Update current state and history
            self.current_state = state
            self.history.append(state)
            
            # Maintain history size
            if len(self.history) > self.max_history:
                self.history.pop(0)
            
            return state
            
        except Exception as e:
            print(f"Error processing emotional data: {e}")
            return EmotionalState(
                emotions={},
                prosody={},
                confidence=0.0
            )
    
    def get_emotional_summary(self) -> Dict:
        """
        Get summary of emotional context
        
        Returns:
            Dictionary with emotional summary
        """
        if not self.current_state:
            return {
                'has_emotional_data': False,
                'dominant_emotion': None,
                'emotional_intensity': 0.0
            }
        
        # Find dominant emotion
        emotions = self.current_state.emotions
        if emotions:
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])
            emotional_intensity = dominant_emotion[1]
        else:
            dominant_emotion = None
            emotional_intensity = 0.0
        
        return {
            'has_emotional_data': True,
            'dominant_emotion': dominant_emotion,
            'emotional_intensity': emotional_intensity,
            'confidence': self.current_state.confidence
        }
    
    def should_adapt_response(self) -> bool:
        """
        Determine if response should be adapted based on emotional context
        
        Returns:
            True if response should be adapted
        """
        if not self.current_state:
            return False
        
        # Check for high emotional intensity
        summary = self.get_emotional_summary()
        if summary['emotional_intensity'] > 0.7:
            return True
        
        # Check for specific emotions that need adaptation
        emotions = self.current_state.emotions
        if any(emotion in emotions and emotions[emotion] > 0.6 
               for emotion in ['frustration', 'confusion', 'excitement']):
            return True
        
        return False
    
    def get_adaptation_guidance(self) -> Dict:
        """
        Get guidance for adapting response based on emotional context
        
        Returns:
            Dictionary with adaptation guidance
        """
        if not self.should_adapt_response():
            return {
                'should_adapt': False,
                'guidance': None
            }
        
        emotions = self.current_state.emotions
        guidance = {
            'should_adapt': True,
            'tone': 'neutral',
            'pace': 'normal',
            'detail_level': 'normal'
        }
        
        # Adapt based on emotions
        if emotions.get('frustration', 0) > 0.6:
            guidance.update({
                'tone': 'supportive',
                'pace': 'slower',
                'detail_level': 'simplified'
            })
        elif emotions.get('excitement', 0) > 0.6:
            guidance.update({
                'tone': 'enthusiastic',
                'pace': 'faster',
                'detail_level': 'detailed'
            })
        elif emotions.get('confusion', 0) > 0.6:
            guidance.update({
                'tone': 'patient',
                'pace': 'slower',
                'detail_level': 'simplified'
            })
        
        return guidance 