import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from config import Config
from prompt.extract_resume import generate_resume_extraction_prompt
from typing import List, Dict, Union, Tuple
import json
import hashlib
import google.generativeai as genai
from utils.cache_manager import create_text_cache
from utils.chunk_size_manager import validate_and_split_chunks
from utils.logger import get_logger, log_execution_time
from utils.text_utils import extract_json_from_text
from utils.exceptions import (
    ResumeParsingError,
    PDFExtractionError,
    LLMError,
    MissingAPIKeyError
)

# Initialize logger
logger = get_logger(__name__)

class ResumePreprocessor:
    def __init__(self, api_key: str = None, enable_cache: bool = True):
        """
        Initialize resume preprocessor with LLM client and cache

        Args:
            api_key: Google API key (optional, will use config if not provided)
            enable_cache: Whether to enable response caching

        Raises:
            MissingAPIKeyError: If API key is not found
        """
        try:
            logger.info("Initializing ResumePreprocessor")

            if api_key is None:
                api_key = Config.GOOGLE_API_KEY
            if not api_key:
                raise MissingAPIKeyError(
                    "Google API key not found. Please set GOOGLE_API_KEY in .env file"
                )

            genai.configure(api_key=api_key)
            self.llm_client = genai.GenerativeModel(Config.RESUME_LLM_MODEL)
            logger.debug(f"LLM client initialized with {Config.RESUME_LLM_MODEL}")

            # Initialize cache
            self.enable_cache = enable_cache if enable_cache is not None else Config.ENABLE_CACHE
            if self.enable_cache:
                self.cache = create_text_cache(cache_dir=Config.RESUME_CACHE_DIR)
                logger.info("LLM response caching enabled")
            else:
                logger.info("LLM response caching disabled")

            logger.info("ResumePreprocessor initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize ResumePreprocessor: {str(e)}", exc_info=True)
            raise
    
    def _get_cache_key(self, content: Union[str, bytes]) -> str:
        """Generate a cache key from content (text or PDF bytes)"""
        if isinstance(content, str):
            return content
        else:
            # For PDF bytes, use hash as cache key
            return hashlib.sha256(content).hexdigest()

    @log_execution_time(logger)
    def parse_with_llm(self, resume_input: Union[str, bytes], is_pdf: bool = False) -> Dict:
        """
        Parse resume using LLM

        Args:
            resume_input: Either text string or PDF file bytes
            is_pdf: True if resume_input is PDF bytes, False if it's text

        Returns:
            Dictionary containing parsed resume data

        Raises:
            PDFExtractionError: If PDF processing fails
            LLMError: If LLM API call fails
            ResumeParsingError: If response parsing fails
        """
        try:
            logger.info(f"Parsing resume (PDF: {is_pdf})")

            # Generate cache key
            cache_key = self._get_cache_key(resume_input)

            # Check cache first if enabled
            if self.enable_cache:
                cached_result = self.cache.get(cache_key, max_age_days=Config.CACHE_MAX_AGE_DAYS)
                if cached_result is not None:
                    logger.info("Using cached LLM response (cache hit)")
                    return cached_result

            # Cache miss or caching disabled - call LLM
            logger.debug("Cache miss - calling Gemini API")

            if is_pdf:
                # Upload PDF file to Gemini
                logger.info("Uploading PDF to Gemini for processing")

                # Save PDF bytes to a temporary file for upload
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(resume_input)
                    tmp_path = tmp_file.name

                try:
                    # Upload file to Gemini
                    uploaded_file = genai.upload_file(tmp_path)
                    logger.debug(f"PDF uploaded: {uploaded_file.name}")

                    # Wait for file processing
                    import time
                    attempts = 0
                    max_attempts = Config.MAX_PDF_UPLOAD_ATTEMPTS
                    while uploaded_file.state.name == "PROCESSING":
                        logger.debug(f"Processing PDF (attempt {attempts+1}/{max_attempts})")
                        time.sleep(1)
                        uploaded_file = genai.get_file(uploaded_file.name)
                        attempts += 1
                        if attempts >= max_attempts:
                            raise PDFExtractionError(
                                "PDF processing timeout",
                                details={'attempts': attempts}
                            )

                    if uploaded_file.state.name == "FAILED":
                        raise PDFExtractionError("PDF processing failed on server")

                    logger.debug("PDF processed successfully, generating content")
                    response = self.llm_client.generate_content([generate_resume_extraction_prompt(), uploaded_file])

                    # Clean up uploaded file
                    genai.delete_file(uploaded_file.name)
                    logger.debug("Cleaned up uploaded file")

                except Exception as e:
                    logger.error(f"PDF processing error: {str(e)}", exc_info=True)
                    if isinstance(e, (PDFExtractionError, LLMError)):
                        raise
                    raise PDFExtractionError(
                        f"Failed to process PDF: {str(e)}",
                        details={'error_type': type(e).__name__}
                    )
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        logger.debug("Cleaned up temporary file")
            else:
                # Use text-based prompt
                logger.debug("Using text-based extraction")
                prompt = generate_resume_extraction_prompt() + f""" Resume Text:
                {resume_input}
                """
                try:
                    response = self.llm_client.generate_content(prompt)
                except Exception as e:
                    logger.error(f"LLM API call failed: {str(e)}", exc_info=True)
                    raise LLMError(
                        f"Failed to call LLM API: {str(e)}",
                        details={'model': 'gemini-2.5-flash'}
                    )

            # Parse response
            response_text = response.text.strip()
            logger.debug(f"Received response ({len(response_text)} chars)")

            try:
                # Extract JSON using utility function
                json_str = extract_json_from_text(response_text)
                if json_str:
                    data = json.loads(json_str)
                    logger.debug("Response parsed as valid JSON")
                else:
                    data = {}
                    logger.warning("No JSON found in response, using empty dict")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from response: {str(e)}")
                raise ResumeParsingError(
                    "Failed to parse LLM response as JSON",
                    details={'response_preview': response_text[:Config.CHUNK_PREVIEW_LENGTH]}
                )

            # Ensure all required fields exist with default empty arrays
            data.setdefault("name", "Unknown")
            data.setdefault("experience", [])
            data.setdefault("skills", [])
            data.setdefault("education", [])
            data.setdefault("projects", [])

            logger.info(f"Resume parsed successfully: name={data.get('name')}, "
                       f"skills={len(data.get('skills', []))}, "
                       f"experience={len(data.get('experience', []))}")

            # Save to cache for future use
            if self.enable_cache:
                self.cache.set(cache_key, data)
                logger.debug("Response cached for future use")

            return data

        except Exception as e:
            logger.error(f"Resume parsing failed: {str(e)}", exc_info=True)
            if isinstance(e, (PDFExtractionError, LLMError, ResumeParsingError)):
                raise
            raise ResumeParsingError(
                f"Unexpected error during resume parsing: {str(e)}",
                details={'error_type': type(e).__name__}
            )

    def generate_resume_chunks(self, resume_json, resume_id):

        chunks = []

        # Skills
        if resume_json.get("skills"):
            chunks.append({
                "chunk_id": f"{resume_id}_skills",
                "field": "skills",
                "content": "Skills: " + ", ".join(resume_json["skills"]),
                "metadata": {
                    "document_id": resume_id,
                    "document_type": "resume",
                    "field": "skills"
                }
            })
            
        for i, exp in enumerate(resume_json.get("experience", [])):
            # Combine achievements into one string for embedding/chunking
            achievements_text = " ".join(exp.get("achievements", []))
            
            # Optional: include period/location in the text for context
            period = exp.get("period", "")
            location = exp.get("location", "")
            
            text_parts = [
                f"Role: {exp.get('role', '')}",
                f"Company: {exp.get('company', '')}"
            ]
            if period:
                text_parts.append(f"Period: {period}")
            if location:
                text_parts.append(f"Location: {location}")
            if achievements_text:
                text_parts.append(f"Achievements: {achievements_text}")
            
            chunk_text = " | ".join(text_parts)
            
            chunks.append({
                "chunk_id": f"{resume_id}_{i}_experience",
                "field": "experience",
                "content": chunk_text.strip(),
                "metadata": {
                    "document_id": resume_id,
                    "document_type": "resume",
                    "field": "experience"
                }
            })

        for i, edu in enumerate(resume_json.get("education", [])):
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            period = edu.get("period", "")
            details = edu.get("details", "")  # optional extra info

            # Build a single string to represent this education entry for embedding
            text_parts = [f"{degree} at {school}"]  # required fields
            if period:
                text_parts.append(f"Period: {period}")
            if details:
                text_parts.append(details)

            text = " | ".join(text_parts)

            chunks.append({
                "chunk_id": f"{resume_id}_{i}_education",
                "field": "education",
                "content": text.strip(),
                "metadata": {
                    "document_id": resume_id,
                    "document_type": "resume",
                    "field": "education"
                }
            })
            
        for i, proj in enumerate(resume_json.get("projects", [])):
            name = proj.get("name", "")
            desc = proj.get("description", "")
            text = f"Project: {name} — {desc}"
            chunks.append({
                "chunk_id": f"{resume_id}_{i}_projects",
                "field": "projects",
                "content": text.strip(),
                "metadata": {
                    "document_id": resume_id,
                    "document_type": "resume",
                    "field": "projects"
                }
            })
        
        return chunks
        
    @log_execution_time(logger)
    def preprocess_resume(
        self,
        resume_input: Union[str, bytes],
        resume_id: str = None,
        is_pdf: bool = False
    ) -> Tuple[List[Dict], Dict]:
        """
        Preprocess resume from text or PDF

        Args:
            resume_input: Either text string or PDF file bytes
            resume_id: Unique identifier for the resume
            is_pdf: True if resume_input is PDF bytes, False if it's text

        Returns:
            Tuple of (optimized_chunks, resume_data) where resume_data contains the extracted information

        Raises:
            ResumeParsingError: If preprocessing fails
        """
        try:
            logger.info(f"Preprocessing resume (ID: {resume_id}, PDF: {is_pdf})")

            # Parse resume with LLM
            sections = self.parse_with_llm(resume_input, is_pdf=is_pdf)
            logger.debug(f"Extracted {len(sections)} sections from resume")

            # Generate chunks
            chunks = self.generate_resume_chunks(sections, resume_id)
            logger.debug(f"Generated {len(chunks)} chunks")

            # Optimize chunk sizes for better matching accuracy
            logger.debug("Optimizing chunk sizes")
            optimized_chunks = validate_and_split_chunks(chunks)
            logger.info(f"Chunk optimization complete: {len(chunks)} → {len(optimized_chunks)} chunks")

            return optimized_chunks, sections

        except Exception as e:
            logger.error(f"Resume preprocessing failed: {str(e)}", exc_info=True)
            if isinstance(e, (PDFExtractionError, LLMError, ResumeParsingError)):
                raise
            raise ResumeParsingError(
                f"Failed to preprocess resume: {str(e)}",
                details={'resume_id': resume_id, 'is_pdf': is_pdf}
            )
