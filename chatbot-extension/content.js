console.log("Content script successfully injected.");

console.log("MeublesRD Assistant content script loaded.");

/**
 * Extract ticket main fields
 */
function getFieldValue(labelText) {
    const rows = document.querySelectorAll('.field-row');

    for (let row of rows) {
        const label = row.querySelector('.field-label')?.innerText?.trim();

        if (label === labelText) {

            // Clone row to safely manipulate
            const rowClone = row.cloneNode(true);

            // Remove label and icon
            rowClone.querySelector('.field-label')?.remove();
            rowClone.querySelector('i')?.remove();

            // Get remaining text content
            const valueText = rowClone.innerText.trim();

            return valueText;
        }
    }

    return "";
}

function extractFields() {
    return {
        subject: getFieldValue("Subject"),
        priority: getFieldValue("Priority"),
        status: getFieldValue("Status"),
        description: getFieldValue("Description"),
	caseNumber: getFieldValue("Case number"),
	caseOwner: getFieldValue("Case owner"),
	store: getFieldValue("Store"),
	account: getFieldValue("Account name"),
	date: getFieldValue("Delivery date"),
	maccount: getFieldValue("Meublex customer account number")

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
