import os
import json
import logging
from pypdf import PdfReader
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ResumeParser:
    """Extracts text from PDF resumes and processes them using Google Gemini API to structure data and match roles."""

    def __init__(self, api_key=None):
        # Configure Gemini API
        from utils.helpers import get_gemini_api_key
        self.api_key = api_key or get_gemini_api_key()
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("Gemini API Key is not set. ResumeParser will fail until API is configured.")

    def extract_text_from_pdf(self, pdf_file):
        """Extracts text from an uploaded PDF file or filepath."""
        try:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            
            if not text.strip():
                raise ValueError("Could not extract any readable text from the PDF. The file might be scanned or empty.")
            
            logger.info("Successfully extracted text from PDF resume.")
            return text
        except Exception as e:
            logger.error(f"Error reading PDF file: {e}", exc_info=True)
            raise e

    def parse_resume_text(self, resume_text):
        """Uses Gemini API to structure raw resume text into JSON format."""
        if not self.api_key:
            # Check env again in case it was set dynamically
            from utils.helpers import get_gemini_api_key
            self.api_key = get_gemini_api_key()
            if not self.api_key:
                raise ValueError("Gemini API Key is not configured.")
            genai.configure(api_key=self.api_key)

        prompt = f"""
        You are a professional recruiting assistant. Analyze the following candidate resume text and extract the key information in structured JSON.
        Make sure to identify and separate technical skills, tools, and programming languages.
        Also extract education, projects, certifications, and give a concise resume summary.
        Provide initial generic strengths and weaknesses based on their profile.

        Resume Text:
        ---
        {resume_text}
        ---

        Output JSON format strictly conforming to this schema:
        {{
            "name": "Candidate's full name",
            "email": "Candidate's email",
            "summary": "A professional summary of the candidate (2-3 sentences)",
            "skills": ["List of core technical concepts/skills (e.g. Machine Learning, OOP, Agile)"],
            "tools": ["List of specific tools/software (e.g. Git, Docker, Kubernetes, Jira)"],
            "programming_languages": ["List of programming languages (e.g. Python, SQL, C++, Java)"],
            "projects": [
                {{
                    "title": "Project Title",
                    "description": "Short project summary"
                }}
            ],
            "education": [
                {{
                    "degree": "Degree / Field of study",
                    "institution": "University / College Name",
                    "year": "Graduation year or 'Present'"
                }}
            ],
            "certifications": ["List of certifications"],
            "strengths": ["List of overall candidate strengths"],
            "weaknesses": ["List of overall areas of improvement/weaknesses"]
        }}

        Return ONLY the valid JSON block. Do not include markdown code block formatting or explanation.
        """

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )
            
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()
                
            parsed_data = json.loads(response_text, strict=False)
            logger.info("Successfully parsed resume text via Gemini API.")
            return parsed_data
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON response from Gemini: {je}. Raw response was: {response.text}")
            raise ValueError("Failed to parse Gemini response as JSON.")
        except Exception as e:
            logger.error(f"Error parsing resume: {e}", exc_info=True)
            raise e

    def analyze_role_alignment(self, resume_data, role, custom_requirements=None):
        """Analyzes how well the candidate's parsed resume fits the selected job role."""
        if not self.api_key:
            from utils.helpers import get_gemini_api_key
            self.api_key = get_gemini_api_key()
            if not self.api_key:
                raise ValueError("Gemini API Key is not configured.")
            genai.configure(api_key=self.api_key)

        # Standard requirements for typical roles to inject context
        role_benchmarks = {
            "Data Analyst": "SQL, Excel, PowerBI/Tableau, Python (Pandas/NumPy), Data Visualisation, Statistics, Basic Dashboarding",
            "Data Scientist": "Python, SQL, Machine Learning, Statistics, Pandas/NumPy, Scikit-Learn, Jupyter, Model Evaluation",
            "Python Developer": "Python, Django/Flask/FastAPI, OOP, Git, REST APIs, Databases (SQL/NoSQL), Unit Testing, Web Scraping",
            "AI/ML Engineer": "Python, PyTorch/TensorFlow, Machine Learning, Deep Learning, NLP, Computer Vision, Model Deployment, Git",
            "Software Engineer": "Data Structures & Algorithms, OOP, System Design, Git, Database Management, Python/Java/C++, Testing/Debugging"
        }

        role_desc = custom_requirements if role == "Custom Role" else role_benchmarks.get(role, "General Software/Data Engineering skills")
        
        # Safely convert list elements to prevent TypeError: can only join an iterable
        def safe_join(field_name):
            val = resume_data.get(field_name)
            if not val:
                return "None listed"
            if isinstance(val, list):
                return ', '.join([str(item) for item in val if item])
            return str(val)

        skills_str = safe_join("skills")
        tools_str = safe_join("tools")
        langs_str = safe_join("programming_languages")

        prompt = f"""
        You are an AI Interview Coach. Compare the candidate's parsed resume details with the standard requirements for a "{role}" role.
        
        Job Role Requirements Overview:
        {role_desc}

        Candidate Resume Summary:
        {resume_data.get("summary", "")}

        Candidate Skills: {skills_str}
        Candidate Tools: {tools_str}
        Candidate Languages: {langs_str}

        Analyze the fit and identify:
        1. Missing skills/technologies that are usually expected for this role.
        2. Candidate strengths specifically in the context of this job role.
        3. Candidate weaknesses or areas to improve specifically for this job role.
        4. A suitability score (0-100) based on their background vs role requirements.
        5. A short explanation of the fit alignment.

        Output JSON format strictly conforming to this schema:
        {{
            "missing_skills": ["Skill A", "Skill B"],
            "role_strengths": ["Strength A tailored to role", "Strength B tailored to role"],
            "role_weaknesses": ["Weakness A tailored to role", "Weakness B tailored to role"],
            "suitability_score": 75,
            "fit_explanation": "A concise paragraph (3-4 sentences) outlining how well the candidate matches the requirements."
        }}

        Return ONLY the valid JSON block. Do not include markdown code block formatting or explanation.
        """

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )
            
            response_text = response.text.strip()
            # Clean up markdown code blocks if Gemini returned them
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            alignment_data = json.loads(response_text, strict=False)
            logger.info(f"Successfully analyzed role alignment for {role}.")
            return alignment_data
        except Exception as e:
            logger.error(f"Error performing role alignment: {e}", exc_info=True)
            # Return safe default structure on error with error message in fit_explanation
            return {
                "missing_skills": ["Unable to determine missing skills due to API issue"],
                "role_strengths": ["Skills extracted from resume"],
                "role_weaknesses": ["Improvement areas to be verified during interview"],
                "suitability_score": 50,
                "fit_explanation": f"Could not calculate fit analysis: {str(e)}. Proceeding with interview session."
            }
