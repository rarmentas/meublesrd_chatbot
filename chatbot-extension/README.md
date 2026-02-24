\# Meubles RD Chatbot – Chrome Extension





\## Description





This is a basic Chrome/Edge extension providing a chatbot UI shell for service agents working in Salesforce Claims View.





\## Installation (Chrome / Edge)





1\. Clone or download this repository

2\. Open Chrome or Edge

3\. Go to `chrome://extensions`

4\. Enable \*\*Developer mode\*\*

5\. Click \*\*Load unpacked\*\*

6\. Select the `chatbot-extension` folder





The chatbot icon will appear in the browser toolbar. Click it to open the interface.




Overview
MeublesRD Service Assistant is a Chrome/Edge extension (Manifest V3) designed to support service agents by providing a contextual assistant directly in the browser. The extension adds a popup-based UI that can analyze the current screen, extract relevant case data from a supported web application, and send this information to a backend service for evaluation and recommendations.
The extension is intended to be used while agents are working in a claims or service-case view and aims to reduce manual data handling by automatically collecting on-screen information and presenting a structured analysis.


Key Features

Popup-based Assistant UI accessible from the browser toolbar
Screen analysis triggered by a single action (“Analyze Screen”)
Automatic data extraction from supported pages (case fields, comments, attachment metadata)
Backend integration to evaluate claims and return structured results
Formatted results display including summary, criteria evaluation, eligibility decision, and recommendations


Supported Environment

Browser: Google Chrome / Microsoft Edge (Chromium-based)
Manifest version: 3
Target pages: Pages matching https://mockup.gac.asware.com.mx/*
Backend API: https://api.gac.asware.com.mx/*


Architecture
The extension is composed of four main parts:
1. Manifest (manifest.json)
Defines the extension metadata, permissions, and wiring between components:

Registers the popup UI
Registers a background service worker
Injects a content script into supported pages
Declares required permissions (activeTab, scripting) and allowed host domains
2. Popup UI (popup.html, popup.js)
The popup provides the user-facing interface:

Header identifying the assistant
Analyze Screen button to trigger data extraction
Chat-style input (present for future/extended use)
Results panel for displaying backend responses
The popup script:

Identifies the active browser tab
Requests extracted data from the content script
Builds a structured JSON payload
Sends the payload to the backend API
Renders the response in a human-readable format
3. Content Script (content.js)
Runs inside supported web pages and is responsible for data extraction:

Reads visible case fields (e.g., subject, priority, status, description, case number, owner, store, account)
Collects all visible comments
Collects attachment metadata only (file name and URL, not file contents)
Adds contextual metadata (current URL and extraction timestamp)
The content script listens for messages from the popup and responds with the aggregated data.
4. Background Service Worker (background.js)
Implements a generic message-based mechanism to forward requests to backend endpoints.


Data Flow

User opens the extension popup from the browser toolbar
User clicks Analyze Screen
Popup sends an extractData message to the content script
Content script extracts case data from the page DOM
Popup receives extracted data and builds a JSON payload
Popup sends the payload to the backend API via HTTP POST
Backend responds with a structured evaluation
Popup renders the response (summary, criteria evaluation, final decision, recommendation)


Backend Integration

Endpoint: /api/agent-feedback/
Method: POST
Authentication: HTTP Basic Authentication
Payload: JSON object representing the claim/case context
Response: JSON containingClaim summary
Criteria evaluations
Final eligibility decision
Recommended next steps


Styling

The popup UI follows the Meubles RD visual identity (red, dark, and light color palette)
Styles are currently defined inline in popup.html
A separate popup.css file exists and may be used for future cleanup or refactoring


Installation (Developer Mode)

Clone or download the extension source code
Open Chrome or Edge
Navigate to chrome://extensions
Enable Developer mode
Click Load unpacked
Select the extension project folder
The MeublesRD Service Assistant icon will appear in the toolbar


Known Limitations

Extracted page data is not yet fully mapped into the backend payload (some values are currently hardcoded)
Chat input is present in the UI but not fully implemented as a conversational feature
Credentials are embedded in client-side code
CSS is partially duplicated between inline styles and popup.css


Intended Use
This extension is intended as an agent-assist tool to:

Speed up claim or case review
Reduce manual data transcription
Provide consistent eligibility evaluations and recommendations
It is best suited for controlled environments (internal tools, mockups, demos) and should be hardened before production deployment.


Version

Current version: 1.1


Disclaimer
This extension extracts only visible on-screen data and attachment metadata. It does not access or transmit file contents or hidden system data.

