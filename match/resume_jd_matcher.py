"""
Resume-JD Matching Logic
Merges resume chunks and compares with JD to determine qualification
"""

import json
from typing import Dict, List, Any, Optional
from functools import lru_cache
import hashlib
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from config import Config
from prompt.match_resume_jd import generate_match_prompt
import google.generativeai as genai
from utils.logger import get_logger, log_execution_time
from utils.text_utils import extract_json_from_text, truncate_text
from utils.exceptions import MissingAPIKeyError, LLMError

# Initialize logger
logger = get_logger(__name__)


class ResumeJDMatcher:
    """Matches resumes with job descriptions and provides qualification analysis"""

    def __init__(self, api_key: str = None):
        """
        Initialize the matcher with LLM client

        Args:
            api_key: Google API key (optional, will use config if not provided)

        Raises:
            MissingAPIKeyError: If API key is not found
        """
        try:
            logger.info("Initializing ResumeJDMatcher")

            if api_key is None:
                api_key = Config.GOOGLE_API_KEY
            if not api_key:
                raise MissingAPIKeyError(
                    "Google API key not found. Please set GOOGLE_API_KEY in .env file"
                )

            genai.configure(api_key=api_key)
            self.llm_client = genai.GenerativeModel(Config.MATCHING_LLM_MODEL)
            logger.debug(f"LLM client initialized with {Config.MATCHING_LLM_MODEL}")

            # Initialize cache for merged content
            self._merge_cache = {}

            logger.info("ResumeJDMatcher initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize ResumeJDMatcher: {str(e)}", exc_info=True)
            raise

    def _generate_chunks_hash(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Generate a unique hash for a list of chunks

        Args:
            chunks: List of chunk dictionaries

        Returns:
            Hash string
        """
        # Create a deterministic string representation
        chunk_str = json.dumps(chunks, sort_keys=True)
        return hashlib.md5(chunk_str.encode()).hexdigest()

    def merge_resume_chunks(self, chunks: List[Dict[str, Any]], resume_id: str = None) -> str:
        """
        Merge all chunks of a resume into a single text (with caching)

        Args:
            chunks: List of chunk dictionaries with 'field' and 'content'
            resume_id: Optional resume ID for cache key (more readable)

        Returns:
            Merged resume content as a single string
        """
        if not chunks:
            return ""

        # Check cache first
        cache_key = resume_id if resume_id else self._generate_chunks_hash(chunks)
        if cache_key in self._merge_cache:
            logger.debug(f"Cache hit for resume merge: {cache_key}")
            return self._merge_cache[cache_key]

        # Group chunks by field
        field_groups = {}
        for chunk in chunks:
            field = chunk.get('metadata', {}).get('field', 'unknown')
            content = chunk.get('content', '')

            if field not in field_groups:
                field_groups[field] = []
            field_groups[field].append(content)

        # Merge chunks with field headers
        merged_sections = []

        # Define field order for better readability
        field_order = [
            'summary',
            'experience',
            'skills',
            'education',
            'certifications',
            'projects',
            'achievements'
        ]

        # Add fields in preferred order
        for field in field_order:
            if field in field_groups:
                section_content = '\n'.join(field_groups[field])
                merged_sections.append(f"## {field.upper()}\n{section_content}")

        # Add any remaining fields not in the order
        for field, contents in field_groups.items():
            if field not in field_order:
                section_content = '\n'.join(contents)
                merged_sections.append(f"## {field.upper()}\n{section_content}")

        merged_content = '\n\n'.join(merged_sections)

        # Cache the result
        self._merge_cache[cache_key] = merged_content
        logger.debug(f"Cached resume merge: {cache_key}")

        return merged_content

    def merge_jd_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Merge all chunks of a job description into a single text

        Args:
            chunks: List of JD chunk dictionaries

        Returns:
            Merged JD content as a single string
        """
        if not chunks:
            return ""

        # Group chunks by field
        field_groups = {}
        for chunk in chunks:
            field = chunk.get('metadata', {}).get('field', 'unknown')
            content = chunk.get('content', '')

            if field not in field_groups:
                field_groups[field] = []
            field_groups[field].append(content)

        # Merge chunks with field headers
        merged_sections = []
        for field, contents in field_groups.items():
            section_content = '\n'.join(contents)
            merged_sections.append(f"## {field.upper()}\n{section_content}")

        return '\n\n'.join(merged_sections)

    def clear_cache(self):
        """Clear the merge cache"""
        self._merge_cache.clear()
        logger.info("Merge cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'cached_items': len(self._merge_cache),
            'total_memory_chars': sum(len(v) for v in self._merge_cache.values())
        }

    @log_execution_time(logger)
    def match_resume_with_jd(
        self,
        resume_chunks: List[Dict[str, Any]],
        jd_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Match a resume with a job description and get qualification result

        Args:
            resume_chunks: List of resume chunk dictionaries
            jd_chunks: List of JD chunk dictionaries

        Returns:
            Dictionary containing match results with qualification decision
        """
        try:
            logger.info("Matching resume with job description")

            # Merge chunks
            resume_content = self.merge_resume_chunks(resume_chunks)
            jd_content = self.merge_jd_chunks(jd_chunks)

            if not resume_content or not jd_content:
                logger.warning("Missing resume or job description content")
                return {
                    "qualified": False,
                    "match_score": 0,
                    "summary": "Missing resume or job description content",
                    "error": "Insufficient data for matching"
                }

            # Generate prompt
            prompt = generate_match_prompt(resume_content, jd_content)

            # Call LLM
            try:
                response = self.llm_client.generate_content(prompt)
                response_text = response.text.strip()
                logger.debug(f"Received match response ({len(response_text)} chars)")
            except Exception as e:
                logger.error(f"LLM API call failed: {str(e)}", exc_info=True)
                raise LLMError(
                    f"Failed to call LLM API: {str(e)}",
                    details={'model': Config.MATCHING_LLM_MODEL}
                )

            # Parse JSON response
            try:
                json_str = extract_json_from_text(response_text)
                if json_str:
                    result = json.loads(json_str)
                    logger.info(f"Match completed: score={result.get('match_score', 0)}")
                    return result
                else:
                    logger.error("No JSON found in LLM response")
                    return {
                        "qualified": False,
                        "match_score": 0,
                        "summary": "Error parsing match results",
                        "error": "No JSON found in response",
                        "raw_response": truncate_text(response_text, 500)
                    }

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                return {
                    "qualified": False,
                    "match_score": 0,
                    "summary": "Error parsing match results",
                    "error": f"JSON parsing failed: {str(e)}",
                    "raw_response": truncate_text(response_text, 500)
                }

        except Exception as e:
            logger.error(f"Matching failed: {str(e)}", exc_info=True)
            return {
                "qualified": False,
                "match_score": 0,
                "summary": "Error during matching process",
                "error": str(e)
            }

    def batch_match_resumes(
        self,
        resume_chunks_list: List[tuple],
        jd_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match multiple resumes with a single job description (Precise Mode)

        Args:
            resume_chunks_list: List of tuples (resume_id, resume_chunks)
            jd_chunks: List of JD chunk dictionaries

        Returns:
            List of match results for each resume
        """
        results = []

        for resume_id, resume_chunks in resume_chunks_list:
            match_result = self.match_resume_with_jd(resume_chunks, jd_chunks)
            match_result['resume_id'] = resume_id
            results.append(match_result)

        # Sort by match_score descending
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        return results

    @log_execution_time(logger)
    def rough_match_resumes(
        self,
        db_storage,
        jd_text: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Rough matching mode: Query JD against all resume chunks and rank by similarity

        Args:
            db_storage: ChromaDB storage instance
            jd_text: Job description text to query
            top_k: Number of top chunks to retrieve (default from config)

        Returns:
            List of resume rankings with scores
        """
        if top_k is None:
            top_k = Config.ROUGH_MATCH_TOP_K

        logger.info(f"Running rough match with top_k={top_k}")

        # Search for similar resume chunks using JD text
        search_results = db_storage.search_similar_chunks(
            query_text=jd_text,
            document_type="resume",
            top_k=top_k
        )

        logger.debug(f"Retrieved {len(search_results)} chunk results")

        # Aggregate scores by resume_id
        resume_scores = {}
        resume_chunk_counts = {}
        resume_top_chunks = {}

        for result in search_results:
            resume_id = result['metadata'].get('document_id')
            similarity = result.get('similarity', 0)

            if resume_id:
                # Accumulate scores
                if resume_id not in resume_scores:
                    resume_scores[resume_id] = 0
                    resume_chunk_counts[resume_id] = 0
                    resume_top_chunks[resume_id] = []

                resume_scores[resume_id] += similarity
                resume_chunk_counts[resume_id] += 1

                # Keep track of top matching chunks for this resume
                resume_top_chunks[resume_id].append({
                    'chunk_id': result['chunk_id'],
                    'field': result['metadata'].get('field', 'unknown'),
                    'content': truncate_text(result['content'], Config.CHUNK_PREVIEW_LENGTH),
                    'similarity': similarity
                })

        # Calculate average scores and create results
        results = []
        for resume_id, total_score in resume_scores.items():
            chunk_count = resume_chunk_counts[resume_id]
            avg_score = total_score / chunk_count if chunk_count > 0 else 0

            # Convert similarity to 0-100 scale
            # ChromaDB cosine similarity is typically in [0, 1] range
            # Apply non-linear scaling to better differentiate candidates
            if avg_score >= 0 and avg_score <= 1:
                # Direct percentage conversion with slight boosting for high scores
                # This makes scores above 0.8 more competitive
                if avg_score >= 0.8:
                    match_score = 80 + (avg_score - 0.8) * 100  # 0.8-1.0 → 80-100
                else:
                    match_score = avg_score * 100  # 0-0.8 → 0-80
            else:
                # Fallback for other similarity metrics (e.g., dot product)
                match_score = max(0, min(100, (avg_score + 1) * 50))

            match_score = round(match_score, 2)

            # Determine qualification based on score
            qualified = match_score >= Config.MIN_MATCH_SCORE

            # Determine recommendation
            if match_score >= Config.STRONG_MATCH_THRESHOLD:
                recommendation = "STRONG_MATCH"
            elif match_score >= Config.GOOD_MATCH_THRESHOLD:
                recommendation = "GOOD_MATCH"
            elif match_score >= Config.PARTIAL_MATCH_THRESHOLD:
                recommendation = "PARTIAL_MATCH"
            else:
                recommendation = "NOT_MATCH"

            results.append({
                'resume_id': resume_id,
                'qualified': qualified,
                'match_score': match_score,
                'recommendation': recommendation,
                'summary': f"Found {chunk_count} matching chunks with average similarity {avg_score:.3f}",
                'matching_chunks_count': chunk_count,
                'total_similarity': round(total_score, 4),
                'average_similarity': round(avg_score, 4),
                'top_matching_chunks': resume_top_chunks[resume_id][:5],  # Top 5 chunks
                'matching_mode': 'rough'
            })

        # Sort by match_score descending
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        logger.info(f"Rough match completed: found {len(results)} candidate resumes")
        return results

    @log_execution_time(logger)
    def hybrid_match_resumes(
        self,
        db_storage,
        jd_text: str,
        jd_chunks: List[Dict[str, Any]],
        rough_top_k: int = None,
        precise_top_n: int = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid matching mode: First filter with rough matching, then precise analysis on top candidates

        Args:
            db_storage: ChromaDB storage instance
            jd_text: Job description text for rough matching
            jd_chunks: JD chunks for precise matching
            rough_top_k: Number of chunks to retrieve in rough mode (default from config)
            precise_top_n: Number of top resumes to analyze with precise mode (default from config)

        Returns:
            List of match results with both rough and precise analysis for top candidates
        """
        if rough_top_k is None:
            rough_top_k = Config.HYBRID_ROUGH_TOP_K
        if precise_top_n is None:
            precise_top_n = Config.HYBRID_PRECISE_TOP_N

        logger.info(f"[Hybrid Mode] Step 1: Running rough matching with top_k={rough_top_k}")

        # Step 1: Rough matching to filter candidates
        rough_results = self.rough_match_resumes(
            db_storage=db_storage,
            jd_text=jd_text,
            top_k=rough_top_k
        )

        if not rough_results:
            logger.warning("[Hybrid Mode] No results from rough matching")
            return []

        logger.info(f"[Hybrid Mode] Found {len(rough_results)} resumes in rough matching")
        logger.info(f"[Hybrid Mode] Step 2: Running precise matching on top {precise_top_n} resumes")

        # Step 2: Get top N resumes from rough matching
        top_resumes = rough_results[:precise_top_n]
        top_resume_ids = [r['resume_id'] for r in top_resumes]

        # Step 3: Prepare resume chunks for precise matching
        resume_chunks_list = []
        for resume_id in top_resume_ids:
            resume_chunks = db_storage.get_chunks_by_document(resume_id)
            if resume_chunks:
                resume_chunks_list.append((resume_id, resume_chunks))

        # Step 4: Run precise matching on filtered resumes
        precise_results = []
        for resume_id, resume_chunks in resume_chunks_list:
            logger.debug(f"[Hybrid Mode] Analyzing {resume_id} with LLM")
            precise_result = self.match_resume_with_jd(resume_chunks, jd_chunks)
            precise_result['resume_id'] = resume_id

            # Add rough matching info to precise result
            rough_info = next((r for r in top_resumes if r['resume_id'] == resume_id), None)
            if rough_info:
                precise_result['rough_match_score'] = rough_info.get('match_score', 0)
                precise_result['rough_similarity'] = rough_info.get('average_similarity', 0)
                precise_result['rough_matching_chunks'] = rough_info.get('matching_chunks_count', 0)

            precise_result['matching_mode'] = 'hybrid'
            precise_results.append(precise_result)

        # Step 5: Include remaining rough results without precise analysis
        remaining_resumes = rough_results[precise_top_n:]
        for result in remaining_resumes:
            result['matching_mode'] = 'hybrid_rough_only'
            result['note'] = 'Filtered out after rough matching - did not qualify for precise analysis'

        # Combine results
        all_results = precise_results + remaining_resumes

        # Sort by match_score descending (precise results will naturally rank higher)
        all_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        logger.info(
            f"[Hybrid Mode] Complete: {len(precise_results)} with precise analysis, "
            f"{len(remaining_resumes)} rough only"
        )

        return all_results

    @log_execution_time(logger)
    def explain_match(
        self,
        resume_id: str,
        resume_chunks: List[Dict[str, Any]],
        jd_chunks: List[Dict[str, Any]],
        match_result: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate detailed explanation for why a resume matches or doesn't match a JD

        Args:
            resume_id: Resume identifier
            resume_chunks: List of resume chunk dictionaries
            jd_chunks: List of JD chunk dictionaries
            match_result: Optional pre-computed match result to enhance

        Returns:
            Dictionary with detailed explanation including:
            - Top matching sections
            - Missing requirements
            - Standout qualities
            - Visual match breakdown
        """
        try:
            logger.info(f"Generating match explanation for {resume_id}")

            # Get or compute match result
            if match_result is None:
                match_result = self.match_resume_with_jd(resume_chunks, jd_chunks)

            # Extract resume content by field
            resume_by_field = {}
            for chunk in resume_chunks:
                field = chunk.get('metadata', {}).get('field', 'unknown')
                content = chunk.get('content', '')
                if field not in resume_by_field:
                    resume_by_field[field] = []
                resume_by_field[field].append(content)

            # Extract JD requirements by field
            jd_by_field = {}
            for chunk in jd_chunks:
                field = chunk.get('metadata', {}).get('field', 'unknown')
                content = chunk.get('content', '')
                if field not in jd_by_field:
                    jd_by_field[field] = []
                jd_by_field[field].append(content)

            # Build explanation
            explanation = {
                'resume_id': resume_id,
                'overall_score': match_result.get('match_score', 0),
                'qualified': match_result.get('qualified', False),
                'recommendation': match_result.get('recommendation', 'UNKNOWN'),

                # Breakdown by section
                'field_breakdown': {},

                # Key insights
                'top_strengths': match_result.get('strengths', [])[:3],
                'top_weaknesses': match_result.get('weaknesses', [])[:3],

                # Actionable insights
                'missing_skills': [],
                'standout_qualities': [],

                # Detailed analysis
                'detailed_scores': match_result.get('detailed_analysis', {}),

                # Summary
                'summary': match_result.get('summary', ''),
                'next_steps': match_result.get('next_steps', 'Review candidate profile')
            }

            # Analyze field coverage
            for field in ['skills', 'experience', 'education', 'certifications']:
                has_resume = field in resume_by_field and resume_by_field[field]
                has_jd = field in jd_by_field and jd_by_field[field]

                explanation['field_breakdown'][field] = {
                    'resume_has': has_resume,
                    'jd_requires': has_jd,
                    'match_status': 'match' if (has_resume and has_jd) else
                                   ('missing' if has_jd else 'extra'),
                    'resume_content_preview': ' '.join(resume_by_field.get(field, []))[:200] if has_resume else None,
                    'jd_requirement_preview': ' '.join(jd_by_field.get(field, []))[:200] if has_jd else None
                }

            # Extract missing skills from weaknesses
            for weakness in match_result.get('weaknesses', []):
                if any(keyword in weakness.lower() for keyword in ['lack', 'missing', 'no', 'limited', 'insufficient']):
                    explanation['missing_skills'].append(weakness)

            # Extract standout qualities from strengths
            for strength in match_result.get('strengths', []):
                if any(keyword in strength.lower() for keyword in ['strong', 'excellent', 'extensive', 'proven', 'expert']):
                    explanation['standout_qualities'].append(strength)

            logger.info(f"Match explanation generated for {resume_id}")
            return explanation

        except Exception as e:
            logger.error(f"Failed to generate match explanation: {str(e)}", exc_info=True)
            return {
                'resume_id': resume_id,
                'error': str(e),
                'summary': 'Failed to generate explanation'
            }

    def batch_explain_matches(
        self,
        match_results: List[Dict[str, Any]],
        resume_chunks_dict: Dict[str, List[Dict[str, Any]]],
        jd_chunks: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate explanations for top N match results

        Args:
            match_results: List of match results from matching methods
            resume_chunks_dict: Dictionary mapping resume_id to chunks
            jd_chunks: JD chunks
            top_n: Number of top results to explain

        Returns:
            List of explanations for top N candidates
        """
        explanations = []

        # Sort by score and take top N
        sorted_results = sorted(match_results, key=lambda x: x.get('match_score', 0), reverse=True)
        top_results = sorted_results[:top_n]

        for result in top_results:
            resume_id = result.get('resume_id')
            if resume_id and resume_id in resume_chunks_dict:
                explanation = self.explain_match(
                    resume_id=resume_id,
                    resume_chunks=resume_chunks_dict[resume_id],
                    jd_chunks=jd_chunks,
                    match_result=result
                )
                explanations.append(explanation)

        return explanations

    def calculate_adaptive_parameters(
        self,
        db_storage,
        mode: str = 'hybrid'
    ) -> Dict[str, int]:
        """
        Dynamically calculate optimal matching parameters based on database size

        Args:
            db_storage: ChromaDB storage instance
            mode: Matching mode ('rough', 'hybrid')

        Returns:
            Dictionary with recommended parameters
        """
        try:
            # Get total resume count
            total_resumes = db_storage.count_documents(document_type='resume')

            logger.info(f"Calculating adaptive parameters for {total_resumes} resumes in {mode} mode")

            if mode == 'rough':
                # For rough mode, adjust top_k based on database size
                if total_resumes <= 20:
                    top_k = total_resumes * 3  # Small DB: get more chunks per resume
                elif total_resumes <= 100:
                    top_k = 50  # Medium DB: standard setting
                elif total_resumes <= 500:
                    top_k = min(100, total_resumes // 2)  # Large DB: proportional
                else:
                    top_k = 200  # Very large DB: cap at 200

                params = {
                    'top_k': top_k,
                    'total_resumes': total_resumes
                }

            elif mode == 'hybrid':
                # For hybrid mode, calculate both rough and precise parameters
                if total_resumes <= 10:
                    # Very small DB: use precise mode for all
                    rough_top_k = total_resumes * 5
                    precise_top_n = total_resumes
                elif total_resumes <= 50:
                    # Small DB: analyze 50% with LLM
                    rough_top_k = total_resumes * 3
                    precise_top_n = max(5, total_resumes // 2)
                elif total_resumes <= 200:
                    # Medium DB: analyze top 20%
                    rough_top_k = min(100, total_resumes)
                    precise_top_n = max(10, total_resumes // 5)
                elif total_resumes <= 1000:
                    # Large DB: analyze top 5%
                    rough_top_k = 200
                    precise_top_n = max(15, total_resumes // 20)
                else:
                    # Very large DB: fixed cap
                    rough_top_k = 300
                    precise_top_n = 20

                params = {
                    'rough_top_k': rough_top_k,
                    'precise_top_n': precise_top_n,
                    'total_resumes': total_resumes,
                    'precise_percentage': round((precise_top_n / total_resumes) * 100, 1) if total_resumes > 0 else 0
                }

            else:
                # Default to config values
                params = {
                    'rough_top_k': Config.HYBRID_ROUGH_TOP_K,
                    'precise_top_n': Config.HYBRID_PRECISE_TOP_N,
                    'total_resumes': total_resumes
                }

            logger.info(f"Adaptive parameters: {params}")
            return params

        except Exception as e:
            logger.error(f"Failed to calculate adaptive parameters: {str(e)}", exc_info=True)
            # Fallback to config defaults
            return {
                'rough_top_k': Config.HYBRID_ROUGH_TOP_K,
                'precise_top_n': Config.HYBRID_PRECISE_TOP_N,
                'total_resumes': 0
            }

    @log_execution_time(logger)
    def adaptive_hybrid_match(
        self,
        db_storage,
        jd_text: str,
        jd_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Hybrid matching with automatically adjusted parameters based on database size

        Args:
            db_storage: ChromaDB storage instance
            jd_text: Job description text for rough matching
            jd_chunks: JD chunks for precise matching

        Returns:
            List of match results with adaptive parameter selection
        """
        # Calculate optimal parameters
        params = self.calculate_adaptive_parameters(db_storage, mode='hybrid')

        logger.info(
            f"[Adaptive Hybrid] Using dynamic parameters: "
            f"rough_top_k={params['rough_top_k']}, "
            f"precise_top_n={params['precise_top_n']} "
            f"(analyzing {params.get('precise_percentage', 0)}% of {params['total_resumes']} resumes)"
        )

        # Use hybrid matching with calculated parameters
        return self.hybrid_match_resumes(
            db_storage=db_storage,
            jd_text=jd_text,
            jd_chunks=jd_chunks,
            rough_top_k=params['rough_top_k'],
            precise_top_n=params['precise_top_n']
        )
