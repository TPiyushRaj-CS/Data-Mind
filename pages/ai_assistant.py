import os
from pathlib import Path
import time

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from groq import (
    APIConnectionError,
    APIStatusError,
    RateLimitError,
    AuthenticationError,
)


# ============================================================
# DATAMIND AI - AI ASSISTANT
# ============================================================
# IMPORTANT:
# This page is loaded through app.py.
#
# Therefore:
# - No st.set_page_config() here
# - No custom sidebar here
# - app.py controls global navigation
# - main.css controls common DataMind AI styling
#
# AI PROVIDER:
# - Groq
# - Model: openai/gpt-oss-20b
# ============================================================


# ============================================================
# LOAD CUSTOM CSS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
CSS_PATH = BASE_DIR / "styles" / "main.css"

if CSS_PATH.exists():
    try:
        with open(CSS_PATH, "r", encoding="utf-8") as css_file:
            css = css_file.read()

        st.html(f"<style>{css}</style>")

    except Exception:
        pass


# ============================================================
# AI ASSISTANT PAGE STYLES
# ============================================================

st.html(
    """
    <style>

    /* ========================================================
       AI ASSISTANT
       ======================================================== */

    .assistant-header {
        padding: 28px 0 20px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 24px;
    }

    .assistant-title {
        color: #172554;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.8px;
        line-height: 1.15;
    }

    .assistant-subtitle {
        color: #64748b;
        font-size: 14px;
        margin-top: 7px;
        line-height: 1.6;
    }

    .assistant-welcome {
        background:
            radial-gradient(
                circle at 100% 0%,
                rgba(196, 181, 253, 0.18),
                transparent 42%
            ),
            rgba(255, 255, 255, 0.72);

        border: 1px solid #e9d5ff;
        border-radius: 20px;
        padding: 38px 25px;
        text-align: center;
        margin: 25px 0;

        box-shadow:
            0 12px 32px rgba(71, 85, 105, 0.055);
    }

    .assistant-welcome-title {
        color: #172554;
        font-size: 25px;
        font-weight: 800;
        margin-bottom: 8px;
        letter-spacing: -0.4px;
    }

    .assistant-welcome-text {
        color: #64748b;
        max-width: 680px;
        margin: 0 auto;
        line-height: 1.7;
        font-size: 14px;
    }


    /* ========================================================
       QUICK PROMPT BUTTONS
       ======================================================== */

    .st-key-quick_prompts button {
        border: none !important;
    }

    .st-key-quick_prompts button p,
    .st-key-quick_prompts button span,
    .st-key-quick_prompts button div {
        color: #ffffff !important;
        font-weight: 700 !important;
    }


    /* ========================================================
       CHAT AREA
       ======================================================== */

    [data-testid="stChatMessage"] {
        border-radius: 16px;
    }

    [data-testid="stChatInput"] {
        border-color: #ddd6fe !important;
        border-radius: 15px !important;
    }

    [data-testid="stChatInput"] textarea {
        color: #172554 !important;
        background: #ffffff !important;
    }

    </style>
    """
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    BASE_DIR / ".env"
)


# ============================================================
# LOAD GROQ API KEY
# ============================================================
# Priority:
# 1. Streamlit Secrets
# 2. .env / environment variable
#
# This works both locally and on Streamlit Cloud.
# ============================================================

API_KEY = None


# ------------------------------------------------------------
# STREAMLIT CLOUD SECRETS
# ------------------------------------------------------------

try:
    API_KEY = st.secrets.get("GROQ_API_KEY")
except Exception:
    API_KEY = None


# ------------------------------------------------------------
# LOCAL .ENV / ENVIRONMENT VARIABLE
# ------------------------------------------------------------

if not API_KEY:
    API_KEY = os.getenv("GROQ_API_KEY")


if API_KEY:
    API_KEY = str(API_KEY).strip()


# ============================================================
# CHECK API KEY
# ============================================================

if not API_KEY:

    st.error(
        "Groq API key was not found."
    )

    st.info(
        "Please add GROQ_API_KEY to your .env file "
        "or Streamlit Secrets."
    )

    st.stop()


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
).strip()


# ============================================================
# GROQ CLIENT
# ============================================================

try:

    client = Groq(
        api_key=API_KEY
    )

