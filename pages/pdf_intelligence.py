import html
import streamlit as st
from pathlib import Path

from modules.pdf_processor import (
    extract_pdf_text,
    get_pdf_page_count,
    create_text_chunks,
)

from modules.embeddings import (
    create_embeddings,
    semantic_search,
)

from modules.ai_insights import (
    answer_pdf_question,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PDF Intelligence | DataMind AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# LOAD CUSTOM CSS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
CSS_PATH = BASE_DIR / "styles" / "main.css"

if CSS_PATH.exists():
    try:
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            css = f.read()

        st.html(f"<style>{css}</style>")

    except Exception:
        pass


# ============================================================
# ADDITIONAL DATAMIND AI LIGHT THEME STYLES
# ============================================================

st.html(
    """
    <style>

    /* ========================================================
       PDF INTELLIGENCE LIGHT THEME
       ======================================================== */

    .pdf-card {
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 22px;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.08);
    }

    .pdf-soft-card {
        background: linear-gradient(
            135deg,
            rgba(237, 233, 254, 0.75),
            rgba(207, 250, 254, 0.55)
        );
        border: 1px solid #ddd6fe;
        border-radius: 18px;
        padding: 18px;
    }

    .pdf-section-title {
        color: #1e293b;
        font-weight: 800;
        font-size: 20px;
        margin-bottom: 5px;
    }

    .pdf-section-subtitle {
        color: #64748b;
        font-size: 13px;
        line-height: 1.6;
    }

    .pdf-label {
        color: #7c3aed;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    .pdf-stat-value {
        color: #1e293b;
        font-size: 25px;
        font-weight: 800;
        line-height: 1.1;
    }

    .pdf-stat-label {
        color: #64748b;
        font-size: 12px;
        margin-top: 6px;
    }

    .pdf-status {
        display: inline-flex;
        align-items: center;
        padding: 7px 13px;
        border-radius: 999px;
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        color: #047857;
        font-size: 12px;
        font-weight: 700;
    }

    .pdf-status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10b981;
        margin-right: 7px;
    }

    .pdf-feature-title {
        color: #1e293b;
        font-size: 15px;
        font-weight: 750;
        margin-top: 4px;
    }

    .pdf-feature-text {
        color: #64748b;
        font-size: 12px;
        line-height: 1.6;
        margin-top: 5px;
    }

    .pdf-answer-card {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #ddd6fe;
        border-radius: 18px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.07);
    }

    .pdf-page-card {
        background: linear-gradient(
            135deg,
            #ffffff,
            #f5f3ff
        );
        border: 1px solid #ddd6fe;
        border-radius: 15px;
        padding: 13px;
        text-align: center;
    }

    </style>
    """
)


# ============================================================
# SESSION STATE
# ============================================================

if "pdf_pages" not in st.session_state:
    st.session_state["pdf_pages"] = []

if "pdf_chunks" not in st.session_state:
    st.session_state["pdf_chunks"] = []

if "pdf_name" not in st.session_state:
    st.session_state["pdf_name"] = None

if "pdf_upload_signature" not in st.session_state:
    st.session_state["pdf_upload_signature"] = None

if "pdf_answer" not in st.session_state:
    st.session_state["pdf_answer"] = None

if "pdf_sources" not in st.session_state:
    st.session_state["pdf_sources"] = []

if "pdf_relevant_chunks" not in st.session_state:
    st.session_state["pdf_relevant_chunks"] = []

if "pdf_question_value" not in st.session_state:
    st.session_state["pdf_question_value"] = ""

if "pdf_selected_page" not in st.session_state:
    st.session_state["pdf_selected_page"] = 1


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def process_pdf(uploaded_pdf):
    """Extract, chunk and store a PDF."""

    pages = extract_pdf_text(uploaded_pdf)

    page_count = get_pdf_page_count(uploaded_pdf)

    chunks = create_text_chunks(pages)

    st.session_state["pdf_pages"] = pages
    st.session_state["pdf_chunks"] = chunks
    st.session_state["pdf_name"] = uploaded_pdf.name

    st.session_state["pdf_upload_signature"] = (
        uploaded_pdf.name,
        uploaded_pdf.size,
    )

    st.session_state["pdf_answer"] = None
    st.session_state["pdf_sources"] = []
    st.session_state["pdf_relevant_chunks"] = []
    st.session_state["pdf_selected_page"] = 1
    st.session_state["pdf_question_value"] = ""

    return pages, page_count, chunks


def reset_pdf():
    """Reset all PDF-related session state."""

    st.session_state["pdf_pages"] = []
    st.session_state["pdf_chunks"] = []
    st.session_state["pdf_name"] = None
    st.session_state["pdf_upload_signature"] = None
    st.session_state["pdf_answer"] = None
    st.session_state["pdf_sources"] = []
    st.session_state["pdf_relevant_chunks"] = []
    st.session_state["pdf_selected_page"] = 1
    st.session_state["pdf_question_value"] = ""


def get_document_stats(pages, chunks):
    """Calculate document statistics."""

    total_characters = sum(
        len(page.get("text", ""))
        for page in pages
    )

    total_words = sum(
        len(page.get("text", "").split())
        for page in pages
    )

    total_chunks = len(chunks)

    readable_pages = sum(
        1
        for page in pages
        if page.get("text", "").strip()
    )

    return (
        total_characters,
        total_words,
        total_chunks,
        readable_pages,
    )


def display_stat_card(label, value):
    """Display a DataMind AI styled statistic card."""

    st.html(
        f"""
        <div class="pdf-card"
             style="
                min-height:105px;
                padding:18px;
                margin-bottom:8px;
             ">

            <div class="pdf-stat-value">
                {value}
            </div>

            <div class="pdf-stat-label">
                {label}
            </div>

        </div>
        """
    )


def ask_pdf_ai(question):
    """Search the PDF and generate an AI answer."""

    chunks = st.session_state.get(
        "pdf_chunks",
        [],
    )

    if not chunks:
        st.warning(
            "No searchable text was found in this PDF."
        )
        return False

    if not question.strip():
        st.warning(
            "Please enter a question first."
        )
        return False

    try:

        with st.spinner(
            "Searching the document..."
        ):

            relevant_chunks = semantic_search(
                question,
                chunks,
                top_k=5,
            )

        if not relevant_chunks:

            st.warning(
                "No relevant information was found in the document."
            )

            return False

        with st.spinner(
            "DataMind AI is analyzing the document..."
        ):

            result = answer_pdf_question(
                question,
                relevant_chunks,
            )

        if not isinstance(result, dict):

            st.error(
                "The AI response returned an unexpected format."
            )

            return False

        st.session_state["pdf_answer"] = result.get(
            "answer",
            "No answer was generated.",
        )

        st.session_state["pdf_sources"] = result.get(
            "sources",
            [],
        )

        st.session_state["pdf_relevant_chunks"] = (
            relevant_chunks
        )

        return True

    except Exception as e:

        st.error(
            f"Error while analyzing PDF: {e}"
        )

        return False


# ============================================================
# PREMIUM HERO
# ============================================================

st.html(
    """
    <div class="hero"
         style="
            margin-bottom:24px;
         ">

        <div style="
            display:inline-flex;
            align-items:center;
            padding:6px 12px;
            border-radius:999px;
            background:rgba(124,58,237,0.07);
            border:1px solid #ddd6fe;
            color:#6d28d9;
            font-size:13px;
            font-weight:600;
            margin-bottom:14px;
        ">
            AI-Powered Document Intelligence
        </div>

        <div class="hero-title">
            PDF Intelligence
        </div>

        <div class="hero-subtitle">
            Upload a document, extract its content,
            search it semantically, and ask DataMind AI
            questions using intelligent document understanding.
        </div>

        <div style="
            display:flex;
            flex-wrap:wrap;
            gap:9px;
            margin-top:18px;
            font-size:12px;
        ">

            <span style="
                padding:7px 11px;
                border-radius:999px;
                background:#ede9fe;
                border:1px solid #ddd6fe;
                color:#6d28d9;
            ">
                Upload
            </span>

            <span style="
                padding:7px 11px;
                border-radius:999px;
                background:#ecfeff;
                border:1px solid #a5f3fc;
                color:#0e7490;
            ">
                Extract
            </span>

            <span style="
                padding:7px 11px;
                border-radius:999px;
                background:#eef2ff;
                border:1px solid #c7d2fe;
                color:#4338ca;
            ">
                Search
            </span>

            <span style="
                padding:7px 11px;
                border-radius:999px;
                background:#f5f3ff;
                border:1px solid #ddd6fe;
                color:#7c3aed;
            ">
                Ask AI
            </span>

        </div>

    </div>
    """
)


# ============================================================
# UPLOAD DOCUMENT (MAIN AREA)
# ============================================================
# Moved out of the sidebar so it's the first thing the user
# interacts with in the middle of the page, not tucked away
# on the side.

st.html(
    """
    <div class="pdf-label" style="margin-bottom:6px;">
        STEP 1
    </div>
    """
)

st.markdown("### Upload Document")

upload_col, status_col = st.columns([2, 1])

with upload_col:

    uploaded_pdf = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help=(
            "Upload a text-based PDF document "
            "for extraction and AI analysis."
        ),
        label_visibility="collapsed",
    )

