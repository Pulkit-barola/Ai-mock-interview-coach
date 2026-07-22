import os
import streamlit as st
from database.db import DatabaseManager

def init_session_state():
    """Initializes standard state variables in Streamlit session_state."""
    # Database
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager()

    # Candidate Profile
    if "candidate" not in st.session_state:
        st.session_state.candidate = None # Holds dict with: id, name, email
    if "resume_parsed" not in st.session_state:
        st.session_state.resume_parsed = False
    if "resume_data" not in st.session_state:
        st.session_state.resume_data = None # Parsed resume JSON
    if "resume_db_id" not in st.session_state:
        st.session_state.resume_db_id = None

    # Job Fit Details
    if "selected_role" not in st.session_state:
        st.session_state.selected_role = "Software Engineer"
    if "custom_role_desc" not in st.session_state:
        st.session_state.custom_role_desc = ""
    if "role_alignment" not in st.session_state:
        st.session_state.role_alignment = None

    # Interview Session
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "interview_active" not in st.session_state:
        st.session_state.interview_active = False
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "current_difficulty" not in st.session_state:
        st.session_state.current_difficulty = "Medium"
    if "current_question" not in st.session_state:
        st.session_state.current_question = None # Dict with: id, text, expected, type
    if "session_history" not in st.session_state:
        st.session_state.session_history = [] # List of past question-answer evaluations
    if "tts_audio_cache" not in st.session_state:
        st.session_state.tts_audio_cache = None

    # OTP Verification State
    if "otp_sent" not in st.session_state:
        st.session_state.otp_sent = False
    if "otp_code" not in st.session_state:
        st.session_state.otp_code = None
    if "temp_name" not in st.session_state:
        st.session_state.temp_name = None
    if "temp_email" not in st.session_state:
        st.session_state.temp_email = None

def validate_email_deliverability(email):
    """Checks if the email domain has valid, non-null MX records.
    
    Returns True if valid or if domain has MX records.
    Returns False otherwise.
    """
    import urllib.request
    import json
    import ssl
    try:
        domain = email.split('@')[-1].strip()
        url = f"https://cloudflare-dns.com/dns-query?name={domain}&type=MX"
        req = urllib.request.Request(
            url, 
            headers={"Accept": "application/dns-json"}
        )
        context = ssl._create_unverified_context()
        with urllib.request.urlopen(req, context=context, timeout=5) as response:
            data = json.loads(response.read().decode())
            if "Answer" in data and len(data["Answer"]) > 0:
                for record in data["Answer"]:
                    mx_target = record.get("data", "").strip()
                    # "0 ." represents Null MX record (RFC 7505) indicating domain rejects mail
                    if mx_target == "0 ." or mx_target == ".":
                        return False
                return True
    except Exception as e:
        # Fallback to direct resolution check on network failure or context errors
        try:
            import socket
            socket.gethostbyname(domain)
            return True
        except Exception:
            return False
    return False

def generate_otp():
    """Generates a random 6-digit OTP."""
    import random
    return f"{random.randint(100000, 999999)}"


