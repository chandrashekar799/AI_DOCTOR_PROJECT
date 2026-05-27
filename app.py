import streamlit as st
import os
import uuid
import json
import tempfile
import re
from dotenv import load_dotenv
from groq import Groq
from streamlit_mic_recorder import mic_recorder
from database import save_chat, load_chats
from auth import login, sign_up, activate_login_background
from file_parser import extract_text_from_pdf, extract_text_from_docx
from supabase_client import save_case, get_patient_cases

load_dotenv()
st.set_page_config(page_title="AI Doctor", layout="wide")

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# =========================================================
# DEBUG MODE
# =========================================================
DEBUG_MODE = False
if DEBUG_MODE:
    st.session_state.user = "Test User"
    st.session_state.role = "patient"
    st.session_state.page = "chatbot"

# =========================================================
# PAGE ROUTING
# =========================================================
if "page" not in st.session_state:
    st.session_state.page = "login"

if st.session_state.page == "login":
    activate_login_background()
    login()
    st.stop()

elif st.session_state.page == "signup":
    activate_login_background()
    sign_up()
    st.stop()

# =========================================================
# FORCE LOGIN IF SESSION LOST
# =========================================================
if "user" not in st.session_state or "role" not in st.session_state:

    st.session_state.clear()
    st.session_state.page = "login"

    activate_login_background()
    login()
    st.stop()

# =========================================================
# ROLE BASED PORTAL ROUTING
# =========================================================
if st.session_state.get("role") == "admin":
    import admin_portal
    admin_portal.show_admin_portal()
    st.stop()

if st.session_state.get("role") == "doctor":
    import doctor_portal
    doctor_portal.show_doctor_portal()
    st.stop()

# =========================================================
# CHATBOT STARTS HERE
# =========================================================
if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_input" not in st.session_state:
    st.session_state.last_input = ""

if "patient_details" not in st.session_state:
    st.session_state.patient_details = {}

# flag for new chat
if "new_chat" not in st.session_state:
    st.session_state.new_chat = False

# =========================================================
# NAVBAR CSS
# =========================================================
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"]:first-of-type {
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
    padding: 8px 15px !important;
    border-radius: 12px;
    margin-top: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    align-items: center;
}
section[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] * {
    color: #0f172a !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("🧠 AI Doctor")
    st.subheader("📜 Chat History")

    # Reset Chat Memory Button
    if st.button("🧹 Reset Chat Memory"):
        st.session_state.clear()
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    if st.button("➕ New Chat", key="new_chat_button"):

        if st.session_state.messages:
            save_chat(
                user=st.session_state.user,
                chat_id=st.session_state.chat_id,
                messages=st.session_state.messages
            )

        # reset session
        st.session_state.chat_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.last_input = ""
        st.session_state.patient_details = {}
        st.session_state.new_chat = True

        st.rerun()

    st.divider()
    past_chats = load_chats(st.session_state.user) or []

    # if no chats exist clear session memory
    if len(past_chats) == 0:
        st.session_state.messages = []
        st.session_state.chat_id = str(uuid.uuid4())

    # remove invalid chats
    past_chats = [c for c in past_chats if c.get("messages")]

    # keep order saved in chats.json (latest already on top)

    for index, chat in enumerate(past_chats):

        title = chat.get("title") or chat["messages"][0]["content"][:30]
        chat_id = chat.get("chat_id") or str(uuid.uuid4())
        key = f"{chat_id}_{index}"

        if st.button(title, key=key):
            st.session_state.chat_id = chat_id
            st.session_state.messages = chat.get("messages", [])
            st.session_state.last_input = ""
            st.session_state.patient_details = {}
            st.session_state.new_chat = False
            st.rerun()

# ---------------- NAVBAR ROW ----------------
col1, col2, col3, col4, col5 = st.columns([1,1,6,1,1])

with col1:
    uploaded_file = st.file_uploader("📎", type=["pdf","docx","txt"], label_visibility="collapsed")

with col2:
    audio = mic_recorder(
        start_prompt="🎤 Say something...",
        stop_prompt="⏹ Stop Recording",
        key="recorder"
    )

with col3:
    st.markdown("""
        <div style="text-align:center;font-size:26px;font-weight:700;color:white;">
        🧠 AI Doctor Assistant
        </div>
    """, unsafe_allow_html=True)

with col4:
    if st.session_state.messages:
        chat_json = json.dumps(st.session_state.messages, indent=4)
        st.download_button("⬇ Download", chat_json, "chat_history.json")

with col5:
    if st.button("🚪 LOGOUT", key="main_logout"):

        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.session_state.page = "login"
        st.rerun()

# ---------------- DISPLAY CHAT ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================================================
# MIC TRANSCRIPTION
# =========================================================
voice_text = ""

if audio and isinstance(audio, dict) and "bytes" in audio:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio["bytes"])
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3"
            )

        voice_text = transcription.text

    except Exception as e:
        st.error(f"Mic transcription error: {e}")