with status_col:

    if st.session_state.get("pdf_name"):

        st.success("Document Ready")
        st.caption(st.session_state["pdf_name"])

        if st.button(
            "Remove Document",
            use_container_width=True,
            key="remove_document_main",
        ):

            reset_pdf()
            st.rerun()

    else:

        st.info("No PDF uploaded yet.")

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.html(
        """
        <div style="
            padding:8px 0 16px 0;
        ">

            <div style="
                font-size:25px;
                font-weight:800;
                color:#1e293b;
            ">
                PDF Intelligence
            </div>

            <div style="
                font-size:12px;
                color:#64748b;
                margin-top:4px;
            ">
                Understand documents with AI
            </div>

        </div>
        """
    )

    st.divider()

    # ========================================================
    # CURRENT DOCUMENT
    # ========================================================

    st.subheader("Current Document")

    if st.session_state.get("pdf_name"):

        st.success(
            "Document Ready"
        )

        st.caption(
            st.session_state["pdf_name"]
        )

        if st.button(
            "Remove Document",
            use_container_width=True,
            key="remove_document_sidebar",
        ):

            reset_pdf()
            st.rerun()

    else:

        st.info(
            "No PDF uploaded yet."
        )

    st.divider()

    # ========================================================
    # WORKFLOW
    # ========================================================

    st.subheader("Workflow")

    st.markdown(
        """
        **1.** Upload PDF

        **2.** Extract text

        **3.** Create chunks

        **4.** Semantic search

        **5.** Ask AI

        **6.** Review sources
        """
    )

    st.divider()

    st.caption(
        "DataMind AI | PDF Intelligence"
    )


