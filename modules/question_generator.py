import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class QuestionGenerator:
    """Generates personalized, structured interview questions based on resumes, roles, difficulty levels, and history."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("Gemini API Key is not set. QuestionGenerator will fail until API is configured.")

    def generate_question(self, resume_summary, candidate_skills, role, difficulty, history=None, target_type=None):
        """Generates a question using Gemini API tailored to candidate details, role, difficulty, and type."""
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("Gemini API Key is not configured.")
            genai.configure(api_key=self.api_key)

        history_context = ""
        if history:
            history_context = "\n- " + "\n- ".join([f"({h['type']} - {h['difficulty']}): {h['question']}" for h in history])

        # Define question types if target_type is not selected
        q_type_instructions = {
            "Technical": "Ask a core conceptual or coding question related to the job role and their resume skills. Test logic, theory, or engineering patterns.",
            "HR": "Ask a standard HR, behavioral, or cultural fit question (e.g. conflict resolution, career goals, team dynamics).",
            "Scenario": "Present a realistic workplace scenario or design problem (e.g., 'What would you do if a database went down?' or 'How would you design X system?').",
            "Project": "Ask a deep-dive question about a project listed on their resume, or ask them to explain how they would build a specific project related to their skill list."
        }

        selected_type = target_type or "Technical"
        type_instruction = q_type_instructions.get(selected_type, q_type_instructions["Technical"])

        prompt = f"""
        You are a Senior interviewer conducting a professional interview for the role of "{role}".
        Generate a highly targeted interview question.
        
        Candidate Profile:
        - Skills: {', '.join(candidate_skills) if candidate_skills else 'General technical background'}
        - Summary: {resume_summary}
        
        Interview Parameters:
        - Target Role: {role}
        - Target Difficulty: {difficulty}
        - Question Type: {selected_type}
        - Type Instruction: {type_instruction}

        Questions already asked in this session (DO NOT repeat topics or ask similar questions):
        {history_context if history_context else "None yet"}

        Create a single, realistic question tailored to these parameters.
        Adjust the difficulty scale:
        - Easy: Basic conceptual definitions, simple syntax, high-level overview.
        - Medium: Analytical problems, implementation details, comparisons, common system flows.
        - Hard: Deep architectural design, optimization, debugging complex edge cases, behavioral dilemmas with high stakes.

        Provide the output in structured JSON.
        
        Output JSON format strictly conforming to this schema:
        {{
            "question": "The actual question text to ask the candidate.",
            "type": "{selected_type}",
            "difficulty": "{difficulty}",
            "expected_concepts": ["Concept 1", "Concept 2", "Keyword 3"],
            "ideal_response_guideline": "A concise outline of what a strong answer should address, including key points, logic, or design considerations."
        }}

        Return ONLY the valid JSON block. Do not include markdown code block formatting or explanation.
        """

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7  # Higher temperature for variety in questions
                }
            )
            
            question_data = json.loads(response.text.strip())
            logger.info(f"Successfully generated {selected_type} ({difficulty}) question.")
            return question_data
        except Exception as e:
            logger.error(f"Error generating question: {e}", exc_info=True)
            # Safe fallback question structure in case of API issues
            fallback_questions = {
                "Technical": {
                    "question": f"Can you explain the core architecture of a project you built using Python?",
                    "type": "Technical",
                    "difficulty": difficulty,
                    "expected_concepts": ["Python", "Architecture", "Database", "APIs"],
                    "ideal_response_guideline": "A good response covers project goals, key library selections, database integration, and performance bottlenecks encountered."
                },
                "HR": {
                    "question": "Tell me about a time you faced a difficult technical challenge and how you resolved it.",
                    "type": "HR",
                    "difficulty": difficulty,
                    "expected_concepts": ["STAR method", "Problem-solving", "Collaboration", "Learning"],
                    "ideal_response_guideline": "Candidate should detail the Situation, Task, Action they took, and the final positive Result."
                },
                "Scenario": {
                    "question": f"If you were asked to design a scalable pipeline for a {role} project, what components would you choose?",
                    "type": "Scenario",
                    "difficulty": difficulty,
                    "expected_concepts": ["Caching", "Scalability", "Data Ingestion", "Storage"],
                    "ideal_response_guideline": "The answer should cover raw ingestion, processing, database writing, and scaling triggers under load."
                },
                "Project": {
                    "question": "Choose a main project from your resume and explain your architectural design decisions.",
                    "type": "Project",
                    "difficulty": difficulty,
                    "expected_concepts": ["Frameworks", "Databases", "APIs", "Trade-offs"],
                    "ideal_response_guideline": "The candidate should clearly justify why they chose certain technologies over alternatives and identify key project constraints."
                }
            }
            return fallback_questions.get(selected_type, fallback_questions["Technical"])
