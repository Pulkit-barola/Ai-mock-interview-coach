# AI Mock Interview Platform

An intelligent, production-ready mock interview coach built using Python, Streamlit, Gemini API, SQLite, Plotly, and Speech Recognition. Designed to help students and job seekers prepare for interviews by providing resume feedback, simulating mock interviews, dynamically adjusting difficulty, and delivering comprehensive performance analytics and PDF report cards.

## Features

1. **Resume Analysis**: Extracts resume content, parses skills/tools/programming languages, generates a summary, and evaluates fit (identifying gaps, strengths, and weaknesses) against 5 core job roles (Data Analyst, Data Scientist, Python Developer, AI/ML Engineer, Software Engineer) or custom user-defined roles.
2. **AI Question Generator**: Custom-generates technical, HR, scenario-based, and project-based questions dynamically using Gemini.
3. **Adaptive Difficulty Engine**: Shifts interview difficulty ('Easy', 'Medium', 'Hard') based on the accuracy and depth of candidate answers.
4. **Answer Evaluation Module**: Assesses text or spoken inputs across multiple dimensions (Technical Accuracy, Completeness, Communication, Overall), exposes missing concepts, and proposes ideal answers.
5. **Voice Interview Mode**: Employs Google Text-to-Speech (gTTS) to vocalize questions and processes browser microphone recordings using Gemini's native audio capabilities.
6. **Analytics Dashboard**: Interactive Plotly visualizations tracking skill benchmarks, score progression, topic weaknesses, and difficulty level changes.
7. **Report Generation**: Instant generation and download of professional PDF performance cards using ReportLab.
8. **Robust Database Layer**: SQLite schema preserving history of candidates, resume profiles, session states, questions, answers, and scores.

## Project Structure

```
ai_mock_interview/
│
├── app.py                     # Streamlit Main App & Landing Page
├── requirements.txt           # Python Dependencies
├── .env.example               # Template for API Key Configuration
├── README.md                  # Documentation
│
├── pages/                     # Streamlit Page Directory
│   ├── 1_Resume_Analyzer.py   # Resume Upload & Parsing
│   ├── 2_Interview_Session.py # Interactive Interview (Text/Voice)
│   ├── 3_Analytics_Dashboard.py# Plotly Charts & Metrics
│   └── 4_Reports.py           # Session Review & PDF Download
│
├── modules/                   # Core Logic Engines
│   ├── __init__.py
│   ├── resume_parser.py       # PyPDF & Gemini Resume Parsing
│   ├── question_generator.py  # Interview Questions Engine
│   ├── evaluator.py           # Answer Evaluation and Scoring
│   ├── voice_interview.py     # TTS & Gemini Audio Transcription
│   ├── analytics.py           # Plotly Plot Generators
│   └── report_generator.py    # ReportLab PDF Generator
│
└── database/                  # Storage Layer
    ├── __init__.py
    └── db.py                  # SQLite Connection Manager
```

## Setup Instructions

1. **Clone or copy this folder structure** to your local machine.
2. **Create a virtual environment** and activate it:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   ```
3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure your API Key**:
   - Duplicate `.env.example` and name the new file `.env`.
   - Edit `.env` and fill in your Gemini API Key:
     ```env
     GEMINI_API_KEY=AIzaSy...
     ```
5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Database Schema

- **candidates**: Main candidate profiling table.
- **resumes**: Persists parsed skills, summary, strengths, weaknesses, and matching details.
- **sessions**: Tracks active/completed roles, initial difficulty levels, and accumulated score.
- **interview_qa**: Records each question asked, answers submitted, feedback, accuracy/completeness/communication breakdown scores, missing concepts, and ideal answer templates.
