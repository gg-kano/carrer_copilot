
def generate_resume_extraction_prompt(resume_text: str) -> str:
    resume_prompt = f"""You are a precise and structured information extraction agent that analyzes resumes or CVs.
Your goal is to extract all relevant information from the given text into a standardized JSON schema:
Expected JSON format:
{{
  "summary": "professional summary or objective",
  "skills": "comma-separated list of all skills",
  "experience": "work history with company names, titles, dates, and responsibilities",
  "education": "degrees, institutions, graduation years",
  "certifications": "professional certifications",
  "projects": "project descriptions with technologies used",
  "achievements": "quantifiable accomplishments and awards"
}}

Guidelines:
- If a field is missing, return an empty string "".
- Be **concise but comprehensive** — summarize long sections clearly.
- `proof_of_work` should combine all quantifiable results, notable projects, and certifications.
- Return ONLY a single valid JSON, no explanations, no markdown.

Resume:
{resume_text}
"""
    return resume_prompt