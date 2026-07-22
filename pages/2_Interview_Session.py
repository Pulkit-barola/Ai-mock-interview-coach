import streamlit as st
import time
from utils.helpers import init_session_state, apply_custom_css, render_sidebar_status
from modules.question_generator import QuestionGenerator
from modules.evaluator import AnswerEvaluator
from modules.voice_interview import VoiceInterviewManager

# Page config
st.set_page_config(
    page_title="Interview Session - AI Mock Interview",
    page_icon="🎙️",
    layout="wide"
)

init_session_state()
apply_custom_css()
render_sidebar_status()

st.markdown("<h1>🎙️ <span class='gradient-text'>Interview Session</span></h1>", unsafe_allow_html=True)

# Guard checks
if not st.session_state.candidate:
    st.warning("⚠️ **No candidate profile configured!** Please register on the **Home Page** first.")
    st.stop()

if not st.session_state.resume_parsed or not st.session_state.resume_data:
    st.warning("⚠️ **No resume uploaded!** Please go to the **Resume Analyzer** page and upload your resume to generate personalized questions.")
    st.stop()

db = st.session_state.db
candidate_id = st.session_state.candidate["id"]

# Distribute question types based on question count
def get_target_question_type(index, total):
    if index == 1:
        return "Technical"
    elif index == 2:
        return "Project"
    elif index == total:
        return "HR"
    elif index == 3:
        return "Scenario"
    else:
        return "Technical"

# UI Flow: Configuration vs Active Session vs Summary
if not st.session_state.interview_active:
    # 1. Config screen
    st.markdown("### ⚙️ Mock Interview Setup")
    
    col1, col2 = st.columns(2)
    with col1:
        role = st.selectbox(
            "Selected Role for Interview",
            options=["Software Engineer", "Data Scientist", "Data Analyst", "AI/ML Engineer", "Python Developer", "Custom Role"],
            index=["Software Engineer", "Data Scientist", "Data Analyst", "AI/ML Engineer", "Python Developer", "Custom Role"].index(st.session_state.selected_role)
        )
        st.session_state.selected_role = role
        
        difficulty = st.selectbox(
            "Starting Difficulty Level",
            options=["Easy", "Medium", "Hard"],
            index=1
        )
        
    with col2:
        q_count = st.slider("Total Number of Questions", min_value=3, max_value=8, value=5)
        mode = st.radio("Interview Mode", options=["Text Mode (Type answers)", "Voice Mode (Microphone enabled)"], index=0)
        
    st.info("💡 **Adaptive Engine Notice:** The system will dynamically increase question difficulty if you score high, or downgrade difficulty if you score low.")
    
    if st.button("🚀 Start Interview Session"):
        with st.spinner("Initializing session..."):
            session_db_id = db.create_session(candidate_id, role, difficulty)
            
            st.session_state.session_id = session_db_id
            st.session_state.interview_active = True
            st.session_state.current_question_index = 1
            st.session_state.current_difficulty = difficulty
            st.session_state.current_question = None
            st.session_state.session_history = []
            st.session_state.total_questions_count = q_count
            st.session_state.interview_mode = mode
            st.session_state.tts_audio_cache = None
            st.session_state.latest_feedback = None
            st.rerun()