def send_otp_email(email_to, otp):
    """Sends OTP to the target email.
    
    If SMTP credentials are set in .env:
      - Sends a real email.
      - Returns True if successful, or raises/logs error and returns ("error", details).
    If credentials are NOT set:
      - Simulates email sending by printing the OTP to the console.
      - Returns False to indicate simulation/mock.
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    # Check if credentials exist
    if all([smtp_server, smtp_port, smtp_email, smtp_password]):
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            port = int(smtp_port)
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = email_to
            msg['Subject'] = "Your AI Mock Interview OTP Verification Code"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px; color: #1f2937;">
                <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 30px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <h2 style="color: #4f46e5; margin-bottom: 20px;">AI Mock Interview Verification</h2>
                    <p style="font-size: 16px; line-height: 1.5;">Hello,</p>
                    <p style="font-size: 16px; line-height: 1.5;">You requested a verification code to access the AI Mock Interview Coach. Please use the following One-Time Password (OTP) to complete your log in:</p>
                    <div style="background-color: #f3f4f6; border-radius: 8px; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #1e1b4b; margin: 25px 0;">
                        {otp}
                    </div>
                    <p style="font-size: 14px; color: #6b7280; line-height: 1.5; margin-top: 30px; border-top: 1px solid #f3f4f6; padding-top: 20px;">
                        This code is valid for 10 minutes. If you did not request this verification, please ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(smtp_server, port)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, email_to, msg.as_string())
            server.quit()
            
            print(f"[OTP SUCCESS] Real email sent to {email_to} with OTP {otp}")
            return True
        except Exception as e:
            print(f"[OTP ERROR] Failed to send email to {email_to}: {e}")
            return "error", str(e)
    else:
        # SMTP not configured - simulate
        print(f"\n==================================================", flush=True)
        print(f"[OTP SIMULATION] OTP for {email_to}: {otp}", flush=True)
        print(f"==================================================\n", flush=True)
        
        # Also write to local text files for easy programmatic/manual retrieval
        try:
            with open(r"C:\Users\DS4U\.gemini\antigravity-ide\brain\3a285dd4-da30-492b-a6c3-42d86cff0a89\simulated_otp.txt", "w") as f:
                f.write(otp)
        except Exception:
            pass
        try:
            with open("simulated_otp.txt", "w") as f:
                f.write(otp)
        except Exception:
            pass
            
        return False


def check_env_api_key():
    """Checks if GEMINI_API_KEY is configured in the environment."""
    from dotenv import load_dotenv
    load_dotenv(override=True) # Load from .env if present

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return False
    return True

def apply_custom_css():
    """Injects custom Google Fonts and premium CSS styling into Streamlit."""
    css = """
    <style>
        /* Import Outfit or Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"]  {
            font-family: 'Outfit', sans-serif;
        }

        /* Glassmorphic cards */
        .premium-card {
            background: rgba(255, 255, 255, 0.75);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(229, 231, 235, 0.5);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            margin-bottom: 20px;
        }
        
        .dark-premium-card {
            background: rgba(30, 41, 59, 0.85);
            color: #f8fafc;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(71, 85, 105, 0.3);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        /* Accent text and headings */
        .gradient-text {
            background: linear-gradient(135deg, #4f46e5 0%, #0d9488 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }
        
        /* Metric badges */
        .metric-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.875rem;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        
        .badge-success { background-color: #D1FAE5; color: #065F46; }
        .badge-warning { background-color: #FEF3C7; color: #92400E; }
        .badge-danger { background-color: #FEE2E2; color: #991B1B; }
        .badge-info { background-color: #E0F2FE; color: #075985; }

        /* Custom buttons styling */
        .stButton>button {
            border-radius: 8px;
            background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
            color: white;
            border: none;
            font-weight: 500;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
            transform: translateY(-1px);
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def render_sidebar_status():
    """Renders candidate status and environment configurations in the sidebar."""
    st.sidebar.image("https://img.icons8.com/clouds/100/gender-neutral-user.png", width=70)
    
    # Check Gemini API status
    if check_env_api_key():
        st.sidebar.success("Gemini API Key: Configured")
    else:
        st.sidebar.error("Gemini API Key: Missing")
        st.sidebar.info("Set GEMINI_API_KEY in a .env file or environment variables to enable all AI capabilities.")

    # Candidate Status
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Profile Status")
    if st.session_state.candidate:
        st.sidebar.write(f"**Candidate:** {st.session_state.candidate['name']}")
        st.sidebar.write(f"**Email:** {st.session_state.candidate['email']}")
        if st.session_state.resume_parsed:
            st.sidebar.success("Resume Loaded")
            st.sidebar.write(f"**Role:** {st.session_state.selected_role}")
        else:
            st.sidebar.warning("No Resume Uploaded")
    else:
        st.sidebar.warning("No active profile. Configure on Home page.")
