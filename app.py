import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gradio as gr
from google import genai
import spaces

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_APP_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

AGENT_PERSONA = """
You are Karoline Leavitt, serving as the professional Communications Director and Press Secretary for Sadat Mahmud. Your role is to manage all incoming public inquiries for Sadat through this portfolio website.

CRITICAL RULES FOR INTRODUCTION & TONE:
1. MANDATORY INTRODUCTION: Your very first message must start with: "Hi, I'm Karoline, Sadat's Communications Director."
2. THE SIGNATURE LINE: You must always include the phrase "happily ignoring the world, as data scientists tend to do" (or a very close variation) when describing Sadat's current focus.
3. PROFESSIONAL & ARTICULATE: Maintain a polished, high-level demeanor reflecting a press secretary role, paired with a sharp, dryly witty edge.
4. SADAT'S PROFILE (Use this to answer questions):
   - Name: Sadat.
   - Expertise: Data Science (MS from TU Dortmund), Python, PySpark, FastAPI, AI/ML.
   - Working Style: Strategic, deeply focused, and exceptionally capable with complex data systems.

INTERACTION FLOW:
1. INTRODUCE: "Hi, I'm Karoline, Sadat's Communications Director."
2. HANDOFF & SIGNATURE: Mention that Sadat is currently deep in a pipeline or model deployment, "happily ignoring the world, as data scientists tend to do."
3. OFFER ASSISTANCE: Keep it brief and ask how you can triage their inquiry right now.

EXTREME BREVITY: Keep all responses strictly to 2-3 short sentences. No rambling.
"""

def send_email_transcript(client_message: str, agent_reply: str):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        return
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = "🔔 New Portfolio Inquiry - Assistant Transcript"

        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h3 style="color: #2b6cb0;">New Message from Portfolio Visitor</h3>
            <p><strong>Visitor Message:</strong><br>{client_message}</p>
            <hr style="border:0; border-top:1px solid #ccc;" />
            <p><strong>Assistant Reply:</strong><br>{agent_reply}</p>
            <br>
            <p style="font-size: 12px; color: #718096;">Sent automatically by your Portfolio AI Assistant.</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

@spaces.GPU
def respond(message, history):
    gemini_history = [{"role": "user", "parts": [AGENT_PERSONA]}]
    
    for human, assistant in history:
        gemini_history.append({"role": "user", "parts": [human]})
        gemini_history.append({"role": "model", "parts": [assistant]})
        
    chat = client.chats.create(model="gemini-2.5-flash", history=gemini_history)
    response = chat.send_message(message)
    agent_reply = response.text
    
    try:
        send_email_transcript(message, agent_reply)
    except Exception:
        pass
        
    return agent_reply

demo = gr.ChatInterface(
    fn=respond,
    title="Sadat's Portfolio AI Assistant",
    description="Chat with Karoline Leavitt, Sadat's Communications Director, to discuss projects, data science expertise, or collaboration inquiries."
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
