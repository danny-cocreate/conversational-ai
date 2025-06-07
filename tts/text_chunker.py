"""
Smart Text Chunker for TTS Streaming
Intelligently splits text into chunks while preserving natural speech boundaries
"""

import re
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    text: str
    index: int
    is_final: bool
    original_start: int
    original_end: int

class SmartTextChunker:
    """
    Intelligently chunks text for TTS processing while maintaining natural speech flow
    """
    
    def __init__(self, max_chunk_size: int = 995):
        """
        Initialize the chunker
        
        Args:
            max_chunk_size: Maximum characters per chunk (maximize to 995 for 1000 char limit)
        """
        self.max_chunk_size = max_chunk_size
        
        # Sentence boundary patterns (in order of preference)
        self.sentence_endings = [
            r'[.!?]+\s+',           # Strong sentence endings with space
            r'[.!?]+$',             # Strong sentence endings at end
            r'[;]\s+',              # Semicolon with space
            r'[:]\s+',              # Colon with space (for lists, explanations)
            r'[,]\s+',              # Comma with space (weaker boundary)
        ]
        
        # Phrase boundary patterns (fallback)
        self.phrase_boundaries = [
            r'\s+(?:and|but|or|so|yet|for|nor|because|since|although|though|while|whereas|however|nevertheless|furthermore|moreover|therefore|thus|consequently|meanwhile|subsequently|finally|ultimately|in conclusion|in summary|additionally|furthermore)\s+',
            r'\s+(?:first|second|third|next|then|after|before|during|meanwhile|finally|lastly)\s+',
            r'\s+(?:for example|for instance|such as|including|like|namely|specifically|particularly)\s+',
            r'\s+(?:in other words|that is|i\.e\.|e\.g\.)\s+',
        ]
        
        # Word boundary pattern (last resort)
        self.word_boundary = r'\s+'
    
    def chunk_text(self, text: str) -> List[TextChunk]:
        """
        Split text into smart chunks that respect natural speech boundaries
        
        Args:
            text: Text to chunk
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # If text is already under the limit, return as single chunk
        if len(text) <= self.max_chunk_size:
            return [TextChunk(
                text=text,
                index=0,
                is_final=True,
                original_start=0,
                original_end=len(text)
            )]
        
        chunks = []
        remaining_text = text
        current_position = 0
        chunk_index = 0
        
        while remaining_text:
            if len(remaining_text) <= self.max_chunk_size:
                # Last chunk
                chunks.append(TextChunk(
                    text=remaining_text.strip(),
                    index=chunk_index,
                    is_final=True,
                    original_start=current_position,
                    original_end=current_position + len(remaining_text)
                ))
                break
            
            # Find the best split point
            chunk_text, split_position = self._find_best_split(remaining_text, self.max_chunk_size)
            
            if chunk_text:
                chunks.append(TextChunk(
                    text=chunk_text.strip(),
                    index=chunk_index,
                    is_final=False,
                    original_start=current_position,
                    original_end=current_position + len(chunk_text)
                ))
                
                # Update position and remaining text
                current_position += split_position
                remaining_text = remaining_text[split_position:].strip()
                chunk_index += 1
            else:
                # Fallback: force split at max size
                chunk_text = remaining_text[:self.max_chunk_size]
                chunks.append(TextChunk(
                    text=chunk_text.strip(),
                    index=chunk_index,
                    is_final=False,
                    original_start=current_position,
                    original_end=current_position + len(chunk_text)
                ))
                
                current_position += self.max_chunk_size
                remaining_text = remaining_text[self.max_chunk_size:].strip()
                chunk_index += 1
        
        # Mark the last chunk as final
        if chunks:
            chunks[-1].is_final = True
        
        return chunks
    
    def _find_best_split(self, text: str, max_size: int) -> Tuple[str, int]:
        """
        Find the best split point in the text that respects natural boundaries
        
        Args:
            text: Text to split
            max_size: Maximum size for this chunk
            
        Returns:
            Tuple of (chunk_text, split_position)
        """
        if len(text) <= max_size:
            return text, len(text)
        
        # Search window - look for split points in the last portion of the allowed size
        search_start = max(0, max_size // 2)  # Don't make chunks too small
        search_text = text[search_start:max_size + 100]  # Look a bit beyond max_size
        
        # Try sentence boundaries first (preferred)
        for pattern in self.sentence_endings:
            matches = list(re.finditer(pattern, search_text))
            if matches:
                # Find the last match within our size limit
                for match in reversed(matches):
                    split_pos = search_start + match.end()
                    if split_pos <= max_size:
                        return text[:split_pos], split_pos
        
        # Try phrase boundaries
        for pattern in self.phrase_boundaries:
            matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
            if matches:
                for match in reversed(matches):
                    split_pos = search_start + match.start()
                    if split_pos <= max_size and split_pos > search_start:
                        return text[:split_pos], split_pos
        
        # Try word boundaries (last resort)
        matches = list(re.finditer(self.word_boundary, text[:max_size]))
        if matches:
            # Find the last word boundary within the limit
            last_match = matches[-1]
            split_pos = last_match.start()
            if split_pos > max_size // 2:  # Don't make chunks too small
                return text[:split_pos], split_pos
        
        # Absolute fallback: split at max_size
        return text[:max_size], max_size
    
    def get_chunking_info(self, text: str) -> dict:
        """
        Get information about how text would be chunked
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with chunking statistics
        """
        chunks = self.chunk_text(text)
        
        return {
            'original_length': len(text),
            'chunk_count': len(chunks),
            'chunks': [
                {
                    'index': chunk.index,
                    'length': len(chunk.text),
                    'text_preview': chunk.text[:50] + '...' if len(chunk.text) > 50 else chunk.text,
                    'is_final': chunk.is_final
                }
                for chunk in chunks
            ],
            'avg_chunk_size': sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0,
            'max_chunk_size_used': max(len(chunk.text) for chunk in chunks) if chunks else 0
        }

# Convenience function for quick chunking
def chunk_text_for_tts(text: str, max_chunk_size: int = 995) -> List[str]:
    """
    Quick function to chunk text and return just the text strings
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of text chunks
    """
    chunker = SmartTextChunker(max_chunk_size)
    chunks = chunker.chunk_text(text)
    return [chunk.text for chunk in chunks]


if __name__ == "__main__":
    # Test the chunker
    test_text = """
    This is a long piece of text that needs to be chunked for TTS processing. It contains multiple sentences with various punctuation marks! Some sentences are longer than others, and we need to ensure that the chunking respects natural speech boundaries. For example, we shouldn't split in the middle of a sentence if we can avoid it. Instead, we should look for sentence endings, semicolons, or other natural pause points. This approach will result in much more natural-sounding speech synthesis, as the pauses will occur at appropriate points in the text. Additionally, this method helps maintain the semantic coherence of each chunk, which is important for both speech quality and listener comprehension.
    """
    
    chunker = SmartTextChunker(max_chunk_size=200)  # Small size for testing
    chunks = chunker.chunk_text(test_text)
    
    print("Chunking Results:")
    print(f"Original length: {len(test_text)} characters")
    print(f"Number of chunks: {len(chunks)}")
    print("\nChunks:")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i + 1} ({len(chunk.text)} chars):")
        print(f"'{chunk.text}'")
        print(f"Final: {chunk.is_final}")
