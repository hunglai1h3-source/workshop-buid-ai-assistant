from pathlib import Path
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "data" / "company_policy.pdf"

document_chunks = []


def read_pdf(pdf_path: Path):

    reader = PdfReader(str(pdf_path))

    full_text = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:
            full_text += text + "\n"

    return full_text


def chunk_text(text: str, chunk_size=500, overlap=100):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunks.append(text[start:end])

        start += chunk_size - overlap

    return chunks


def ingest_pdf():

    global document_chunks

    if not PDF_PATH.exists():

        return {
            "success": False,
            "message": f"Không tìm thấy PDF: {PDF_PATH}"
        }

    text = read_pdf(PDF_PATH)

    if not text.strip():

        return {
            "success": False,
            "message": "Không đọc được nội dung PDF."
        }

    document_chunks = chunk_text(text)

    return {
        "success": True,
        "message": "Đã đọc PDF thành công.",
        "chunks": len(document_chunks)
    }


def search_document(query: str, top_k=3):

    global document_chunks

    if not document_chunks:
        ingest_pdf()

    if not document_chunks:
        return ""

    query_words = set(query.lower().split())

    scored_chunks = []

    for chunk in document_chunks:

        chunk_lower = chunk.lower()

        score = sum(
            1
            for word in query_words
            if word in chunk_lower
        )

        scored_chunks.append(
            (score, chunk)
        )

    scored_chunks.sort(
        key=lambda x: x[0],
        reverse=True
    )

    best_chunks = [
        chunk
        for score, chunk in scored_chunks[:top_k]
        if score > 0
    ]

    if not best_chunks:
        return ""

    return "\n\n---\n\n".join(best_chunks)