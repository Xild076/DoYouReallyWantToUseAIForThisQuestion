let backendHost = "http://127.0.0.1:8000";

function normalizeHost(host) {
  const value = (host || "").trim();
  if (!value) return "http://127.0.0.1:8000";
  if (value.startsWith("http://") || value.startsWith("https://")) {
    return value.replace(/\/$/, "");
  }
  return `http://${value.replace(/\/$/, "")}`;
}

fetch(chrome.runtime.getURL('settings.json'))
  .then(r => r.json())
  .then(data => {
    if (data.backendHost) {
      backendHost = normalizeHost(data.backendHost);
    }
  })
  .catch(err => console.error("Failed to load settings.json", err));

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== "check_prompt") {
    return false;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 12000);

  (async () => {
    try {
      const response = await fetch(`${backendHost}/infer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: message.text, model_type: message.mode }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errText = await response.text();
        sendResponse({ error: "backend_error", status: response.status, detail: errText });
        return;
      }

      const payload = await response.json();
      sendResponse({ ...payload, ok: response.ok });
    } catch (err) {
      const detail = err?.message || String(err);
      console.error("Prompt Sentinel backend request failed", { backendHost, detail });
      sendResponse({ error: "backend_unreachable", detail });
    } finally {
      clearTimeout(timeoutId);
    }
  })();

  return true;
});