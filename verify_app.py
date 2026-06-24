import os
import sys

def verify_all():
    print("=== AI Mock Interview Platform Validation Script ===")
    
    # 1. Check directories
    dirs = ["database", "modules", "utils", "pages"]
    for d in dirs:
        if os.path.exists(d):
            print(f"[OK] Directory '{d}' exists.")
        else:
            print(f"[FAIL] Directory '{d}' is missing.")
            
    # 2. Add current path to PYTHONPATH
    sys.path.append(os.getcwd())
    
    # 3. Test Database Imports & Initialisation
    try:
        from database.db import DatabaseManager
        db = DatabaseManager("test_temp.db")
        print("[OK] DatabaseManager imported and initialized successfully.")
        
        # Verify schema table existence
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"    Available Tables: {', '.join(tables)}")
        
        expected_tables = ["candidates", "resumes", "sessions", "interview_qa"]
        all_ok = True
        for t in expected_tables:
            if t in tables:
                print(f"    - Table '{t}': [OK] Found")
            else:
                print(f"    - Table '{t}': [FAIL] Missing")
                all_ok = False
        
        conn.close()
        # Clean up references to unlock file on Windows
        conn = None
        db = None
        import gc
        gc.collect()
        
        if os.path.exists("test_temp.db"):
            os.remove("test_temp.db")
            
    except Exception as e:
        print(f"[FAIL] Database verification failed: {e}")
        
    # 4. Test Modules Imports
    modules_to_test = [
        ("modules.resume_parser", "ResumeParser"),
        ("modules.question_generator", "QuestionGenerator"),
        ("modules.evaluator", "AnswerEvaluator"),
        ("modules.voice_interview", "VoiceInterviewManager"),
        ("modules.report_generator", "ReportGenerator"),
        ("modules.analytics", "InterviewAnalytics"),
        ("utils.helpers", "init_session_state")
    ]
    
    for mod_name, class_name in modules_to_test:
        try:
            mod = __import__(mod_name, fromlist=[class_name])
            cls = getattr(mod, class_name)
            print(f"[OK] Module '{mod_name}' - Class/Func '{class_name}' imported successfully.")
        except ImportError as ie:
            print(f"[FAIL] Module '{mod_name}' failed to import: {ie}")
        except AttributeError as ae:
            print(f"[FAIL] Module '{mod_name}' does not contain '{class_name}': {ae}")
            
    print("====================================================")

if __name__ == "__main__":
    verify_all()
