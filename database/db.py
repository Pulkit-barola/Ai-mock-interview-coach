import os
import sqlite3
import json
import logging
from datetime import datetime

# Setup simple logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database transactions and schema initialisation for the AI Mock Interview system."""

    def __init__(self, db_path="interview_platform.db"):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        """Returns a connection to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Returns rows as dictionary-like objects
        return conn

    def _initialize_db(self):
        """Creates the database schema if it doesn't already exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys = ON;")

                # Table: Candidates
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS candidates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # Table: Resumes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS resumes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        candidate_id INTEGER NOT NULL,
                        file_name TEXT NOT NULL,
                        extracted_text TEXT NOT NULL,
                        summary TEXT,
                        skills TEXT,              -- JSON string
                        tools TEXT,               -- JSON string
                        programming_languages TEXT, -- JSON string
                        education TEXT,           -- JSON string
                        projects TEXT,            -- JSON string
                        certifications TEXT,      -- JSON string
                        strengths TEXT,           -- JSON string
                        weaknesses TEXT,          -- JSON string
                        missing_skills TEXT,      -- JSON string mapping role -> list
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
                    );
                """)

                # Table: Sessions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        candidate_id INTEGER NOT NULL,
                        role TEXT NOT NULL,
                        initial_difficulty TEXT NOT NULL,
                        current_difficulty TEXT NOT NULL,
                        status TEXT DEFAULT 'active', -- 'active' or 'completed'
                        overall_score REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
                    );
                """)

                # Table: Interview Q&A
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interview_qa (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL,
                        question_text TEXT NOT NULL,
                        question_type TEXT NOT NULL, -- 'Technical', 'HR', 'Scenario', 'Project'
                        difficulty TEXT NOT NULL,    -- 'Easy', 'Medium', 'Hard'
                        expected_concepts TEXT,       -- JSON string list
                        answer_text TEXT,
                        score_accuracy REAL DEFAULT 0.0,
                        score_completeness REAL DEFAULT 0.0,
                        score_communication REAL DEFAULT 0.0,
                        score_overall REAL DEFAULT 0.0,
                        feedback TEXT,
                        missing_concepts TEXT,        -- JSON string list
                        ideal_answer TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    );
                """)

                conn.commit()
                logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise e

    # --- Candidate CRUD operations ---

    def create_or_get_candidate(self, name, email):
        """Creates a candidate or retrieves existing candidate based on email."""
        query_get = "SELECT id, name, email FROM candidates WHERE email = ?;"
        query_insert = "INSERT INTO candidates (name, email) VALUES (?, ?);"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query_get, (email.lower().strip(),))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                
                # Create new
                cursor.execute(query_insert, (name.strip(), email.lower().strip()))
                conn.commit()
                candidate_id = cursor.lastrowid
                return {"id": candidate_id, "name": name, "email": email}
        except Exception as e:
            logger.error(f"Error saving/fetching candidate {email}: {e}")
            raise e

    def get_candidate(self, candidate_id):
        """Retrieves a candidate profile by id."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM candidates WHERE id = ?;", (candidate_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error fetching candidate {candidate_id}: {e}")
            return None

    # --- Resume Operations ---

    def save_resume(self, candidate_id, file_name, extracted_text, parsed_data, missing_skills_data=None):
        """Saves parsed resume details associated with a candidate."""
        query_insert = """
            INSERT INTO resumes (
                candidate_id, file_name, extracted_text, summary, skills, tools, 
                programming_languages, education, projects, certifications, strengths, weaknesses, missing_skills
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete any existing resume for the candidate first to keep it clean (one resume per candidate)
                cursor.execute("DELETE FROM resumes WHERE candidate_id = ?;", (candidate_id,))
                
                skills_json = json.dumps(parsed_data.get("skills", []))
                tools_json = json.dumps(parsed_data.get("tools", []))
                languages_json = json.dumps(parsed_data.get("programming_languages", []))
                education_json = json.dumps(parsed_data.get("education", []))
                projects_json = json.dumps(parsed_data.get("projects", []))
                certs_json = json.dumps(parsed_data.get("certifications", []))
                strengths_json = json.dumps(parsed_data.get("strengths", []))
                weaknesses_json = json.dumps(parsed_data.get("weaknesses", []))
                missing_json = json.dumps(missing_skills_data if missing_skills_data else {})

                cursor.execute(query_insert, (
                    candidate_id,
                    file_name,
                    extracted_text,
                    parsed_data.get("summary", ""),
                    skills_json,
                    tools_json,
                    languages_json,
                    education_json,
                    projects_json,
                    certs_json,
                    strengths_json,
                    weaknesses_json,
                    missing_json
                ))
                conn.commit()
                logger.info(f"Resume saved for candidate {candidate_id}")
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error saving resume for candidate {candidate_id}: {e}")
            raise e

    def get_resume(self, candidate_id):
        """Retrieves parsed resume profile for a candidate."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM resumes WHERE candidate_id = ? ORDER BY id DESC LIMIT 1;", (candidate_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                res = dict(row)
                # Parse JSON fields back to objects
                res["skills"] = json.loads(res["skills"]) if res["skills"] else []
                res["tools"] = json.loads(res["tools"]) if res["tools"] else []
                res["programming_languages"] = json.loads(res["programming_languages"]) if res["programming_languages"] else []
                res["education"] = json.loads(res["education"]) if res["education"] else []
                res["projects"] = json.loads(res["projects"]) if res["projects"] else []
                res["certifications"] = json.loads(res["certifications"]) if res["certifications"] else []
                res["strengths"] = json.loads(res["strengths"]) if res["strengths"] else []
                res["weaknesses"] = json.loads(res["weaknesses"]) if res["weaknesses"] else []
                res["missing_skills"] = json.loads(res["missing_skills"]) if res["missing_skills"] else {}
                return res
        except Exception as e:
            logger.error(f"Error loading resume for candidate {candidate_id}: {e}")
            return None

    def update_resume_missing_skills(self, candidate_id, missing_skills_data):
        """Updates missing skills cache for specific job roles."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Load current resume missing_skills
                cursor.execute("SELECT id, missing_skills FROM resumes WHERE candidate_id = ? ORDER BY id DESC LIMIT 1;", (candidate_id,))
                row = cursor.fetchone()
                if row:
                    curr_data = json.loads(row["missing_skills"]) if row["missing_skills"] else {}
                    curr_data.update(missing_skills_data)
                    cursor.execute(
                        "UPDATE resumes SET missing_skills = ? WHERE id = ?;",
                        (json.dumps(curr_data), row["id"])
                    )
                    conn.commit()
                    logger.info(f"Updated missing skills for candidate {candidate_id}")
        except Exception as e:
            logger.error(f"Error updating missing skills for candidate {candidate_id}: {e}")

    # --- Interview Session Operations ---

    def create_session(self, candidate_id, role, initial_difficulty):
        """Creates a new interview session."""
        query = """
            INSERT INTO sessions (candidate_id, role, initial_difficulty, current_difficulty) 
            VALUES (?, ?, ?, ?);
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (candidate_id, role, initial_difficulty, initial_difficulty))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise e

    def get_session(self, session_id):
        """Gets a session metadata by id."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sessions WHERE id = ?;", (session_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None

    def update_session_difficulty(self, session_id, new_difficulty):
        """Updates current difficulty level of an active session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET current_difficulty = ? WHERE id = ?;",
                    (new_difficulty, session_id)
                )
                conn.commit()
                logger.info(f"Updated difficulty to {new_difficulty} for session {session_id}")
        except Exception as e:
            logger.error(f"Error updating difficulty: {e}")

    def complete_session(self, session_id, overall_score):
        """Marks session as completed and sets the aggregated overall score."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE sessions SET status = 'completed', overall_score = ? WHERE id = ?;",
                    (overall_score, session_id)
                )
                conn.commit()
                logger.info(f"Completed session {session_id} with score {overall_score}")
        except Exception as e:
            logger.error(f"Error completing session {session_id}: {e}")

    # --- Interview Q&A Operations ---

    def add_question(self, session_id, question_text, question_type, difficulty, expected_concepts, ideal_answer):
        """Adds a newly generated question to the session (prior to candidate answering)."""
        query = """
            INSERT INTO interview_qa (session_id, question_text, question_type, difficulty, expected_concepts, ideal_answer)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                concepts_json = json.dumps(expected_concepts if expected_concepts else [])
                cursor.execute(query, (
                    session_id,
                    question_text,
                    question_type,
                    difficulty,
                    concepts_json,
                    ideal_answer
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding question: {e}")
            raise e

    def submit_answer(self, qa_id, answer_text, evaluation_result):
        """Saves candidate answer, score ratings, and evaluation feedback."""
        query = """
            UPDATE interview_qa 
            SET answer_text = ?,
                score_accuracy = ?,
                score_completeness = ?,
                score_communication = ?,
                score_overall = ?,
                feedback = ?,
                missing_concepts = ?,
                ideal_answer = COALESCE(ideal_answer, ?)
            WHERE id = ?;
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                missing_json = json.dumps(evaluation_result.get("missing_concepts", []))
                cursor.execute(query, (
                    answer_text.strip(),
                    evaluation_result.get("score_accuracy", 0.0),
                    evaluation_result.get("score_completeness", 0.0),
                    evaluation_result.get("score_communication", 0.0),
                    evaluation_result.get("score_overall", 0.0),
                    evaluation_result.get("feedback", ""),
                    missing_json,
                    evaluation_result.get("ideal_answer", ""),
                    qa_id
                ))
                conn.commit()
                logger.info(f"Answer submitted for QA ID {qa_id}")
        except Exception as e:
            logger.error(f"Error submitting answer for QA {qa_id}: {e}")
            raise e

    def get_session_qa(self, session_id):
        """Retrieves list of Q&As associated with an interview session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM interview_qa WHERE session_id = ? ORDER BY id ASC;",
                    (session_id,)
                )
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    r = dict(row)
                    r["expected_concepts"] = json.loads(r["expected_concepts"]) if r["expected_concepts"] else []
                    r["missing_concepts"] = json.loads(r["missing_concepts"]) if r["missing_concepts"] else []
                    result.append(r)
                return result
        except Exception as e:
            logger.error(f"Error getting QA for session {session_id}: {e}")
            return []

    # --- Analytics & Reporting Queries ---

    def get_candidate_sessions(self, candidate_id):
        """Returns all completed and active sessions for a candidate."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM sessions WHERE candidate_id = ? ORDER BY created_at DESC;",
                    (candidate_id,)
                )
                return [dict(r) for r in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching candidate sessions: {e}")
            return []

    def get_session_performance_summary(self, session_id):
        """Aggregates metrics for a given session."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        COUNT(id) as total_questions,
                        AVG(score_accuracy) as avg_accuracy,
                        AVG(score_completeness) as avg_completeness,
                        AVG(score_communication) as avg_communication,
                        AVG(score_overall) as avg_overall
                    FROM interview_qa 
                    WHERE session_id = ? AND answer_text IS NOT NULL;
                """, (session_id,))
                row = cursor.fetchone()
                return dict(row) if row and row["total_questions"] > 0 else None
        except Exception as e:
            logger.error(f"Error fetching performance summary: {e}")
            return None
