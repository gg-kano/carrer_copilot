"""
Diagnose Google Gemini API issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def check_api_key():
    """Check if API key is set"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in .env file")
        return False

    print(f"✓ API Key found: {api_key[:10]}...{api_key[-5:]}")
    return True

def test_model(model_name):
    """Test a specific model"""
    try:
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        print(f"\nTesting model: {model_name}")
        print("-" * 60)

        model = genai.GenerativeModel(model_name)

        # Simple test
        response = model.generate_content("Say 'Hello'")

        print(f"✓ Model works: {model_name}")
        print(f"  Response: {response.text[:50]}...")
        return True

    except Exception as e:
        error_str = str(e)

        if "429" in error_str or "quota" in error_str.lower():
            print(f"❌ QUOTA EXCEEDED: {model_name}")
            print(f"   Error: {error_str[:200]}")
            return False
        elif "404" in error_str:
            print(f"❌ MODEL NOT FOUND: {model_name}")
            print(f"   This model may not exist or is not available")
            return False
        else:
            print(f"❌ ERROR: {model_name}")
            print(f"   {error_str[:200]}")
            return False

def main():
    print("=" * 60)
    print("Google Gemini API Diagnostics")
    print("=" * 60)

    # Check API key
    if not check_api_key():
        return

    # Test different models
    models_to_test = [
        ("gemini-2.0-flash-lite", "Lite version (Recommended)"),
        ("gemini-1.5-flash", "Stable flash model"),
        ("gemini-1.5-pro", "Pro model (higher limits)"),
        ("gemini-2.0-flash-exp", "Experimental (may have low quota)"),
    ]

    print("\n" + "=" * 60)
    print("Testing Available Models")
    print("=" * 60)

    working_models = []

    for model_name, description in models_to_test:
        if test_model(model_name):
            working_models.append(model_name)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if working_models:
        print(f"\n✓ Working models ({len(working_models)}):")
        for model in working_models:
            print(f"   - {model}")

        print(f"\nRECOMMENDATION:")
        print(f"Update config.py to use: {working_models[0]}")
        print(f"\nEdit config.py and set:")
        print(f'   RESUME_LLM_MODEL = "{working_models[0]}"')
        print(f'   JD_LLM_MODEL = "{working_models[0]}"')
        print(f'   MATCHING_LLM_MODEL = "{working_models[0]}"')
    else:
        print("\n❌ No working models found!")
        print("\nPossible causes:")
        print("1. API quota exceeded - wait and try again later")
        print("2. Invalid API key - check your .env file")
        print("3. Network issues - check your internet connection")

        print("\nTo check your quota:")
        print("Visit: https://ai.dev/usage?tab=rate-limit")

if __name__ == "__main__":
    main()
