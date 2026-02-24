console.log("Content script successfully injected.");

console.log("MeublesRD Assistant content script loaded.");

/** Valores a ignorar: la página repite campos con "Not used for copilot" en secciones resumidas */
const SKIP_VALUES = ["Not used for copilot", ""];

/**
 * Extract ticket main fields.
 * Si hay varios rows con el mismo label, prefiere el que tenga contenido real (no "Not used for copilot").
 */
function getFieldValue(labelText) {
    const rows = document.querySelectorAll('.field-row');

    for (let row of rows) {
        const label = row.querySelector('.field-label')?.innerText?.trim();
        if (label !== labelText) continue;

        const rowClone = row.cloneNode(true);
        rowClone.querySelector('.field-label')?.remove();
        rowClone.querySelectorAll('i').forEach(el => el.remove());
        const valueText = rowClone.innerText.trim();

        if (!valueText || SKIP_VALUES.includes(valueText)) continue;
        return valueText;
    }
    return "";
}

function extractFields() {
    return {
        subject: getFieldValue("Subject"),
        classification: getFieldValue("Classification"),
        priority: getFieldValue("Priority"),
        status: getFieldValue("Status"),
        description: getFieldValue("Description"),
	caseNumber: getFieldValue("Case number"),
	caseOwner: getFieldValue("Case owner"),
	store: getFieldValue("Store"),
	account: getFieldValue("Account name"),
	date: getFieldValue("Delivery date"),
	maccount: getFieldValue("Meublex customer account number"),
        damageType: getFieldValue("Damage type"),
        productType: getFieldValue("Product type"),
        productCode: getFieldValue("Product code"),
        contract: getFieldValue("Purchase contract number"),
        manufacturer: getFieldValue("Manufacturer"),
        openDate: getFieldValue("Open date:")



    };
}

/**
 * Extract ticket comments
 */
function extractComments() {
    const commentNodes = document.querySelectorAll('.comment');
    const comments = [];

    commentNodes.forEach(node => {
        const text = node.innerText?.trim();
        if (text) {
            comments.push(text);
        }
    });

    return comments;
}

/**
 * Detect attachment metadata (NO file content)
 */
function extractAttachments() {
    const attachmentNodes = document.querySelectorAll('.attachment');
    const attachments = [];

    attachmentNodes.forEach(node => {
        attachments.push({
            name: node.innerText?.trim() || "Unnamed file",
            url: node.href || null
        });
    });

    return attachments;
}

/**
 * Aggregate everything
 */
function extractTicketData() {
    
    const data = {
        fields: extractFields(),
        comments: extractComments(),
        attachments: extractAttachments(),
        metadata: {
            url: window.location.href,
            extractedAt: new Date().toISOString()
        }
    };

    console.log("Extracted Data:", data);

    return {
        fields: extractFields(),
        comments: extractComments(),
        attachments: extractAttachments(),
        metadata: {
            url: window.location.href,
            extractedAt: new Date().toISOString()
        }
    };
}

/**
 * Listen for message from popup
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

    if (request.action === "extractData") {
        console.log("Extracting ticket data...");

        const ticketData = extractTicketData();

        sendResponse(ticketData);
    }

    return true;
});
