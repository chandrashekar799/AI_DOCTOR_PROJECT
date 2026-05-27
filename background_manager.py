import streamlit as st
import base64

def set_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>
        html, body, .stApp {{
            height: 100%;
            margin: 0;
        }}

        .stApp {{
            background-image:
                linear-gradient(
                    rgba(13, 71, 161, 0.15),
                    rgba(13, 71, 161, 0.15)
                ),
                url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        .block-container {{
            padding-top: 0rem !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )