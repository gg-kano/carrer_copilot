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

## Quick Start

```bash
# Clone the repository
git clone https://github.com/gg-kano/carrer_copilot.git
cd carrer_copilot

# Install uv (if you don't have it)
pip install uv

# Install dependencies and create virtual environment
uv sync

# Set up your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Launch the app
streamlit run app.py
```

Visit `http://localhost:8501` in your browser and start matching candidates!

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
├── 📦 pyproject.toml                  # Project dependencies
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

