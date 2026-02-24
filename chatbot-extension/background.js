// JavaScript source code

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "SEND_TO_BACKEND") {
    (async () => {
      try {
        const res = await fetch(msg.endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(msg.payload)
        });

        const contentType = res.headers.get("content-type") || "";
        const data = contentType.includes("application/json") ? await res.json() : await res.text();

        sendResponse({ ok: res.ok, status: res.status, data });
      } catch (err) {
        sendResponse({ ok: false, error: err?.message || String(err) });
      }
    })();

    return true; // keep the message channel open for async
  }
});
