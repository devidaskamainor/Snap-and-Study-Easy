import json
import smtplib
from email.message import EmailMessage

import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import (
    SUMMARY_REQUEST_PROMPT,
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
)


MODEL_NAME = "gemini-3.5-flash"

st.set_page_config(
    page_title="Snap & Study Easy",
    page_icon="📚",
    layout="centered",
)


# -----------------------------
# API KEYS
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]
SMTP_HOST = st.secrets.get("SMTP_HOST", "")
SMTP_PORT = int(st.secrets.get("SMTP_PORT", 587))
SMTP_USERNAME = st.secrets.get("SMTP_USERNAME", "")
SMTP_PASSWORD = st.secrets.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = SMTP_USERNAME


# -----------------------------
# CREATE GEMINI CLIENT
# -----------------------------

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_twilio_client():
    return TwilioClient(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN
    )


gemini_client = get_gemini_client()
twilio_client = get_twilio_client()


# -----------------------------
# DISPLAY CHAT MESSAGE
# -----------------------------

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


# -----------------------------
# SAVE CHAT MESSAGE
# -----------------------------

def add_message(role, kind, content):

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content,
        }
    )

    render_message(
        st.session_state.messages[-1]
    )


# -----------------------------
# ASK GEMINI
# -----------------------------

def ask_gemini(parts):

    try:

        response = st.session_state.chat.send_message(parts)

        return response.text

    except Exception as error:

        return f"Sorry, something went wrong: {error}"


# -----------------------------
# CLEAN WHATSAPP MESSAGE
# -----------------------------

def clean_whatsapp_text(text):

    if not text:
        return "No study summary available."

    text = " ".join(text.split())

    return text[:1500] + "..." if len(text) > 1500 else text


# -----------------------------
# SEND WHATSAPP MESSAGE
# -----------------------------

def send_whatsapp(to_number, user_name, summary):

    try:

        content_variables = json.dumps(
            {
                "1": user_name,
                "2": clean_whatsapp_text(summary),
            },
            ensure_ascii=False,
        )

        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )

        return True, message.sid

    except Exception as error:

        return False, str(error)


# -----------------------------
# SEND EMAIL
# -----------------------------

def send_email(to_email, subject, body):

    if not all((SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL)):
        return False, "Email is not configured. Add the SMTP settings to Streamlit secrets."

    message = EmailMessage()
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)

        return True, "Email sent."

    except Exception as error:

        return False, str(error)


# =========================================================
# ONBOARDING
# =========================================================

if "onboarded" not in st.session_state:

    st.title("📚 Snap & Study Easy")

    st.caption(
        "Snap it. Understand it. Study it."
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name",
            placeholder="Enter your name"
        )

        whatsapp_number = st.text_input(
            "WhatsApp number with country code",
            placeholder="+91XXXXXXXXXX"
        )

        email_address = st.text_input(
            "Email address",
            placeholder="you@example.com"
        )

        submitted = st.form_submit_button(
            "Start Studying 🚀"
        )

        if submitted:

            if not name.strip() or not whatsapp_number.strip() or not email_address.strip():

                st.warning(
                    "Please enter your name, WhatsApp number, and email address."
                )

            elif "@" not in email_address or "." not in email_address.rsplit("@", 1)[-1]:

                st.warning("Please enter a valid email address.")

            else:

                st.session_state.name = name.strip()

                st.session_state.whatsapp_number = (
                    whatsapp_number.strip()
                )

                st.session_state.email_address = email_address.strip()

                st.session_state.chat = (
                    gemini_client.chats.create(
                        model=MODEL_NAME,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT
                        ),
                    )
                )

                st.session_state.messages = []

                st.session_state.onboarded = True

                st.rerun()

    st.stop()


# =========================================================
# HEADER
# =========================================================

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center"
)


with header_col:

    st.title("📚 Snap & Study Easy")


with button_col:

    send_disabled = (
        len(st.session_state.messages) <= 2
    )

    if st.button(
        "📤 Send to WhatsApp",
        disabled=send_disabled,
        use_container_width=True,
    ):

        with st.spinner(
            "Preparing your study summary..."
        ):

            summary = ask_gemini(
                [SUMMARY_REQUEST_PROMPT]
            )

            success, info = send_whatsapp(
                st.session_state.whatsapp_number,
                st.session_state.name,
                summary,
            )

            if success:

                st.success(
                    "Study summary sent to WhatsApp! 📲"
                )

            else:

                st.error(
                    f"Couldn't send the summary: {info}"
                )


st.caption(
    f"Student: {st.session_state.name}"
)


# =========================================================
# CHAT HISTORY
# =========================================================

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        ),
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# =========================================================
# CHAT INPUT
# =========================================================

user_input = st.chat_input(
    "Ask a question or upload a study image...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png",
        "webp"
    ],
)


# =========================================================
# PROCESS USER INPUT
# =========================================================

if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # -----------------------------
    # IMAGE
    # -----------------------------

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes,
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type,
            )
        )


    # -----------------------------
    # TEXT
    # -----------------------------

    if text:

        add_message(
            "user",
            "text",
            text,
        )

        parts.append(text)


    # -----------------------------
    # IMAGE WITHOUT TEXT
    # -----------------------------

    elif photo is not None:

        parts.append(
            """
            Analyze this study image.

            Identify what the student needs to understand.

            Explain:
            1. What is shown
            2. The main concept
            3. Important points
            4. Step-by-step explanation
            5. A simple example if useful

            Use simple English.
            """
        )


    # -----------------------------
    # GEMINI RESPONSE
    # -----------------------------

    with st.spinner(
        "Understanding your question..."
    ):

        answer = ask_gemini(parts)

        add_message(
            "assistant",
            "text",
            answer,
        )

        email_sent, email_info = send_email(
            st.session_state.email_address,
            "Your Snap & Study Easy answer",
            answer,
        )

        if email_sent:
            st.success("Answer sent to your email.")
        else:
            st.warning(f"Answer is in the chat, but email delivery failed: {email_info}")