else:
    # Check if interview limit reached
    total_q = st.session_state.total_questions_count
    curr_idx = st.session_state.current_question_index
    
    if curr_idx > total_q:
        # 2. Session finished - calculate metrics & complete session
        st.balloons()
        st.markdown("### 🎉 Interview Completed!")
        
        qas = db.get_session_qa(st.session_state.session_id)
        if qas:
            overall_scores = [q["score_overall"] for q in qas if q.get("answer_text")]
            final_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
        else:
            final_overall = 0.0
            
        db.complete_session(st.session_state.session_id, final_overall)
        
        st.markdown(f"""
        <div class='premium-card' style='text-align: center; max-width: 600px; margin: 0 auto;'>
            <h3>Congratulations on completing the mock interview!</h3>
            <p>You have answered {len(overall_scores)} questions in the <b>{st.session_state.selected_role}</b> category.</p>
            <div style='font-size: 3rem; font-weight: 800; color: #4f46e5; margin: 20px 0;'>{final_overall:.1f}%</div>
            <p>Aggregated Performance Score</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write(" ")
        cc1, cc2, cc3 = st.columns([1, 1, 1])
        with cc1:
            if st.button("📊 View Performance Charts"):
                st.switch_page("pages/3_Analytics_Dashboard.py")
        with cc2:
            if st.button("📄 Generate PDF Report"):
                st.switch_page("pages/4_Reports.py")
        with cc3:
            if st.button("🔄 Start New Interview"):
                st.session_state.interview_active = False
                st.session_state.session_id = None
                st.rerun()
        st.stop()

    # 3. Active questioning
    # Generate question if not already cached
    if st.session_state.current_question is None:
        with st.spinner("AI Coach is formulating the next question..."):
            try:
                generator = QuestionGenerator()
                target_type = get_target_question_type(curr_idx, total_q)
                
                # Fetch history context
                history_list = []
                past_qas = db.get_session_qa(st.session_state.session_id)
                for q in past_qas:
                    history_list.append({
                        "question": q["question_text"],
                        "type": q["question_type"],
                        "difficulty": q["difficulty"]
                    })
                
                # Generate question
                q_data = generator.generate_question(
                    resume_summary=st.session_state.resume_data.get("summary", ""),
                    candidate_skills=st.session_state.resume_data.get("skills", []),
                    role=st.session_state.selected_role,
                    difficulty=st.session_state.current_difficulty,
                    history=history_list,
                    target_type=target_type
                )
                
                # Save to database
                qa_db_id = db.add_question(
                    session_id=st.session_state.session_id,
                    question_text=q_data["question"],
                    question_type=q_data["type"],
                    difficulty=q_data["difficulty"],
                    expected_concepts=q_data["expected_concepts"],
                    ideal_answer=q_data.get("ideal_response_guideline", "")
                )
                
                # Load TTS if voice mode
                tts_bytes = None
                if "Voice" in st.session_state.interview_mode:
                    v_manager = VoiceInterviewManager()
                    tts_bytes = v_manager.text_to_speech_bytes(q_data["question"])
                
                st.session_state.current_question = {
                    "qa_id": qa_db_id,
                    "question": q_data["question"],
                    "type": q_data["type"],
                    "difficulty": q_data["difficulty"],
                    "expected_concepts": q_data["expected_concepts"],
                    "ideal_guideline": q_data.get("ideal_response_guideline", "")
                }
                st.session_state.tts_audio_cache = tts_bytes
                
            except Exception as e:
                st.error(f"Error generating interview question: {e}")
                st.stop()

    # Render Active Question Card
    q = st.session_state.current_question
    
    st.markdown(f"#### Question {curr_idx} of {total_q}")
    
    # Styled badges
    st.markdown(f"""
    <div>
        <span class='metric-badge badge-info'>{q['type']}</span>
        <span class='metric-badge badge-warning'>{q['difficulty']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='premium-card' style='border-left: 5px solid #4f46e5;'>
        <h3 style='margin: 0;'>{q['question']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Text-to-Speech Playback
    if st.session_state.tts_audio_cache:
        st.write("🔊 **AI Spoken Audio:**")
        st.audio(st.session_state.tts_audio_cache, format="audio/mp3")

    # Answer input options
    candidate_answer = ""
    
    if "Voice" in st.session_state.interview_mode:
        st.markdown("### 🎙️ Submit Spoken Answer")
        audio_file = st.audio_input(label="Record your answer using your microphone")
        
        if audio_file is not None:
            # Calculate hash of the audio to detect new recordings
            audio_data = audio_file.getvalue()
            import hashlib
            audio_hash = hashlib.md5(audio_data).hexdigest()
            
            if st.session_state.get("last_transcribed_audio_hash") != audio_hash:
                with st.spinner("🎤 Auto-transcribing your speech..."):
                    try:
                        v_manager = VoiceInterviewManager()
                        transcript = v_manager.transcribe_audio_bytes(audio_data, mime_type=audio_file.type)
                        
                        st.session_state.voice_transcript_text = transcript
                        st.session_state.voice_answer_textarea = transcript
                        st.session_state.last_transcribed_audio_hash = audio_hash
                        st.success("Speech auto-transcribed!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Auto-transcription error: {e}")
        
        # Display transcription in editable box
        val_text = st.session_state.get("voice_transcript_text", "")
        candidate_answer = st.text_area("Review / Edit Transcribed Answer:", value=val_text, height=180, key="voice_answer_textarea")
        
    else:
        st.markdown("### ✏️ Submit Text Answer")
        candidate_answer = st.text_area("Type your answer here:", height=200, placeholder="Explain your answer with details, examples, and technical concepts...")

    # Action Buttons
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Submit Answer"):
            if not candidate_answer.strip() or len(candidate_answer.strip()) < 10:
                st.warning("Please provide a more complete answer before submitting (minimum 10 characters).")
            else:
                with st.spinner("AI Coach is evaluating your answer..."):
                    try:
                        evaluator = AnswerEvaluator()
                        eval_res = evaluator.evaluate_answer(
                            question=q["question"],
                            answer=candidate_answer,
                            expected_concepts=q["expected_concepts"],
                            ideal_guideline=q["ideal_guideline"]
                        )
                        
                        # Save answer and scores
                        db.submit_answer(
                            qa_id=q["qa_id"],
                            answer_text=candidate_answer,
                            evaluation_result=eval_res
                        )
                        
                        # Adaptive Difficulty Algorithm
                        score = eval_res.get("score_overall", 50.0)
                        current_diff = st.session_state.current_difficulty
                        
                        if score >= 75.0:
                            # Increase difficulty
                            if current_diff == "Easy":
                                st.session_state.current_difficulty = "Medium"
                            elif current_diff == "Medium":
                                st.session_state.current_difficulty = "Hard"
                        elif score < 50.0:
                            # Decrease difficulty
                            if current_diff == "Hard":
                                st.session_state.current_difficulty = "Medium"
                            elif current_diff == "Medium":
                                st.session_state.current_difficulty = "Easy"
                        
                        # Update session database table with difficulty
                        db.update_session_difficulty(st.session_state.session_id, st.session_state.current_difficulty)
                        
                        # Save feedback to display in UI temporarily
                        st.session_state.latest_feedback = {
                            "question": q["question"],
                            "answer": candidate_answer,
                            "scores": eval_res,
                        }
                        
                        # Advance state
                        st.session_state.current_question_index += 1
                        st.session_state.current_question = None
                        st.session_state.tts_audio_cache = None
                        if "voice_transcript_text" in st.session_state:
                            del st.session_state.voice_transcript_text
                        if "voice_answer_textarea" in st.session_state:
                            del st.session_state.voice_answer_textarea
                        if "last_transcribed_audio_hash" in st.session_state:
                            del st.session_state.last_transcribed_audio_hash
                            
                        st.success("Answer successfully submitted!")
                        time.sleep(1) # Visual feedback pause
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error evaluating answer: {e}")
                        
    with col2:
        # Quit button
        if st.button("Quit Session"):
            st.session_state.interview_active = False
            st.session_state.session_id = None
            st.session_state.current_question = None
            st.rerun()

    # Display real-time feedback for the previous question at the bottom
    if st.session_state.latest_feedback:
        fb = st.session_state.latest_feedback
        scores = fb["scores"]
        
        st.markdown("---")
        st.markdown("### 📊 Live Coach Feedback (Previous Question)")
        
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        fcol1.metric("Overall Score", f"{scores.get('score_overall'):.1f}%")
        fcol2.metric("Technical Accuracy", f"{scores.get('score_accuracy'):.1f}%")
        fcol3.metric("Completeness", f"{scores.get('score_completeness'):.1f}%")
        fcol4.metric("Communication", f"{scores.get('score_communication'):.1f}%")
        
        st.markdown(f"""
        <div class='premium-card' style='border-left: 4px solid #10b981; background-color: #f0fdf4;'>
            <p><b>Feedback:</b> {scores.get('feedback', 'No feedback provided.')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Show Ideal Model Answer"):
            st.write(scores.get("ideal_answer", "No ideal response available."))
            
        with st.expander("Missing Concepts Flagged"):
            missing = scores.get("missing_concepts", [])
            if missing:
                st.write(", ".join(missing))
            else:
                st.write("None! You hit all expected conceptual keywords.")
