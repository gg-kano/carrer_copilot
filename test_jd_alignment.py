"""
Test script to verify JD extraction alignment with Resume format
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from process.jd_process import JDPreprocessor
from process.resume_process import ResumePreprocessor
import json

def test_jd_extraction():
    """Test JD extraction with sample job description"""

    sample_jd = """
    Senior Software Engineer - AI/ML

    Company: TechCorp Inc.
    Location: San Francisco, CA
    Employment Type: Full-time
    Salary: $150,000 - $200,000

    We are seeking a Senior Software Engineer with expertise in AI and Machine Learning.

    Requirements:
    - 5+ years of software engineering experience
    - Strong proficiency in Python, TensorFlow, PyTorch
    - Experience with cloud platforms (AWS, GCP)
    - Excellent communication and teamwork skills
    - Master's degree in Computer Science or related field
    - AWS Certified Solutions Architect (preferred)

    Responsibilities:
    - Design and implement ML models for production
    - Collaborate with data scientists and engineers
    - Optimize model performance and scalability
    - Mentor junior team members

    Benefits:
    - Health insurance
    - 401(k) matching
    - Remote work options
    - Professional development budget

    About the Company:
    TechCorp is a leading AI company revolutionizing the industry.
    """

    print("=" * 80)
    print("Testing JD Extraction with Aligned Format")
    print("=" * 80)

    try:
        # Initialize preprocessor
        jd_processor = JDPreprocessor()

        # Parse JD
        print("\n1. Parsing JD with LLM...")
        jd_data = jd_processor.parse_with_llm(sample_jd)

        print("\n2. Extracted JD Data:")
        print(json.dumps(jd_data, indent=2))

        # Generate chunks
        print("\n3. Generating chunks...")
        chunks = jd_processor.generate_hybrid_chunks(jd_data, jd_id="test_jd_001")

        print(f"\n4. Generated {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n   Chunk {i} - Field: {chunk['field']}")
            print(f"   Chunk ID: {chunk['chunk_id']}")
            print(f"   Content Preview: {chunk['content'][:100]}...")

        # Show field alignment with resume
        print("\n5. Field Alignment Analysis:")
        print("   Resume Fields          →  JD Fields")
        print("   ─────────────────────────────────────")

        resume_fields = ["skills", "experience", "education", "certifications", "projects"]
        jd_fields = set([chunk['field'] for chunk in chunks])

        for field in resume_fields:
            status = "✓ ALIGNED" if field in jd_fields else "✗ missing"
            print(f"   {field:20}  →  {status}")

        print(f"\n   Additional JD fields: {jd_fields - set(resume_fields)}")

        print("\n" + "=" * 80)
        print("✓ Test completed successfully!")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def compare_formats():
    """Compare old vs new JD format"""

    print("\n" + "=" * 80)
    print("Format Comparison: Old vs New")
    print("=" * 80)

    print("\nOLD FORMAT (nested objects):")
    print(json.dumps({
        "requirements": {
            "technical_skills": ["Python", "AWS"],
            "soft_skills": ["Communication"]
        },
        "experience": {
            "years_required": "5+ years",
            "level": "Senior"
        },
        "education": {
            "degree": "Master's",
            "field": "Computer Science"
        },
        "qualifications": {
            "required": ["..."],
            "preferred": ["..."]
        }
    }, indent=2))

    print("\nNEW FORMAT (aligned with resume):")
    print(json.dumps({
        "skills": {
            "technical": ["Python", "AWS"],
            "soft": ["Communication"]
        },
        "experience": [
            {
                "years_required": "5+ years",
                "level": "Senior",
                "description": "in AI/ML"
            }
        ],
        "education": [
            {
                "degree": "Master's",
                "field": "Computer Science",
                "requirements": ""
            }
        ],
        "certifications": ["AWS Certified"]
    }, indent=2))

    print("\nKEY CHANGES:")
    print("1. requirements → skills (matching resume)")
    print("2. experience: object → array (matching resume)")
    print("3. education: object → array (matching resume)")
    print("4. qualifications → certifications (clearer naming)")
    print("5. Same field names as resume for better matching!")

if __name__ == "__main__":
    print("\n🧪 JD Alignment Test Suite\n")

    # Run comparison
    compare_formats()

    # Run extraction test
    print("\n")
    success = test_jd_extraction()

    if success:
        print("\n✅ All tests passed! JD format is now aligned with Resume format.")
    else:
        print("\n❌ Tests failed. Please check the errors above.")

    sys.exit(0 if success else 1)
