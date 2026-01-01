# JD Format Migration Guide

## Overview

The Job Description (JD) extraction format has been updated to align with the Resume extraction format. This improves matching accuracy and makes the codebase more consistent.

---

## What Changed

### 1. JSON Schema Alignment

#### Before (Old Format):
```json
{
  "title": "Senior Engineer",
  "requirements": {
    "technical_skills": ["Python", "AWS"],
    "soft_skills": ["Communication"]
  },
  "experience": {
    "years_required": "5+ years",
    "level": "Senior",
    "description": "in AI/ML"
  },
  "education": {
    "degree": "Master's",
    "field": "Computer Science",
    "requirements": ""
  },
  "qualifications": {
    "required": ["..."],
    "preferred": ["..."]
  }
}
```

#### After (New Format - Aligned with Resume):
```json
{
  "title": "Senior Engineer",
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
}
```

### 2. Key Differences

| Aspect | Old Format | New Format | Benefit |
|--------|-----------|------------|---------|
| **Skills Field Name** | `requirements` | `skills` | Matches resume |
| **Technical Skills** | `technical_skills` | `technical` | Consistent naming |
| **Soft Skills** | `soft_skills` | `soft` | Consistent naming |
| **Experience Type** | Object | Array | Supports multiple entries |
| **Education Type** | Object | Array | Supports multiple entries |
| **Certifications** | In `qualifications` | Top-level `certifications` | Clearer structure |

---

## Why This Change?

### Problem with Old Format

1. **Inconsistent Field Names**: Resume used `skills`, JD used `requirements`
2. **Mismatched Structures**: Resume used arrays for experience/education, JD used objects
3. **Harder Matching**: LLM had to understand different schemas
4. **Confusing for Users**: Different field names for same concepts

### Benefits of New Format

1. ✅ **Direct Field Matching**: `skills` matches `skills`, `education` matches `education`
2. ✅ **Better LLM Understanding**: Same structure for resume and JD
3. ✅ **Clearer Chunks**: Chunks use identical field names
4. ✅ **Easier Maintenance**: One schema to understand
5. ✅ **More Accurate Matching**: Vector search finds relevant fields more easily

---

## Chunk Generation Changes

### Old Chunk Generation

Chunks were created with mixed field names:
- `requirements_responsibilities` (combined)
- `experience_education` (combined)
- `benefits_location_salary` (combined)

**Problem**: Resume chunks used `skills`, `experience`, `education` separately.

### New Chunk Generation

Chunks now match resume structure:

```python
# Skills chunk (matches resume skills chunk)
{
  "field": "skills",
  "content": "Technical Skills: Python, AWS | Soft Skills: Communication"
}

# Experience chunk (matches resume experience chunk)
{
  "field": "experience",
  "content": "Years Required: 5+ years | Level: Senior | Description: in AI/ML"
}

# Education chunk (matches resume education chunk)
{
  "field": "education",
  "content": "Master's in Computer Science | Requirements: ..."
}

# Certifications chunk (matches resume certifications chunk)
{
  "field": "certifications",
  "content": "Required Certifications: AWS Certified, PMP"
}
```

**Benefit**: When matching, the LLM compares `skills` to `skills`, `experience` to `experience`, etc.

---

## Migration Impact

### ✅ Backward Compatibility

**Good News**: The old code will still work! Here's why:

1. **LLM Parsing**: The prompt guides the LLM to extract in new format automatically
2. **Chunk Generation**: `generate_hybrid_chunks()` handles both old and new data gracefully
3. **Matching Logic**: Works with any field names (just more accurate with aligned names)

### ⚠️ Breaking Changes

**None for end users!** The changes are internal:

- Existing JDs in database: Old chunks still work
- New JDs: Will use new format automatically
- Matching: Works with both formats

### 🔄 Recommended Actions

1. **No immediate action required** - system works with both formats
2. **Optional**: Re-process existing JDs to use new format
3. **Future**: Delete old JD entries and re-upload for consistency

---

## Code Changes

### 1. Updated Files

- `prompt/extract_job_description.py` - New extraction prompt
- `process/jd_process.py` - New chunk generation logic

### 2. How to Re-process Existing JDs

If you want to update old JDs to new format:

