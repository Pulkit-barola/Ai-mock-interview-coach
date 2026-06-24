import streamlit as st
import pandas as pd
from utils.helpers import init_session_state, apply_custom_css, render_sidebar_status
from modules.analytics import InterviewAnalytics

# Page config
st.set_page_config(
    page_title="Analytics Dashboard - AI Mock Interview",
    page_icon="📊",
    layout="wide"
)

init_session_state()
apply_custom_css()
render_sidebar_status()

st.markdown("<h1>📊 <span class='gradient-text'>Interview Analytics Dashboard</span></h1>", unsafe_allow_html=True)
st.write("Track your preparation journey, identify conceptual weaknesses, and monitor your communication and technical growth.")

# Guard check
if not st.session_state.candidate:
    st.warning("⚠️ **No candidate profile configured!** Please register on the **Home Page** first.")
    st.stop()

candidate_id = st.session_state.candidate["id"]
db = st.session_state.db
analytics = InterviewAnalytics()

# Load all sessions for this candidate
sessions = db.get_candidate_sessions(candidate_id)

if not sessions:
    st.info("💡 **You haven't conducted any interviews yet.** Go to the **Interview Session** tab to start your first session and generate performance metrics.")
    st.stop()

# 1. Historical sessions overview
st.markdown("### 📈 Preparation Progress")
hcol1, hcol2 = st.columns([2, 1])

with hcol1:
    trend_fig = analytics.create_historical_sessions_trend(sessions)
    if trend_fig:
        st.plotly_chart(trend_fig, use_container_width=True)
    else:
        st.write("Insufficient historical data to render trends.")
        
with hcol2:
    # Quick statistics across all sessions
    completed_sessions = [s for s in sessions if s.get("status") == "completed"]
    total_interviews = len(sessions)
    avg_perf = sum(s.get("overall_score", 0.0) for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0.0
    
    st.markdown(f"""
    <div class='premium-card' style='height: 250px;'>
        <h4>Quick Statistics</h4>
        <p><b>Total Sessions Started:</b> {total_interviews}</p>
        <p><b>Total Sessions Completed:</b> {len(completed_sessions)}</p>
        <div style='font-size: 2.2rem; font-weight: 800; color: #0d9488; margin-top: 15px;'>{avg_perf:.1f}%</div>
        <p>Average Aggregated Score</p>
    </div>
    """, unsafe_allow_html=True)

# 2. Dropdown to select specific session for deep-dive
st.markdown("### 🔍 Session-Specific Deep Dive")

session_options = []
session_map = {}

for s in sessions:
    status_label = "Completed" if s.get("status") == "completed" else "Active/Incomplete"
    score_label = f"{s.get('overall_score', 0.0):.1f}%" if s.get("status") == "completed" else "N/A"
    date_str = s.get("created_at")[:16] if s.get("created_at") else "N/A"
    
    label = f"ID: {s['id']} | Role: {s['role']} | Score: {score_label} | {status_label} ({date_str})"
    session_options.append(label)
    session_map[label] = s

selected_label = st.selectbox("Select Interview Session to Analyze", options=session_options)
selected_session = session_map[selected_label]
session_id = selected_session["id"]

# Load QAs for this session
qa_history = db.get_session_qa(session_id)
answered_qas = [q for q in qa_history if q.get("answer_text")]

if not answered_qas:
    st.warning("⚠️ **This session has no answered questions.** Complete questions in the **Interview Session** tab to display metrics.")
    st.stop()

# Layout grid for selected session charts
col1, col2 = st.columns([1, 1])

with col1:
    # Gauge Chart
    gauge_fig = analytics.create_overall_score_gauge(selected_session.get("overall_score", 0.0))
    if gauge_fig:
        st.plotly_chart(gauge_fig, use_container_width=True)
        
with col2:
    # Radar Chart of Dimensions
    radar_fig = analytics.create_dimension_comparison_radar(answered_qas)
    if radar_fig:
        st.plotly_chart(radar_fig, use_container_width=True)

# Row 2
col3, col4 = st.columns(2)

with col3:
    # Score Trend Over Questions
    trend_line = analytics.create_score_trends_line(answered_qas)
    if trend_line:
        st.plotly_chart(trend_line, use_container_width=True)

with col4:
    # Difficulty Progression
    prog_fig = analytics.create_difficulty_progression_step(answered_qas)
    if prog_fig:
        st.plotly_chart(prog_fig, use_container_width=True)

# Row 3
col5, col6 = st.columns(2)

with col5:
    # Question type performance
    type_fig = analytics.create_question_type_performance(answered_qas)
    if type_fig:
        st.plotly_chart(type_fig, use_container_width=True)

with col6:
    # Topics / Missing concepts summary
    st.markdown("#### 💡 Missing Concepts List")
    
    all_missing = []
    for q in answered_qas:
        all_missing.extend(q.get("missing_concepts", []))
    all_missing = list(set([c.strip() for c in all_missing if c.strip()]))
    
    if all_missing:
        st.write("Revisit these conceptual fields to boost your next session accuracy:")
        for concept in all_missing:
            st.markdown(f"- <span style='color: #EF4444; font-weight: 500;'>{concept}</span>", unsafe_allow_html=True)
    else:
        st.success("Excellent! No major conceptual gaps were flagged in this interview session.")

# Render table of history
st.markdown("### 📋 Historical Session Logs Table")
logs_data = []
for s in sessions:
    logs_data.append({
        "Session ID": s["id"],
        "Target Role": s["role"],
        "Status": s["status"].upper(),
        "Ending Difficulty": s["current_difficulty"],
        "Aggregated Score": f"{s['overall_score']:.1f}%" if s["status"] == "completed" else "N/A",
        "Created Date": s["created_at"][:19] if s["created_at"] else "N/A"
    })
df_logs = pd.DataFrame(logs_data)
st.dataframe(df_logs, use_container_width=True, hide_index=True)
