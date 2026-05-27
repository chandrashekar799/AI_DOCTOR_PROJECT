import streamlit as st
import streamlit.components.v1 as components
import os
import io
import uuid
from dotenv import load_dotenv
from database import save_chat, load_chats
from file_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_image
)
from analysis_engine import (
    extract_lab_values,
    flag_abnormal,
    generate_structured_summary
)
from risk_rules import calculate_risk
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from groq import Groq


def generate_pdf(content):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("MediChat - AI Clinical Report", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    for line in content.split("\n"):
        if line.strip():
            elements.append(Paragraph(line, styles["Normal"]))
            elements.append(Spacer(1, 0.15 * inch))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def run_chatbot():

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        st.error("⚠ GROQ_API_KEY missing in .env file")
        return

    client = Groq(api_key=api_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "last_response" not in st.session_state:
        st.session_state.last_response = None

    if "file_uploader_key" not in st.session_state:
        st.session_state.file_uploader_key = str(uuid.uuid4())

    # -------- SIDEBAR --------
    with st.sidebar:
        st.title("💬 Your Chats")

        if st.button("➕ New Chat"):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.rerun()

        previous_chats = load_chats(st.session_state.user_id)

        for i, chat in enumerate(previous_chats):
            if st.button(chat["message"][:40] + "...", key=f"chat_{i}"):
                st.session_state.messages = [
                    {"role": "user", "content": chat["message"]},
                    {"role": "assistant", "content": chat["response"]}
                ]
                st.session_state.last_response = chat["response"]
                st.rerun()

    # -------- CHAT DISPLAY --------
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    st.markdown("</div>", unsafe_allow_html=True)

    # -------- HIDDEN NATIVE INPUT --------
    user_text = st.chat_input("")

    # -------- LOAD CUSTOM HTML UI --------
    with open("input_ui.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    components.html(html_content, height=120)

    # -------- PROMPT --------
    prompt = user_text.strip() if user_text else None

    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})

    labs = extract_lab_values(prompt)

    if labs:
        risk, anemia_stage = calculate_risk(labs)
        flagged = flag_abnormal(labs)
        response = generate_structured_summary(labs, risk, flagged)
    else:
        ai_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=st.session_state.messages,
            temperature=0.4
        )
        response = ai_response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.last_response = response
    save_chat(st.session_state.user_id, prompt, response)

    st.rerun()