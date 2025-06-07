"""
Hume EVI3 CLM Wrapper
====================
Handles Custom Language Model integration with Hume EVI3
"""

from typing import Dict, List, Optional, AsyncGenerator
import json
import asyncio
from flask import Response
from .emotional import EmotionalContext

class HumeCLMWrapper:
    """Wrapper for Hume EVI3 Custom Language Model integration"""
    
    def __init__(self, coaching_system, emotional_context: Optional[EmotionalContext] = None):
        """
        Initialize CLM wrapper
        
        Args:
            coaching_system: Your existing coaching system
            emotional_context: Optional emotional context handler
        """
        self.coaching_system = coaching_system
        self.emotional_context = emotional_context or EmotionalContext()
    
    async def process_request(self, request_data: Dict) -> Response:
        """
        Process incoming request from Hume EVI3
        
        Args:
            request_data: Raw request data from Hume
            
        Returns:
            Flask Response with streaming SSE
        """
        try:
            # Extract message history
            messages = []
            for msg in request_data.get('messages', []):
                messages.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                })
            
            # Extract emotional context if available
            emotional_data = None
            for msg in request_data.get('messages', []):
                if 'prosody' in msg:
                    emotional_data = msg['prosody']
                    break
            
            # Process emotional data if available
            if emotional_data:
                self.emotional_context.process_emotional_data(emotional_data)
            
            # Get adaptation guidance if needed
            guidance = self.emotional_context.get_adaptation_guidance()
            
            # Generate response using coaching system
            response_text = await self.coaching_system.generate_coaching_response(
                messages=messages,
                emotional_context=guidance if guidance['should_adapt'] else None
            )
            
            # Stream response back to Hume
            return self._stream_response(response_text)
            
        except Exception as e:
            print(f"Error processing CLM request: {e}")
            return self._stream_error(str(e))
    
    def _stream_response(self, text: str) -> Response:
        """
        Stream response back to Hume in SSE format
        
        Args:
            text: Response text to stream
            
        Returns:
            Flask Response with SSE
        """
        def generate_sse():
            # Break response into chunks for streaming
            words = text.split()
            for i, word in enumerate(words):
                chunk = {
                    "id": f"chunk_{i}",
                    "choices": [{
                        "delta": {"content": word + " "},
                        "finish_reason": None if i < len(words)-1 else "stop"
                    }]
                }
                yield f"data: {json.dumps(chunk)}\n\n"
        
        return Response(generate_sse(), mimetype='text/event-stream')
    
    def _stream_error(self, error_message: str) -> Response:
        """
        Stream error response
        
        Args:
            error_message: Error message to stream
            
        Returns:
            Flask Response with SSE error
        """
        def generate_error():
            chunk = {
                "id": "error",
                "choices": [{
                    "delta": {"content": f"Error: {error_message}"},
                    "finish_reason": "error"
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        
        return Response(generate_error(), mimetype='text/event-stream')
    
    async def test_connection(self) -> bool:
        """
        Test CLM connection
        
        Returns:
            True if connection is working
        """
        try:
            # Simple test message
            test_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a test message."
                    }
                ]
            }
            
            # Process test request
            response = await self.process_request(test_data)
            
            # Check if response is valid
            return response.status_code == 200
            
        except Exception as e:
            print(f"CLM connection test failed: {e}")
            return False 