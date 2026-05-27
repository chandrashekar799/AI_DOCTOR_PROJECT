import streamlit as st
from supabase import create_client
import os
import base64
import bcrypt
import random
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ================= BACKGROUND =================

def set_heartbeat_bg(image_file):
    try:
        with open(image_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        particles_html = ""
        for _ in range(30):
            size = random.choice([3, 5, 7, 9])
            left = random.randint(0, 100)
            delay = random.uniform(0, 8)
            duration = random.uniform(10, 20)
            opacity = random.uniform(0.3, 0.8)

            particles_html += f"""
            <div class="particle"
                 style="
                    left:{left}%;
                    width:{size}px;
                    height:{size}px;
                    animation-delay:{delay}s;
                    animation-duration:{duration}s;
                    opacity:{opacity};
                 ">
            </div>
            """

        st.markdown(
            f"""
            <style>

            html, body {{
                height: 100%;
                margin: 0;
                color: white !important;
            }}

            .stApp {{
                background:
                    linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)),
                    url("data:image/png;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                overflow: hidden;
            }}

            .main > div {{
                padding-top: 0rem !important;
            }}

            .block-container {{
                padding-top: 0.5rem !important;
                background: rgba(0, 15, 35, 0.5)!important;
                backdrop-filter: blur(15px);
                border-radius: 20px;
                padding: 1rem 1rem;
                box-shadow: 0 0 35px rgba(0,255,255,0.5);
                max-width: 650px;
                margin: 0 auto;
                position: relative;
                z-index: 5;
            }}

            .stTextInput label {{
                color: #00ffff !important;
                font-weight: 600;
            }}

            .stTextInput input {{
                background-color: rgba(0, 25, 50, 0.9) !important;
                color: white !important;
                border-radius: 8px;
                border: 1px solid #00ffff !important;
            }}

            .stTextInput input::placeholder {{
                color: rgba(255,255,255,0.6) !important;
                opacity: 1 !important;
            }}

            .stButton button {{
                background: linear-gradient(90deg, #00ffff, #0088ff);
                color: black;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                padding: 0.6rem 1.2rem;
                width: 100%;
            }}

            .stButton button:hover {{
                transform: scale(1.05);
                transition: 0.2s;
            }}

            /* Particles */
            .particles {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: -1;
            }}

            .particle {{
                position: absolute;
                top: 100%;
                background: #00ffff;
                border-radius: 50%;
                box-shadow: 0 0 10px #00ffff;
                animation: floatUp linear infinite;
            }}

            @keyframes floatUp {{
                from {{ top: 100%; }}
                to {{ top: -10%; }}
            }}

            /* ECG inside box */
            .ecg {{
                width: 100%;
                height: 120px;
                margin: 10px 0 20px 0;
                opacity: 0.9;
            }}

            .ecg svg {{
                width: 100%;
                height: 100%;
            }}

            .ecg path {{
                stroke: #00ffff;
                stroke-width: 3;
                fill: none;
                stroke-dasharray: 2000;
                stroke-dashoffset: 2000;
                animation: ecgMove 4s linear infinite;
                filter: drop-shadow(0 0 8px #00ffff)
                        drop-shadow(0 0 18px #00ffff);
            }}

            @keyframes ecgMove {{
                from {{ stroke-dashoffset: 2000; }}
                to {{ stroke-dashoffset: 0; }}
            }}

            </style>

            <div class="particles">
                {particles_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Background error: {e}")


def activate_login_background():
    set_heartbeat_bg("heartbeat_bg.png")


# ================= PASSWORD =================

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ================= SIGN UP =================

def sign_up():

    # TITLE (MOVED LITTLE DOWN)
    st.markdown(
        """
        <div style='margin-top:60px; text-align:center;'>
            <h1 style='
                font-size:36px;
                font-weight:800;
                color:#00ffff;
                margin-bottom:5px;'>
                🧠 AI Doctor Assistant
            </h1>
            <p style='
                color:white;
                font-size:16px;
                margin-bottom:25px;'>
                Create your medical assistant account
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ECG Animation
    st.markdown("""
        <div class="ecg">
            <svg viewBox="0 0 1440 320">
                <path d="
                    M0 200 
                    L150 200 
                    L200 120 
                    L250 280 
                    L300 200 
                    L450 200 
                    L500 140 
                    L550 260 
                    L600 200 
                    L750 200 
                    L800 100 
                    L850 300 
                    L900 200 
                    L1440 200" />
            </svg>
        </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username", key="signup_username")
    email = st.text_input(
        "Email",
        placeholder="Enter your email (e.g. example@mail.com)",
        key="signup_email"
    )
    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter strong password",
        key="signup_password"
    )
    # NEW ROLE SELECTION
    role = st.selectbox(
    "Register As",
    ["patient", "doctor",],
    key="signup_role"
    )
    doctor_id = None
    license_file = None

    if role == "doctor":

        doctor_id = st.text_input(
            "Doctor License ID",
            placeholder="Enter your medical license ID"
        )

        license_file = st.file_uploader(
            "Upload License PDF",
            type=["pdf"]
        )
    

    if st.button("Sign Up", key="signup_btn"):
        if not username or not email or not password:
            st.error("All fields are required")
            return
        # NEW → doctor validation
        if role == "doctor":
            st.info("Doctor must provide Doctor ID or License PDF for verification")

            if not doctor_id and not license_file:
                st.error("Please provide Doctor ID or upload License PDF")
                return

        hashed_pw = hash_password(password)

        try:
            role_value = role

            if role == "doctor":
                role_value = "pending_doctor"

            license_url = None

            # upload license if doctor
            if role == "doctor" and license_file:

                file_bytes = license_file.read()
                import uuid
                file_name = f"{uuid.uuid4()}_{email}_license.pdf"

                supabase.storage.from_("licenses").upload(
                    file_name,
                    file_bytes
                )

                license_url = supabase.storage.from_("licenses").get_public_url(file_name)

            supabase.table("users").insert({

            "username": username,
            "email": email,
            "password": hashed_pw,
            "role": role_value,
            "doctor_id": doctor_id,
            "license_file": license_url

            }).execute()

            st.success("Account created successfully")
            st.session_state.page = "login"
            st.rerun()

        except Exception as e:
            st.error(f"Signup failed: {e}")

    st.markdown(
        "<p style='text-align:center;color:white;'>Already have an account?</p>",
        unsafe_allow_html=True
    )

    if st.button("Go to Login", key="goto_login_btn"):
        st.session_state.page = "login"
        st.rerun()


# ================= LOGIN =================

# ================= LOGIN =================

def login():

    # TITLE
    st.markdown(
        """
        <div style='margin-top:60px; text-align:center;'>
            <h1 style='
                font-size:36px;
                font-weight:800;
                color:#00ffff;
                margin-bottom:5px;'>
                🧠 AI Doctor Assistant
            </h1>
            <p style='
                color:white;
                font-size:16px;
                margin-bottom:25px;'>
                Login to continue
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ECG Animation
    st.markdown("""
        <div class="ecg">
            <svg viewBox="0 0 1440 320">
                <path d="
                    M0 200 
                    L150 200 
                    L200 120 
                    L250 280 
                    L300 200 
                    L450 200 
                    L500 140 
                    L550 260 
                    L600 200 
                    L750 200 
                    L800 100 
                    L850 300 
                    L900 200 
                    L1440 200" />
            </svg>
        </div>
    """, unsafe_allow_html=True)

    email = st.text_input(
        "Email",
        placeholder="Enter your registered email",
        key="login_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password"
    )

    if st.button("Login", key="login_btn"):

        if not email or not password:
            st.error("All fields are required")
            return

        try:

            response = supabase.table("users") \
                .select("*") \
                .eq("email", email) \
                .execute()

            if not response.data:
                st.error("User not found")
                return

            user = response.data[0]

            # verify bcrypt password
            if not verify_password(password, user["password"]):
                st.error("Invalid password")
                return

            # doctor approval check
            if user.get("role") == "pending_doctor":
                st.warning("Doctor account waiting for admin approval")
                return

            # ---------------- SESSION SET ----------------
            st.session_state.user = user.get("username")
            st.session_state.user_id = user.get("id")

            # ensure role always exists
            st.session_state.role = user.get("role", "patient")

            # page routing
            st.session_state.page = "chatbot"

            st.rerun()

        except Exception as e:
            st.error(f"Login failed: {e}")

    st.markdown(
        "<p style='text-align:center;color:white;'>Don't have an account?</p>",
        unsafe_allow_html=True
    )

    if st.button("Go to Signup", key="goto_signup_btn"):
        st.session_state.page = "signup"
        st.rerun()