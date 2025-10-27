def generate_job_description_prompt(jd_text: str) -> str:   
    jd_prompt = f"""Analyze this job description and extract it into structured sections. Return ONLY valid JSON with these exact keys:

    {{
    "title": "extracted job title",
    "company": "company information if present",
    "requirements": "all technical and soft skill requirements",
    "responsibilities": "all job duties and responsibilities",
    "experience": "required experience level",
    "education": "education requirements",
    "benefits": "benefits and perks if mentioned",
    "location": "job location if mentioned",
    "salary": "salary information if mentioned"
    }}

    Rules:
    - If a section is not found, use empty string ""
    - Combine bullet points into paragraph form
    - Extract the core information, removing fluff
    - Be comprehensive for each section
    - Return ONLY the JSON, no other text.

    Job Description:
    {jd_text}

    """
    return jd_prompt