```python
from process.jd_process import JDPreprocessor
from database.chroma_db import ChromaDBStorage

db = ChromaDBStorage()
processor = JDPreprocessor()

# Get all JD IDs
jds = db.list_all_documents(document_type="job_description")

for jd in jds:
    jd_id = jd['id']
    jd_text = jd['metadata']['full_text']  # Assuming you stored full text

    # Re-process with new format
    new_chunks = processor.preprocess_jd(jd_text, jd_id)

    # Delete old JD
    db.delete_document(jd_id)

    # Store new JD with updated chunks
    db.store_document(
        document_id=jd_id,
        document_type="job_description",
        raw_text=jd_text
    )

    for chunk in new_chunks:
        db.add_chunk(
            chunk_id=chunk['chunk_id'],
            document_id=jd_id,
            field=chunk['field'],
            content=chunk['content'],
            chunk_metadata=chunk['metadata']
        )

    print(f"✓ Re-processed {jd_id}")
```

---

## Testing

### Verify Format Alignment

Run the verification script:

```bash
python verify_jd_format.py
```

This shows:
- Old vs new format comparison
- Chunk generation examples
- Field alignment analysis

### Test with Real JD

```python
from process.jd_process import JDPreprocessor

processor = JDPreprocessor()

jd_text = """
Your job description text here...
"""

# Parse JD
jd_data = processor.parse_with_llm(jd_text)

# Check format
print("Skills:", jd_data.get('skills'))  # Should be dict with technical/soft
print("Experience:", jd_data.get('experience'))  # Should be array
print("Education:", jd_data.get('education'))  # Should be array

# Generate chunks
chunks = processor.generate_hybrid_chunks(jd_data, "test_jd")

# Verify field names
fields = set(chunk['field'] for chunk in chunks)
print("Chunk fields:", fields)
# Should include: skills, experience, education, certifications
```

---

## FAQ

### Q: Do I need to update my code?

**A**: No! The changes are internal. Your existing code continues to work.

### Q: Will old JDs still match with resumes?

**A**: Yes! The matching logic works with both formats. However, new format provides better accuracy.

### Q: Should I delete and re-upload all JDs?

**A**: Optional. For best results, yes. But not required immediately.

### Q: What about resumes?

**A**: No changes to resume extraction. JD format was updated to match resume format.

### Q: How do I know if a JD uses the new format?

**A**: Check if it has `skills` field instead of `requirements`:

```python
jd_data = db.get_document("jd_123")
if 'skills' in jd_data:
    print("New format")
else:
    print("Old format")
```

### Q: Can I use both formats simultaneously?

**A**: Yes! The system handles both gracefully. Chunks will be generated appropriately for each.

---

## Example: Before & After

### Input JD Text

```
Senior Data Scientist

Requirements:
- 5+ years of data science experience
- Expert in Python, R, SQL
- Strong communication skills
- Master's degree in Statistics or related field
- AWS certification preferred

Responsibilities:
- Build ML models
- Analyze large datasets
```

### Old Extraction Result

```json
{
  "title": "Senior Data Scientist",
  "requirements": {
    "technical_skills": ["Python", "R", "SQL"],
    "soft_skills": ["Communication"]
  },
  "experience": {
    "years_required": "5+ years",
    "level": "Senior"
  },
  "education": {
    "degree": "Master's",
    "field": "Statistics"
  }
}
```

**Old Chunks**: `requirements_responsibilities`, `experience_education`

### New Extraction Result

```json
{
  "title": "Senior Data Scientist",
  "skills": {
    "technical": ["Python", "R", "SQL"],
    "soft": ["Communication"]
  },
  "experience": [
    {
      "years_required": "5+ years",
      "level": "Senior",
      "description": "in data science"
    }
  ],
  "education": [
    {
      "degree": "Master's",
      "field": "Statistics",
      "requirements": ""
    }
  ],
  "certifications": ["AWS certification"]
}
```

**New Chunks**: `skills`, `experience`, `education`, `certifications`, `responsibilities`

### Matching Improvement

**Before**:
- Resume `skills` chunk vs JD `requirements_responsibilities` chunk
- Partial field overlap

**After**:
- Resume `skills` chunk vs JD `skills` chunk
- Direct field-to-field comparison!

---

## Summary

| Aspect | Impact | Action Required |
|--------|--------|-----------------|
| **Extraction Prompt** | Updated | None - automatic |
| **JSON Schema** | Aligned with resume | None |
| **Chunk Generation** | More consistent | None |
| **Matching Accuracy** | Improved | None |
| **Existing JDs** | Still work | Optional: re-process |
| **Code Compatibility** | Fully compatible | None |

**Bottom Line**: Your system automatically benefits from better matching with zero code changes required! 🎉

---

## Need Help?

- Run `python verify_jd_format.py` to see format comparison
- Check `MATCHING_IMPROVEMENTS.md` for overall matching enhancements
- Review code changes in `process/jd_process.py` and `prompt/extract_job_description.py`

---

Generated with Claude Code
