import streamlit as st
import os
import io
from utils.helpers import init_session_state, apply_custom_css, render_sidebar_status
from modules.report_generator import ReportGenerator

# Page config
st.set_page_config(
    page_title="Performance Reports - AI Mock Interview",
    page_icon="📄",
    layout="wide"
)

init_session_state()
apply_custom_css()
render_sidebar_status()

st.markdown("<h1>📄 <span class='gradient-text'>Performance Reports</span></h1>", unsafe_allow_html=True)
st.write("Generate and download comprehensive PDF performance report cards containing candidate resumes, session reviews, scores, and mock feedback.")

# Guard check
if not st.session_state.candidate:
    st.warning("⚠️ **No candidate profile configured!** Please register on the **Home Page** first.")
    st.stop()

candidate = st.session_state.candidate
candidate_id = candidate["id"]
db = st.session_state.db

# Get resume details
resume_info = db.get_resume(candidate_id)

# Load completed sessions
sessions = db.get_candidate_sessions(candidate_id)
completed_sessions = [s for s in sessions if s.get("status") == "completed"]

if not completed_sessions:
    st.info("💡 **No completed interview sessions found.** Complete a mock interview in the **Interview Session** tab to enable PDF generation.")
    st.stop()

# Selector for completed sessions
session_options = []
session_map = {}

for s in completed_sessions:
    date_str = s.get("created_at")[:16] if s.get("created_at") else "N/A"
    label = f"Session ID: {s['id']} | Role: {s['role']} | Score: {s['overall_score']:.1f}% | Date: {date_str}"
    session_options.append(label)
    session_map[label] = s

selected_label = st.selectbox("Select Interview Session for Report Generation", options=session_options)
selected_session = session_map[selected_label]
session_id = selected_session["id"]

# Fetch QA data for the session
qa_history = db.get_session_qa(session_id)
answered_qas = [q for q in qa_history if q.get("answer_text")]

if not answered_qas:
    st.warning("⚠️ **This session has no answered questions.**")
    st.stop()

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 Session Summary")
    
    score = selected_session.get("overall_score", 0.0)
    score_color = "#ef4444"
    recommendation = "Needs Improvement"
    if score >= 80:
        score_color = "#10b981"
        recommendation = "Strong Recommendation"
    elif score >= 60:
        score_color = "#f59e0b"
        recommendation = "Recommend with Reservations"
        
    st.markdown(f"""
    <div class='premium-card' style='border-left: 4px solid {score_color};'>
        <h4>Interview Results</h4>
        <p><b>Target Role:</b> {selected_session.get('role', 'N/A')}</p>
        <p><b>Completion Date:</b> {selected_session.get('created_at')[:19]}</p>
        <p><b>Ending Difficulty:</b> {selected_session.get('current_difficulty', 'N/A')}</p>
        <div style='font-size: 2rem; font-weight: 800; color: {score_color}; margin: 15px 0;'>{score:.1f}%</div>
        <p><b>Status:</b> <span style='color: {score_color}; font-weight: 600;'>{recommendation}</span></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 📂 Compile PDF Report Card")
    st.write("Click below to compile all scores, transcripts, and AI feedback into a professional ReportLab PDF format.")
    
    # PDF generation trigger
    pdf_filename = f"interview_report_{session_id}.pdf"
    
    if st.button("🛠️ Compile PDF Report"):
        with st.spinner("Compiling ReportLab layout..."):
            try:
                # Create a temporary file path inside the workspace
                temp_pdf_path = os.path.join(os.getcwd(), pdf_filename)
                
                # Instantiate report generator
                generator = ReportGenerator()
                success = generator.generate_pdf_report(
                    candidate=candidate,
                    resume_info=resume_info,
                    session=selected_session,
                    qa_history=answered_qas,
                    output_path=temp_pdf_path
                )
                
                if success and os.path.exists(temp_pdf_path):
                    st.success("PDF Compiled successfully!")
                    
                    # Read binary data for download button
                    with open(temp_pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    # Remove temporary file
                    os.remove(temp_pdf_path)
                    
                    # Offer download button
                    st.download_button(
                        label="📥 Download Performance PDF Report",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to generate PDF file. Please verify database contents.")
            except Exception as e:
                st.error(f"Error compiling PDF: {e}")

# Detailed Q&A Preview inside the dashboard
st.markdown("### 📋 Interview Summary Preview")
for idx, q in enumerate(answered_qas, 1):
    with st.expander(f"Question {idx}: {q['question_text'][:80]}..."):
        st.write(f"**Full Question:** {q['question_text']}")
        st.write(f"**Difficulty:** {q['difficulty']} | **Type:** {q['question_type']}")
        st.write(" ")
        st.markdown(f"**Candidate Answer:**")
        st.info(q['answer_text'])
        st.markdown(f"**AI Evaluation Feedback:**")
        st.write(q['feedback'])
        
        # Scores grid
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Overall Score", f"{q['score_overall']:.1f}%")
        sc2.metric("Technical Accuracy", f"{q['score_accuracy']:.1f}%")
        sc3.metric("Completeness", f"{q['score_completeness']:.1f}%")
        sc4.metric("Communication", f"{q['score_communication']:.1f}%")
        
        if q.get("missing_concepts"):
            st.write(f"**Concepts Missing:** {', '.join(q['missing_concepts'])}")
        
        if q.get("ideal_answer"):
            st.write(f"**Ideal Answer Outline:** {q['ideal_answer']}")
