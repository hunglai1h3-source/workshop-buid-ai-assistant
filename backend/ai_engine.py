import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import get_current_weather, calculate_expression
from rag_engine import search_document


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=GEMINI_API_KEY)


# Bộ nhớ hội thoại tạm thời
conversation_memory = []


def ask_ai(message: str):
    try:
        # Lưu câu hỏi của user
        conversation_memory.append({
            "role": "user",
            "content": message
        })

        # Chỉ giữ 10 tin nhắn gần nhất
        recent_memory = conversation_memory[-10:]

        # Ghép lịch sử hội thoại thành context
        history_text = ""

        for item in recent_memory:
            role = "Người dùng" if item["role"] == "user" else "Trợ lý"
            history_text += f"{role}: {item['content']}\n"

        # Tìm dữ liệu liên quan trong PDF bằng RAG
        rag_context = search_document(message)

        prompt = f"""
Bạn là một trợ lý AI thông minh.

Dưới đây là lịch sử hội thoại gần đây:

{history_text}

Dưới đây là dữ liệu được truy xuất từ tài liệu PDF:

--- TÀI LIỆU ---

{rag_context}

--- HẾT TÀI LIỆU ---

Câu hỏi mới nhất của người dùng:

{message}

Yêu cầu:
- Nếu câu hỏi liên quan đến tài liệu, ưu tiên trả lời dựa trên tài liệu.
- Không tự bịa thông tin không có trong tài liệu.
- Nếu tài liệu không đủ thông tin, hãy nói rõ.
- Có thể sử dụng Tool nếu cần.
- Trả lời bằng tiếng Việt rõ ràng.
"""

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[
                    get_current_weather,
                    calculate_expression,
                ],
                system_instruction="""
Bạn là một trợ lý AI thông minh.

Bạn cần:
- Ghi nhớ thông tin trong lịch sử hội thoại.
- Trả lời dựa trên bối cảnh các tin nhắn trước.
- Dùng get_current_weather khi người dùng hỏi thời tiết.
- Dùng calculate_expression khi người dùng yêu cầu tính toán.
- Trả lời bằng tiếng Việt, rõ ràng và dễ hiểu.
"""
            ),
        )

        reply = response.text

        # Lưu câu trả lời của AI
        conversation_memory.append({
            "role": "assistant",
            "content": reply
        })

        return reply

    except Exception as e:
        return f"Lỗi AI: {str(e)}"


def clear_memory():
    conversation_memory.clear()
    return True
def ask_ai_stream(message: str):
    try:
        # Lưu câu hỏi user
        conversation_memory.append({
            "role": "user",
            "content": message
        })

        # Lấy 10 tin nhắn gần nhất
        recent_memory = conversation_memory[-10:]

        history_text = ""

        for item in recent_memory:
            role = "Người dùng" if item["role"] == "user" else "Trợ lý"
            history_text += f"{role}: {item['content']}\n"

        # Truy xuất dữ liệu từ PDF
        rag_context = search_document(message)

        prompt = f"""
Bạn là một trợ lý AI thông minh.

LỊCH SỬ HỘI THOẠI:

{history_text}

DỮ LIỆU TRUY XUẤT TỪ PDF:

--- TÀI LIỆU ---

{rag_context}

--- HẾT TÀI LIỆU ---

CÂU HỎI MỚI NHẤT:

{message}

Yêu cầu:
- Ghi nhớ lịch sử hội thoại.
- Nếu câu hỏi liên quan tài liệu, ưu tiên dữ liệu trong tài liệu.
- Không tự bịa thông tin.
- Nếu cần tính toán hoặc thời tiết, có thể sử dụng Tool.
- Trả lời bằng tiếng Việt rõ ràng.
"""

        stream = client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[
                    get_current_weather,
                    calculate_expression,
                ],
                system_instruction="""
Bạn là một trợ lý AI thông minh.

Bạn có khả năng:
- Ghi nhớ hội thoại.
- Tra cứu tài liệu bằng RAG.
- Sử dụng Tool Calling.
- Trả lời bằng tiếng Việt.
"""
            ),
        )

        full_reply = ""

        for chunk in stream:
            if chunk.text:
                full_reply += chunk.text

                # Gửi từng phần ra ngoài
                yield chunk.text

        # Sau khi stream xong mới lưu vào Memory
        conversation_memory.append({
            "role": "assistant",
            "content": full_reply
        })

    except Exception as e:
        yield f"❌ Lỗi AI: {str(e)}"