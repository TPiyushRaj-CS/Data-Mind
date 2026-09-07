from pypdf import PdfReader
import re


def extract_pdf_text(uploaded_file):

    reader = PdfReader(uploaded_file)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text()

        if text:

            pages.append({
                "page": page_number,
                "text": text
            })

    return pages


def get_pdf_page_count(uploaded_file):

    reader = PdfReader(uploaded_file)

    return len(reader.pages)


def create_text_chunks(
    pages,
    chunk_size=1200,
    overlap=200
):

    chunks = []

    for page in pages:

        page_number = page["page"]

        text = page["text"]

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        if not text:
            continue

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk_text = text[start:end]

            if chunk_text.strip():

                chunks.append({
                    "page": page_number,
                    "text": chunk_text
                })

            start += chunk_size - overlap

    return chunks