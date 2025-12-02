"""
Chunk Size Management Utility

Ensures chunks are optimally sized for embedding models and vector search.
"""

import re
from typing import List, Dict

class ChunkSizeManager:
    """
    Manages chunk sizes to ensure optimal performance for embeddings and search.

    Why this matters:
    - Embedding models work best with 128-512 tokens
    - Too large: Information overload, poor embeddings, low accuracy
    - Too small: Lack of context, incomplete information
    - Just right: Best semantic representation and matching
    """

    # Optimal ranges based on sentence-transformers models
    MAX_TOKENS = 512   # Maximum tokens per chunk (hard limit)
    IDEAL_TOKENS = 256 # Target size for optimal embeddings
    MIN_TOKENS = 50    # Minimum to maintain context

    # Rough estimation: 1 token ≈ 0.75 words ≈ 4 characters
    MAX_CHARS = MAX_TOKENS * 4
    IDEAL_CHARS = IDEAL_TOKENS * 4
    MIN_CHARS = MIN_TOKENS * 4

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count (rough approximation).

        For accurate counting, use: tiktoken library
        For this use case, word count is sufficient.
        """
        return len(text.split())

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences while preserving meaning"""
        # Use regex to split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @classmethod
    def validate_chunk_size(cls, text: str) -> Dict[str, any]:
        """
        Check if chunk is appropriately sized.

        Returns:
            dict with 'status', 'tokens', 'recommendation'
        """
        tokens = cls.estimate_tokens(text)
        chars = len(text)

        if tokens > cls.MAX_TOKENS:
            return {
                'status': 'TOO_LARGE',
                'tokens': tokens,
                'chars': chars,
                'recommendation': f'Split into {tokens // cls.IDEAL_TOKENS + 1} chunks',
                'action_required': True
            }
        elif tokens < cls.MIN_TOKENS:
            return {
                'status': 'TOO_SMALL',
                'tokens': tokens,
                'chars': chars,
                'recommendation': 'Consider merging with adjacent chunks',
                'action_required': True
            }
        elif tokens > cls.IDEAL_TOKENS:
            return {
                'status': 'LARGE',
                'tokens': tokens,
                'chars': chars,
                'recommendation': 'Acceptable but could be split for better precision',
                'action_required': False
            }
        else:
            return {
                'status': 'OPTIMAL',
                'tokens': tokens,
                'chars': chars,
                'recommendation': 'Perfect size for embeddings',
                'action_required': False
            }

    @classmethod
    def split_oversized_chunk(
        cls,
        chunk_data: Dict,
        preserve_metadata: bool = True
    ) -> List[Dict]:
        """
        Split a chunk that's too large into smaller, optimal chunks.

        Strategy:
        1. Split by sentences (maintains semantic coherence)
        2. Group sentences to reach IDEAL_TOKENS
        3. Preserve metadata across all sub-chunks

        Args:
            chunk_data: Original chunk dict with 'content', 'chunk_id', 'field', 'metadata'
            preserve_metadata: Whether to copy metadata to sub-chunks

        Returns:
            List of optimally-sized chunks
        """
        text = chunk_data['content']
        tokens = cls.estimate_tokens(text)

        # If already optimal, return as-is
        if tokens <= cls.MAX_TOKENS:
            return [chunk_data]

        # Split into sentences
        sentences = cls.split_into_sentences(text)

        # Group sentences into optimal chunks
        sub_chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = cls.estimate_tokens(sentence)

            # If single sentence exceeds max, split by clauses/words
            if sentence_tokens > cls.MAX_TOKENS:
                # Save current chunk if exists
                if current_chunk:
                    sub_chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence by commas or semicolons
                parts = re.split(r'[,;]', sentence)
                for part in parts:
                    part = part.strip()
                    part_tokens = cls.estimate_tokens(part)

                    if current_tokens + part_tokens > cls.IDEAL_TOKENS and current_chunk:
                        sub_chunks.append(" ".join(current_chunk))
                        current_chunk = [part]
                        current_tokens = part_tokens
                    else:
                        current_chunk.append(part)
                        current_tokens += part_tokens
                continue

            # Add sentence to current chunk if within limits
            if current_tokens + sentence_tokens > cls.IDEAL_TOKENS and current_chunk:
                # Save current chunk and start new one
                sub_chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Don't forget the last chunk
        if current_chunk:
            sub_chunks.append(" ".join(current_chunk))

        # Create chunk dicts with metadata
        result_chunks = []
        original_id = chunk_data['chunk_id']

        for i, sub_text in enumerate(sub_chunks):
            new_chunk = {
                'chunk_id': f"{original_id}_part{i}",
                'field': chunk_data['field'],
                'content': sub_text,
                'metadata': {
                    **chunk_data['metadata'],
                    'is_split': True,
                    'original_chunk_id': original_id,
                    'part_number': i,
                    'total_parts': len(sub_chunks)
                } if preserve_metadata else chunk_data['metadata'].copy()
            }
            result_chunks.append(new_chunk)

        return result_chunks

    @classmethod
    def process_chunks(cls, chunks: List[Dict]) -> List[Dict]:
        """
        Process all chunks, splitting oversized ones.

        Args:
            chunks: List of chunk dictionaries

        Returns:
            List of optimally-sized chunks (may be larger than input)
        """
        processed_chunks = []

        for chunk in chunks:
            validation = cls.validate_chunk_size(chunk['content'])

            if validation['status'] == 'TOO_LARGE':
                # Split oversized chunk
                sub_chunks = cls.split_oversized_chunk(chunk)
                processed_chunks.extend(sub_chunks)
                print(f"⚠️ Split large chunk '{chunk['chunk_id']}' "
                      f"({validation['tokens']} tokens) into {len(sub_chunks)} parts")
            else:
                # Keep as-is
                processed_chunks.append(chunk)
                if validation['status'] == 'OPTIMAL':
                    print(f"✅ Chunk '{chunk['chunk_id']}' size optimal ({validation['tokens']} tokens)")
                elif validation['status'] == 'LARGE':
                    print(f"⚠️ Chunk '{chunk['chunk_id']}' is large ({validation['tokens']} tokens) but acceptable")
                else:  # TOO_SMALL
                    print(f"ℹ️ Chunk '{chunk['chunk_id']}' is small ({validation['tokens']} tokens)")

        return processed_chunks

    @classmethod
    def get_statistics(cls, chunks: List[Dict]) -> Dict:
        """Get statistics about chunk sizes"""
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_tokens': 0,
                'min_tokens': 0,
                'max_tokens': 0,
                'oversized_count': 0,
                'undersized_count': 0,
                'optimal_count': 0
            }

        token_counts = [cls.estimate_tokens(c['content']) for c in chunks]

        oversized = sum(1 for t in token_counts if t > cls.MAX_TOKENS)
        undersized = sum(1 for t in token_counts if t < cls.MIN_TOKENS)
        optimal = sum(1 for t in token_counts if cls.MIN_TOKENS <= t <= cls.IDEAL_TOKENS)

        return {
            'total_chunks': len(chunks),
            'avg_tokens': sum(token_counts) // len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'oversized_count': oversized,
            'undersized_count': undersized,
            'optimal_count': optimal,
            'optimal_percentage': round(optimal / len(chunks) * 100, 1)
        }


# Convenience function
def validate_and_split_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    One-line function to validate and split chunks.

    Usage:
        chunks = processor.generate_resume_chunks(resume_json, resume_id)
        optimized_chunks = validate_and_split_chunks(chunks)
    """
    manager = ChunkSizeManager()
    return manager.process_chunks(chunks)
