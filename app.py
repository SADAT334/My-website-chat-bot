import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import gradio as gr
import spaces
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize Client
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

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

def respond(message, history):
    try:
        sdk_history = []

        for turn in history:
            role = "user" if turn["role"] == "user" else "model"
            content = turn["content"]

            # Gradio 6 can return content as a list of dictionaries
            # e.g. [{"text": "hi", "type": "text"}]
            if isinstance(content, list):
                text_parts = []

                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))

                text = "".join(text_parts)

            else:
                text = str(content)

            # Only add messages that actually contain text
            if text:
                sdk_history.append({
                    "role": role,
                    "parts": [{"text": text}]
                })

        chat = client.chats.create(
            model="gemini-3.6-flash",
            history=sdk_history,
            config=types.GenerateContentConfig(
                system_instruction=AGENT_PERSONA
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

demo = gr.ChatInterface(fn=respond)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)