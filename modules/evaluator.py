import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class AnswerEvaluator:
    """Evaluates candidate answers against expectations using Gemini API, scoring multiple performance dimensions."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("Gemini API Key is not set. AnswerEvaluator will fail until API is configured.")

    def evaluate_answer(self, question, answer, expected_concepts, ideal_guideline):
        """Evaluates the candidate's answer and returns scores, feedback, missing concepts, and ideal response."""
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("Gemini API Key is not configured.")
            genai.configure(api_key=self.api_key)

        concepts_str = ", ".join(expected_concepts) if expected_concepts else "General logic"

        prompt = f"""
        You are an expert technical interviewer and communication coach. Evaluate the candidate's answer for the following question.

        Question:
        "{question}"

        Expected Core Concepts/Keywords:
        [{concepts_str}]

        Ideal Answer Guidelines:
        "{ideal_guideline}"

        Candidate's Answer:
        ---
        "{answer if answer.strip() else '[No answer provided]'}"
        ---

        Please rate the response out of 100 on these three metrics:
        1. Technical Accuracy: Is the answer factually correct and free of errors? (Score 0-100)
        2. Completeness: Did the candidate cover all parts of the question and include key expected concepts? (Score 0-100)
        3. Communication: Is the answer structured, clear, and professional? (Score 0-100)

        Also calculate an Overall Score (typically the average of the three, but adjusted if they gave a brilliant or completely missing answer).
        
        Provide constructive, specific feedback detailing:
        - What they did well.
        - What they missed or got wrong.
        - Which of the expected concepts they failed to cover (put these in the "missing_concepts" array).
        - A fully articulated, polished "ideal_answer" that shows how a senior candidate would answer this question.

        Output JSON format strictly conforming to this schema:
        {{
            "score_accuracy": 85,
            "score_completeness": 70,
            "score_communication": 90,
            "score_overall": 81.6,
            "feedback": "Your detailed feedback paragraph here...",
            "missing_concepts": ["Concept Name 1", "Concept Name 2"],
            "ideal_answer": "A perfect, complete response to the interview question."
        }}

        Return ONLY the valid JSON block. Do not include markdown code block formatting or explanation.
        """

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )
            
            evaluation = json.loads(response.text.strip())
            logger.info("Successfully evaluated candidate answer.")
            return evaluation
        except Exception as e:
            logger.error(f"Error evaluating candidate answer: {e}", exc_info=True)
            # Safe fallback response in case of API failure
            return {
                "score_accuracy": 50.0,
                "score_completeness": 50.0,
                "score_communication": 50.0,
                "score_overall": 50.0,
                "feedback": "There was an error processing your answer evaluation via the API. Please review the ideal answer below for comparison.",
                "missing_concepts": expected_concepts if expected_concepts else [],
                "ideal_answer": f"Please consult resources regarding: {concepts_str}. Guideline: {ideal_guideline}"
            }
