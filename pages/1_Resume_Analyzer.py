import streamlit as st
import os
from utils.helpers import init_session_state, apply_custom_css, render_sidebar_status
from modules.resume_parser import ResumeParser

# Page config
st.set_page_config(
    page_title="Resume Analyzer - AI Mock Interview",
    page_icon="📄",
    layout="wide"
)

init_session_state()
apply_custom_css()
render_sidebar_status()

st.markdown("<h1>📄 <span class='gradient-text'>Resume Analyzer</span></h1>", unsafe_allow_html=True)
st.write("Upload your resume and select your target job role to identify skill gaps and analyze alignment.")

# Check if candidate is registered
if not st.session_state.candidate:
    st.warning("⚠️ **No profile set up!** Please go to the **Home Page** (app.py) first to enter your Name and Email.")
    st.stop()

candidate_id = st.session_state.candidate["id"]
db = st.session_state.db

# Try to load existing resume from database on load
if not st.session_state.resume_parsed:
    existing_resume = db.get_resume(candidate_id)
    if existing_resume:
        st.session_state.resume_parsed = True
        st.session_state.resume_data = existing_resume
        st.session_state.resume_db_id = existing_resume["id"]
        # Restore role alignment if it exists for this role
        if existing_resume.get("missing_skills"):
            role = st.session_state.selected_role
            if role in existing_resume["missing_skills"]:
                # Restore the cache
                missing = existing_resume["missing_skills"][role]
                st.session_state.role_alignment = {
                    "missing_skills": missing,
                    "role_strengths": existing_resume["strengths"], # generic fallback or cache
                    "role_weaknesses": existing_resume["weaknesses"],
                    "suitability_score": 70, # general suitability default
                    "fit_explanation": "Resume loaded from cache. Perform re-match for fresh analysis."
                }

col1, col2 = st.columns([3, 2])