# ============================================================
# PROCESS UPLOADED PDF
# ============================================================

if uploaded_pdf is not None:

    current_signature = (
        uploaded_pdf.name,
        uploaded_pdf.size,
    )

    if (
        st.session_state.get(
            "pdf_upload_signature"
        )
        != current_signature
    ):

        try:

            with st.spinner(
                "Reading and indexing your PDF..."
            ):

                pages, page_count, chunks = (
                    process_pdf(uploaded_pdf)
                )

            st.success(
                f"{uploaded_pdf.name} is ready for analysis."
            )

        except Exception as e:

            st.error(
                f"Error processing PDF: {e}"
            )


# ============================================================
# GET CURRENT DOCUMENT
# ============================================================

pages = st.session_state.get(
    "pdf_pages",
    [],
)

chunks = st.session_state.get(
    "pdf_chunks",
    [],
)

pdf_name = st.session_state.get(
    "pdf_name",
)

pdf_answer = st.session_state.get(
    "pdf_answer",
)

pdf_sources = st.session_state.get(
    "pdf_sources",
    [],
)

relevant_chunks = st.session_state.get(
    "pdf_relevant_chunks",
    [],
)


# ============================================================
# EMPTY STATE
# ============================================================

if not pdf_name:

    st.html(
        """
        <div class="pdf-card"
             style="
                text-align:center;
                padding:50px 25px;
                margin-top:10px;
             ">

            <div style="
                width:62px;
                height:62px;
                margin:0 auto 18px auto;
                border-radius:18px;
                background:linear-gradient(
                    135deg,
                    #ede9fe,
                    #cffafe
                );
                border:1px solid #ddd6fe;
                display:flex;
                align-items:center;
                justify-content:center;
                color:#7c3aed;
                font-size:24px;
                font-weight:800;
            ">
                PDF
            </div>

            <div style="
                color:#1e293b;
                font-size:25px;
                font-weight:800;
                margin-bottom:9px;
            ">
                Your document workspace is ready
            </div>

            <div style="
                max-width:650px;
                margin:auto;
                color:#64748b;
                line-height:1.7;
            ">
                Upload a PDF above to extract its text,
                search through its content, and ask DataMind AI
                questions about the document.
            </div>

        </div>
        """
    )

    st.markdown("### What you can do")

    feature_col1, feature_col2, feature_col3 = st.columns(3)

    with feature_col1:

        st.html(
            """
            <div class="pdf-soft-card">

                <div class="pdf-label">
                    DOCUMENT
                </div>

                <div class="pdf-feature-title">
                    Extract Text
                </div>

                <div class="pdf-feature-text">
                    Extract readable content from your PDF
                    page by page.
                </div>

            </div>
            """
        )

    with feature_col2:

        st.html(
            """
            <div class="pdf-soft-card">

                <div class="pdf-label">
                    RETRIEVAL
                </div>

                <div class="pdf-feature-title">
                    Semantic Search
                </div>

                <div class="pdf-feature-text">
                    Find relevant information using intelligent
                    document search.
                </div>

            </div>
            """
        )

    with feature_col3:

        st.html(
            """
            <div class="pdf-soft-card">

                <div class="pdf-label">
                    INTELLIGENCE
                </div>

                <div class="pdf-feature-title">
                    Ask AI
                </div>

                <div class="pdf-feature-text">
                    Ask natural-language questions and receive
                    document-grounded answers.
                </div>

            </div>
            """
        )

    st.divider()

    st.html(
        """
        <div style="
            text-align:center;
            padding:10px;
            color:#94a3b8;
            font-size:12px;
        ">
            DataMind AI | Intelligent Document Analysis
        </div>
        """
    )

    st.stop()


