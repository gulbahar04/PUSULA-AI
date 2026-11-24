
// ==========================================
// PUSULA-AI | FRONTEND APPLICATION
// ==========================================

const API_BASE = "";

// DOM ELEMENTS
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("question");
const chatArea = document.getElementById("chat");
const welcomeScreen = document.getElementById("welcomeScreen");

const traceContainer = document.getElementById("trace");
const sourceUsed = document.getElementById("sourceUsed");

const newChatButton = document.getElementById("newChat");

const uploadModal = document.getElementById("uploadModal");
const openUploadButton = document.getElementById("openUpload");
const closeUploadButton = document.getElementById("closeUpload");
const uploadButton = document.getElementById("uploadBtn");

const adminKeyInput = document.getElementById("adminKey");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");

const sendButton = chatForm.querySelector(".send-button");


// ==========================================
// CHAT MESSAGE FUNCTIONS
// ==========================================



function addMessage(content, sender) {
    const message = document.createElement("div");
    message.className = `message ${sender}`;

    if (sender === "assistant") {
        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "AI";
        message.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    if (sender === "assistant") {
        // Markdown metnini HTML'e dönüştür
        const parsedHTML = marked.parse(String(content ?? ""));

        // Güvenli HTML olarak temizle
        bubble.innerHTML = DOMPurify.sanitize(parsedHTML);

        // Kod bloklarına kopyalama butonu ekle
        bubble.querySelectorAll("pre").forEach((pre) => {
            const copyButton = document.createElement("button");

            copyButton.className = "copy-code-btn";
            copyButton.type = "button";
            copyButton.innerHTML = "⧉";
            copyButton.title = "Kodu kopyala";
            copyButton.setAttribute("aria-label", "Kodu kopyala");

            copyButton.addEventListener("click", async () => {
                const code = pre.querySelector("code");

                const codeText = code
                    ? code.textContent
                    : pre.textContent;

                try {
                    await navigator.clipboard.writeText(codeText);

                    copyButton.innerHTML = "✓";
                    copyButton.title = "Kopyalandı";

                    setTimeout(() => {
                        copyButton.innerHTML = "⧉";
                        copyButton.title = "Kodu kopyala";
                    }, 2000);

                } catch (error) {
                    copyButton.innerHTML = "!";
                    copyButton.title = "Kopyalama başarısız";
                }
            });

            pre.appendChild(copyButton);
        });

        bubble.classList.add("markdown-content");

    } else {
        // Kullanıcı mesajlarını düz metin olarak göster
        bubble.textContent = String(content ?? "");
    }

    message.appendChild(bubble);
    chatArea.appendChild(message);

    chatArea.scrollTop = chatArea.scrollHeight;

    return message;
}




function showTrace(trace) {
    traceContainer.replaceChildren();

    if (!Array.isArray(trace) || trace.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "Bu istek için işlem detayı bulunamadı.";
        traceContainer.appendChild(empty);
        return;
    }

    trace.forEach((step) => {
        const item = document.createElement("div");
        item.className = "trace-item";

        if (typeof step === "string") {
            item.textContent = step;
        } else {
            item.textContent = JSON.stringify(step);
        }

        traceContainer.appendChild(item);
    });
}


function resetTrace() {
    traceContainer.replaceChildren();

    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Henüz bir istek yapılmadı.";

    traceContainer.appendChild(empty);
    sourceUsed.textContent = "—";
}


// ==========================================
// CHAT API
// ==========================================

async function sendMessage(question) {
    const cleanedQuestion = question.trim();

    if (!cleanedQuestion) return;

    // Karşılama ekranını kaldır
    if (welcomeScreen) {
        welcomeScreen.remove();
    }

    addMessage(cleanedQuestion, "user");

    questionInput.value = "";
    questionInput.disabled = true;
    sendButton.disabled = true;

    const loadingMessage = addMessage(
        "Yanıt hazırlanıyor...",
        "assistant"
    );

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: cleanedQuestion
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "İstek işlenemedi."
            );
        }

        // Yükleniyor mesajını kaldır
        loadingMessage.remove();

        // Asistan yanıtı
        addMessage(
            data.answer || "Yanıt oluşturulamadı.",
            "assistant"
        );

        // Agent işlem geçmişi
        showTrace(data.trace);

        // Yanıt kaynağı
        sourceUsed.textContent = data.source_used || "Bilinmiyor";

    } catch (error) {
        loadingMessage.remove();

        addMessage(
            `Bir hata oluştu: ${error.message}`,
            "assistant"
        );

        showTrace([
            "İstek sırasında hata meydana geldi.",
            error.message
        ]);

        sourceUsed.textContent = "Hata";
    } finally {
        questionInput.disabled = false;
        sendButton.disabled = false;
        questionInput.focus();
    }
}


