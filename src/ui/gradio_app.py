# pylint: disable=no-member

"""
Gradio UI for Business AI Copilot.
Compatible with gradio==6.6.0
"""

import gradio as gr
import logging
from datetime import datetime
from typing import Tuple

from src.main import BusinessCopilot
from config.settings import GOOGLE_API_KEY, JIRA_URL

logger = logging.getLogger(__name__)

custom_css = """
.gradio-container {
    font-family: 'Inter', sans-serif;
}

/* Reduce spacing between messages */
.gr-chatbot {
    border: 2px solid #2196F3 !important;
    border-radius: 12px !important;
    padding: 10px !important;
    gap: 6px !important;
}

/* Reduce padding inside bubbles */
.gr-chatbot .message {
    padding: 8px 10px !important;
    border: 2px solid #2196F3 !important;
}

/* Query input styling */
textarea {
    border: 2px solid #4CAF50 !important;
    border-radius: 10px !important;
    padding: 10px !important;
}

input[type="text"] {
    border: 2px solid #4CAF50 !important;
    border-radius: 10px !important;
    padding: 8px !important;
}
"""


class CopilotUI:

    def __init__(self):
        self.copilot = None
        self.setup_status = "Not initialized"

        try:
            self.copilot = BusinessCopilot()
            self.setup_status = "Ready"
            logger.info("✅ Business AI Copilot auto-initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to auto-initialize copilot: {str(e)}", exc_info=True)
            self.setup_status = f"Error: {str(e)}"

    def initialize_copilot(self) -> Tuple[str, str]:
        try:
            self.copilot = BusinessCopilot()
            self.setup_status = "Ready"
            return (
                "✅ Business AI Copilot initialized successfully!",
                self._build_config_info()
            )
        except Exception as e:
            return (f"❌ Initialization failed: {str(e)}", str(e))

    def _build_config_info(self) -> str:
        return "\n".join([
            "**Configuration Status:**",
            "",
            f"- Google API: {'✅ Configured' if GOOGLE_API_KEY else '❌ Not configured'}",
            f"- Jira Integration: {'✅ Connected' if JIRA_URL else '⚠️ Not configured'}",
            f"- Vector Database: ✅ Active",
            f"- Available Tools: {len(self.copilot.tools) if self.copilot else 0}",
        ])

    def process_query(self, query, user_email, user_role, chat_history):

        if chat_history is None:
            chat_history = []

        if not self.copilot:
            chat_history.append({
                "role": "assistant",
                "content": "⚠️ Please initialize the copilot first."
            })
            return chat_history, ""

        if not query.strip():
            return chat_history, ""

        user_context = {
            "user_email": user_email or "user@company.com",
            "role": user_role or "Product Manager"
        }

        chat_history.append({
            "role": "user",
            "content": query
        })

        response = self.copilot.process_query(query, user_context)

        chat_history.append({
            "role": "assistant",
            "content": response
        })

        return chat_history, ""

    def clear_chat(self):
        return [], ""


def create_ui() -> gr.Blocks:

    copilot_ui = CopilotUI()

    with gr.Blocks(title="Business AI Copilot") as demo:

        gr.Markdown("""
        # 🤖 Business AI Copilot
        Your intelligent assistant for planning and communication.
        """)

        with gr.Tabs():

            # ================= CHAT TAB =================
            with gr.Tab("💬 Chat"):

                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=350
                )

                query_input = gr.Textbox(
                    label="Your message",
                    lines=2
                )

                submit_btn = gr.Button("Send")
                clear_btn = gr.Button("🗑️ Clear Chat")

                user_email = gr.Textbox(
                    label="Email",
                    value="john.doe@company.com"
                )

                user_role = gr.Textbox(
                    label="Role",
                    value="Product Manager"
                )

                submit_btn.click(
                    fn=copilot_ui.process_query,
                    inputs=[query_input, user_email, user_role, chatbot],
                    outputs=[chatbot, query_input]
                )

                query_input.submit(
                    fn=copilot_ui.process_query,
                    inputs=[query_input, user_email, user_role, chatbot],
                    outputs=[chatbot, query_input]
                )

                clear_btn.click(
                    fn=copilot_ui.clear_chat,
                    outputs=[chatbot, query_input]
                )

            # ================= SETUP TAB =================
            with gr.Tab("💬 Sample Prompts"):

                gr.Markdown("""## Sample Prompts

                            ### **📅 Daily Planning**
                            ```
                            Create my priority plan for today
                            What should I focus on today?
                            Show me my schedule and top priorities
                            Help me plan my day with my meetings and tasks
                            ```

                            ### **📊 Project Status**
                            ```
                            Get the status of Project Phoenix
                            What are the current blockers for Phoenix?
                            Show me Phoenix sprint progress
                            How is Project Atlas doing?
                            What's the completion percentage for Phoenix?
                            ```

                            ### **✉️ Email Composition**
                            ```
                            Get Phoenix status and draft an update email for stakeholders
                            Draft a professional status email about project delays
                            Compose an email updating the team on current blockers
                            Write an email to Sarah about the API integration issue
                            ```

                            ### **📚 Knowledge Search**
                            ```
                            Search for Phoenix team documentation
                            Find the stakeholder list for Phoenix
                            Who are the team members on Project Atlas?
                            What's our vacation policy?
                            ```

                            ### **🔄 Combined Workflows**
                            ```
                            Get project status, identify blockers, and draft an escalation email
                            Check my calendar, find my tasks, and create a priority plan
                            Search for team contacts and draft a meeting invite
                            """)

        gr.Markdown("---")
        gr.Markdown("Business AI Copilot | Version 1.0")

    return demo


def launch_ui(
    share=False,
    server_name="127.0.0.1",
    server_port=7860
):

    demo = create_ui()

    demo.launch(
        share=share,
        server_name=server_name,
        server_port=server_port,
        theme=gr.themes.Soft(),
        css=custom_css,
        show_error=True
    )
