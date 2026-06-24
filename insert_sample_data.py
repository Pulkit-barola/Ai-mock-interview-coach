import os
import json
import sqlite3
from database.db import DatabaseManager

def seed_database():
    db_path = "interview_platform.db"
    print(f"Seeding database '{db_path}' with sample candidate and interview session data...")
    
    db = DatabaseManager(db_path)
    
    # 1. Create or get candidate
    candidate = db.create_or_get_candidate("Jane Student", "jane.student@university.edu")
    candidate_id = candidate["id"]
    print(f"[OK] Candidate created/retrieved: ID {candidate_id} - {candidate['name']}")

    # 2. Insert Resume Profile
    resume_data = {
        "name": "Jane Student",
        "email": "jane.student@university.edu",
        "summary": "Motivated Computer Science undergraduate seeking entry-level software development roles. Passionate about algorithms, API development, and object-oriented backend programming.",
        "skills": ["Object Oriented Programming", "REST APIs", "Relational Databases", "Data Structures", "Unit Testing"],
        "tools": ["Git", "VS Code", "Docker", "Postman", "GitHub Actions"],
        "programming_languages": ["Python", "SQL", "Java", "C++"],
        "projects": [
            {
                "title": "E-Commerce Backend REST API",
                "description": "Designed and implemented a modular shopping cart API using Python, Flask, and SQLite. Features include user authentication, order processing, and product catalog endpoints. Achieved 90% unit test coverage."
            },
            {
                "title": "Pathfinding Algorithm Visualizer",
                "description": "Built a graphical tool in Python with Pygame to demonstrate search algorithms like Dijkstra's and A* pathfinding. Features adjustable maze layouts and speed parameters."
            }
        ],
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": "State Tech University",
                "year": "2025"
            }
        ],
        "certifications": ["AWS Certified Cloud Practitioner", "Python Institute PCEP"],
        "strengths": ["Strong understanding of OOP concepts", "Good project implementation records", "Clean code habits"],
        "weaknesses": ["Limited industrial cloud deployment experience", "Minimal frontend/UI frameworks skills"]
    }

    missing_skills_data = {
        "Software Engineer": ["System Design", "CI/CD Deployment", "NoSQL Databases"],
        "Python Developer": ["FastAPI/Django", "Asynchronous Python (asyncio)", "Redis Caching"]
    }

    db.save_resume(
        candidate_id=candidate_id,
        file_name="Jane_Student_Resume.pdf",
        extracted_text="Jane Student Resume. State Tech CS. Projects: E-Commerce REST API in Python, Pathfinding visualizer. AWS Certified.",
        parsed_data=resume_data,
        missing_skills_data=missing_skills_data
    )
    print("[OK] Resume details and role alignment gaps cached.")

    # 3. Create Session 1 (Software Engineer - Completed with Medium difficulty progression)
    session_id_1 = db.create_session(candidate_id, "Software Engineer", "Medium")
    
    # QA 1
    qa_id_1 = db.add_question(
        session_id_1,
        question_text="Explain the concept of method resolution order (MRO) in Python multiple inheritance.",
        question_type="Technical",
        difficulty="Medium",
        expected_concepts=["MRO", "C3 Linearization", "super()", "__mro__"],
        ideal_answer="Method Resolution Order (MRO) is the sequence in which Python searches for a method or attribute in a class hierarchy. Python uses the C3 Linearization algorithm. You can check MRO using the ClassName.__mro__ attribute or ClassName.mro(). Using super() ensures children call base classes according to this sequence."
    )
    eval_1 = {
        "score_accuracy": 85.0,
        "score_completeness": 80.0,
        "score_communication": 90.0,
        "score_overall": 85.0,
        "feedback": "Great explanation of multiple inheritance and super(). You correctly identified that Python searches depth-first/left-to-right. You missed mentioning the exact name of the C3 Linearization algorithm, but otherwise, the response was highly technical and structured.",
        "missing_concepts": ["C3 Linearization"]
    }
    db.submit_answer(qa_id_1, "Method resolution order is the way Python resolves which parent class method to call first when a child class inherits from multiple parents. We use super() to navigate MRO safely.", eval_1)
    
    # Since score was 85.0 (>= 75), difficulty goes Medium -> Hard
    db.update_session_difficulty(session_id_1, "Hard")
    
    # QA 2
    qa_id_2 = db.add_question(
        session_id_1,
        question_text="How would you design a rate limiter for an e-commerce API to prevent brute-force login attempts?",
        question_type="Scenario",
        difficulty="Hard",
        expected_concepts=["Token Bucket / Leaky Bucket", "Redis", "IP Whitelisting", "HTTP 429 Too Many Requests"],
        ideal_answer="Use Redis to track request frequencies per IP address or user account. Implement a Token Bucket algorithm. When a user exceeds the threshold, return HTTP 429 (Too Many Requests) headers detailing wait time."
    )
    eval_2 = {
        "score_accuracy": 70.0,
        "score_completeness": 65.0,
        "score_communication": 75.0,
        "score_overall": 70.0,
        "feedback": "You understood the target goal of returning a blocked message, but did not specify standard algorithms like Token Bucket or Leaky Bucket. You suggested storing attempts in a standard database instead of an in-memory cache like Redis, which could lead to DB bottlenecks.",
        "missing_concepts": ["Token Bucket / Leaky Bucket", "Redis cache store"]
    }
    db.submit_answer(qa_id_2, "I would count the number of hits in the SQLite database for that username. If the counter is greater than 10 in a minute, I block them.", eval_2)
    
    # Since score was 70.0 (< 75), difficulty stays Hard (or drops to Medium depending on strictness - here we keep it Hard/Medium)
    db.update_session_difficulty(session_id_1, "Medium")

    # QA 3
    qa_id_3 = db.add_question(
        session_id_1,
        question_text="Tell me about a challenging technical project you built, the architectural choices you made, and what went wrong.",
        question_type="Project",
        difficulty="Medium",
        expected_concepts=["Trade-offs", "Database Selection", "Scaling", "Error handling"],
        ideal_answer="A complete project walkthrough using the STAR method: describe architecture, justify technology (e.g. SQLite vs PostgreSQL), and explain lessons learned from a technical bottleneck."
    )
    eval_3 = {
        "score_accuracy": 90.0,
        "score_completeness": 85.0,
        "score_communication": 90.0,
        "score_overall": 88.3,
        "feedback": "Excellent response using the STAR format. You spoke extensively about your E-Commerce Backend REST API, detailing the decision to use Flask for micro-services and the database constraints you encountered with sqlite lockouts under concurrent test calls.",
        "missing_concepts": []
    }
    db.submit_answer(qa_id_3, "I built an E-Commerce backend API using Flask. I had to choose a database. I chose SQLite for simplicity, but when running concurrent unit tests, it locked up. I solved this by managing session pool lifecycles and learned to appreciate PostgreSQL's concurrency.", eval_3)

    # QA 4
    qa_id_4 = db.add_question(
        session_id_1,
        question_text="Where do you see yourself in five years, and how does this role align with your aspirations?",
        question_type="HR",
        difficulty="Medium",
        expected_concepts=["Mentorship", "Technical Leadership", "Continuous Learning", "Career Path"],
        ideal_answer="Describe alignment with engineering growth. Talk about developing domain expertise, transitioning into a mentoring/leadership role, and contributing to core system architectures."
    )
    eval_4 = {
        "score_accuracy": 95.0,
        "score_completeness": 90.0,
        "score_communication": 95.0,
        "score_overall": 93.3,
        "feedback": "Excellent behavioral answer. You expressed a solid commitment to learning backend architectures, mastering software patterns, and eventually taking on technical leadership and mentorship tasks.",
        "missing_concepts": []
    }
    db.submit_answer(qa_id_4, "In five years, I hope to grow from an associate developer into a senior backend architect, leading core feature integrations, helping design scalable systems, and mentoring junior interns.", eval_4)

    # Calculate overall session score
    db.complete_session(session_id_1, 84.1)
    
    # 4. Create Session 2 (Software Engineer - Completed on another date with higher score)
    session_id_2 = db.create_session(candidate_id, "Software Engineer", "Medium")
    # Add dummy question to database to count as completed session
    qa_id_s2 = db.add_question(
        session_id_2,
        question_text="Explain the time complexity of lookup and insertion operations in a Hash Map.",
        question_type="Technical",
        difficulty="Medium",
        expected_concepts=["O(1) average", "O(N) worst case", "Hash collision", "Chaining / Open addressing"],
        ideal_answer="Lookup and insertion take O(1) time on average. If hash collisions occur frequently, Mappings collapse to linked lists or BSTs, raising lookup complexity to O(N) or O(log N) in the worst case."
    )
    eval_s2 = {
        "score_accuracy": 90.0,
        "score_completeness": 90.0,
        "score_communication": 90.0,
        "score_overall": 90.0,
        "feedback": "Excellent response. You accurately defined O(1) average complexity and detailed how collision resolution like chaining affects worst-case scaling.",
        "missing_concepts": []
    }
    db.submit_answer(qa_id_s2, "Hash maps take O(1) constant time on average for both reading and writing. But in case of multiple hash collisions, they can degrade to O(N) if we resolve collisions using chaining.", eval_s2)
    db.complete_session(session_id_2, 90.0)

    print("[OK] Database seeded successfully with two completed mock sessions.")

if __name__ == "__main__":
    seed_database()
