<div align="center">

# AI Resume Manager & Job Matcher

### Intelligent Resume Management and Candidate Matching Powered by AI

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-FF4B4B.svg)](https://streamlit.io)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-orange.svg)](https://www.trychroma.com/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%20AI-4285F4.svg)](https://ai.google.dev/)

[Features](#features) • [Quick Start](#quick-start) • [Installation](#installation) • [Usage](#usage) • [Documentation](#project-structure)

</div>

---

## Overview

**Career Copilot** is an advanced AI-powered recruitment assistant that revolutionizes how you manage resumes and match candidates to job openings. Built with cutting-edge technologies like Google Gemini AI, ChromaDB vector database, and Streamlit, it provides intelligent resume parsing, semantic search, and automated candidate ranking.

### Why Career Copilot?

- **Save Time**: Automate resume screening and candidate matching
- **Improve Quality**: AI-powered analysis ensures better candidate-job fit
- **Scale Easily**: Handle hundreds of resumes with batch processing
- **Data-Driven**: Vector similarity search finds the best matches, not just keyword matches
- **User-Friendly**: Beautiful web interface - no technical knowledge required

## Features

### Core Capabilities

- **Intelligent Resume Parsing**: Extract structured data from PDF resumes using Google Gemini AI
- **Semantic Job Matching**: Find the best candidates using vector similarity, not just keywords
- **Batch Processing**: Upload and process entire folders of resumes at once
- **Interactive Dashboard**: Beautiful Streamlit interface for managing your recruitment pipeline
- **Vector Search**: Powered by ChromaDB for fast and accurate candidate retrieval
- **Resume Analytics**: View detailed breakdowns of skills, experience, and qualifications
- **Persistent Storage**: All data stored locally in a vector database for instant access

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit - Beautiful web interface |
| **AI Engine** | Google Gemini - Resume parsing & analysis |
| **Vector DB** | ChromaDB - Semantic search & storage |
| **Embeddings** | Sentence Transformers - Text embeddings |
| **PDF Parser** | PyPDF2 - PDF text extraction |
| **Language** | Python 3.12+ |

## Quick Start

Get up and running in 3 minutes:

```bash
# Clone the repository
git clone https://github.com/gg-kano/carrer_copilot.git
cd carrer_copilot

# Install dependencies (using pip)
pip install -r requirements.txt

# Set up your API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# Launch the app
streamlit run app.py
```

Visit `http://localhost:8501` in your browser and start matching candidates!

## Installation

### Prerequisites

- **Python 3.12+** - [Download here](https://www.python.org/downloads/)
- **Google Gemini API Key** - [Get free API key](https://makersuite.google.com/app/apikey)

### Detailed Setup

<details>
<summary>Click to expand installation instructions</summary>

#### 1. Clone the Repository

```bash
git clone https://github.com/gg-kano/carrer_copilot.git
cd carrer_copilot
```

#### 2. Install Dependencies

**Option A: Using uv (Recommended - Faster)**
```bash
pip install uv
uv sync
```

**Option B: Using pip**
```bash
pip install -r requirements.txt
```

#### 3. Configure Environment Variables

Copy the example file and add your API key:

```bash
# Linux/Mac
cp .env.example .env

# Windows
copy .env.example .env
```

Edit `.env` and add your Google Gemini API key:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

#### 4. Run the Application

```bash
streamlit run app.py
```

The application will automatically open in your browser at `http://localhost:8501`

</details>

## Usage

### Web Interface Workflow

#### 1. Upload Resumes

**Single Upload:**
1. Click on **"📄 Upload Resume"** tab
2. Drag and drop a PDF resume or click **"Browse files"**
3. The AI automatically extracts:
   - Candidate name and contact info
   - Skills and technologies
   - Work experience and education
   - Projects and achievements
4. View the parsed data and confirm

**Batch Upload:**
1. Navigate to **"📁 Batch Upload"** section
2. Enter the folder path containing multiple PDF resumes
3. Click **"Process Folder"**
4. Watch as all resumes are processed automatically

#### 2. Manage Job Descriptions

1. Go to **"💼 Job Description"** tab
2. Paste or type the job description
3. Click **"Analyze Job Description"**
4. AI extracts:
   - Required skills and qualifications
   - Experience level needed
   - Key responsibilities
5. Save the job description for matching

#### 3. Find Perfect Matches

1. Open **"🎯 Match Candidates"** tab
2. Select a job description from the dropdown
3. Set the number of top candidates to display
4. Click **"Find Matches"**
5. View ranked candidates with:
   - Match percentage score
   - AI-generated reasoning
   - Skill alignment breakdown
   - Missing qualifications

### Screenshots

> **Note**: Add screenshots of your application here to showcase the UI

```
[Upload Resume Interface]  [Batch Processing]  [Matching Results]
```

### Programmatic Usage (Advanced)

For developers who want to integrate Career Copilot into their own applications:

```python
from database.chroma_db import ChromaDBStorage
from process.resume_process import ResumePreprocessor
from process.jd_process import JDPreprocessor
from match.resume_jd_matcher import ResumeJDMatcher

# Initialize components
db = ChromaDBStorage(persist_directory="./chroma_db")
resume_processor = ResumePreprocessor()
jd_processor = JDPreprocessor()
matcher = ResumeJDMatcher()

# Process and store a resume
with open("candidate_resume.pdf", "rb") as f:
    resume_bytes = f.read()
    resume_data = resume_processor.parse_with_llm(resume_bytes, is_pdf=True)
    db.add_resume(
        resume_id=resume_data['name'].lower().replace(' ', '_'),
        resume_data=resume_data
    )

# Process a job description
jd_text = """
Senior Software Engineer - AI/ML
Requirements:
- 5+ years Python development
- Experience with LLMs and vector databases
- Strong background in web applications
- Bachelor's degree in Computer Science
"""
jd_data = jd_processor.process(jd_text)

# Find top 5 matching candidates
matches = matcher.find_matches(jd_data, top_k=5)

# Display results
for i, match in enumerate(matches, 1):
    print(f"\n{i}. {match['name']}")
    print(f"   Match Score: {match['score']}%")
    print(f"   Reasoning: {match['reason']}")
    print(f"   Top Skills: {', '.join(match['skills'][:5])}")
```

**Output:**
```
1. John Doe
   Match Score: 92%
   Reasoning: Strong Python background with 7 years experience. Has worked with ChromaDB and LLMs in previous role.
   Top Skills: Python, Machine Learning, FastAPI, ChromaDB, LangChain

2. Jane Smith
   Match Score: 87%
   Reasoning: Extensive AI/ML experience with focus on NLP. Good Python skills but limited vector database experience.
   Top Skills: Python, TensorFlow, NLP, PyTorch, Scikit-learn
...
```

## Use Cases

Career Copilot is perfect for:

- **Recruiters & HR Teams**: Screen hundreds of resumes in minutes, not hours
- **Hiring Managers**: Find the best candidates based on actual requirements, not just keywords
- **Staffing Agencies**: Manage large candidate databases and match them to client needs
- **Job Seekers**: Analyze your resume against job descriptions to improve your chances
- **Small Businesses**: Professional recruitment tools without enterprise costs

## Performance

- **Resume Processing**: ~3-5 seconds per resume (with Gemini AI)
- **Batch Upload**: Process 100 resumes in ~5-8 minutes
- **Search Speed**: Instant results from thousands of resumes using vector search
- **Accuracy**: AI-powered semantic matching (not just keyword matching)
- **Storage**: All data persisted locally - no cloud storage required

## Project Structure

```
career-copilot/
├── 📄 app.py                          # Main Streamlit application
├── 🗄️ database/
│   └── chroma_db.py                  # ChromaDB vector storage
├── ⚙️ process/
│   ├── resume_process.py             # AI resume parsing
│   └── jd_process.py                 # Job description analysis
├── 🎯 match/
│   └── resume_jd_matcher.py          # Semantic matching engine
├── 🛠️ utils/
│   ├── cache_manager.py              # API response caching
│   ├── chunk_size_manager.py         # LLM context optimization
│   ├── logger.py                     # Logging system
│   └── exceptions.py                 # Custom error handling
├── 💬 prompt/                         # AI prompt templates
├── 📋 .env.example                    # Environment config template
├── 📦 pyproject.toml                  # Dependencies (uv)
├── 📦 requirements.txt                # Dependencies (pip)
├── 📖 README.md                       # Documentation
└── 📜 LICENSE                         # MIT License
```

## Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Your Google Gemini API key (required)

### Database

The application uses ChromaDB for vector storage. Data is persisted in the `chroma_db/` directory.

### Logging

Logs are stored in the `logs/` directory:
- `career_copilot_YYYYMMDD.log`: Application logs
- `errors_YYYYMMDD.log`: Error logs

## Development

### Adding New Features

1. **Custom Resume Parsers**: Extend `ResumePreprocessor` in `process/resume_process.py`
2. **Matching Algorithms**: Modify `ResumeJDMatcher` in `match/resume_jd_matcher.py`
3. **UI Components**: Add new sections in `app.py`

### Testing

```bash
# Run tests (if available)
pytest

# Check code style
black .
flake8 .
```

## Troubleshooting

<details>
<summary>Common Issues & Solutions</summary>

### API Key Errors

**Problem**: `"API key not found"` or `"Invalid API key"`

**Solutions:**
1. Verify `.env` file exists in the project root
2. Check that the variable name is exactly `GOOGLE_API_KEY`
3. Ensure no quotes around the API key value
4. Restart the application after changing `.env`

```bash
# Correct format in .env
GOOGLE_API_KEY=AIzaSyD...your_key_here
```

### PDF Extraction Issues

**Problem**: `"PDF extraction failed"` or blank text extracted

**Solutions:**
1. Ensure PDF is not password-protected
2. Check if PDF contains actual text (not scanned images)
3. Try opening PDF in Adobe Reader first to verify it's valid
4. For scanned PDFs, consider using OCR preprocessing

### ChromaDB Errors

**Problem**: Database connection or corruption errors

**Solutions:**
1. Delete `chroma_db/` directory (data will be lost)
2. Restart the application
3. Re-upload your resumes

```bash
# Clean slate
rm -rf chroma_db/
streamlit run app.py
```

### Memory Issues

**Problem**: Application crashes when processing large batches

**Solutions:**
1. Process fewer resumes at once (try batches of 20-50)
2. Increase system memory allocation
3. Clear cache periodically

### Slow Performance

**Problem**: Resume processing is very slow

**Possible Causes:**
- Slow internet connection (affects Gemini API calls)
- Large PDF files
- First-time model loading

**Solutions:**
1. Check internet connection
2. Enable caching in settings
3. Process during off-peak hours

</details>

## Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- **🐛 Report Bugs**: Open an issue with details about the problem
- **💡 Suggest Features**: Share your ideas for improvements
- **📖 Improve Documentation**: Fix typos, add examples, clarify instructions
- **🔧 Submit Code**: Fix bugs or add new features

### Development Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/carrer_copilot.git
   cd carrer_copilot
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write clean, documented code
   - Follow existing code style
   - Test your changes thoroughly

4. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Describe your changes clearly
   - Reference any related issues
   - Wait for review

### Code Style

- Use **Black** for Python formatting
- Follow **PEP 8** conventions
- Add docstrings to functions
- Keep functions focused and small

## Roadmap

Future enhancements we're considering:

- [ ] Multi-language support (resumes in different languages)
- [ ] Export matched candidates to CSV/Excel
- [ ] Email integration for candidate outreach
- [ ] Resume scoring and suggestions
- [ ] Interview scheduling integration
- [ ] Docker containerization
- [ ] REST API for programmatic access
- [ ] Support for more file formats (DOCX, TXT)

## FAQ

<details>
<summary>Is my data secure?</summary>

Yes! All data is stored locally on your machine. Nothing is sent to external servers except API calls to Google Gemini for AI processing. Your resumes and candidate data never leave your control.
</details>

<details>
<summary>How much does it cost?</summary>

Career Copilot is free and open-source. You only need a Google Gemini API key, which has a free tier that's generous for most use cases.
</details>

<details>
<summary>Can I use this commercially?</summary>

Yes! This project is licensed under the MIT License, which allows commercial use. See the LICENSE file for details.
</details>

<details>
<summary>Does it work offline?</summary>

Partially. The vector search and matching work offline, but resume parsing requires an internet connection for the Gemini API calls.
</details>

## Support

- **Issues**: [GitHub Issues](https://github.com/gg-kano/carrer_copilot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gg-kano/carrer_copilot/discussions)

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with amazing open-source technologies:

- **[Google Gemini](https://ai.google.dev/)** - Advanced AI for resume parsing
- **[ChromaDB](https://www.trychroma.com/)** - High-performance vector database
- **[Streamlit](https://streamlit.io/)** - Beautiful Python web framework
- **[Sentence Transformers](https://www.sbert.net/)** - State-of-the-art embeddings

---

<div align="center">

**Made with ❤️ for recruiters and hiring managers**

⭐ Star this repo if you find it helpful! ⭐

</div>
