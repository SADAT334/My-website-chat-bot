import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import gradio as gr
import spaces
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

# --- YOUR PERSONA IS FULLY RESTORED HERE ---
AGENT_PERSONA = """
You are Karoline Leavitt, serving as the professional Communications Director and Press Secretary for Sadat Mahmud.
Your role is to manage all incoming public inquiries for Sadat through this portfolio website.

CRITICAL RULES:
1. MANDATORY INTRODUCTION: Your first message must start with: "Hi, I'm Karoline, Sadat's Communications Director."
2. THE SIGNATURE LINE: Include the phrase "happily ignoring the world, as data scientists tend to do" when describing Sadat's current focus.
3. PROFESSIONAL & ARTICULATE: Maintain a polished, press-secretary demeanor with a dryly witty edge.
4. SADAT'S PROFILE: Name: Sadat. Expertise: Data Science (MS from TU Dortmund), Python, PySpark, FastAPI, AI/ML.
5. EXTREME BREVITY: Keep all responses strictly to 2-3 short sentences. No rambling.
"""


# --- Required so HF Spaces will start this app on ZeroGPU hardware. ---
# This app never actually needs a GPU (Gemini calls are pure API calls),
# but new free-tier Spaces are provisioned on ZeroGPU by default, and the
# runtime refuses to start unless at least one @spaces.GPU function exists.
# We never call this function, so no GPU is ever actually allocated.
@spaces.GPU(duration=1)
def _dummy_gpu_touch():
    return True


def send_email_transcript(client_message: str, agent_reply: str):
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
    SENDER_PASSWORD = os.environ.get("SENDER_APP_PASSWORD")
    RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")
    if not all([SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL]):
        return

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
        print(f"Email failed: {e}")


def respond(message, history):
    try:
        # Gradio 6.x ChatInterface passes history as a list of
        # {"role": ..., "content": ...} dicts, not (human, assistant) tuples.
        gemini_history = [{"role": "user", "parts": [AGENT_PERSONA]}]
        for turn in history:
            role = "user" if turn["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [turn["content"]]})

        chat = client.chats.create(model="gemini-1.5-flash", history=gemini_history)
        response = chat.send_message(message)

        # Try to send email
        send_email_transcript(message, response.text)

        return response.text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


demo = gr.ChatInterface(fn=respond)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)