# Resume Manager & Job Matcher

A powerful AI-powered resume management and job matching system built with Streamlit and ChromaDB. This application helps you manage resumes, analyze job descriptions, and find the best candidate-job matches using advanced AI technology.

## Features

- **Resume Management**: Upload, store, and manage resumes in PDF format
- **Job Description Processing**: Parse and analyze job descriptions
- **AI-Powered Matching**: Intelligent matching between resumes and job descriptions using Google Gemini
- **Vector Database**: Efficient storage and retrieval using ChromaDB
- **Interactive Web Interface**: User-friendly interface built with Streamlit

## Tech Stack

- **Frontend**: Streamlit
- **Vector Database**: ChromaDB
- **AI/ML**: Google Gemini API, Sentence Transformers
- **PDF Processing**: PyPDF2
- **Python**: 3.12+

## Installation

### Prerequisites

- Python 3.12 or higher
- Google Gemini API key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Setup Steps

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd resume
```

2. **Install dependencies**

Using uv (recommended):
```bash
pip install uv
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:
```
GOOGLE_API_KEY=your_google_api_key_here
```

4. **Run the application**
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage Examples

### 1. Upload a Resume

```python
# The app will automatically process PDF resumes
# Navigate to the "Upload Resume" section
# Click "Browse files" and select a PDF resume
# The system will:
#   - Extract text from the PDF
#   - Parse skills, experience, and education
#   - Store in the vector database
```

### 2. Add a Job Description

```python
# Navigate to "Job Description" section
# Paste the job description text
# The system will:
#   - Extract required skills and qualifications
#   - Analyze job requirements
#   - Store for matching
```

### 3. Match Resumes to Jobs

```python
# Navigate to "Match" section
# Select a job description
# The system will:
#   - Search through all stored resumes
#   - Rank candidates by relevance
#   - Display match scores and reasons
```

### Example: Programmatic Usage

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

# Process a resume
with open("resume.pdf", "rb") as f:
    resume_text = extract_text_from_pdf(f)
    resume_data = resume_processor.process(resume_text)
    db.add_resume(resume_data)

# Process a job description
jd_text = """
Senior Software Engineer
Requirements:
- 5+ years Python experience
- Experience with AI/ML
- Strong background in web development
"""
jd_data = jd_processor.process(jd_text)

# Find matches
matches = matcher.find_matches(jd_data, top_k=5)
for match in matches:
    print(f"Candidate: {match['name']}")
    print(f"Score: {match['score']}")
    print(f"Reason: {match['reason']}\n")
```

## Project Structure

```
resume/
├── app.py                  # Main Streamlit application
├── database/
│   └── chroma_db.py       # ChromaDB storage implementation
├── process/
│   ├── resume_process.py  # Resume preprocessing
│   └── jd_process.py      # Job description processing
├── match/
│   └── resume_jd_matcher.py  # Matching algorithm
├── utils/
│   ├── cache_manager.py   # Cache management
│   ├── chunk_size_manager.py  # Chunk size optimization
│   ├── logger.py          # Logging utilities
│   └── exceptions.py      # Custom exceptions
├── prompt/                 # AI prompts
├── .env.example           # Environment variables template
├── pyproject.toml         # Project dependencies
└── README.md              # This file
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

### Common Issues

**Issue**: "API key not found"
- **Solution**: Make sure you've created `.env` file with your `GOOGLE_API_KEY`

**Issue**: "PDF extraction failed"
- **Solution**: Ensure the PDF is not password-protected and is a valid text-based PDF

**Issue**: "ChromaDB error"
- **Solution**: Delete the `chroma_db/` directory and restart the application

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini for AI capabilities
- ChromaDB for vector database
- Streamlit for the web framework