// Form gönderimi
chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(questionInput.value);
});


// Enter ile gönder, Shift + Enter ile yeni satır
questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});


// Yazdıkça textarea yüksekliğini ayarla
questionInput.addEventListener("input", () => {
    questionInput.style.height = "auto";

    questionInput.style.height =
        `${Math.min(questionInput.scrollHeight, 150)}px`;
});


// Örnek sorular
document.querySelectorAll(".example").forEach((button) => {
    button.addEventListener("click", () => {
        questionInput.value = button.textContent.trim();
        questionInput.focus();
    });
});


// ==========================================
// NEW CHAT
// ==========================================

newChatButton.addEventListener("click", () => {
    chatArea.replaceChildren();

    // Karşılama ekranını tekrar göster
    const newWelcome = document.createElement("div");
    newWelcome.className = "welcome-screen";
    newWelcome.id = "welcomeScreen";

    const badge = document.createElement("div");
    badge.className = "welcome-badge";
    badge.textContent = "PUSULA-AI";

    const heading = document.createElement("h1");
    heading.append(
        document.createTextNode("Size nasıl yardımcı ")
    );

    const headingAccent = document.createElement("span");
    headingAccent.textContent = "olabilirim?";
    heading.appendChild(headingAccent);

    const description = document.createElement("p");
    description.textContent =
        "Şirketinizin IT destek süreçleri için sorularınızı buradan iletebilirsiniz.";

    const suggestions = document.createElement("div");
    suggestions.className = "suggestion-list";

    const examples = [
        "Şirket VPN ağına nasıl bağlanırım?",
        "Parola sıfırlama politikamız nedir?",
        "Microsoft Teams bağlantı sorunu"
    ];

    examples.forEach((text) => {
        const button = document.createElement("button");
        button.className = "example";
        button.type = "button";
        button.textContent = text;

        button.addEventListener("click", () => {
            questionInput.value = text;
            questionInput.focus();
        });

        suggestions.appendChild(button);
    });

    newWelcome.append(
        badge,
        heading,
        description,
        suggestions
    );

    chatArea.appendChild(newWelcome);

    questionInput.value = "";
    questionInput.disabled = false;

    resetTrace();
    questionInput.focus();
});


// ==========================================
// DOCUMENT UPLOAD MODAL
// ==========================================

openUploadButton.addEventListener("click", () => {
    uploadModal.classList.remove("hidden");
});

closeUploadButton.addEventListener("click", () => {
    uploadModal.classList.add("hidden");
});


// Modal dışına tıklayınca kapat
uploadModal.addEventListener("click", (event) => {
    if (event.target === uploadModal) {
        uploadModal.classList.add("hidden");
    }
});


// ==========================================
// DOCUMENT INGESTION API
// ==========================================

