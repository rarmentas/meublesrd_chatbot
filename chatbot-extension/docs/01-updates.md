# MeublesRD Chrome Extension – Updates Log

## Overview

This document describes the main updates applied to the MeublesRD Service Assistant Chrome extension.

---

## 1. Data extraction from frontend

- **Payload uses extracted fields** from the page DOM instead of hardcoded values.
- **Mapping**: Classification → claim_type, Damage type → damage_type, Delivery date → delivery_date, Product type → product_type, Manufacturer, Store, Product code, Description, Purchase contract number, Open date → claim_date.
- **`has_attachments`** is always set to `false`.
- **`eligible`** defaults to `false`.

---

## 2. Markdown formatting

- Backend responses (e.g. `**text**`) are converted to HTML so formatting is visible.
- Supports: `**bold**`, `*italic*`, `` `code` ``, line breaks.
- Used for chat answers, Claim Summary justification and recommendation.

---

## 3. Full conversation in chat

- Chat sends the full conversation history instead of just the last message.
- Format: `User: ...`, `Assistant: ...`, alternating.
- Improves context for follow-up questions.

---

## 4. Tab detection (Side Panel / standalone window)

- When the UI runs in Side Panel or a standalone window, `currentWindow` has no tabs.
- **Solution**: Query tabs with `url: "https://mockup.gac.asware.com.mx/*"`.
- Uses the active mockup tab, or the first one if none is active.
- Requires `tabs` permission.

---

## 5. Content script injection

- Inject `content.js` on demand before sending messages.
- Prevents “Could not establish connection. Receiving end does not exist” when the tab was opened before installing/updating the extension.
- Injects script before extraction; no need to manually reload the page.

---

## 6. Field extraction (skip “Not used for copilot”)

- Multiple DOM nodes can have the same label (e.g. two “Description” rows).
- First occurrence often shows “Not used for copilot”.
- **Solution**: Ignore values in `SKIP_VALUES` and prefer the next matching value.
- Ensures the real Description (e.g. in “Description Information”) is used.
- Uses `querySelectorAll('i')` to remove all icons when extracting text.

---

## 7. Extracted fields and Description in UI

- After extraction, all read fields are shown in “Extracted fields”.
- Claim Summary includes the **Description** block.
- Order: Analyzing message → Extracted fields → Processing → Claim Summary.

---

## 8. Persistent UI (Side Panel)

- **Before**: Popup closed when clicking outside.
- **Now**: Side Panel stays open while using the page.
- Opening: click extension icon; panel opens in the sidebar.
- Requires `sidePanel` permission and `side_panel.default_path` in `manifest.json`.

---

## 9. Minimize button

- For popup windows only (not Side Panel).
- Minimize: shrink window to a small bar (240×48 px).
- Restore: return to full size (400×620 px).
- Button is hidden when running in Side Panel.

---

## 10. Frontend language (English)

- All UI strings in English:
  - “Campos extraídos” → “Extracted fields”
  - “(vacío)” → “(empty)”
  - “Usuario” / “Asistente” → “User” / “Assistant”
  - Error and placeholder messages in English.

---

## 11. Larger chat input

- Switched from single-line `<input>` to multi-line `<textarea>`.
- Min height: 80px (~4 lines).
- Max height: 200px; vertically resizable.
- **Enter**: send message; **Shift+Enter**: new line.

---

## 12. Loading spinner

- Spinner shown during:
  - **“Analyzing current case...”** – extraction and backend call.
  - **“Processing...”** – backend processing.
  - **“Thinking...”** – chat responses.
- CSS-only circular spinner, brand color `#b5121b`.

---

## File changes summary

| File           | Changes                                                                 |
|----------------|-------------------------------------------------------------------------|
| `manifest.json`| v1.5, sidePanel, side_panel, tabs, storage, action.default_title       |
| `background.js`| Side Panel instead of window creation                                   |
| `popup.html`   | Minimize/restore bar, textarea, spinner CSS                             |
| `popup.js`     | Extraction flow, markdown, chat history, tab query, English, spinner    |
| `content.js`   | Skip “Not used for copilot”, improve field extraction                   |

---

## Version history

- **1.2**: Initial popup-based extension.
- **1.3**: Frontend extraction, markdown, chat history.
- **1.4**: Standalone window, minimize, tab query.
- **1.5**: Side Panel, English UI, larger input, spinner.
