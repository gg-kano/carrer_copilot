
def generate_resume_extraction_prompt(resume_text: str) -> str:
    resume_prompt = f"""You are a precise resume parser. Extract information from the resume and output ONLY valid JSON following this exact schema:

{{
  "experience": [
    {{
      "company": "Company Name",
      "title": "Job Title",
      "description": [
        "First responsibility or achievement",
        "Second responsibility or achievement",
        "Additional bullet points..."
      ]
    }}
  ],
  "skills": ["Skill1", "Skill2", "Skill3"],
  "education": [
    {{
      "school": "University Name",
      "degree": "Degree Type and Major",
      "gpa": "GPA if available"
    }},
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief project summary"
    }},
  ]
}}

### EXTRACTION RULES

**1. EXPERIENCE**
- Extract each distinct job/position as one object.
- "company": organization name (string)
- "title": job title (string)
- "description": array of concise bullet points (1–2 sentences each)
- Split paragraphs into clear, individual achievements or tasks.
- Keep quantifiable results (e.g. “improved accuracy by 15%”).
- If no experience found, use `"experience": []`.

**2. SKILLS**
- Extract as an array of individual skills.
- Include tools, frameworks, languages, and technologies.
- Remove duplicates and keep general naming (e.g. "Python" not "Python 3.8").
- If none found, use `"skills": []`.

**3. EDUCATION**
- Extract each degree/program as one object.
- "school": institution/university name.
- "degree": full degree name with field of study (e.g. "BSc Computer Science", "MBA").
- Include GPA if mentioned.
- If none found, use `"education": []`.

**4. PROJECTS**
- Extract each notable project as one object.
- "name": project title or short name.
- "description": 1–2 sentence summary of purpose or result.
- If none found, use `"projects": []`.

### OUTPUT RULES
- Output ONLY the JSON object — no markdown, no text, no explanations.
- Always include all four top-level keys: `experience`, `skills`, `education`, `projects`.
- Use double quotes for all strings.
- Escape special characters properly.
- Ensure JSON is valid and parseable.

Resume Text:
{resume_text}
"""
    return resume_prompt