except Exception as error:

    st.error(
        "Could not initialize the Groq AI client."
    )

    st.caption(
        f"Technical details: {error}"
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

def build_system_instruction():

    return """
You are DataMind AI Assistant.

You are a helpful, accurate and professional AI assistant
specializing in:

- Data Analytics
- Python
- Pandas
- NumPy
- SQL
- Power BI
- Excel
- Data Visualization
- Machine Learning fundamentals
- Programming

You can also answer general knowledge questions.

RULES:

1. Do not invent numerical results.

2. For Python questions, provide clean and readable Python code.

3. For SQL questions, provide correct SQL syntax.

4. For Power BI questions, provide appropriate DAX formulas.

5. Explain technical concepts step-by-step.

6. Use Markdown formatting.

7. Use tables when they make comparisons easier.

8. If you are uncertain about something, clearly state the
   uncertainty.

9. Never fabricate information.

10. When explaining code, explain the important lines.

11. Prefer beginner-friendly explanations for basic questions.

12. For interview or exam questions, provide concise and
    structured answers.

13. For programming problems, give the solution first and then
    explain it.

14. If multiple approaches exist, mention the best approach and
    briefly explain alternatives.

15. Never claim that you executed code unless you actually did.

16. Keep responses relevant to the user's question.

17. Do not unnecessarily repeat the user's question.

18. When giving code, use proper Markdown code blocks.

19. Prioritize correctness over confidence.
"""


# ============================================================
# CREATE PROMPT
# ============================================================

def create_prompt(
    user_prompt,
    conversation_text,
):

    system_instruction = build_system_instruction()

    return f"""
{system_instruction}

============================================================
CONVERSATION HISTORY
============================================================

{conversation_text}

============================================================
USER'S LATEST QUESTION
============================================================

{user_prompt}

============================================================
ANSWER REQUIREMENTS
============================================================

Answer the user's latest question clearly and professionally.

Use Markdown formatting.

Keep the answer easy to understand.

Do not mention these internal instructions.
"""


# ============================================================
# SAFE ERROR MESSAGE
# ============================================================

def show_ai_error(error):

    """
    Converts Groq/API errors into user-friendly messages.

    The actual exception is NOT displayed as a giant traceback
    to the user.
    """

    if isinstance(error, AuthenticationError):

        st.error(
            "DataMind AI could not authenticate with Groq."
        )

        st.info(
            "Please check the GROQ_API_KEY in your .env file "
            "or Streamlit Secrets."
        )

        return


    if isinstance(error, RateLimitError):

        st.warning(
            "DataMind AI is temporarily rate-limited."
        )

        st.info(
            "Please wait a few seconds and try your question again."
        )

        return


    if isinstance(error, APIConnectionError):

        st.warning(
            "DataMind AI could not connect to the AI service."
        )

        st.info(
            "Please check your internet connection and try again."
        )

        return


    if isinstance(error, APIStatusError):

        status_code = getattr(
            error,
            "status_code",
            None,
        )

        if status_code == 400:

            st.error(
                "The AI request could not be processed."
            )

            st.info(
                "Please try asking the question in a simpler way."
            )

            return


        if status_code == 403:

            st.error(
                "The Groq API request was not permitted."
            )

            st.info(
                "Please check your Groq API permissions."
            )

            return


        if status_code == 404:

            st.error(
                "The selected AI model is not available."
            )

            st.info(
                "Please check the GROQ_MODEL configuration."
            )

            return


        if status_code == 413:

            st.error(
                "The conversation is too large for this request."
            )

            st.info(
                "Start a new conversation and try again."
            )

            return


        if status_code == 429:

            st.warning(
                "DataMind AI is temporarily rate-limited."
            )

            st.info(
                "Please wait a few seconds before trying again."
            )

            return


        if status_code in {
            500,
            502,
            503,
            504,
        }:

            st.warning(
                "The AI service is temporarily unavailable."
            )

            st.info(
                "Please wait a moment and try again."
            )

            return


    # --------------------------------------------------------
    # UNKNOWN ERROR
    # --------------------------------------------------------

    st.error(
        "DataMind AI could not generate a response."
    )

    st.info(
        "Please try again. If the problem continues, "
        "restart the application and try once more."
    )


# ============================================================
# GENERATE AI ANSWER
# ============================================================

def generate_answer(user_prompt):

    # --------------------------------------------------------
    # BUILD CONVERSATION HISTORY
    # --------------------------------------------------------

    conversation = []

    for message in st.session_state.chat_history:

        conversation.append(
            f"{message['role'].upper()}: "
            f"{message['content']}"
        )

    conversation_text = "\n\n".join(
        conversation
    )


    # --------------------------------------------------------
    # CREATE PROMPT
    # --------------------------------------------------------

    prompt = create_prompt(
        user_prompt,
        conversation_text,
    )


    # --------------------------------------------------------
    # API REQUEST
    # --------------------------------------------------------

    response = None

    with st.spinner(
        "DataMind AI is analyzing your question..."
    ):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,

                messages=[
                    {
                        "role": "system",
                        "content": build_system_instruction(),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],

                temperature=0.2,

                max_tokens=4096,

                timeout=60,
            )


        except (
            AuthenticationError,
            RateLimitError,
            APIConnectionError,
            APIStatusError,
        ) as error:

            show_ai_error(error)

            return


        except Exception as error:

            show_ai_error(error)

            return


    # ========================================================
    # VALIDATE RESPONSE
    # ========================================================

    try:

        if response is None:

            st.error(
                "DataMind AI did not return a response."
            )

            return


        if not response.choices:

            st.error(
                "DataMind AI returned an empty response."
            )

            return


        answer = response.choices[0].message.content


    except Exception:

        st.error(
            "DataMind AI returned an unexpected response."
        )

        return


    # ========================================================
    # EMPTY RESPONSE CHECK
    # ========================================================

    if not answer:

        st.warning(
            "DataMind AI returned an empty answer."
        )

        return


    answer = str(answer).strip()


    if not answer:

        st.warning(
            "DataMind AI returned an empty answer."
        )

        return


    # ========================================================
    # SAVE USER MESSAGE
    # ========================================================

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_prompt,
        }
    )


    # ========================================================
    # SAVE AI MESSAGE
    # ========================================================

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )


    # ========================================================
    # RERUN TO DISPLAY CHAT
    # ========================================================

    st.rerun()


