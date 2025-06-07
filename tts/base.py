"""
Base TTS Provider Interface
Defines the contract that all TTS providers must implement
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, List, Tuple
import asyncio

class TTSProvider(ABC):
    """Abstract base class for all TTS providers"""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize TTS provider
        
        Args:
            api_key: Provider API key
            **kwargs: Additional configuration
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def synthesize(self, text: str, voice_id: str, **options) -> bytes:
        """
        Synthesize text to audio
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            **options: Additional options
            
        Returns:
            Audio data as bytes
        """
        pass
    
    @abstractmethod
    async def stream(self, text: str, voice_id: str, **options) -> AsyncGenerator[bytes, None]:
        """
        Stream audio chunks
        
        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            **options: Additional options
            
        Yields:
            Audio data chunks as bytes
        """
        pass
    
    @abstractmethod
    def get_voices(self) -> List[Dict]:
        """Get available voices"""
        pass
    
    @abstractmethod
    def validate_text(self, text: str) -> Tuple[bool, str]:
        """
        Validate text for synthesis
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    # Synchronous wrappers for backward compatibility
    def synthesize_sync(self, text: str, voice_id: str, **options) -> bytes:
        """Synchronous wrapper for synthesize"""
        return asyncio.run(self.synthesize(text, voice_id, **options))
    
    def stream_sync_generator(self, text: str, voice_id: str, **options):
        """
        Optimized synchronous streaming generator for Flask compatibility
        Uses larger chunks for better performance and reduced latency
        """
        import threading
        import queue
        import time
        
        # Performance monitoring
        start_time = time.time()
        chunk_count = 0
        total_bytes = 0
        first_chunk_time = None
        
        # Create queues for results and exceptions
        result_queue = queue.Queue()
        exception_holder = [None]
        
        def run_async():
            """Run async stream in background thread"""
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def collect_chunks():
                    """Collect chunks from async stream"""
                    try:
                        async for chunk in self.stream(text, voice_id, **options):
                            if chunk:
                                result_queue.put(('chunk', chunk))
                        result_queue.put(('done', None))
                    except Exception as e:
                        result_queue.put(('error', e))
                
                # Run async collection
                loop.run_until_complete(collect_chunks())
                loop.close()
                
            except Exception as e:
                exception_holder[0] = e
                result_queue.put(('error', e))
        
        # Start async collection in background thread
        thread = threading.Thread(target=run_async)
        thread.daemon = True  # Allow thread to be killed when main thread exits
        thread.start()
        
        # Yield chunks as they become available
        while True:
            try:
                # Get next item with timeout
                item_type, item_value = result_queue.get(timeout=30)  # 30 second timeout
                
                if item_type == 'chunk':
                    chunk_count += 1
                    total_bytes += len(item_value)
                    
                    if first_chunk_time is None:
                        first_chunk_time = (time.time() - start_time) * 1000
                        print(f"⚡ First chunk in {first_chunk_time:.0f}ms")
                        print(f"📦 First chunk size: {len(item_value)} bytes")
                    
                    yield item_value
                    
                elif item_type == 'done':
                    total_time = (time.time() - start_time) * 1000
                    print(f"✅ Stream complete: {chunk_count} chunks, {total_bytes} bytes in {total_time:.0f}ms")
                    break
                    
                elif item_type == 'error':
                    print(f"❌ Streaming error: {item_value}")
                    raise item_value
                    
            except queue.Empty:
                print("❌ Streaming timeout after 30 seconds")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                break
        
        # Ensure thread cleanup
        thread.join(timeout=1)
        if thread.is_alive():
            print("⚠️ Background thread did not exit cleanly")