# ============================================================
# DOCUMENT HEADER
# ============================================================

safe_pdf_name = html.escape(
    str(pdf_name)
)

st.html(
    f"""
    <div class="pdf-card"
         style="
            padding:18px 20px;
            margin-bottom:20px;
         ">

        <div style="
            display:flex;
            align-items:center;
            gap:14px;
        ">

            <div style="
                width:48px;
                height:48px;
                border-radius:14px;
                display:flex;
                align-items:center;
                justify-content:center;
                background:#ede9fe;
                border:1px solid #ddd6fe;
                color:#7c3aed;
                font-size:12px;
                font-weight:800;
            ">
                PDF
            </div>

            <div style="flex:1;">

                <div style="
                    color:#1e293b;
                    font-size:18px;
                    font-weight:800;
                ">
                    {safe_pdf_name}
                </div>

                <div style="
                    color:#64748b;
                    font-size:12px;
                    margin-top:3px;
                ">
                    Document successfully indexed and ready
                    for intelligent search
                </div>

            </div>

            <div class="pdf-status">
                <span class="pdf-status-dot"></span>
                Ready
            </div>

        </div>

    </div>
    """
)


# ============================================================
# DOCUMENT STATISTICS
# ============================================================

(
    total_characters,
    total_words,
    total_chunks,
    readable_pages,
) = get_document_stats(
    pages,
    chunks,
)


try:

    page_count = (
        get_pdf_page_count(uploaded_pdf)
        if uploaded_pdf is not None
        else len(pages)
    )

except Exception:

    page_count = len(pages)


st.markdown("### Document Overview")

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:

    display_stat_card(
        "Total Pages",
        f"{page_count:,}",
    )

with stat_col2:

    display_stat_card(
        "Total Words",
        f"{total_words:,}",
    )

with stat_col3:

    display_stat_card(
        "Search Chunks",
        f"{total_chunks:,}",
    )

with stat_col4:

    display_stat_card(
        "Readable Pages",
        f"{readable_pages:,}",
    )


# ============================================================
# TABS
# ============================================================

tab_document, tab_ask, tab_sources = st.tabs(
    [
        "Document",
        "Ask AI",
        "Sources",
    ]
)


# ============================================================
# DOCUMENT TAB
# ============================================================

