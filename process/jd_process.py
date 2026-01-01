import json
from typing import List, Dict
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from config import Config
from prompt.extract_job_description import generate_job_description_prompt
import google.generativeai as genai
from utils.chunk_size_manager import validate_and_split_chunks
from utils.text_utils import normalize_text, extract_json_from_text
from utils.logger import get_logger, log_execution_time
from utils.exceptions import MissingAPIKeyError, LLMError

# Initialize logger
logger = get_logger(__name__)


class JDPreprocessor:
    def __init__(self, api_key: str = None):
        """
        Initialize job description preprocessor with LLM client

        Args:
            api_key: Google API key (optional, will use config if not provided)

        Raises:
            MissingAPIKeyError: If API key is not found
        """
        try:
            logger.info("Initializing JDPreprocessor")

            if api_key is None:
                api_key = Config.GOOGLE_API_KEY
            if not api_key:
                raise MissingAPIKeyError(
                    "Google API key not found. Please set GOOGLE_API_KEY in .env file"
                )

            genai.configure(api_key=api_key)
            self.llm_client = genai.GenerativeModel(Config.JD_LLM_MODEL)
            logger.debug(f"LLM client initialized with {Config.JD_LLM_MODEL}")

            logger.info("JDPreprocessor initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize JDPreprocessor: {str(e)}", exc_info=True)
            raise
    
    @log_execution_time(logger)
    def parse_with_llm(self, jd_text: str) -> Dict[str, str]:
        """
        Parse job description using LLM

        Args:
            jd_text: Job description text

        Returns:
            Dictionary containing parsed JD data

        Raises:
            LLMError: If LLM API call fails
        """
        try:
            logger.info("Parsing job description with LLM")

            prompt = generate_job_description_prompt()

            try:
                response = self.llm_client.generate_content([prompt, jd_text])
                response_text = response.text.strip()
            except Exception as e:
                logger.error(f"LLM API call failed: {str(e)}", exc_info=True)
                raise LLMError(
                    f"Failed to call LLM API: {str(e)}",
                    details={'model': Config.JD_LLM_MODEL}
                )

            logger.debug(f"Received response ({len(response_text)} chars)")

            # Extract JSON using utility function
            json_str = extract_json_from_text(response_text)
            if json_str:
                try:
                    data = json.loads(json_str)
                    logger.debug("Response parsed as valid JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {str(e)}")
                    data = {}
            else:
                logger.warning("No JSON found in response, using empty dict")
                data = {}

            # Normalize string values only (skip nested dicts/lists)
            normalized_data = {}
            for key, val in data.items():
                if isinstance(val, str):
                    normalized_data[key] = normalize_text(val)
                else:
                    normalized_data[key] = val

            normalized_data["full_text"] = normalize_text(jd_text)

            logger.info("Job description parsed successfully")
            return normalized_data

        except Exception as e:
            logger.error(f"JD parsing failed: {str(e)}", exc_info=True)
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                f"Failed to parse job description: {str(e)}",
                details={'error_type': type(e).__name__}
            )
    
    def generate_hybrid_chunks(
            self,
            jd_json: Dict,
            jd_id: str = None
        ) -> List[Dict[str, str]]:
        """
        Generate chunks from JD JSON in a format aligned with resume chunks

        Args:
            jd_json: Parsed JD data
            jd_id: Job description identifier

        Returns:
            List of chunk dictionaries
        """
        if jd_id is None:
            import uuid
            jd_id = f"jd_{uuid.uuid4().hex[:12]}"

        chunks = []

        def add_chunk(field_name: str, content: str, chunk_index: int = None):
            """Add chunk to list"""
            if content.strip():
                chunk_suffix = f"_{chunk_index}_{field_name}" if chunk_index is not None else f"_{field_name}"
                chunks.append({
                    "chunk_id": f"{jd_id}{chunk_suffix}",
                    "field": field_name,
                    "content": content.strip(),
                    "metadata": {
                        "document_id": jd_id,
                        "document_type": "job_description",
                        "field": field_name,
                    }
                })

        # Extract skills (matching resume format)
        skills = jd_json.get('skills', {})
        technical_skills = skills.get('technical', []) if isinstance(skills, dict) else []
        soft_skills = skills.get('soft', []) if isinstance(skills, dict) else []

        # Skills chunk (matching resume skills format)
        skills_parts = []
        if technical_skills:
            tech_str = ', '.join(technical_skills) if isinstance(technical_skills, list) else str(technical_skills)
            skills_parts.append(f"Technical Skills: {tech_str}")
        if soft_skills:
            soft_str = ', '.join(soft_skills) if isinstance(soft_skills, list) else str(soft_skills)
            skills_parts.append(f"Soft Skills: {soft_str}")

        if skills_parts:
            add_chunk("skills", ' | '.join(skills_parts))

        # Experience chunks (matching resume experience format)
        experiences = jd_json.get('experience', [])
        if isinstance(experiences, list):
            for i, exp in enumerate(experiences):
                exp_parts = []
                years = exp.get('years_required', '')
                level = exp.get('level', '')
                desc = exp.get('description', '')

                if years:
                    exp_parts.append(f"Years Required: {years}")
                if level:
                    exp_parts.append(f"Level: {level}")
                if desc:
                    exp_parts.append(f"Description: {desc}")

                if exp_parts:
                    add_chunk("experience", ' | '.join(exp_parts), i)

        # Education chunks (matching resume education format)
        educations = jd_json.get('education', [])
        if isinstance(educations, list):
            for i, edu in enumerate(educations):
                degree = edu.get('degree', '')
                field = edu.get('field', '')
                reqs = edu.get('requirements', '')

                edu_parts = []
                if degree and field:
                    edu_parts.append(f"{degree} in {field}")
                elif degree:
                    edu_parts.append(degree)
                elif field:
                    edu_parts.append(f"Degree in {field}")

                if reqs:
                    edu_parts.append(f"Requirements: {reqs}")

                if edu_parts:
                    add_chunk("education", ' | '.join(edu_parts), i)

        # Certifications chunk (matching resume certifications format)
        certifications = jd_json.get('certifications', [])
        if certifications:
            certs_str = ', '.join(certifications) if isinstance(certifications, list) else str(certifications)
            add_chunk("certifications", f"Required Certifications: {certs_str}")

        # Responsibilities chunk
        responsibilities = jd_json.get('responsibilities', [])
        if responsibilities:
            resp_str = '\n'.join([f"- {r}" for r in responsibilities]) if isinstance(responsibilities, list) else str(responsibilities)
            add_chunk("responsibilities", f"Key Responsibilities:\n{resp_str}")

        # Additional info chunk (company, benefits, etc.)
        additional_parts = []

        title = jd_json.get('title', '')
        if title:
            additional_parts.append(f"Position: {title}")

        company = jd_json.get('company', '')
        if company:
            additional_parts.append(f"Company: {company}")

        location = jd_json.get('location', '')
        if location:
            additional_parts.append(f"Location: {location}")

        employment_type = jd_json.get('employment_type', '')
        if employment_type:
            additional_parts.append(f"Employment Type: {employment_type}")

        salary = jd_json.get('salary', '')
        if salary:
            additional_parts.append(f"Salary: {salary}")

        benefits = jd_json.get('benefits', [])
        if benefits:
            ben_str = ', '.join(benefits) if isinstance(benefits, list) else str(benefits)
            additional_parts.append(f"Benefits: {ben_str}")

        about_company = jd_json.get('about_company', '')
        if about_company:
            additional_parts.append(f"About: {about_company}")

        if additional_parts:
            add_chunk("additional_info", ' | '.join(additional_parts))

        return chunks
        
    @log_execution_time(logger)
    def preprocess_jd(self, jd_text: str, jd_id: str) -> List[Dict[str, str]]:
        """
        Preprocess job description into optimized chunks

        Args:
            jd_text: Job description text
            jd_id: Unique identifier for the job description

        Returns:
            List of optimized chunk dictionaries

        Raises:
            LLMError: If preprocessing fails
        """
        try:
            logger.info(f"Preprocessing job description (ID: {jd_id})")

            sections = self.parse_with_llm(jd_text)

            # Generate chunks
            chunks = self.generate_hybrid_chunks(sections, jd_id)
            logger.debug(f"Generated {len(chunks)} chunks")

            # Optimize chunk sizes for better matching accuracy
            logger.debug("Optimizing JD chunk sizes")
            optimized_chunks = validate_and_split_chunks(chunks)
            logger.info(f"JD chunk optimization complete: {len(chunks)} → {len(optimized_chunks)} chunks")

            return optimized_chunks

        except Exception as e:
            logger.error(f"JD preprocessing failed: {str(e)}", exc_info=True)
            if isinstance(e, LLMError):
                raise
            raise LLMError(
                f"Failed to preprocess job description: {str(e)}",
                details={'jd_id': jd_id, 'error_type': type(e).__name__}
            )
        
