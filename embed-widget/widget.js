(function () {

    const API_URL = "https://workshop-buid-ai-assistant.onrender.com";


    // =========================
    // 1. TẠO HOST + SHADOW DOM
    // =========================

    const host = document.createElement("div");

    host.id = "ai-assistant-widget-root";

    document.body.appendChild(host);


    const shadow = host.attachShadow({
        mode: "open"
    });


    // =========================
    // 2. CSS
    // =========================

    const style = document.createElement("style");

    style.textContent = `
        * {
            box-sizing: border-box;
        }

        .chat-bubble {
            position: fixed;
            right: 25px;
            bottom: 25px;

            width: 62px;
            height: 62px;

            border-radius: 50%;

            display: flex;
            align-items: center;
            justify-content: center;

            background:
                linear-gradient(
                    135deg,
                    #6366f1,
                    #4f46e5
                );

            color: white;

            font-size: 29px;

            cursor: pointer;

            box-shadow:
                0 12px 30px
                rgba(79, 70, 229, 0.45);

            z-index: 999999;

            transition: 0.25s;
        }


        .chat-bubble:hover {
            transform: scale(1.08);
        }


        .chat-window {
            position: fixed;

            right: 25px;
            bottom: 100px;

            width: 380px;
            height: 540px;

            display: none;
            flex-direction: column;

            overflow: hidden;

            border-radius: 20px;

            background: #111827;

            color: white;

            box-shadow:
                0 20px 60px
                rgba(0, 0, 0, 0.4);

            border:
                1px solid
                rgba(255, 255, 255, 0.12);

            z-index: 999999;

            font-family:
                Arial,
                Helvetica,
                sans-serif;
        }


        .chat-window.open {
            display: flex;
        }


        .header {
            padding: 16px;

            display: flex;
            align-items: center;
            justify-content: space-between;

            background: #1f2937;

            border-bottom:
                1px solid
                rgba(255, 255, 255, 0.1);
        }


        .header-title {
            font-weight: bold;
            font-size: 16px;
        }


        .header-subtitle {
            margin-top: 3px;

            font-size: 11px;

            color: #9ca3af;
        }


        .close-btn {
            cursor: pointer;

            font-size: 18px;

            padding: 5px;
        }


        .body {
            flex: 1;

            padding: 15px;

            overflow-y: auto;

            display: flex;
            flex-direction: column;

            gap: 12px;

            background: #111827;
        }


        .msg {
            max-width: 82%;

            padding: 10px 13px;

            border-radius: 14px;

            font-size: 14px;

            line-height: 1.5;

            white-space: pre-wrap;
        }


        .msg.user {
            align-self: flex-end;

            background: #4f46e5;

            color: white;

            border-bottom-right-radius: 4px;
        }


        .msg.assistant {
            align-self: flex-start;

            background: #374151;

            color: white;

            border-bottom-left-radius: 4px;
        }


        .footer {
            padding: 12px;

            display: flex;

            gap: 8px;

            background: #1f2937;

            border-top:
                1px solid
                rgba(255, 255, 255, 0.1);
        }


        .footer input {
            flex: 1;

            padding: 11px 12px;

            border-radius: 10px;

            border:
                1px solid #4b5563;

            outline: none;

            background: #111827;

            color: white;
        }


        .footer input::placeholder {
            color: #9ca3af;
        }


        .footer button {
            border: none;

            border-radius: 10px;

            padding: 10px 14px;

            background: #6366f1;

            color: white;

            font-weight: bold;

            cursor: pointer;
        }


        .footer button:disabled {
            opacity: 0.6;

            cursor: not-allowed;
        }


        @media (max-width: 500px) {

            .chat-window {
                width:
                    calc(100vw - 20px);

                height:
                    calc(100vh - 120px);

                right: 10px;

                bottom: 90px;
            }

            .chat-bubble {
                right: 15px;
                bottom: 15px;
            }

        }
    `;


    shadow.appendChild(style);


    // =========================
    // 3. HTML
    // =========================

    const container =
        document.createElement("div");


    container.innerHTML = `
        <div
            class="chat-bubble"
            id="toggleBtn"
            title="Mở AI Assistant"
        >
            🤖
        </div>


        <div
            class="chat-window"
            id="chatWindow"
        >

            <div class="header">

                <div>
                    <div class="header-title">
                        ✨ AI Assistant
                    </div>

                    <div class="header-subtitle">
                        Gemini + RAG + Memory
                    </div>
                </div>


                <div
                    class="close-btn"
                    id="closeBtn"
                >
                    ✕
                </div>

            </div>


            <div
                class="body"
                id="messageContainer"
            >

                <div class="msg assistant">
                    Xin chào! Tôi có thể giúp gì cho bạn trên trang web này?
                </div>

            </div>


            <div class="footer">

                <input
                    id="widgetInput"
                    type="text"
                    placeholder="Hỏi AI..."
                >

                <button id="sendBtn">
                    Gửi
                </button>

            </div>

        </div>
    `;


    shadow.appendChild(container);


    // =========================
    // 4. LẤY ELEMENT
    // =========================

    const toggleBtn =
        shadow.getElementById("toggleBtn");

    const closeBtn =
        shadow.getElementById("closeBtn");

    const chatWindow =
        shadow.getElementById("chatWindow");

    const messageContainer =
        shadow.getElementById(
            "messageContainer"
        );

    const input =
        shadow.getElementById(
            "widgetInput"
        );

    const sendBtn =
        shadow.getElementById(
            "sendBtn"
        );


    // =========================
    // 5. MỞ / ĐÓNG CHAT
    // =========================

    toggleBtn.onclick = function () {

        chatWindow.classList.toggle(
            "open"
        );


        if (
            chatWindow.classList.contains(
                "open"
            )
        ) {
            input.focus();
        }
    };


    closeBtn.onclick = function () {

        chatWindow.classList.remove(
            "open"
        );
    };


    // =========================
    // 6. THÊM MESSAGE
    // =========================

    function addMessage(
        role,
        text
    ) {

        const msg =
            document.createElement("div");


        msg.className =
            `msg ${role}`;


        msg.textContent =
            text;


        messageContainer.appendChild(
            msg
        );


        messageContainer.scrollTop =
            messageContainer.scrollHeight;


        return msg;
    }


    // =========================
    // 7. GỬI MESSAGE + STREAM
    // =========================

    async function sendMessage() {

        const text =
            input.value.trim();


        if (!text) {
            return;
        }


        addMessage(
            "user",
            text
        );


        input.value = "";

        sendBtn.disabled = true;


        const aiMessage =
            addMessage(
                "assistant",
                ""
            );


        // Lấy context trang hiện tại
        const pageContext = {
            url:
                window.location.href,

            title:
                document.title
        };


        try {

            const response =
                await fetch(
                    `${API_URL}/api/chat/stream`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify({
                                message: `
Thông tin trang hiện tại:

URL: ${pageContext.url}

Tiêu đề trang:
${pageContext.title}

Câu hỏi của người dùng:
${text}
`
                            })
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Server error: " +
                    response.status
                );

            }


            const reader =
                response.body.getReader();


            const decoder =
                new TextDecoder(
                    "utf-8"
                );


            let buffer = "";

            let fullText = "";


            while (true) {

                const {
                    value,
                    done
                } =
                    await reader.read();


                if (done) {
                    break;
                }


                buffer +=
                    decoder.decode(
                        value,
                        {
                            stream: true
                        }
                    );


                const events =
                    buffer.split(
                        "\n\n"
                    );


                buffer =
                    events.pop();


                for (
                    const event of events
                ) {

                    if (
                        !event.startsWith(
                            "data: "
                        )
                    ) {
                        continue;
                    }


                    const raw =
                        event
                            .substring(6)
                            .trim();


                    if (
                        raw === "[DONE]"
                    ) {
                        continue;
                    }


                    try {

                        const data =
                            JSON.parse(raw);


                        if (
                            data.type ===
                            "text_delta"
                        ) {

                            fullText +=
                                data.content;


                            aiMessage.textContent =
                                fullText;


                            messageContainer.scrollTop =
                                messageContainer
                                    .scrollHeight;

                        }

                    } catch (error) {

                        console.log(
                            "SSE parse error:",
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

            sendBtn.disabled =
                false;


            input.focus();

        }

    }


    // =========================
    // 8. EVENT
    // =========================

    sendBtn.onclick =
        sendMessage;


    input.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter"
            ) {

                sendMessage();

            }

        }
    );


})();