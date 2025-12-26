"""
Career Copilot - API Usage Example

This script demonstrates how to use Career Copilot programmatically
for resume processing and candidate matching.
"""

import os
from pathlib import Path

# Add parent directory to path to import modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from database.chroma_db import ChromaDBStorage
from process.resume_process import ResumePreprocessor
from process.jd_process import JDPreprocessor
from match.resume_jd_matcher import ResumeJDMatcher


def initialize_components():
    """Initialize all Career Copilot components."""
    print("Initializing Career Copilot components...")

    db = ChromaDBStorage(persist_directory="./chroma_db")
    resume_processor = ResumePreprocessor()
    jd_processor = JDPreprocessor()
    matcher = ResumeJDMatcher()

    print("✓ Components initialized successfully\n")
    return db, resume_processor, jd_processor, matcher


def process_single_resume(resume_processor, db, pdf_path):
    """
    Process a single resume PDF.

    Args:
        resume_processor: ResumePreprocessor instance
        db: ChromaDBStorage instance
        pdf_path: Path to PDF resume file
    """
    print(f"Processing resume: {pdf_path}")

    # Read PDF file
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()

    # Parse resume using AI
    resume_data = resume_processor.parse_with_llm(pdf_bytes, is_pdf=True)

    # Generate resume ID
    resume_id = resume_data.get('name', 'unknown').lower().replace(' ', '_')

    # Store in database
    db.add_resume(resume_id=resume_id, resume_data=resume_data)

    print(f"✓ Processed: {resume_data.get('name', 'Unknown')}")
    print(f"  Skills: {', '.join(resume_data.get('skills', [])[:5])}")
    print(f"  Experience: {len(resume_data.get('experience', []))} positions\n")

    return resume_data


def match_candidates(matcher, jd_data, top_k=5):
    """
    Find and display top matching candidates.

    Args:
        matcher: ResumeJDMatcher instance
        jd_data: Processed job description data
        top_k: Number of top candidates to return
    """
    print(f"\nFinding top {top_k} matching candidates...")

    matches = matcher.find_matches(jd_data, top_k=top_k)

    print("\n" + "="*70)
    print("MATCHING RESULTS")
    print("="*70 + "\n")

    for i, match in enumerate(matches, 1):
        print(f"{i}. {match.get('name', 'Unknown')}")
        print(f"   Match Score: {match.get('score', 0)}%")
        print(f"   Top Skills: {', '.join(match.get('skills', [])[:5])}")
        print(f"   Reasoning: {match.get('reason', 'N/A')}")
        print()

    return matches


def main():
    """Main example workflow."""
    print("\n" + "="*70)
    print("CAREER COPILOT - API USAGE EXAMPLE")
    print("="*70 + "\n")

    # Initialize components
    db, resume_processor, jd_processor, matcher = initialize_components()

    # Example 1: Process a resume (if you have a PDF file)
    # Uncomment and modify the path below
    # resume_path = "path/to/your/resume.pdf"
    # if os.path.exists(resume_path):
    #     resume_data = process_single_resume(resume_processor, db, resume_path)

    # Example 2: Process a job description
    jd_text = """
    Senior Software Engineer - AI/ML

    We are seeking an experienced Senior Software Engineer with expertise in
    AI/ML technologies to join our innovative team.

    Requirements:
    - 5+ years of Python development experience
    - Strong background in machine learning and AI
    - Experience with vector databases (ChromaDB, Pinecone, Weaviate)
    - Proficiency with LLM frameworks (LangChain, LlamaIndex)
    - Experience with web frameworks (FastAPI, Flask, Streamlit)
    - Bachelor's degree in Computer Science or related field

    Nice to have:
    - Experience with Google Gemini or OpenAI APIs
    - Knowledge of RAG (Retrieval-Augmented Generation)
    - Docker and cloud deployment experience

    Responsibilities:
    - Design and implement AI-powered features
    - Build and optimize vector search systems
    - Collaborate with cross-functional teams
    - Mentor junior developers
    """

    print("Processing job description...")
    jd_data = jd_processor.process(jd_text)
    print("✓ Job description processed\n")

    # Example 3: Find matching candidates
    # Note: This will only work if you have resumes in your database
    try:
        matches = match_candidates(matcher, jd_data, top_k=5)

        # Example 4: Access match data programmatically
        if matches:
            print("\nTop candidate details:")
            top_match = matches[0]
            print(f"Name: {top_match.get('name')}")
            print(f"Email: {top_match.get('email', 'Not available')}")
            print(f"Phone: {top_match.get('phone', 'Not available')}")
    except Exception as e:
        print(f"Note: Matching requires resumes in database. Error: {e}")

    print("\n" + "="*70)
    print("Example completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
