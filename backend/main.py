import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from ai_engine import ask_ai, ask_ai_stream, clear_memory
from rag_engine import ingest_pdf 


app = FastAPI(
    title="AI Assistant Workshop",
    description="AI Assistant sử dụng FastAPI + Gemini",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {
        "status": "success",
        "message": "AI Assistant Server đang hoạt động",
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        reply = ask_ai(request.message)

        return {
            "success": True,
            "message": request.message,
            "reply": reply,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
@app.delete("/api/memory")
def delete_memory():
    clear_memory()

    return {
        "success": True,
        "message": "Đã xóa bộ nhớ hội thoại"
    }
@app.post("/api/rag/ingest")
def rag_ingest():
    try:
        return ingest_pdf()
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):

    def event_generator():

        for text_chunk in ask_ai_stream(request.message):

            data = json.dumps(
                {
                    "type": "text_delta",
                    "content": text_chunk
                },
                ensure_ascii=False
            )

            yield f"data: {data}\n\n"

        yield "data: [DONE]\n\n"


    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )