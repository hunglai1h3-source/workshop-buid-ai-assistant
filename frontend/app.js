const API_URL = "http://127.0.0.1:8000";

const chatBody = document.getElementById("chatBody");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");


function addMessage(role, text) {
    const message = document.createElement("div");

    message.className = `message ${role}`;


    const avatar = document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent =
        role === "user" ? "👤" : "🤖";


    const content = document.createElement("div");

    content.className = "message-content";

    content.textContent = text;


    message.appendChild(avatar);

    message.appendChild(content);


    chatBody.appendChild(message);


    chatBody.scrollTop =
        chatBody.scrollHeight;


    return content;
}


async function sendMessage() {
    const text = messageInput.value.trim();

    if (!text) {
        return;
    }


    // Hiện câu hỏi của user
    addMessage("user", text);

    messageInput.value = "";

    sendBtn.disabled = true;


    // Tạo ô trả lời AI
    const aiMessage = addMessage(
        "assistant",
        ""
    );


    try {
        const response = await fetch(
            `${API_URL}/api/chat/stream`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: text
                })
            }
        );


        if (!response.ok) {
            throw new Error(
                "Server trả về lỗi " + response.status
            );
        }


        const reader = response.body.getReader();

        const decoder = new TextDecoder("utf-8");

        let buffer = "";

        let fullText = "";


        while (true) {
            const {
                value,
                done
            } = await reader.read();


            if (done) {
                break;
            }


            buffer += decoder.decode(
                value,
                {
                    stream: true
                }
            );


            const events = buffer.split("\n\n");

            // Giữ lại đoạn event chưa hoàn chỉnh
            buffer = events.pop();


            for (const event of events) {
                if (!event.startsWith("data: ")) {
                    continue;
                }


                const dataText =
                    event.substring(6).trim();


                if (dataText === "[DONE]") {
                    continue;
                }


                try {
                    const data =
                        JSON.parse(dataText);


                    if (
                        data.type === "text_delta"
                    ) {
                        fullText += data.content;

                        aiMessage.textContent =
                            fullText;


                        chatBody.scrollTop =
                            chatBody.scrollHeight;
                    }

                } catch (error) {
                    console.log(
                        "Không parse được SSE:",
                        error
                    );
                }
            }
        }


        if (!fullText) {
            aiMessage.textContent =
                "AI không trả về nội dung.";
        }


    } catch (error) {
        console.error(error);

        aiMessage.textContent =
            "❌ Không kết nối được AI Server.";

    } finally {
        sendBtn.disabled = false;

        messageInput.focus();
    }
}


sendBtn.addEventListener(
    "click",
    sendMessage
);


messageInput.addEventListener(
    "keydown",
    function(event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    }
);


clearBtn.addEventListener(
    "click",
    async function() {
        try {
            await fetch(
                `${API_URL}/api/memory`,
                {
                    method: "DELETE"
                }
            );


            chatBody.innerHTML = "";


            addMessage(
                "assistant",
                "Đã xóa lịch sử hội thoại. Bạn có thể bắt đầu cuộc trò chuyện mới."
            );

        } catch (error) {
            alert(
                "Không thể xóa bộ nhớ."
            );
        }
    }
);