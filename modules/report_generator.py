import os
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates professional, styled PDF performance reports for candidates using ReportLab."""

    def __init__(self):
        pass

    def generate_pdf_report(self, candidate, resume_info, session, qa_history, output_path):
        """Compiles resume summary, session statistics, questions, answers, and scores into a styled PDF."""
        try:
            # Setup document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=40,
                leftMargin=40,
                topMargin=40,
                bottomMargin=40
            )

            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=24,
                leading=28,
                textColor=colors.HexColor('#1E3A8A'), # Navy
                spaceAfter=15
            )
            
            subtitle_style = ParagraphStyle(
                'ReportSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                leading=16,
                textColor=colors.HexColor('#4B5563'), # Grey
                spaceAfter=25
            )
            
            h1_style = ParagraphStyle(
                'ReportH1',
                parent=styles['Heading2'],
                fontSize=16,
                leading=20,
                textColor=colors.HexColor('#1E3A8A'),
                spaceBefore=15,
                spaceAfter=10,
                keepWithNext=True
            )
            
            h2_style = ParagraphStyle(
                'ReportH2',
                parent=styles['Heading3'],
                fontSize=12,
                leading=16,
                textColor=colors.HexColor('#0D9488'), # Teal
                spaceBefore=10,
                spaceAfter=5,
                keepWithNext=True
            )
            
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#1F2937') # Charcoal
            )
            
            italic_body = ParagraphStyle(
                'ReportItalicBody',
                parent=body_style,
                fontName='Helvetica-Oblique',
                textColor=colors.HexColor('#4B5563')
            )
            
            meta_label_style = ParagraphStyle(
                'MetaLabel',
                parent=body_style,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#1F2937')
            )

            story = []

            # --- Header / Title Block ---
            story.append(Paragraph("AI MOCK INTERVIEW REPORT CARD", title_style))
            date_str = datetime.now().strftime("%B %d, %Y")
            story.append(Paragraph(f"Generated on {date_str}  |  Platform: AI Interview Coach", subtitle_style))
            story.append(Spacer(1, 10))

            # --- Candidate and Session Details Table ---
            details_data = [
                [
                    Paragraph("Candidate Name:", meta_label_style), Paragraph(candidate.get("name", "N/A"), body_style),
                    Paragraph("Job Role:", meta_label_style), Paragraph(session.get("role", "N/A"), body_style)
                ],
                [
                    Paragraph("Email Address:", meta_label_style), Paragraph(candidate.get("email", "N/A"), body_style),
                    Paragraph("Session Date:", meta_label_style), Paragraph(session.get("created_at")[:10] if session.get("created_at") else "N/A", body_style)
                ],
                [
                    Paragraph("Initial Difficulty:", meta_label_style), Paragraph(session.get("initial_difficulty", "N/A"), body_style),
                    Paragraph("Ending Difficulty:", meta_label_style), Paragraph(session.get("current_difficulty", "N/A"), body_style)
                ]
            ]
            
            details_table = Table(details_data, colWidths=[110, 150, 110, 150])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor('#E5E7EB')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 20))

            # --- Resume Analysis summary ---
            if resume_info:
                story.append(Paragraph("Resume Summary & Insights", h1_style))
                story.append(Paragraph(resume_info.get("summary", "No summary available."), body_style))
                story.append(Spacer(1, 10))

            # --- Overall Scores Table ---
            story.append(Paragraph("Performance Metrics Overview", h1_style))
            
            # Fetch summary statistics
            avg_accuracy = 0.0
            avg_completeness = 0.0
            avg_communication = 0.0
            avg_overall = session.get("overall_score", 0.0)
            
            answered_questions = [qa for qa in qa_history if qa.get("answer_text")]
            
            if answered_questions:
                avg_accuracy = sum(q.get("score_accuracy", 0.0) for q in answered_questions) / len(answered_questions)
                avg_completeness = sum(q.get("score_completeness", 0.0) for q in answered_questions) / len(answered_questions)
                avg_communication = sum(q.get("score_communication", 0.0) for q in answered_questions) / len(answered_questions)
            
            # Format recommendation
            recommendation = "NEEDS IMPROVEMENT"
            rec_color = "#EF4444"
            if avg_overall >= 80.0:
                recommendation = "STRONG RECOMMENDATION"
                rec_color = "#10B981"
            elif avg_overall >= 60.0:
                recommendation = "RECOMMEND WITH RESERVATIONS"
                rec_color = "#F59E0B"

            metrics_data = [
                [Paragraph("<b>Metric</b>", meta_label_style), Paragraph("<b>Score (%)</b>", meta_label_style), Paragraph("<b>Evaluation Status</b>", meta_label_style)],
                [Paragraph("Technical Accuracy", body_style), Paragraph(f"{avg_accuracy:.1f}%", body_style), Paragraph("Satisfactory" if avg_accuracy >= 65 else "Focus Area", body_style)],
                [Paragraph("Completeness & Gaps", body_style), Paragraph(f"{avg_completeness:.1f}%", body_style), Paragraph("Satisfactory" if avg_completeness >= 65 else "Focus Area", body_style)],
                [Paragraph("Communication Quality", body_style), Paragraph(f"{avg_communication:.1f}%", body_style), Paragraph("Satisfactory" if avg_communication >= 65 else "Focus Area", body_style)],
                [
                    Paragraph("<b>Final Combined Score</b>", meta_label_style), 
                    Paragraph(f"<b>{avg_overall:.1f}%</b>", meta_label_style), 
                    Paragraph(f"<font color='{rec_color}'><b>{recommendation}</b></font>", body_style)
                ],
            ]
            
            metrics_table = Table(metrics_data, colWidths=[180, 120, 220])
            metrics_table.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#1E3A8A')),
                ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#F9FAFB')]),
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EFF6FF')),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EFF6FF')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 20))

            # --- Weak Areas & Improvement Suggestions ---
            all_missing_concepts = []
            for q in answered_questions:
                all_missing_concepts.extend(q.get("missing_concepts", []))
            
            # Deduplicate missing concepts
            all_missing_concepts = list(set([c.strip() for c in all_missing_concepts if c.strip()]))

            if all_missing_concepts or (resume_info and resume_info.get("missing_skills")):
                story.append(Paragraph("Actionable Improvement Plan", h1_style))
                
                # Role-specific missing skills
                missing_role_skills = []
                if resume_info:
                    role_missing_dict = resume_info.get("missing_skills", {})
                    missing_role_skills = role_missing_dict.get(session.get("role", ""), [])
                
                if missing_role_skills:
                    story.append(Paragraph("<b>Missing Prerequisites for Job Role:</b>", h2_style))
                    story.append(Paragraph(", ".join(missing_role_skills), body_style))
                    story.append(Spacer(1, 5))
                
                if all_missing_concepts:
                    story.append(Paragraph("<b>Conceptual Gaps Identified During Interview:</b>", h2_style))
                    bullet_text = ""
                    for concept in all_missing_concepts[:10]: # Limit to top 10
                        bullet_text += f"• {concept}<br/>"
                    story.append(Paragraph(bullet_text, body_style))
                    story.append(Spacer(1, 5))
                
                story.append(Paragraph("<b>Self-Study Roadmap Recommendations:</b>", h2_style))
                recommendations_text = (
                    "1. <b>Study Gaps First</b>: Revisit standard documentation and tutorials on the conceptual gaps listed above.<br/>"
                    "2. <b>Build Practical Sandbox Projects</b>: Create small-scale scripts or pipelines validating these tools.<br/>"
                    "3. <b>Revise Core Architecture</b>: Review system design trade-offs, space-time complexities, and production deployment flows."
                )
                story.append(Paragraph(recommendations_text, body_style))
                story.append(Spacer(1, 20))

            # Force page break to list Q&As cleanly
            story.append(PageBreak())

            # --- Question by Question Logs ---
            story.append(Paragraph("Detailed Question-by-Question Log", h1_style))
            story.append(Spacer(1, 10))

            for idx, q in enumerate(answered_questions, 1):
                qa_block = []
                qa_block.append(Paragraph(f"<b>Q{idx}. {q.get('question_text')}</b>", h2_style))
                
                meta_info = f"<b>Type:</b> {q.get('question_type')} | <b>Difficulty:</b> {q.get('difficulty')} | <b>Accuracy:</b> {q.get('score_accuracy')}% | <b>Completeness:</b> {q.get('score_completeness')}% | <b>Comm:</b> {q.get('score_communication')}%"
                qa_block.append(Paragraph(meta_info, body_style))
                qa_block.append(Spacer(1, 5))
                
                ans = q.get('answer_text', '[No response submitted]')
                qa_block.append(Paragraph(f"<b>Candidate Answer:</b>", meta_label_style))
                qa_block.append(Paragraph(ans, italic_body))
                qa_block.append(Spacer(1, 5))
                
                qa_block.append(Paragraph(f"<b>AI Coach Feedback:</b>", meta_label_style))
                qa_block.append(Paragraph(q.get('feedback', 'No feedback provided.'), body_style))
                qa_block.append(Spacer(1, 5))
                
                ideal = q.get('ideal_answer')
                if ideal:
                    qa_block.append(Paragraph(f"<b>Ideal Reference Answer Outline:</b>", meta_label_style))
                    qa_block.append(Paragraph(ideal, body_style))
                
                qa_block.append(Spacer(1, 15))
                
                # Keep individual QA block intact together on a page if possible
                story.append(KeepTogether(qa_block))
                story.append(Spacer(1, 10))

            # Build document
            doc.build(story)
            logger.info(f"PDF report successfully compiled at {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error compiling PDF report: {e}", exc_info=True)
            return False
