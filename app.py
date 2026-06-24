import streamlit as st
from utils.helpers import init_session_state, apply_custom_css, render_sidebar_status, check_env_api_key

# Page Config
st.set_page_config(
    page_title="AI Mock Interview Coach",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session variables
init_session_state()

# Custom styles
apply_custom_css()

# Sidebar
render_sidebar_status()

# Main UI layout
st.markdown("<h1>🤖 <span class='gradient-text'>AI Mock Interview Coach</span></h1>", unsafe_allow_html=True)
st.write("Prepare for your placements, internships, and dream job interviews with real-time feedback and adaptive questioning.")

# Check API key alert
if not check_env_api_key():
    st.warning("⚠️ **Gemini API Key is missing!** Please create a `.env` file in the project folder and set `GEMINI_API_KEY` to run the AI features.")

# Split layout into two sections
col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("""
    <div class='premium-card'>
        <h3>👋 Welcome to Your Personal Interview Prep Hub</h3>
        <p>This platform uses cutting-edge artificial intelligence to simulate realistic, technical, and behavioral interview sessions. Here's what you can do:</p>
        <ul>
            <li><b>Resume Analysis:</b> Upload your PDF resume to extract skills, detect gaps for standard roles, and list strengths.</li>
            <li><b>Interactive Mock Interview:</b> Conduct realistic text-based or voice-activated interviews with difficulty levels that adapt automatically to your performance.</li>
            <li><b>Performance Dashboard:</b> Review deep metrics on technical accuracy, completeness, and communication using Plotly charts.</li>
            <li><b>Professional Report:</b> Generate a comprehensive, print-ready PDF scorecard complete with model answers and improvement recommendations.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🛠️ Preparation Workflow")
    st.info("💡 **Step 1:** Enter your candidate details below.  \n"
            "💡 **Step 2:** Go to **Resume Analyzer** page to upload your resume and choose your target job role.  \n"
            "💡 **Step 3:** Start the **Interview Session** (supports microphone answers).  \n"
            "💡 **Step 4:** Analyze your performance trends in the **Analytics Dashboard** and export your feedback report in the **Reports** tab.")

with col2:
    st.markdown("### 👤 Candidate Setup")
    
    if st.session_state.candidate is None:
        st.write("Please configure your profile to start.")
        with st.form("candidate_form"):
            name = st.text_input("Full Name", placeholder="e.g. Jane Doe")
            email = st.text_input("Email Address", placeholder="e.g. jane.doe@example.com")
            submit = st.form_submit_button("Create Profile")
            
            if submit:
                if not name.strip() or not email.strip():
                    st.error("Name and Email are required.")
                elif "@" not in email:
                    st.error("Please enter a valid email address.")
                else:
                    try:
                        # Save candidate details to DB
                        candidate_db = st.session_state.db.create_or_get_candidate(name, email)
                        st.session_state.candidate = candidate_db
                        st.success(f"Profile saved! Welcome, {name}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Database error: {e}")
    else:
        st.markdown(f"""
        <div class='dark-premium-card'>
            <h4>Active Candidate Session</h4>
            <p><b>Name:</b> {st.session_state.candidate['name']}</p>
            <p><b>Email:</b> {st.session_state.candidate['email']}</p>
            <p style='color: #a5f3fc;'>Ready to analyze your resume. Navigate to the <b>Resume Analyzer</b> page to begin.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Change Profile / Sign Out"):
            st.session_state.candidate = None
            st.session_state.resume_parsed = False
            st.session_state.resume_data = None
            st.session_state.session_id = None
            st.session_state.interview_active = False
            st.rerun()

# Feature Highlights Cards Grid
st.markdown("### 🚀 Core Platform Features")
fcol1, fcol2, fcol3 = st.columns(3)

with fcol1:
    st.markdown("""
    <div class='premium-card' style='height: 220px;'>
        <h4>📄 Resume Analyzer</h4>
        <p>Extracts technical skills, certifications, and educational context. Matches credentials against target job role criteria to detect missing skills.</p>
    </div>
    """, unsafe_allow_html=True)

with fcol2:
    st.markdown("""
    <div class='premium-card' style='height: 220px;'>
        <h4>🎙️ Adaptive Speech Engine</h4>
        <p>Conducts mock interviews by adjusting question difficulties. Allows answers to be keyed in or spoken using browser-based audio transcription.</p>
    </div>
    """, unsafe_allow_html=True)

with fcol3:
    st.markdown("""
    <div class='premium-card' style='height: 220px;'>
        <h4>📊 Interactive Analytics</h4>
        <p>Presents overall performance gauges, step-wise difficulty tracking, category benchmarks, and compiles professional, downloadable PDF reports.</p>
    </div>
    """, unsafe_allow_html=True)