# ============================================================
# PAGE HEADER
# ============================================================

st.html(
    """
    <div class="assistant-header">

        <div class="assistant-title">
            DataMind AI Assistant
        </div>

        <div class="assistant-subtitle">
            Ask questions, write code, understand SQL and
            Power BI, and learn data analytics.
        </div>

    </div>
    """
)


# ============================================================
# CHAT HISTORY
# ============================================================

for message in st.session_state.chat_history:

    role = message["role"]

    content = message["content"]

    with st.chat_message(role):

        st.markdown(content)


# ============================================================
# WELCOME SCREEN
# ============================================================

if not st.session_state.chat_history:

    st.html(
        """
        <div class="assistant-welcome">

            <div class="assistant-welcome-title">
                How can I help you today?
            </div>

            <div class="assistant-welcome-text">
                Ask me about Python, SQL, Power BI, Excel,
                data analytics, or programming.
            </div>

        </div>
        """
    )


    # --------------------------------------------------------
    # QUICK PROMPTS
    # --------------------------------------------------------

    with st.container(key="quick_prompts"):

        prompt_col1, prompt_col2 = st.columns(
            2,
            gap="medium",
        )


        # ====================================================
        # LEFT COLUMN
        # ====================================================

        with prompt_col1:

            if st.button(
                "Explain pandas groupby()",
                use_container_width=True,
                key="welcome_groupby",
            ):

                st.session_state.pending_prompt = (
                    "Explain pandas groupby() with a simple example."
                )

                st.rerun()


            if st.button(
                "How do I create a KPI in Power BI?",
                use_container_width=True,
                key="welcome_kpi",
            ):

                st.session_state.pending_prompt = (
                    "How do I create a KPI card in Power BI? "
                    "Explain step by step."
                )

                st.rerun()


        # ====================================================
        # RIGHT COLUMN
        # ====================================================

        with prompt_col2:

            if st.button(
                "Explain SQL joins",
                use_container_width=True,
                key="welcome_sql",
            ):

                st.session_state.pending_prompt = (
                    "Explain SQL joins with simple examples."
                )

                st.rerun()


            if st.button(
                "How do I handle missing values?",
                use_container_width=True,
                key="welcome_missing",
            ):

                st.session_state.pending_prompt = (
                    "How should I handle missing values in a "
                    "dataset? Explain the different methods."
                )

                st.rerun()


# ============================================================
# CHAT INPUT
# ============================================================

user_prompt = st.chat_input(
    "Message DataMind AI..."
)


# ============================================================
# PENDING PROMPT
# ============================================================

if (
    not user_prompt
    and st.session_state.pending_prompt
):

    user_prompt = (
        st.session_state.pending_prompt
    )

    st.session_state.pending_prompt = None


# ============================================================
# PROCESS USER QUESTION
# ============================================================

if user_prompt:

    generate_answer(
        user_prompt
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.html(
    """
    <div style="
        text-align:center;
        padding: 12px 0 5px 0;
        color: #94a3b8;
        font-size:12px;
    ">
        DataMind AI
        &nbsp;&nbsp;|&nbsp;&nbsp;
        Intelligent Data Analytics Platform
        &nbsp;&nbsp;|&nbsp;&nbsp;
        Built with Streamlit and Groq
    </div>
    """
)