with tab_document:

    st.markdown("### Extracted Document")

    if not pages:

        st.warning(
            "No readable text was found in this PDF."
        )

        st.info(
            "This may be a scanned or image-based PDF. "
            "OCR support can be added later."
        )

    else:

        page_numbers = list(
            range(1, len(pages) + 1)
        )

        selected_page = st.selectbox(
            "Select a page to inspect",
            page_numbers,
            index=min(
                st.session_state.get(
                    "pdf_selected_page",
                    1
                ) - 1,
                len(page_numbers) - 1,
            ),
            format_func=lambda x: f"Page {x}",
        )

        st.session_state["pdf_selected_page"] = selected_page

        selected_page_data = pages[
            selected_page - 1
        ]

        page_text = selected_page_data.get(
            "text",
            "",
        )

        st.html(
            f"""
            <div class="pdf-soft-card"
                 style="
                    padding:14px 18px;
                    margin:12px 0;
                 ">

                <div style="
                    color:#1e293b;
                    font-weight:700;
                    font-size:14px;
                ">
                    Page {selected_page}
                </div>

                <div style="
                    color:#64748b;
                    font-size:12px;
                    margin-top:3px;
                ">
                    Extracted text
                </div>

            </div>
            """
        )

        if page_text.strip():

            st.text_area(
                "Extracted content",
                page_text,
                height=470,
                label_visibility="collapsed",
            )

        else:

            st.warning(
                f"No readable text was extracted from page "
                f"{selected_page}."
            )

        # ----------------------------------------------------
        # PAGE NAVIGATION
        # ----------------------------------------------------

        if len(pages) > 1:

            nav1, nav2 = st.columns(2)

            with nav1:

                if selected_page > 1:

                    if st.button(
                        "Previous Page",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "pdf_selected_page"
                        ] = selected_page - 1

                        st.rerun()

            with nav2:

                if selected_page < len(pages):

                    if st.button(
                        "Next Page",
                        use_container_width=True,
                    ):

                        st.session_state[
                            "pdf_selected_page"
                        ] = selected_page + 1

                        st.rerun()

    st.divider()

    # ========================================================
    # DOCUMENT PIPELINE
    # ========================================================

    st.markdown("### Document Processing")

    pipeline_col1, pipeline_col2, pipeline_col3 = (
        st.columns(3)
    )

    with pipeline_col1:

        st.html(
            """
            <div class="pdf-soft-card">

                <div class="pdf-label">
                    STEP 01
                </div>

                <div class="pdf-feature-title">
                    Text Extraction
                </div>

                <div class="pdf-feature-text">
                    Document text extracted page by page.
                </div>

            </div>
            """
        )

    with pipeline_col2:

        st.html(
            """
            <div class="pdf-soft-card">

                <div class="pdf-label">
                    STEP 02
                </div>

                <div class="pdf-feature-title">
                    Text Chunking
                </div>

                <div class="pdf-feature-text">
                    Content divided into searchable chunks.
                </div>

            </div>
            """
        )

    with pipeline_col3:

        st.html(
            """
            <div class="pdf-soft-card">

                <div class="pdf-label">
                    STEP 03
                </div>

                <div class="pdf-feature-title">
                    Semantic Retrieval
                </div>

                <div class="pdf-feature-text">
                    Relevant content retrieved for AI answers.
                </div>

            </div>
            """
        )


# ============================================================
# ASK AI TAB
# ============================================================

