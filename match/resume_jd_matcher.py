"""
Resume-JD Matching Logic
Merges resume chunks and compares with JD to determine qualification
"""

import json
from typing import Dict, List, Any, Optional
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

            logger.info("ResumeJDMatcher initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize ResumeJDMatcher: {str(e)}", exc_info=True)
            raise

    def merge_resume_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Merge all chunks of a resume into a single text

        Args:
            chunks: List of chunk dictionaries with 'field' and 'content'

        Returns:
            Merged resume content as a single string
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

        return '\n\n'.join(merged_sections)

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
            # Assuming similarity is in range [-1, 1] or [0, 1]
            # Adjust this based on your actual similarity metric
            match_score = max(0, min(100, (avg_score + 1) * 50))  # Convert [-1,1] to [0,100]

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
                'match_score': round(match_score, 2),
                'recommendation': recommendation,
                'summary': f"Found {chunk_count} matching chunks with average similarity {avg_score:.2f}",
                'matching_chunks_count': chunk_count,
                'total_similarity': round(total_score, 2),
                'average_similarity': round(avg_score, 2),
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