# =========================================================
# FILE PROCESSING
# =========================================================
file_text = ""

if uploaded_file:
    try:
        file_type = uploaded_file.name.split(".")[-1].lower()

        if file_type == "pdf":
            file_text = extract_text_from_pdf(uploaded_file)

        elif file_type == "docx":
            file_text = extract_text_from_docx(uploaded_file)

        elif file_type == "txt":
            file_text = uploaded_file.read().decode("utf-8")

    except Exception as e:
        st.error(f"File error: {e}")

prompt = st.chat_input("Ask your medical question...")

# =========================================================
# CHAT RESPONSE
# =========================================================
current_input = ""

if prompt:
    current_input += prompt.strip()

if voice_text:
    current_input += voice_text.strip()

if file_text:
    if current_input:
        current_input += "\n\nUploaded Content:\n" + file_text.strip()[:4000]
    else:
        current_input = "Analyze this medical report:\n\n" + file_text.strip()[:4000]

if current_input.strip() != "" and current_input != st.session_state.last_input:

    st.session_state.last_input = current_input
    st.session_state.new_chat = False

    st.session_state.messages.append({
        "role": "user",
        "content": current_input
    })

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            try:

                system_prompt = f"""
You are a professional AI Doctor Assistant.

Patient Memory:
{st.session_state.patient_details}

Response format:

1️⃣ Patient Details

2️⃣ Report Analysis Table

3️⃣ Medicines

4️⃣ Food Recommendation

5️⃣ Exercise Recommendation

6️⃣ Medical Summary
"""

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
                    temperature=0.2,
                )

                reply = response.choices[0].message.content

            except Exception as e:
                reply = f"Error: {str(e)}"

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

    save_chat(
        user=st.session_state.user,
        chat_id=st.session_state.chat_id,
        messages=st.session_state.messages
    )

    try:
        save_case(st.session_state.user, current_input, reply)
    except:
        pass

    st.rerun()
# =========================================================
# DOCTOR REVIEW RESULTS
# =========================================================
# =========================================================
# DOCTOR REVIEW RESULTS
# =========================================================
if not st.session_state.new_chat:

    try:

        st.divider()
        st.subheader("🩺 Doctor Review")

        patient_cases = get_patient_cases(st.session_state.user)

        if patient_cases:

            patient_cases = sorted(
                patient_cases,
                key=lambda x: x.get("created_at", "")
            )

            for case in patient_cases:

                st.markdown("**Your Question:**")
                st.write(case.get("question", ""))

                st.markdown("**AI Diagnosis:**")
                st.info(case.get("ai_response", ""))

                status = str(case.get("doctor_status", "pending")).lower()

                if status == "approved":

                    st.success("Doctor Approved AI Diagnosis")

                    if case.get("medicines"):
                        st.markdown("**Doctor Suggested Medicines:**")
                        st.write(case["medicines"])

                elif status == "rejected":

                    st.error("Doctor Rejected This Diagnosis")

                else:

                    st.warning("⏳ Waiting for Doctor Review")

                st.divider()

        else:
            st.info("No doctor reviews yet")

    except Exception as e:
        st.error(e)