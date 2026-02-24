console.log("Meubles RD Chatbot UI loaded");

document.addEventListener("DOMContentLoaded", () => {

    const analyzeBtn = document.getElementById("analyzeBtn");
    const resultDiv = document.getElementById("result");
    const chatInput = document.getElementById("chatInput");
    const sendMessageBtn = document.getElementById("sendMessageBtn");

    const username = "A01796151";
    const password = "tecdemonterrey";
    const credentials = btoa(`${username}:${password}`);

    /* =========================
       CHAT UI HELPERS
    ========================== */

    function addMessage(text, sender = "assistant") {
        const msg = document.createElement("div");
        msg.classList.add("chat-message", sender);
        msg.innerHTML = text;

        resultDiv.appendChild(msg);
        resultDiv.scrollTop = resultDiv.scrollHeight;
    }

    function showTyping() {
        const typing = document.createElement("div");
        typing.classList.add("chat-message", "assistant");
        typing.id = "typingIndicator";
        typing.innerHTML = "Typing...";
        resultDiv.appendChild(typing);
        resultDiv.scrollTop = resultDiv.scrollHeight;
    }

    function removeTyping() {
        const typing = document.getElementById("typingIndicator");
        if (typing) typing.remove();
    }

    function formatDateForBackend(dateTimeString) {
        if (!dateTimeString) return null;
        return dateTimeString.split(" ")[0];
    }

    function clearWelcomeState() {
        if (resultDiv.innerHTML.includes("Click")) {
            resultDiv.innerHTML = "";
        }
    }

    /* =========================
       ANALYZE SCREEN
    ========================== */

    analyzeBtn.addEventListener("click", async () => {

        clearWelcomeState();
        addMessage("Analyzing current case...", "assistant");
        showTyping();

        try {
            const [tab] = await chrome.tabs.query({
                active: true,
                currentWindow: true
            });

            chrome.tabs.sendMessage(tab.id, { action: "extractData" }, async (response) => {

                removeTyping();

                if (chrome.runtime.lastError) {
                    addMessage("Error extracting ticket data.", "assistant");
                    return;
                }

                if (!response) {
                    addMessage("No data received from page.", "assistant");
                    return;
                }

                console.log("Raw Extracted Data:", response);

                const payload = {
                    //claim_type: response.fields?.classification || "",
                    //damage_type: response.fields?.damageType || "",
                    //delivery_date: formatDateForBackend(response.fields?.date || ""),
                    //product_type: response.fields?.productType || "",
                    //manufacturer: response.fields?.manufacturer || "",
                    //store_of_purchase: response.fields?.store || "",
                    //product_code: response.fields?.productCode || "",
                    //description: response.fields?.description || "",
                    //has_attachments: true,
                    //contract_number: response.fields?.contract || "",
                    //claim_date: formatDateForBackend(response.fields?.openDate || ""),
                    //eligible: true
"claim_type": "Defective, damaged product(s) or missing part(s)",
  "damage_type": "Mechanical or Structural",
  "delivery_date": "2025-12-15",
  "product_type": "Furniture",
  "manufacturer": "Ashley Furniture",
  "store_of_purchase": "MueblesRD Santo Domingo",
  "product_code": "ASH-TBL-4521",
  "description": "The dining table leg snapped off during normal use two weeks after delivery.",
  "has_attachments": true,
  "contract_number": "CN-2025-34567",
  "claim_date": "2025-12-30",
  "eligible": true
                };

                console.log("Formatted Payload:", payload);

                showTyping();

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

                handleSuccessfulResponse(result);
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
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendChatMessage();
    });

    async function sendChatMessage() {

        const message = chatInput.value.trim();
        if (!message) return;

        addMessage(message, "user");
        chatInput.value = "";
        showTyping();

        try {
            const response = await fetch(
                "https://api.gac.asware.com.mx/api/chat/", 
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Basic ${credentials}`
                    },
                    body: JSON.stringify({ query: message })
                }
            );

            const data = await response.json();
            removeTyping();
console.log("Chat raw response:", data);

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

   /* ✅ Format assistant response */
        let formattedMessage = `
            ${data.answer}
        `;

        if (data.sources && data.sources.length > 0) {
            formattedMessage += `<br><br><strong>Sources:</strong><ul>`;
            data.sources.forEach(source => {
                formattedMessage += `<li>${source}</li>`;
            });
            formattedMessage += `</ul>`;
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
                    message += `<li><b>${field.replaceAll("_", " ")}</b>: ${msg}</li>`;
                });
            }
        } else {
            message += "<li>Invalid input.</li>";
        }

        message += "</ul>";

        addMessage(message, "assistant");
    }

    function handleSuccessfulResponse(data) {

        const summary = data.claim_summary;
        const decision = data.final_eligibility;

        let message = `
            <strong>🧾 Claim Summary</strong><br>
            Claim Type: ${summary.claim_type}<br>
            Product: ${summary.product_type}<br>
            Manufacturer: ${summary.manufacturer}<br><br>

            <strong>🎯 Final Decision:</strong><br>
            ${decision.isEligible ? "🟢 Eligible" : "🔴 Not Eligible"}<br><br>

            ${decision.justification}<br><br>

            <strong>📌 Recommendation:</strong><br>
            ${data.final_recommendation}
        `;

        addMessage(message, "assistant");
    }

});
