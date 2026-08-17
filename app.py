import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gradio as gr
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini Client with error checking
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY environment variable is not set.")
    # We continue so the app launches, but the first chat message will report the error to the user
client = genai.Client(api_key=GEMINI_KEY)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_APP_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

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

def send_email_transcript(client_message: str, agent_reply: str):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        return # Skip email if configuration is missing
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = "🔔 New Portfolio Inquiry"

        body = f"Visitor: {client_message}\n\nAgent Reply: {agent_reply}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def respond(message, history):
    if not GEMINI_KEY:
        return "⚠️ Configuration Error: GEMINI_API_KEY is missing in Space settings."
    
    try:
        gemini_history = [{"role": "user", "parts": [AGENT_PERSONA]}]
        for human, assistant in history:
            gemini_history.append({"role": "user", "parts": [human]})
            gemini_history.append({"role": "model", "parts": [assistant]})
            
        chat = client.chats.create(model="gemini-2.0-flash", history=gemini_history)
        response = chat.send_message(message)
        agent_reply = response.text
        
        send_email_transcript(message, agent_reply)
        return agent_reply
    except Exception as e:
        return f"⚠️ Error communicating with AI: {str(e)}"

demo = gr.ChatInterface(
    fn=respond,
    title="Sadat's Portfolio AI Assistant",
    description="Chat with Karoline Leavitt, Sadat's Communications Director."
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
