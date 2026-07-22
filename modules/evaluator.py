import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


class AnswerEvaluator:
    """Evaluates interview answers using Gemini."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        genai.configure(api_key=self.api_key)

    def evaluate_answer(
        self,
        question,
        answer,
        expected_concepts,
        ideal_guideline,
    ):

        concepts_str = (
            ", ".join(expected_concepts)
            if expected_concepts
            else "General logic"
        )

        prompt = f"""
You are an expert technical interviewer evaluating a candidate's answer for a mock interview question.

Please perform a thorough and objective evaluation of the candidate's answer based on the question, the expected core concepts, and the ideal answer guideline.

### Evaluation Criteria:
1. **Technical Accuracy (0-100)**: How technically accurate, correct, and sound is the candidate's answer? Award higher scores for precise explanations and correct definitions.
2. **Completeness (0-100)**: Did the candidate hit the expected core concepts and cover all parts of the question? Deduct score for missing keywords or concepts.
3. **Communication Clarity (0-100)**: How clear, professional, well-structured, and easy to understand is their answer?
4. **Overall Score (0-100)**: The overall score representing their performance. Calculate this as the weighted average of Technical Accuracy (45%), Completeness (40%), and Communication (15%).

### Input Data:
- **Question**: {question}
- **Expected Core Concepts**: {concepts_str}
- **Ideal Answer Guideline**: {ideal_guideline}
- **Candidate Answer**: {answer if answer.strip() else "No answer provided"}

### Output Format:
You MUST respond with ONLY a valid JSON object matching the schema below. Do not add any markdown, comments, or extra text.

JSON Schema:
{{
    "score_accuracy": 80,
    "score_completeness": 80,
    "score_communication": 80,
    "score_overall": 80,
    "feedback": "detailed feedback paragraph explaining strengths, weaknesses, and clear actionable recommendations for improvement",
    "missing_concepts": ["concept1","concept2"],
    "ideal_answer": "a complete, polished, and detailed model answer that would score 100%"
}}
"""

        try:

            model = genai.GenerativeModel("gemini-2.5-flash")

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json",
                },
            )

            response_text = ""

            if hasattr(response, "text") and response.text:
                response_text = response.text.strip()

            print("\n========== GEMINI RAW RESPONSE ==========")
            print(response_text)
            print("=========================================\n")

            if not response_text:
                raise Exception("Gemini returned an empty response.")

            if response_text.startswith("```json"):
                response_text = (
                    response_text.replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

            elif response_text.startswith("```"):
                response_text = (
                    response_text.replace("```", "")
                    .strip()
                )

            evaluation = json.loads(response_text)

            required = [
                "score_accuracy",
                "score_completeness",
                "score_communication",
                "score_overall",
                "feedback",
                "missing_concepts",
                "ideal_answer",
            ]

            for key in required:
                if key not in evaluation:
                    raise Exception(f"Missing key: {key}")

            return evaluation

        except json.JSONDecodeError as e:

            print("\nJSON Decode Error")
            print(response_text)

            raise Exception(
                f"Gemini returned invalid JSON.\n\n{response_text}"
            )

        except Exception as e:

            logger.exception(e)

            raise