uploadButton.addEventListener("click", async () => {
    const adminKey = adminKeyInput.value.trim();
    const file = fileInput.files[0];

    uploadStatus.textContent = "";

    if (!adminKey) {
        uploadStatus.textContent =
            "Lütfen yönetici API anahtarını girin.";
        return;
    }

    if (!file) {
        uploadStatus.textContent =
            "Lütfen bir doküman seçin.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadButton.disabled = true;
    uploadButton.textContent = "Yükleniyor...";

    try {
        const response = await fetch(`${API_BASE}/api/ingest`, {
            method: "POST",
            headers: {
                "X-Admin-Key": adminKey
            },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Doküman yüklenemedi."
            );
        }

        uploadStatus.textContent =
            `${data.message} İndekslenen parça: ${data.chunks}`;

        fileInput.value = "";

    } catch (error) {
        uploadStatus.textContent =
            `Hata: ${error.message}`;
    } finally {
        uploadButton.disabled = false;
        uploadButton.textContent = "Dokümanı indeksle";
    }
});


// ==========================================
// INITIALIZATION
// ==========================================

resetTrace();

console.log("PUSULA-AI frontend hazır.");


// ==========================================
// RESIZABLE SIDEBARS
// ==========================================

const appShell = document.getElementById("appShell");

const leftSidebar = document.getElementById("leftSidebar");
const rightSidebar = document.getElementById("rightSidebar");

const leftResize = document.getElementById("leftResize");
const rightResize = document.getElementById("rightResize");

const leftToggle = document.getElementById("leftToggle");
const leftOpen = document.getElementById("leftOpen");

const rightToggle = document.getElementById("rightToggle");
const rightClose = document.getElementById("rightClose");

const MIN_LEFT = 170;
const MAX_LEFT = 420;

const MIN_RIGHT = 200;
const MAX_RIGHT = 420;

// Varsayılan genişlikler
const DEFAULT_LEFT = 245;
const DEFAULT_RIGHT = 285;


// Genişlikleri uygula
function setSidebarWidth(side, width, save = true) {
    const isLeft = side === "left";

    const min = isLeft ? MIN_LEFT : MIN_RIGHT;
    const max = isLeft ? MAX_LEFT : MAX_RIGHT;

    const safeWidth = Math.min(max, Math.max(min, width));

    const variable = isLeft
        ? "--sidebar-width"
        : "--right-width";

    appShell.style.setProperty(
        variable,
        `${safeWidth}px`
    );

    if (save) {
        localStorage.setItem(
            `pusula-${side}-width`,
            safeWidth
        );
    }
}


// Panel görünürlüğünü değiştir
function setSidebarVisibility(side, visible, save = true) {
    const className = side === "left"
        ? "left-collapsed"
        : "right-collapsed";

    appShell.classList.toggle(
        className,
        !visible
    );

    if (save) {
        localStorage.setItem(
            `pusula-${side}-visible`,
            String(visible)
        );
    }
}


// Panel görünürlüğünü değiştir
function toggleSidebar(side) {
    const className = side === "left"
        ? "left-collapsed"
        : "right-collapsed";

    const currentlyVisible =
        !appShell.classList.contains(className);

    setSidebarVisibility(side, !currentlyVisible);
}


// Sürükleme işlemi
function enableResize(handle, side) {
    let isDragging = false;

    handle.addEventListener("pointerdown", (event) => {
        if (window.innerWidth <= 700) return;

        isDragging = true;

        handle.setPointerCapture(event.pointerId);
        document.body.classList.add("is-resizing");

        event.preventDefault();
    });

    handle.addEventListener("pointermove", (event) => {
        if (!isDragging) return;

        const rect = appShell.getBoundingClientRect();

        let width;

        if (side === "left") {
            width = event.clientX - rect.left;
        } else {
            width = rect.right - event.clientX;
        }

        setSidebarWidth(side, width);
    });

    function stopDragging() {
        isDragging = false;
        document.body.classList.remove("is-resizing");
    }

    handle.addEventListener("pointerup", stopDragging);
    handle.addEventListener("pointercancel", stopDragging);
}


// Sol panel kontrolleri
leftToggle.addEventListener("click", () => {
    toggleSidebar("left");
});

leftOpen.addEventListener("click", () => {
    setSidebarVisibility("left", true);
});


// Sağ panel kontrolleri
rightToggle.addEventListener("click", () => {
    toggleSidebar("right");
});

rightClose.addEventListener("click", () => {
    setSidebarVisibility("right", false);
});


// Sürükleme kontrolleri
enableResize(leftResize, "left");
enableResize(rightResize, "right");


// ==========================================
// RESTORE SAVED SIDEBAR SETTINGS
// ==========================================

function initializeSidebarSettings() {
    const savedLeftWidth = Number(
        localStorage.getItem("pusula-left-width")
    );

    const savedRightWidth = Number(
        localStorage.getItem("pusula-right-width")
    );

    const savedLeftVisible =
        localStorage.getItem("pusula-left-visible");

    const savedRightVisible =
        localStorage.getItem("pusula-right-visible");

    setSidebarWidth(
        "left",
        savedLeftWidth || DEFAULT_LEFT,
        false
    );

    setSidebarWidth(
        "right",
        savedRightWidth || DEFAULT_RIGHT,
        false
    );

    if (savedLeftVisible !== null) {
        setSidebarVisibility(
            "left",
            savedLeftVisible === "true",
            false
        );
    }

    if (savedRightVisible !== null) {
        setSidebarVisibility(
            "right",
            savedRightVisible === "true",
            false
        );
    }
}

initializeSidebarSettings();

