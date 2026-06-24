import logging
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

logger = logging.getLogger(__name__)

class InterviewAnalytics:
    """Generates premium interactive Plotly charts for the Streamlit dashboard."""

    def __init__(self):
        # Premium color palette
        self.colors = {
            "primary": "#4F46E5",     # Indigo
            "secondary": "#0D9488",   # Teal
            "accent": "#F59E0B",      # Amber
            "danger": "#EF4444",      # Rose Red
            "success": "#10B981",     # Green
            "dark": "#1F2937",        # Charcoal
            "light": "#F9FAFB",       # Soft Grey
            "transparent": "rgba(0,0,0,0)"
        }

    def create_overall_score_gauge(self, score):
        """Creates an interactive Gauge chart displaying the overall performance score."""
        try:
            score = round(score, 1)
            # Pick a color based on score thresholds
            if score >= 80:
                bar_color = self.colors["success"]
            elif score >= 60:
                bar_color = self.colors["accent"]
            else:
                bar_color = self.colors["danger"]

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Overall Performance Score", 'font': {'size': 18, 'color': self.colors["dark"]}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': self.colors["dark"]},
                    'bar': {'color': bar_color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#E5E7EB",
                    'steps': [
                        {'range': [0, 50], 'color': '#FEE2E2'},    # Soft red
                        {'range': [50, 75], 'color': '#FEF3C7'},   # Soft amber
                        {'range': [75, 100], 'color': '#D1FAE5'}   # Soft green
                    ],
                }
            ))

            fig.update_layout(
                paper_bgcolor=self.colors["transparent"],
                plot_bgcolor=self.colors["transparent"],
                font={'color': self.colors["dark"], 'family': "Inter, sans-serif"},
                height=250,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return fig
        except Exception as e:
            logger.error(f"Error drawing gauge chart: {e}")
            return None

    def create_dimension_comparison_radar(self, qa_history):
        """Creates a Radar/Spider chart comparing Accuracy, Completeness, and Communication averages."""
        try:
            valid_qas = [q for q in qa_history if q.get("answer_text")]
            if not valid_qas:
                return None

            avg_accuracy = sum(q.get("score_accuracy", 0) for q in valid_qas) / len(valid_qas)
            avg_completeness = sum(q.get("score_completeness", 0) for q in valid_qas) / len(valid_qas)
            avg_communication = sum(q.get("score_communication", 0) for q in valid_qas) / len(valid_qas)

            categories = ['Technical Accuracy', 'Completeness', 'Communication']
            values = [avg_accuracy, avg_completeness, avg_communication]
            
            # To close the radar polygon
            categories.append(categories[0])
            values.append(values[0])

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                fillcolor='rgba(79, 70, 229, 0.2)', # Semi-transparent Indigo
                line=dict(color=self.colors["primary"], width=2),
                name='Interview Performance'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        gridcolor="#E5E7EB",
                        linecolor="#E5E7EB"
                    ),
                    angularaxis=dict(
                        gridcolor="#E5E7EB",
                        linecolor="#E5E7EB"
                    ),
                    bgcolor=self.colors["transparent"]
                ),
                showlegend=False,
                paper_bgcolor=self.colors["transparent"],
                plot_bgcolor=self.colors["transparent"],
                height=280,
                margin=dict(l=40, r=40, t=40, b=40)
            )
            return fig
        except Exception as e:
            logger.error(f"Error drawing radar chart: {e}")
            # Fallback to simple bar chart if radar fails
            return self._create_dimension_bar_fallback(qa_history)

    def _create_dimension_bar_fallback(self, qa_history):
        """Standard bar fallback when Radar plot fails or has insufficient dimensions."""
        valid_qas = [q for q in qa_history if q.get("answer_text")]
        avg_accuracy = sum(q.get("score_accuracy", 0) for q in valid_qas) / len(valid_qas)
        avg_completeness = sum(q.get("score_completeness", 0) for q in valid_qas) / len(valid_qas)
        avg_communication = sum(q.get("score_communication", 0) for q in valid_qas) / len(valid_qas)

        df = pd.DataFrame({
            'Dimension': ['Technical Accuracy', 'Completeness', 'Communication'],
            'Score (%)': [avg_accuracy, avg_completeness, avg_communication]
        })
        fig = px.bar(df, x='Dimension', y='Score (%)', color='Dimension',
                     color_discrete_sequence=[self.colors["primary"], self.colors["secondary"], self.colors["accent"]])
        fig.update_layout(height=280, paper_bgcolor=self.colors["transparent"], plot_bgcolor=self.colors["transparent"])
        return fig

    def create_score_trends_line(self, qa_history):
        """Creates a line chart showing progress of scores across each question in a session."""
        try:
            valid_qas = [q for q in qa_history if q.get("answer_text")]
            if not valid_qas:
                return None

            data = []
            for idx, q in enumerate(valid_qas, 1):
                data.append({
                    "Question": f"Q{idx}",
                    "Overall Score": q.get("score_overall", 0),
                    "Accuracy": q.get("score_accuracy", 0),
                    "Completeness": q.get("score_completeness", 0),
                    "Communication": q.get("score_communication", 0)
                })

            df = pd.DataFrame(data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["Question"], y=df["Overall Score"],
                mode='lines+markers', name='Overall',
                line=dict(color=self.colors["primary"], width=3),
                marker=dict(size=8)
            ))
            fig.add_trace(go.Scatter(
                x=df["Question"], y=df["Accuracy"],
                mode='lines+markers', name='Accuracy',
                line=dict(color=self.colors["secondary"], width=1.5, dash='dash'),
                marker=dict(size=6)
            ))
            fig.add_trace(go.Scatter(
                x=df["Question"], y=df["Completeness"],
                mode='lines+markers', name='Completeness',
                line=dict(color=self.colors["accent"], width=1.5, dash='dot'),
                marker=dict(size=6)
            ))

            fig.update_layout(
                title={'text': "Score Breakdown Trend", 'font': {'size': 14}},
                xaxis_title="Questions",
                yaxis_title="Scores (%)",
                yaxis=dict(range=[0, 105], gridcolor="#F3F4F6"),
                xaxis=dict(gridcolor="#F3F4F6"),
                paper_bgcolor=self.colors["transparent"],
                plot_bgcolor=self.colors["transparent"],
                height=280,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            return fig
        except Exception as e:
            logger.error(f"Error drawing line chart: {e}")
            return None

    def create_difficulty_progression_step(self, qa_history):
        """Creates a step chart detailing how difficulty adjusted over the interview session."""
        try:
            valid_qas = [q for q in qa_history if q.get("answer_text")]
            if not valid_qas:
                return None

            diff_map = {"Easy": 1, "Medium": 2, "Hard": 3}
            diff_reverse_map = {1: "Easy", 2: "Medium", 3: "Hard"}

            data = []
            for idx, q in enumerate(valid_qas, 1):
                difficulty_val = diff_map.get(q.get("difficulty", "Medium"), 2)
                data.append({
                    "Question": f"Q{idx}",
                    "Difficulty": difficulty_val,
                    "Difficulty Label": q.get("difficulty", "Medium")
                })

            df = pd.DataFrame(data)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["Question"], y=df["Difficulty"],
                mode='lines+markers',
                line=dict(color=self.colors["secondary"], width=3, shape='hv'), # Step line
                marker=dict(size=10, color=self.colors["secondary"]),
                text=df["Difficulty Label"],
                hoverinfo="x+text"
            ))

            fig.update_layout(
                title={'text': "Adaptive Difficulty Path", 'font': {'size': 14}},
                xaxis_title="Questions",
                yaxis_title="Difficulty Level",
                yaxis=dict(
                    tickvals=[1, 2, 3],
                    ticktext=["Easy", "Medium", "Hard"],
                    range=[0.5, 3.5],
                    gridcolor="#F3F4F6"
                ),
                xaxis=dict(gridcolor="#F3F4F6"),
                paper_bgcolor=self.colors["transparent"],
                plot_bgcolor=self.colors["transparent"],
                height=280,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return fig
        except Exception as e:
            logger.error(f"Error drawing difficulty chart: {e}")
            return None

    def create_question_type_performance(self, qa_history):
        """Bar chart evaluating the candidate's average score across different question types."""
        try:
            valid_qas = [q for q in qa_history if q.get("answer_text")]
            if not valid_qas:
                return None

            df = pd.DataFrame(valid_qas)
            avg_df = df.groupby("question_type")["score_overall"].mean().reset_index()
            avg_df.columns = ["Question Type", "Average Score"]

            fig = px.bar(
                avg_df,
                x="Question Type",
                y="Average Score",
                color="Question Type",
                color_discrete_map={
                    "Technical": self.colors["primary"],
                    "HR": self.colors["secondary"],
                    "Scenario": self.colors["accent"],
                    "Project": "#A78BFA" # Purple
                },
                labels={"Average Score": "Score (%)"}
            )

            fig.update_layout(
                title={'text': "Performance by Question Category", 'font': {'size': 14}},
                yaxis=dict(range=[0, 105], gridcolor="#F3F4F6"),
                xaxis=dict(gridcolor="#F3F4F6"),
                paper_bgcolor=self.colors["transparent"],
                plot_bgcolor=self.colors["transparent"],
                height=280,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return fig
        except Exception as e:
            logger.error(f"Error drawing category chart: {e}")
            return None

    def create_historical_sessions_trend(self, sessions):
        """Draws a trend chart showing overall scores over all interview sessions."""
        try:
            if not sessions:
                return None

            # Sort by date
            sessions_sorted = sorted(sessions, key=lambda x: x.get("created_at", ""))
            
            data = []
            for idx, s in enumerate(sessions_sorted, 1):
                data.append({
                    "Interview #": f"#{idx}",
                    "Role": s.get("role", "General"),
                    "Score (%)": s.get("overall_score", 0.0),
                    "Date": s.get("created_at")[:10] if s.get("created_at") else "N/A"
                })
            
            df = pd.DataFrame(data)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["Interview #"], y=df["Score (%)"],
                mode='lines+markers',
                line=dict(color=self.colors["primary"], width=3),
                marker=dict(size=8, color=self.colors["primary"]),
                hovertext=df["Role"] + " (" + df["Date"] + ")"
            ))

            fig.update_layout(
                title={'text': "Session Performance Trend", 'font': {'size': 14}},
                xaxis_title="Interviews",
                yaxis_title="Aggregated Score (%)",
                yaxis=dict(range=[0, 105], gridcolor="#F3F4F6"),
                xaxis=dict(gridcolor="#F3F4F6"),
                paper_bgcolor=self.colors["transparent"],
                plot_bgcolor=self.colors["transparent"],
                height=280,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return fig
        except Exception as e:
            logger.error(f"Error drawing historical trend chart: {e}")
            return None
