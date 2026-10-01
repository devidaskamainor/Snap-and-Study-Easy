# Snap & Study Easy

A Streamlit study assistant that explains typed questions and uploaded study images with Gemini. It can send answers by email and study summaries through WhatsApp.

## Setup

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` and add your API and service credentials:

```toml
GEMINI_API_KEY = "your-gemini-api-key"

TWILIO_ACCOUNT_SID = "your-twilio-account-sid"
TWILIO_AUTH_TOKEN = "your-twilio-auth-token"
TWILIO_WHATSAPP_FROM = "your-twilio-whatsapp-sender"
TWILIO_CONTENT_SID = "your-twilio-content-template-sid"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-gmail-address"
SMTP_PASSWORD = "your-google-app-password"
```

For Gmail, use a Google App Password for `SMTP_PASSWORD`, not your regular account password. The app sends from `SMTP_USERNAME`.

Keep real credentials private. The `.gitignore` excludes `.streamlit/secrets.toml` and the virtual environment; do not remove those entries or commit secrets.

## Run

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.