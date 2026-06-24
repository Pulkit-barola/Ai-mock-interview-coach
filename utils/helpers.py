import os
import streamlit as st
from database.db import DatabaseManager

def init_session_state():
    """Initializes standard state variables in Streamlit session_state."""
    # Database
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager()

    # Candidate Profile
    if "candidate" not in st.session_state:
        st.session_state.candidate = None # Holds dict with: id, name, email
    if "resume_parsed" not in st.session_state:
        st.session_state.resume_parsed = False
    if "resume_data" not in st.session_state:
        st.session_state.resume_data = None # Parsed resume JSON
    if "resume_db_id" not in st.session_state:
        st.session_state.resume_db_id = None

    # Job Fit Details
    if "selected_role" not in st.session_state:
        st.session_state.selected_role = "Software Engineer"
    if "custom_role_desc" not in st.session_state:
        st.session_state.custom_role_desc = ""
    if "role_alignment" not in st.session_state:
        st.session_state.role_alignment = None

    # Interview Session
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "current_difficulty" not in st.session_state:
        st.session_state.current_difficulty = "Medium"
    if "current_question" not in st.session_state:
        st.session_state.current_question = None # Dict with: id, text, expected, type
    if "session_history" not in st.session_state:
        st.session_state.session_history = [] # List of past question-answer evaluations
    if "tts_audio_cache" not in st.session_state:
        st.session_state.tts_audio_cache = None

def check_env_api_key():
    """Checks if GEMINI_API_KEY is configured in the environment."""
    from dotenv import load_dotenv
    load_dotenv(override=True) # Load from .env if present

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False
    return True

def apply_custom_css():
    """Injects custom Google Fonts and premium CSS styling into Streamlit."""
    css = """
    <style>
        /* Import Outfit or Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Outfit', sans-serif;
        }

        /* Glassmorphic cards */
        .premium-card {
            background: rgba(255, 255, 255, 0.75);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(229, 231, 235, 0.5);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            margin-bottom: 20px;
        }
        
        .dark-premium-card {
            background: rgba(30, 41, 59, 0.85);
            color: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(71, 85, 105, 0.3);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* Accent text and headings */
        .gradient-text {
            background: linear-gradient(135deg, #4f46e5 0%, #0d9488 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }
        
        /* Metric badges */
        .metric-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.875rem;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        
        .badge-success { background-color: #D1FAE5; color: #065F46; }
        .badge-warning { background-color: #FEF3C7; color: #92400E; }
        .badge-danger { background-color: #FEE2E2; color: #991B1B; }
        .badge-info { background-color: #E0F2FE; color: #075985; }

        /* Custom buttons styling */
        .stButton>button {
            border-radius: 8px;
            background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
            color: white;
            border: none;
            font-weight: 500;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
            transform: translateY(-1px);
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_sidebar_status():
    """Renders candidate status and environment configurations in the sidebar."""
    st.sidebar.image("https://img.icons8.com/clouds/100/gender-neutral-user.png", width=70)
    
    # Check Gemini API status
    if check_env_api_key():
        st.sidebar.success("Gemini API Key: Configured")
    else:
        st.sidebar.error("Gemini API Key: Missing")
        st.sidebar.info("Set GEMINI_API_KEY in a .env file or environment variables to enable all AI capabilities.")

    # Candidate Status
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Profile Status")
    if st.session_state.candidate:
        st.sidebar.write(f"**Candidate:** {st.session_state.candidate['name']}")
        st.sidebar.write(f"**Email:** {st.session_state.candidate['email']}")
        if st.session_state.resume_parsed:
            st.sidebar.success("Resume Loaded")
            st.sidebar.write(f"**Role:** {st.session_state.selected_role}")
        else:
            st.sidebar.warning("No Resume Uploaded")
    else:
        st.sidebar.warning("No active profile. Configure on Home page.")
