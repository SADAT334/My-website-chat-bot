# app.py
import gradio as gr
from agent.agent import run_agent_chat

# Launch the Gradio UI directly pointing to your modular agent function
demo = gr.ChatInterface(
    fn=run_agent_chat,
    title="Sadat Mahmud's Portfolio Assistant",
    description="Meet Karoline Ravitt, Sadat's Communications Director. Ask anything about his background, data science projects, and technical stack!"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)