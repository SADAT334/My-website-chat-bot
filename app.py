import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gradio as gr
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

# --- YOUR PERSONA IS HERE ---
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

def respond(message, history):
    if not GEMINI_KEY:
        return "⚠️ Configuration Error: GEMINI_API_KEY is missing."
    
    try:
        # Re-adding the persona to the start of the chat history
        gemini_history = [{"role": "user", "parts": [AGENT_PERSONA]}]
        
        for human, assistant in history:
            gemini_history.append({"role": "user", "parts": [human]})
            gemini_history.append({"role": "model", "parts": [assistant]})
        
        chat = client.chats.create(model="gemini-1.5-flash", history=gemini_history)
        response = chat.send_message(message)
        
        return response.text
    except Exception as e:
        # This print statement is the key! It shows up in your Logs tab.
        print(f"DEBUG ERROR: {type(e).__name__} - {str(e)}")
        return f"⚠️ AI Error: {type(e).__name__}"

demo = gr.ChatInterface(fn=respond)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)