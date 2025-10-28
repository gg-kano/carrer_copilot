"""
Prompt template for matching resume with job description
"""

def generate_match_prompt(resume_content: str, jd_content: str) -> str:
    """
    Generate a prompt to evaluate if a resume matches a job description

    Args:
        resume_content: Merged content from all resume chunks
        jd_content: Job description content

    Returns:
        Formatted prompt for the LLM
    """
    prompt = f"""You are an expert HR recruiter and talent acquisition specialist. Your task is to evaluate whether a candidate's resume matches the requirements of a job description.

# Job Description:
{jd_content}

# Candidate Resume:
{resume_content}

# Your Task:
Analyze the resume against the job description and provide a detailed evaluation.

# Output Format:
Respond ONLY with a valid JSON object in the following format (no markdown, no code blocks):

{{
    "qualified": true/false,
    "match_score": 0-100,
    "summary": "A brief 2-3 sentence summary of the candidate's fit",
    "strengths": [
        "Specific strength 1 with evidence from resume",
        "Specific strength 2 with evidence from resume",
        "Specific strength 3 with evidence from resume"
    ],
    "weaknesses": [
        "Specific gap or weakness 1",
        "Specific gap or weakness 2",
        "Specific gap or weakness 3"
    ],
    "recommendation": "STRONG_MATCH / GOOD_MATCH / PARTIAL_MATCH / NOT_MATCH",
    "detailed_analysis": {{
        "skills_match": {{
            "score": 0-100,
            "details": "Analysis of technical and soft skills alignment"
        }},
        "experience_match": {{
            "score": 0-100,
            "details": "Analysis of years and type of experience"
        }},
        "education_match": {{
            "score": 0-100,
            "details": "Analysis of educational background alignment"
        }},
        "cultural_fit": {{
            "score": 0-100,
            "details": "Analysis based on values, work style, etc."
        }}
    }},
    "next_steps": "Recommended action (e.g., 'Schedule interview', 'Request more information', 'Reject politely')"
}}

# Evaluation Criteria:
1. **Skills Match**: Does the candidate have the required technical and soft skills?
2. **Experience Match**: Does their work history align with the role requirements?
3. **Education Match**: Do they meet educational requirements?
4. **Cultural Fit**: Do their values and work style align with the company?

# Qualification Decision:
- Set "qualified" to true if match_score >= 70
- Set "qualified" to false if match_score < 70

# Recommendation Levels:
- STRONG_MATCH (90-100): Excellent fit, priority candidate
- GOOD_MATCH (75-89): Good fit, proceed with interview
- PARTIAL_MATCH (60-74): Some fit, consider if other candidates unavailable
- NOT_MATCH (<60): Poor fit, not recommended

Be specific and reference actual content from both the resume and job description in your analysis.
"""
    return prompt
