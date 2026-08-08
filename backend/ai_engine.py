import os
import json

from dotenv import load_dotenv
from groq import Groq

from tools import get_current_weather, calculate_expression
from rag_engine import search_document


load_dotenv()


# =========================
# CẤU HÌNH GROQ
# =========================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


if not GROQ_API_KEY:
    raise ValueError(
        "Chưa cấu hình GROQ_API_KEY trong file .env"
    )


client = Groq(
    api_key=GROQ_API_KEY
)


# =========================
# MEMORY
# =========================

conversation_memory = []


# =========================
# TOOL DEFINITIONS
# =========================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Lấy thông tin thời tiết hiện tại của một địa điểm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Tên thành phố hoặc địa điểm"
                    }
                },
                "required": ["location"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "calculate_expression",
            "description": "Thực hiện một phép tính toán học.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Biểu thức toán học cần tính"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


# =========================
# THỰC THI TOOL
# =========================

def execute_tool(tool_name, arguments):

    if tool_name == "get_current_weather":

        return get_current_weather(
            arguments.get("location", "")
        )


    if tool_name == "calculate_expression":

        return calculate_expression(
            arguments.get("expression", "")
        )


    return "Không tìm thấy công cụ."


# =========================
# TẠO CONTEXT
# =========================

def build_messages(message: str):

    # Lưu câu hỏi user vào memory
    conversation_memory.append({
        "role": "user",
        "content": message
    })


    # Chỉ giữ 10 tin nhắn gần nhất
    recent_memory = conversation_memory[-10:]


    history_text = ""

    for item in recent_memory:

        role = (
            "Người dùng"
            if item["role"] == "user"
            else "Trợ lý"
        )

        history_text += (
            f"{role}: {item['content']}\n"
        )


    # RAG
    rag_context = search_document(message)


    system_prompt = """
Bạn là một trợ lý AI thông minh.

Bạn có các khả năng:
- Ghi nhớ lịch sử hội thoại.
- Tra cứu tài liệu bằng RAG.
- Sử dụng công cụ tính toán.
- Sử dụng công cụ thời tiết.
- Trả lời bằng tiếng Việt rõ ràng và dễ hiểu.

Quy tắc:
- Nếu câu hỏi liên quan đến tài liệu, ưu tiên dữ liệu trong tài liệu.
- Không tự bịa thông tin không có trong tài liệu.
- Nếu tài liệu không đủ thông tin, hãy nói rõ.
- Khi cần tính toán, hãy dùng calculate_expression.
- Khi người dùng hỏi thời tiết, hãy dùng get_current_weather.
"""


    user_prompt = f"""
LỊCH SỬ HỘI THOẠI:

{history_text}


DỮ LIỆU TRUY XUẤT TỪ PDF:

--- TÀI LIỆU ---

{rag_context}

--- HẾT TÀI LIỆU ---


CÂU HỎI MỚI NHẤT:

{message}
"""


    return [
        {
            "role": "system",
            "content": system_prompt
        },

        {
            "role": "user",
            "content": user_prompt
        }
    ]


# =========================
# CHAT KHÔNG STREAM
# =========================

def ask_ai(message: str):

    try:

        messages = build_messages(message)


        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )


        assistant_message = (
            response
            .choices[0]
            .message
        )


        # =========================
        # NẾU GROQ GỌI TOOL
        # =========================

        if assistant_message.tool_calls:

            messages.append(
                assistant_message
            )


            for tool_call in assistant_message.tool_calls:

                tool_name = (
                    tool_call
                    .function
                    .name
                )


                arguments = json.loads(
                    tool_call
                    .function
                    .arguments
                )


                tool_result = execute_tool(
                    tool_name,
                    arguments
                )


                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })


            # Gửi kết quả Tool lại Groq
            final_response = (
                client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages
                )
            )


            reply = (
                final_response
                .choices[0]
                .message
                .content
            )


        else:

            reply = (
                assistant_message.content
                or ""
            )


        conversation_memory.append({
            "role": "assistant",
            "content": reply
        })


        return reply


    except Exception as e:

        return f"Lỗi AI: {str(e)}"


# =========================
# CHAT STREAMING
# =========================

def ask_ai_stream(message: str):

    try:

        messages = build_messages(message)


        # Lần đầu gọi không stream
        # để kiểm tra Groq có muốn gọi Tool không
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto"
        )


        assistant_message = (
            response
            .choices[0]
            .message
        )


        # =========================
        # TOOL CALLING
        # =========================

        if assistant_message.tool_calls:

            messages.append(
                assistant_message
            )


            for tool_call in assistant_message.tool_calls:

                tool_name = (
                    tool_call
                    .function
                    .name
                )


                arguments = json.loads(
                    tool_call
                    .function
                    .arguments
                )


                tool_result = execute_tool(
                    tool_name,
                    arguments
                )


                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })


        else:

            # Không có Tool
            # bỏ response đầu và stream lại
            pass


        # =========================
        # STREAM CÂU TRẢ LỜI CUỐI
        # =========================

        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            stream=True
        )


        full_reply = ""


        for chunk in stream:

            delta = (
                chunk
                .choices[0]
                .delta
                .content
            )


            if delta:

                full_reply += delta

                yield delta


        conversation_memory.append({
            "role": "assistant",
            "content": full_reply
        })


    except Exception as e:

        yield f"❌ Lỗi AI: {str(e)}"


# =========================
# XÓA MEMORY
# =========================

def clear_memory():

    conversation_memory.clear()

    return True