with tab_ask:

    st.markdown("### Ask DataMind AI")

    st.write(
        "Ask questions about the contents of your PDF. "
        "DataMind AI searches relevant document sections "
        "before generating an answer."
    )

    st.html(
        """
        <div class="pdf-soft-card"
             style="
                padding:14px 17px;
                margin:15px 0;
             ">

            <div style="
                color:#1e293b;
                font-weight:700;
                margin-bottom:5px;
            ">
                Document-grounded AI
            </div>

            <div style="
                color:#64748b;
                font-size:12px;
                line-height:1.6;
            ">
                Answers are generated using relevant content
                retrieved from your uploaded document.
            </div>

        </div>
        """
    )

    # ========================================================
    # QUICK QUESTIONS
    # ========================================================

    st.markdown("#### Quick Questions")

    quick_col1, quick_col2, quick_col3 = st.columns(3)

    quick_questions = [
        "What is this document mainly about?",
        "Summarize the key points.",
        "What are the main conclusions?",
    ]

    with quick_col1:

        if st.button(
            "Main Topic",
            use_container_width=True,
        ):

            st.session_state[
                "pdf_question_value"
            ] = quick_questions[0]

            st.rerun()

    with quick_col2:

        if st.button(
            "Key Points",
            use_container_width=True,
        ):

            st.session_state[
                "pdf_question_value"
            ] = quick_questions[1]

            st.rerun()

    with quick_col3:

        if st.button(
            "Conclusions",
            use_container_width=True,
        ):

            st.session_state[
                "pdf_question_value"
            ] = quick_questions[2]

            st.rerun()

    # ========================================================
    # QUESTION
    # ========================================================

    question_value = st.session_state.get(
        "pdf_question_value",
        "",
    )

    question = st.text_area(
        "Your question",
        value=question_value,
        placeholder=(
            "Example: What is the main conclusion "
            "of this document?"
        ),
        height=110,
        key="pdf_question_box",
    )

    if st.button(
        "Ask DataMind AI",
        type="primary",
        use_container_width=True,
        key="ask_pdf_ai_premium",
    ):

        success = ask_pdf_ai(question)

        if success:

            st.session_state[
                "pdf_question_value"
            ] = ""

            st.rerun()

    # ========================================================
    # ANSWER
    # ========================================================

    if pdf_answer:

        st.divider()

        st.html(
            """
            <div style="
                margin:10px 0 12px 0;
            ">

                <div class="pdf-label">
                    AI RESPONSE
                </div>

                <div style="
                    color:#1e293b;
                    font-size:20px;
                    font-weight:800;
                    margin-top:4px;
                ">
                    AI Answer
                </div>

                <div style="
                    color:#64748b;
                    font-size:11px;
                    margin-top:3px;
                ">
                    Based on retrieved document content
                </div>

            </div>
            """
        )

        st.markdown(
            pdf_answer
        )

        if pdf_sources:

            st.markdown("#### Referenced Pages")

            source_cols = st.columns(
                min(len(pdf_sources), 5)
            )

            for index, page in enumerate(
                pdf_sources
            ):

                with source_cols[
                    index % len(source_cols)
                ]:

                    st.html(
                        f"""
                        <div class="pdf-page-card">

                            <div style="
                                color:#7c3aed;
                                font-size:11px;
                                font-weight:800;
                                letter-spacing:1px;
                            ">
                                SOURCE
                            </div>

                            <div style="
                                color:#1e293b;
                                font-weight:700;
                                margin-top:5px;
                            ">
                                Page {page}
                            </div>

                        </div>
                        """
                    )

    else:

        st.html(
            """
            <div class="pdf-card"
                 style="
                    text-align:center;
                    padding:35px 20px;
                    margin-top:20px;
                 ">

                <div class="pdf-label">
                    DOCUMENT Q&A
                </div>

                <div style="
                    color:#1e293b;
                    font-size:18px;
                    font-weight:700;
                    margin-top:6px;
                ">
                    Ask your first question
                </div>

                <div style="
                    color:#64748b;
                    font-size:12px;
                    margin-top:6px;
                ">
                    DataMind AI will search your document
                    and generate a grounded answer.
                </div>

            </div>
            """
        )


# ============================================================
# SOURCES TAB
# ============================================================

with tab_sources:

    st.markdown("### Retrieved Document Sources")

    if not relevant_chunks:

        st.info(
            "Sources will appear here after you ask a question."
        )

    else:

        st.write(
            f"Showing {len(relevant_chunks)} relevant "
            "document sections."
        )

        for index, chunk in enumerate(
            relevant_chunks,
            start=1,
        ):

            page = chunk.get(
                "page",
                "?",
            )

            text = chunk.get(
                "text",
                "",
            )

            with st.expander(
                f"Source {index} | Page {page}",
                expanded=index == 1,
            ):

                st.markdown(
                    f"**Source page:** {page}"
                )

                st.write(text)

                if index < len(
                    relevant_chunks
                ):

                    st.divider()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.html(
    """
    <div style="
        text-align:center;
        padding:14px 0 5px 0;
        color:#94a3b8;
        font-size:12px;
    ">
        DataMind AI
        &nbsp;|&nbsp;
        Intelligent PDF Analysis
        &nbsp;|&nbsp;
        Built with Streamlit + AI
    </div>
    """
)