with col1:
    st.markdown("### 1. Upload PDF Resume")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Extract & Parse Resume"):
            with st.spinner("Extracting text and parsing with Gemini API..."):
                try:
                    parser = ResumeParser()
                    # Extract text
                    extracted_text = parser.extract_text_from_pdf(uploaded_file)
                    # Parse using Gemini
                    parsed_json = parser.parse_resume_text(extracted_text)
                    
                    # Save to database
                    resume_id = db.save_resume(
                        candidate_id=candidate_id,
                        file_name=uploaded_file.name,
                        extracted_text=extracted_text,
                        parsed_data=parsed_json
                    )
                    
                    st.session_state.resume_parsed = True
                    st.session_state.resume_data = parsed_json
                    st.session_state.resume_db_id = resume_id
                    
                    # Auto run alignment on upload/parse
                    try:
                        role = st.session_state.selected_role
                        alignment = parser.analyze_role_alignment(
                            resume_data=parsed_json,
                            role=role,
                            custom_requirements=None
                        )
                        st.session_state.role_alignment = alignment
                        missing_skills_dict = {role: alignment.get("missing_skills", [])}
                        db.update_resume_missing_skills(candidate_id, missing_skills_dict)
                    except Exception:
                        st.session_state.role_alignment = None
                    
                    st.success("Resume parsed and analyzed successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing resume: {e}")

    # Display parsed resume info if available
    if st.session_state.resume_parsed and st.session_state.resume_data:
        res = st.session_state.resume_data
        st.markdown("### 📝 Extracted Profile Summary")
        st.markdown(f"""
        <div class='premium-card'>
            <h4>{res.get('name', st.session_state.candidate['name'])}</h4>
            <p style='color: #4B5563;'><b>Email:</b> {res.get('email', st.session_state.candidate['email'])}</p>
            <p><b>Summary:</b> {res.get('summary', 'No summary available.')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for extracted skills
        tab1, tab2, tab3 = st.tabs(["💻 Skills & Languages", "🏗️ Projects", "🎓 Education"])
        
        with tab1:
            st.write("**Programming Languages:**")
            languages = res.get("programming_languages", [])
            st.write(", ".join(languages) if languages else "None detected")
            
            st.write("**Technical Skills / Concepts:**")
            skills = res.get("skills", [])
            st.write(", ".join(skills) if skills else "None detected")
            
            st.write("**Tools & Technologies:**")
            tools = res.get("tools", [])
            st.write(", ".join(tools) if tools else "None detected")
            
        with tab2:
            projects = res.get("projects", [])
            if projects:
                for proj in projects:
                    st.markdown(f"**{proj.get('title', 'Project')}**")
                    st.write(proj.get("description", "No description."))
                    st.write("---")
            else:
                st.write("No projects detected.")
                
        with tab3:
            edu = res.get("education", [])
            if edu:
                for school in edu:
                    st.markdown(f"🎓 **{school.get('degree', 'Degree')}**")
                    st.write(f"{school.get('institution', 'Institution')} ({school.get('year', 'N/A')})")
                    st.write("---")
            else:
                st.write("No education records detected.")

with col2:
    st.markdown("### 2. Job Role Selection")
    
    roles = [
        "Data Analyst",
        "Data Scientist",
        "Python Developer",
        "AI/ML Engineer",
        "Software Engineer",
        "Custom Role"
    ]
    
    selected_role = st.selectbox(
        "Choose target job role",
        options=roles,
        index=roles.index(st.session_state.selected_role) if st.session_state.selected_role in roles else 4
    )
    
    st.session_state.selected_role = selected_role
    custom_desc = ""
    
    if selected_role == "Custom Role":
        custom_desc = st.text_area(
            "Enter custom role description or requirements:",
            value=st.session_state.custom_role_desc,
            placeholder="e.g. Frontend Engineer with React, TypeScript, and state management knowledge."
        )
        st.session_state.custom_role_desc = custom_desc
        
    if st.session_state.resume_parsed and st.session_state.resume_data:
        if st.button("Perform Job Role Match"):
            with st.spinner(f"Analyzing alignment for {selected_role}..."):
                try:
                    parser = ResumeParser()
                    alignment = parser.analyze_role_alignment(
                        resume_data=st.session_state.resume_data,
                        role=selected_role,
                        custom_requirements=custom_desc if selected_role == "Custom Role" else None
                    )
                    
                    st.session_state.role_alignment = alignment
                    
                    # Cache the missing skills in the database
                    missing_skills_dict = {selected_role: alignment.get("missing_skills", [])}
                    db.update_resume_missing_skills(candidate_id, missing_skills_dict)
                    
                    st.success("Role match completed successfully!")
                except Exception as e:
                    st.error(f"Error performing alignment: {e}")
                    
        # Display Alignment Feedback
        if st.session_state.role_alignment:
            align = st.session_state.role_alignment
            score = align.get("suitability_score", 50)
            
            st.markdown("#### 🎯 Suitability & Gap Analysis")
            
            # Score Callout Color
            score_color = "#ef4444"
            if score >= 80:
                score_color = "#10b981"
            elif score >= 60:
                score_color = "#f59e0b"
                
            st.markdown(f"""
            <div style='background-color: {score_color}1a; border: 1px solid {score_color}; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;'>
                <span style='font-size: 2.2rem; font-weight: 800; color: {score_color};'>{score}%</span><br/>
                <span style='font-weight: 500;'>Suitability Score</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.write(f"**Fit Summary:** {align.get('fit_explanation', '')}")
            
            # Missing skills lists (Critical requirements)
            missing = align.get("missing_skills", [])
            st.markdown("⚠️ **Missing Skills / Gaps**")
            if missing:
                for mis in missing:
                    st.markdown(f"- <span style='color: #ef4444; font-weight: 500;'>{mis}</span>", unsafe_allow_html=True)
            else:
                st.success("No critical skill gaps detected for this role!")
                
            # Tailored Strengths and weaknesses
            st.markdown("🌟 **Role Strengths**")
            for strg in align.get("role_strengths", []):
                st.write(f"- {strg}")
                
            st.markdown("🔍 **Role Improvement Areas**")
            for weak in align.get("role_weaknesses", []):
                st.write(f"- {weak}")
    else:
        st.info("💡 **Upload and parse your resume** first to analyze job role match and skill gaps.")
