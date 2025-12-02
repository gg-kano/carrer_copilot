import re
import json
from typing import List, Dict
import sys
import os
from dotenv import load_dotenv

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Load environment variables from .env file
load_dotenv(os.path.join(parent_dir, '.env'))

from prompt.extract_job_description import generate_job_description_prompt
import google.generativeai as genai
from utils.chunk_size_manager import validate_and_split_chunks

class JDPreprocessor:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in .env file")
        genai.configure(api_key=api_key)
        self.llm_client = genai.GenerativeModel("gemini-2.5-flash")
        
    def normalize_text(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'http[s]?://\S+', '[URL]', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_with_llm(self, jd_text: str) -> Dict[str, str]:
        prompt = generate_job_description_prompt()

        response = self.llm_client.generate_content([prompt, jd_text])
        response_text = response.text.strip()
        try:

            data = json.loads(response_text)
        except json.JSONDecodeError:

            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            data = json.loads(match.group()) if match else {}

        # Normalize string values only (skip nested dicts/lists)
        normalized_data = {}
        for key, val in data.items():
            if isinstance(val, str):
                normalized_data[key] = self.normalize_text(val)
            else:
                normalized_data[key] = val

        normalized_data["full_text"] = self.normalize_text(jd_text)
        return normalized_data
    
    def generate_hybrid_chunks(
            self,
            jd_json: Dict,
            jd_id: str = None
        ) -> List[Dict[str, str]]:

            if jd_id is None:
                import uuid
                jd_id = f"jd_{uuid.uuid4().hex[:12]}"

            chunks = []

            def add_chunk(field_name: str, content: str):
                """
                Add chunk to list
                """
                if content.strip():
                    chunks.append({
                        "chunk_id": f"{jd_id}_{field_name}",
                        "field": field_name,
                        "content": content.strip(),
                        "metadata": {
                            "document_id": jd_id,
                            "document_type": "job_description",
                            "field": field_name,
                        }
                    })

            # Extract nested requirements structure (skills only)
            requirements = jd_json.get('requirements', {})
            technical_skills = requirements.get('technical_skills', []) if isinstance(requirements, dict) else []
            soft_skills = requirements.get('soft_skills', []) if isinstance(requirements, dict) else []

            # Extract experience structure
            experience = jd_json.get('experience', {})
            years_required = experience.get('years_required', '') if isinstance(experience, dict) else ''
            experience_level = experience.get('level', '') if isinstance(experience, dict) else ''
            experience_desc = experience.get('description', '') if isinstance(experience, dict) else ''

            # Extract education structure
            education = jd_json.get('education', {})
            education_degree = education.get('degree', '') if isinstance(education, dict) else ''
            education_field = education.get('field', '') if isinstance(education, dict) else ''
            education_reqs = education.get('requirements', '') if isinstance(education, dict) else ''

            # Extract qualifications
            qualifications = jd_json.get('qualifications', {})
            required_quals = qualifications.get('required', []) if isinstance(qualifications, dict) else []
            preferred_quals = qualifications.get('preferred', []) if isinstance(qualifications, dict) else []

            # Chunk 1: Requirements + Responsibilities (skills and responsibilities only, NO experience/education)
            req_resp_parts = []

            if technical_skills:
                tech_skills_str = ', '.join(technical_skills) if isinstance(technical_skills, list) else str(technical_skills)
                req_resp_parts.append(f"Technical Skills Required: {tech_skills_str}")

            if soft_skills:
                soft_skills_str = ', '.join(soft_skills) if isinstance(soft_skills, list) else str(soft_skills)
                req_resp_parts.append(f"Soft Skills Required: {soft_skills_str}")

            responsibilities = jd_json.get('responsibilities', [])
            if responsibilities:
                resp_str = '\n'.join([f"- {r}" for r in responsibilities]) if isinstance(responsibilities, list) else str(responsibilities)
                req_resp_parts.append(f"Responsibilities:\n{resp_str}")

            if required_quals:
                req_quals_str = '\n'.join([f"- {q}" for q in required_quals]) if isinstance(required_quals, list) else str(required_quals)
                req_resp_parts.append(f"Required Qualifications:\n{req_quals_str}")

            if req_resp_parts:
                add_chunk("requirements_responsibilities", '\n\n'.join(req_resp_parts))

            # Chunk 2: Experience + Education (dedicated to experience and education only)
            exp_edu_parts = []

            # Experience section
            exp_parts = []
            if years_required:
                exp_parts.append(f"Years Required: {years_required}")
            if experience_level:
                exp_parts.append(f"Level: {experience_level}")
            if experience_desc:
                exp_parts.append(f"Description: {experience_desc}")

            if exp_parts:
                exp_edu_parts.append("Experience Required:\n" + '\n'.join(exp_parts))

            # Education section
            edu_parts = []
            if education_degree:
                edu_parts.append(f"Degree: {education_degree}")
            if education_field:
                edu_parts.append(f"Field: {education_field}")
            if education_reqs:
                edu_parts.append(f"Requirements: {education_reqs}")

            if edu_parts:
                exp_edu_parts.append("Education Required:\n" + '\n'.join(edu_parts))

            # Preferred qualifications
            if preferred_quals:
                pref_quals_str = '\n'.join([f"- {q}" for q in preferred_quals]) if isinstance(preferred_quals, list) else str(preferred_quals)
                exp_edu_parts.append(f"Preferred Qualifications:\n{pref_quals_str}")

            if exp_edu_parts:
                add_chunk("experience_education", '\n\n'.join(exp_edu_parts))

            # Chunk 3: Benefits + Location + Salary + Company Info
            ben_loc_sal_parts = []

            benefits = jd_json.get('benefits', [])
            if benefits:
                ben_str = '\n'.join([f"- {b}" for b in benefits]) if isinstance(benefits, list) else str(benefits)
                ben_loc_sal_parts.append(f"Benefits:\n{ben_str}")

            location = jd_json.get('location', '')
            if location:
                ben_loc_sal_parts.append(f"Location: {location}")

            salary = jd_json.get('salary', '')
            if salary:
                ben_loc_sal_parts.append(f"Salary: {salary}")

            employment_type = jd_json.get('employment_type', '')
            if employment_type:
                ben_loc_sal_parts.append(f"Employment Type: {employment_type}")

            about_company = jd_json.get('about_company', '')
            if about_company:
                ben_loc_sal_parts.append(f"About Company: {about_company}")

            if ben_loc_sal_parts:
                add_chunk("benefits_location_salary", '\n\n'.join(ben_loc_sal_parts))

            return chunks
        
    def preprocess_jd(self, jd_text: str, jd_id: str) -> List[Dict[str, str]]:
        try:
            sections = self.parse_with_llm(jd_text)

            # Generate chunks
            chunks = self.generate_hybrid_chunks(sections, jd_id)

            # Optimize chunk sizes for better matching accuracy
            print(f"🔧 Optimizing JD chunk sizes...")
            optimized_chunks = validate_and_split_chunks(chunks)
            print(f"✅ JD chunk optimization complete: {len(chunks)} → {len(optimized_chunks)} chunks")

            return optimized_chunks
        except Exception as e:
            print(f"[Warning] LLM parsing failed: {e}.")
        
