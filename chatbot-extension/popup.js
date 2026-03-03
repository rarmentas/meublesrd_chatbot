console.log("Meubles RD Chatbot UI loaded");

const WINDOW_FULL = { width: 400, height: 620 };
const WINDOW_MIN = { width: 240, height: 48 };

document.addEventListener("DOMContentLoaded", async () => {

    let currentTicketContext = null;

    const analyzeBtn = document.getElementById("analyzeBtn");
    const resultDiv = document.getElementById("result");
    const chatInput = document.getElementById("chatInput");
    const sendMessageBtn = document.getElementById("sendMessageBtn");
    const autoLoadSwitch = document.getElementById("autoLoadSwitch");
    const mainContent = document.getElementById("mainContent");
    const headerBar = document.querySelector(".header-bar");
    const minimizedBar = document.getElementById("minimizedBar");
    const minimizeBtn = document.getElementById("minimizeBtn");
    const restoreBtn = document.getElementById("restoreBtn");

    /* Minimizar solo cuando es ventana popup (no en Side Panel) */
    if (minimizeBtn && restoreBtn && typeof chrome !== "undefined" && chrome.windows) {
        chrome.windows.getCurrent((win) => {
            if (win && win.type === "popup") {
                minimizeBtn.style.display = "block";
                minimizeBtn.addEventListener("click", () => {
                    chrome.windows.update(win.id, WINDOW_MIN);
                    if (headerBar) headerBar.style.display = "none";
                    if (mainContent) mainContent.style.display = "none";
                    if (minimizedBar) minimizedBar.style.display = "flex";
                });
                restoreBtn.addEventListener("click", () => {
                    chrome.windows.update(win.id, WINDOW_FULL);
                    if (headerBar) headerBar.style.display = "flex";
                    if (mainContent) mainContent.style.display = "block";
                    if (minimizedBar) minimizedBar.style.display = "none";
                });
            } else {
                if (minimizeBtn) minimizeBtn.style.display = "none";
                if (minimizedBar) minimizedBar.style.display = "none";
            }
        });
    } else if (minimizeBtn) {
        minimizeBtn.style.display = "none";
    }

    /* =========================
       AUTO-LOAD SWITCH (storage local)
    ========================== */
    const storage = await chrome.storage.local.get("automatic_loading");
    const automaticLoading = storage.automatic_loading !== false;
    if (autoLoadSwitch) {
        if (automaticLoading) {
            autoLoadSwitch.classList.add("on");
            autoLoadSwitch.setAttribute("aria-checked", "true");
        } else {
            autoLoadSwitch.classList.remove("on");
            autoLoadSwitch.setAttribute("aria-checked", "false");
        }
        autoLoadSwitch.addEventListener("click", () => {
            const isOn = autoLoadSwitch.classList.toggle("on");
            chrome.storage.local.set({ automatic_loading: isOn });
            autoLoadSwitch.setAttribute("aria-checked", String(isOn));
        });
    }

    const username = "A01796151";
    const password = "tecdemonterrey";
    const credentials = btoa(`${username}:${password}`);

    /* Historial de conversación para el chat (user + assistant) */
    const conversationHistory = [];

    /* =========================
       CHAT UI HELPERS
    ========================== */

    /**
     * Convierte markdown básico a HTML para mostrar correctamente negritas, cursivas, etc.
     */
    function markdownToHtml(text) {
        if (!text || typeof text !== "string") return "";
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
        html = html
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.+?)\*/g, "<em>$1</em>")
            .replace(/__(.+?)__/g, "<strong>$1</strong>")
            .replace(/_(.+?)_/g, "<em>$1</em>")
            .replace(/`(.+?)`/g, "<code>$1</code>")
            .replace(/\n/g, "<br>");
        return html;
    }

    function addMessage(text, sender = "assistant", formatMarkdown = true) {
        const msg = document.createElement("div");
        msg.classList.add("chat-message", "chat-bubble", sender);
        if (sender === "user") {
            const escaped = (text || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
            msg.innerHTML = escaped;
        } else {
            msg.innerHTML = formatMarkdown ? markdownToHtml(text) : text;
        }
        resultDiv.appendChild(msg);
        resultDiv.scrollTop = resultDiv.scrollHeight;
    }

    function showTyping(message = "Analyzing...") {
        const typing = document.createElement("div");
        typing.classList.add("chat-message", "assistant", "loading-spinner");
        typing.id = "typingIndicator";
        typing.innerHTML = `<span class="spinner"></span>${message}`;
        resultDiv.appendChild(typing);
        resultDiv.scrollTop = resultDiv.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById("typingIndicator");
        if (typing) typing.remove();
    }

    /**
     * Convierte fecha extraída del DOM a formato ISO YYYY-MM-DD para el backend.
     */
    function formatDateForBackend(dateTimeString) {
        if (!dateTimeString || typeof dateTimeString !== "string") return null;
        const trimmed = dateTimeString.trim();
        if (!trimmed) return null;
        const spacePart = trimmed.split(" ")[0];
        if (spacePart && /^\d{4}-\d{2}-\d{2}$/.test(spacePart)) return spacePart;
        const match = trimmed.match(/(\d{4})-(\d{2})-(\d{2})/);
        if (match) return match[0];
        const ddmmyy = trimmed.match(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})/);
        if (ddmmyy) {
            const [, d, m, y] = ddmmyy;
            const year = y.length === 2 ? `20${y}` : y;
            return `${year}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
        }
        return spacePart || trimmed;
    }

    function clearWelcomeState() {
        if (resultDiv.innerHTML.includes("Click")) {
            resultDiv.innerHTML = "";
        }
    }

    /**
     * Formatea los campos extraídos del DOM para mostrarlos en la UI.
     */
    function formatExtractedFields(fields) {
        const labels = {
            subject: "Subject",
            classification: "Classification",
            priority: "Priority",
            status: "Status",
            description: "Description",
            caseNumber: "Case number",
            caseOwner: "Case owner",
            store: "Store",
            account: "Account name",
            date: "Delivery date",
            maccount: "Meublex customer account number",
            damageType: "Damage type",
            productType: "Product type",
            productCode: "Product code",
            contract: "Purchase contract number",
            manufacturer: "Manufacturer",
            openDate: "Open date"
        };
        let html = "<strong>📋 Extracted fields</strong><br><ul style='margin:8px 0; font-size:12px; max-height:200px; overflow-y:auto;'>";
        for (const [key, label] of Object.entries(labels)) {
            const val = fields[key];
            const raw = (val && String(val).trim()) ? String(val).trim() : "";
            const display = raw ? raw.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;") : "<em>(empty)</em>";
            html += `<li><b>${label}:</b> ${display}</li>`;
        }
        html += "</ul>";
        return html;
    }

    /* =========================
       ANALYZE SCREEN
    ========================== */

    analyzeBtn.addEventListener("click", async () => {

        clearWelcomeState();
        showTyping("Analyzing current case...");

        try {
            /* Buscar pestañas del mockup (la ventana del assistant no tiene tabs, currentWindow no sirve) */
            const mockupTabs = await chrome.tabs.query({
                url: "https://mockup.gac.asware.com.mx/*"
            });
            const tab = mockupTabs.length > 0
                ? (mockupTabs.find(t => t.active) || mockupTabs[0])
                : null;

            console.log("[MeublesRD] Tab mockup:", tab?.url, "| id:", tab?.id, "| encontrados:", mockupTabs.length);

            if (!tab?.url?.startsWith("https://mockup.gac.asware.com.mx")) {
                const msg = `Open a tab at mockup.gac.asware.com.mx and try again.`;
                console.warn("[MeublesRD]", msg);
                addMessage(`⚠ ${msg}`, "assistant", false);
                removeTyping();
                return;
            }

            /* Inyectar content script si no está cargado (p. ej. tras actualizar extensión sin recargar la pestaña) */
            try {
                await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
            } catch (injectErr) {
                console.warn("[MeublesRD] Inject script (puede estar ya cargado):", injectErr?.message);
            }

            chrome.tabs.sendMessage(tab.id, { action: "extractData" }, async (response) => {

                removeTyping();

                if (chrome.runtime.lastError) {
                    const errMsg = chrome.runtime.lastError.message || "Unknown error";
                    console.error("[MeublesRD] Error al extraer datos:", errMsg);
                    const hint = errMsg.includes("Receiving end") || errMsg.includes("connection")
                        ? " Reload the page (F5) and try again."
                        : "";
                    addMessage(`Error extracting ticket data.<br><small>${errMsg}${hint}</small>`, "assistant", false);
                    return;
                }

                if (!response) {
                    addMessage("No data received from page.", "assistant");
                    return;
                }

                console.log("Raw Extracted Data:", response);

                const fields = response.fields || {};

                currentTicketContext = fields;

                const payload = {
                    claim_type: fields.classification || "",
                    damage_type: fields.damageType || "",
                    delivery_date: formatDateForBackend(fields.date || ""),
                    product_type: fields.productType || "",
                    manufacturer: fields.manufacturer || "",
                    store_of_purchase: fields.store || "",
                    product_code: fields.productCode || "",
                    description: fields.description || "",
                    has_attachments: false,
                    contract_number: fields.contract || "",
                    claim_date: formatDateForBackend(fields.openDate || ""),
                    eligible: false
                };

                console.log("Formatted Payload:", payload);

                /* Mostrar campos extraídos antes de enviar al backend */
                const extractedHtml = formatExtractedFields(fields);
                addMessage(extractedHtml, "assistant", false);

                showTyping("Processing...");

                const backendResponse = await fetch(
                    "https://api.gac.asware.com.mx/api/agent-feedback/",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Basic ${credentials}`
                        },
                        body: JSON.stringify(payload)
                    }
                );

                const rawText = await backendResponse.text();
                removeTyping();

                let result;
                try {
                    result = JSON.parse(rawText);
                } catch {
                    result = rawText;
                }

                if (!backendResponse.ok) {
                    handleValidationError(result);
                    return;
                }

                handleSuccessfulResponse(result, payload);
            });

        } catch (error) {
            removeTyping();
            addMessage("Unexpected error occurred.", "assistant");
            console.error(error);
        }
    });

    /* =========================
       SEND CHAT MESSAGE
    ========================== */

    sendMessageBtn.addEventListener("click", sendChatMessage);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    async function sendChatMessage() {

        const message = chatInput.value.trim();
        if (!message) return;

        addMessage(message, "user");
        chatInput.value = "";
        conversationHistory.push({ role: "user", content: message });
        showTyping("Thinking...");

        try {
            /* Construir query con toda la conversación y con datos del ticket para chat efectivo */
            let caseContextBlock = "";

	    if (currentTicketContext) {
    		caseContextBlock = `
	    Current Case Information:
	    - Subject: ${currentTicketContext.subject || ""}
	    - Classification: ${currentTicketContext.classification || ""}
	    - Damage Type: ${currentTicketContext.damageType || ""}
	    - Delivery Date: ${currentTicketContext.date || ""}
	    - Open Date: ${currentTicketContext.openDate || ""}
	    - Manufacturer: ${currentTicketContext.manufacturer || ""}
	    - Product Code: ${currentTicketContext.productCode || ""}
	    - Store: ${currentTicketContext.store || ""}
	    - Description: ${currentTicketContext.description || ""}

	    `;
	    }

	    const conversationText = conversationHistory.length > 1
    	    ? conversationHistory.map(m =>
        	    m.role === "user" ? `User: ${m.content}` : `Assistant: ${m.content}`
    	    ).join("\n\n")
    	    : message;

	    const queryWithHistory = `
	    You are assisting a service agent analyzing a customer claim.

	    ${caseContextBlock}

	    Conversation:
	    ${conversationText}

	    User question:
	    ${message}
	    `;

            const response = await fetch(
                "https://api.gac.asware.com.mx/api/chat/", 
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Basic ${credentials}`
                    },
                    body: JSON.stringify({ query: queryWithHistory })
                }
            );

            const data = await response.json();
            removeTyping();

            if (!response.ok) {
                addMessage(`⚠ Backend error ${response.status}`, "assistant");
                return;
            }

            if (!data) {
                addMessage("⚠ Empty response from server.", "assistant");
                return;
            }

            if (data.error) {
                addMessage(`⚠ ${data.error}`, "assistant");
                return;
            }

            if (!data.answer) {
                addMessage("⚠ Unexpected response format.", "assistant");
                console.log("Unexpected format:", data);
                return;
            }

            conversationHistory.push({ role: "assistant", content: data.answer });

            let formattedMessage = data.answer;

            if (data.sources && data.sources.length > 0) {
                formattedMessage += `\n\n**Sources:**\n`;
                data.sources.forEach(source => {
                    formattedMessage += `- ${source}\n`;
                });
            }

            addMessage(formattedMessage, "assistant");

        } catch (error) {
            removeTyping();
            addMessage("Error communicating with assistant.", "assistant");
        }
    }

    /* =========================
       RESPONSE HANDLERS
    ========================== */

    function handleValidationError(result) {

        let message = "<strong>⚠ Validation Issues Found:</strong><br><ul>";

        if (result?.details) {
            for (const [field, messages] of Object.entries(result.details)) {
                messages.forEach(msg => {
                    const escaped = String(msg).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                    message += `<li><b>${String(field).replaceAll("_", " ")}</b>: ${escaped}</li>`;
                });
            }
        } else {
            message += "<li>Invalid input.</li>";
        }

        message += "</ul>";

        addMessage(message, "assistant", false);
    }

    function handleSuccessfulResponse(data, extractedPayload = {}) {

        const summary = data.claim_summary;
        const decision = data.final_eligibility;

        /* Los textos del backend pueden venir en markdown - formatear antes de insertar */
        const justification = markdownToHtml(decision.justification || "");
        const recommendation = markdownToHtml(data.final_recommendation || "");

        /* Descripción del caso (extraída del frontend, no viene en claim_summary del backend) */
        const desc = (extractedPayload.description || "").trim();
        const descriptionBlock = desc
            ? `<br><b>Description:</b><br><span style="font-size:12px; display:block; margin-top:4px; padding:8px; background:#f8f9fa; border-radius:4px; max-height:120px; overflow-y:auto;">${markdownToHtml(desc)}</span><br>`
            : "";

        let message = `
            <strong>🧾 Claim Summary</strong><br>
            Claim Type: ${summary.claim_type}<br>
            Product: ${summary.product_type}<br>
            Manufacturer: ${summary.manufacturer}${descriptionBlock}<br>

            <strong>🎯 Final Decision:</strong><br>
            ${decision.isEligible ? "🟢 Eligible" : "🔴 Not Eligible"}<br><br>

            ${justification}<br><br>

            <strong>📌 Recommendation:</strong><br>
            ${recommendation}
        `;

        addMessage(message, "assistant", false);
    }

    /* Auto-analyze al abrir la extensión si automatic_loading está activo */
    if (automaticLoading && analyzeBtn) {
        setTimeout(() => analyzeBtn.click(), 150);
    }

});
