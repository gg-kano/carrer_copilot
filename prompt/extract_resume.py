
def generate_resume_extraction_prompt() -> str:
    resume_prompt = """
You are a professional resume parser. 
Your task is to read the entire resume and output one complete JSON profile that represents the candidate.

Your output must:
- Be ONLY valid JSON.
- Follow the schema given below.
- Omit any key that is not present in the resume.
- Never invent or guess missing information.
- Keep descriptions concise, factual, and meaningful.

### ALLOWED JSON SCHEMA (use only fields that exist in the resume)

{
  "name": "",
  "skills": {
    "technical": [],
    "soft": []
  },
  "experience": [
    {
      "role": "",
      "company": "",
      "period": "",
      "location": "",
      "achievements": []
    }
  ],
  "projects": [
    {
      "name": "",
      "description": "",
      "tech_stack": []
    }
  ],
  "education": [
    {
      "degree": "",
      "school": "",
      "period": "",
      "details": ""
    }
  ],
  "certifications": [],
  "languages": []
}

### EXTRACTION RULES
- Extract information only if clearly present.
- For experience: summarize responsibilities into short bullet-like achievements.
- For skills: categorize into technical vs soft when possible.
- For projects: list the project name, what was done, and relevant tech stack.
- For education: extract degree, school, and any available dates or details.
- Do NOT duplicate text across fields (e.g., avoid repeating summary inside experience).

### OUTPUT FORMAT RULES
- Return ONLY the final JSON object.
- Do not include explanations, comments, or prose.
"""

    return resume_prompt