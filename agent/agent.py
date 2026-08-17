# agent/agent.py
import os
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import spaces
from google.genai import types
from services.gemini import get_gemini_client
from agent.prompts import KAROLINE_PERSONA
from agent.tools import extract_text_from_pdf, get_github_projects

@spaces.GPU(duration=1)
def _dummy_gpu_touch():
    return True

def send_email_transcript(client_message: str, agent_reply: str):
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
    SENDER_PASSWORD = os.environ.get("SENDER_APP_PASSWORD")
    RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")
    
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        return

    def _send():
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'] = SENDER_EMAIL, RECEIVER_EMAIL
            msg['Subject'] = "🔔 New Portfolio Inquiry"
            msg.attach(MIMEText(f"Visitor: {client_message}\n\nAgent Reply: {agent_reply}", 'plain'))
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"Background email failed: {e}")

    threading.Thread(target=_send).start()

_CACHED_RESUME_TEXT = None

def get_resume_text():
    global _CACHED_RESUME_TEXT
    if _CACHED_RESUME_TEXT is None:
        _CACHED_RESUME_TEXT = extract_text_from_pdf()
    return _CACHED_RESUME_TEXT

def build_system_instruction():
    """Dynamically merges the Karoline persona, cached resume, and live GitHub context."""
    resume_text = get_resume_text()
    
    # Optionally pre-fetch github summary so it's always instantly available without tool-call crashes
    github_text = get_github_projects()
    
    combined_data = f"--- RESUME DATA ---\n{resume_text}\n\n--- GITHUB REPOSITORIES ---\n{github_text}"
    return KAROLINE_PERSONA.format(resume_data=combined_data)

def run_agent_chat(message, history):
    """The main respond function called by Gradio."""
    try:
        client = get_gemini_client()
        sdk_history = []

        for turn in history:
            role = "user" if turn["role"] == "user" else "model"
            content = turn["content"]

            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                text = "".join(text_parts)
            else:
                text = str(content)

            if text:
                sdk_history.append({
                    "role": role,
                    "parts": [{"text": text}]
                })

        system_instruction = build_system_instruction()

        chat = client.chats.create(
            model="gemini-3.7-flash",
            history=sdk_history,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
        )

        response = chat.send_message(message)
        send_email_transcript(message, response.text)

        return response.text

    except Exception as e:
        import traceback
        print("========== DEBUG ERROR ==========")
        traceback.print_exc()
        print("=================================")
        return "⚠️ Technical glitch. Please try again."