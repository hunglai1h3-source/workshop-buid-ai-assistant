import os
from pathlib import Path

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "data" / "company_policy.pdf"
CHROMA_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "company_policy"

embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)


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

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def ingest_pdf():
    if not PDF_PATH.exists():
        return {
            "success": False,
            "message": f"Không tìm thấy PDF: {PDF_PATH}"
        }

    # Nếu đã có dữ liệu rồi thì không thêm lại
    if collection.count() > 0:
        return {
            "success": True,
            "message": "PDF đã được đưa vào ChromaDB trước đó.",
            "chunks": collection.count()
        }

    text = read_pdf(PDF_PATH)

    if not text.strip():
        return {
            "success": False,
            "message": "Không đọc được nội dung PDF."
        }

    chunks = chunk_text(text)

    embeddings = embedding_model.encode(
        chunks
    ).tolist()

    ids = [
        f"chunk_{i}"
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings
    )

    return {
        "success": True,
        "message": "Đã đưa PDF vào ChromaDB.",
        "chunks": len(chunks)
    }


def search_document(query: str, top_k=3):
    if collection.count() == 0:
        ingest_pdf()

    query_embedding = embedding_model.encode(
        [query]
    ).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    documents = results.get("documents", [])

    if not documents:
        return ""

    docs = documents[0]

    context = "\n\n---\n\n".join(docs)

    return context