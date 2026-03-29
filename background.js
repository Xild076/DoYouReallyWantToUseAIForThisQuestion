let backendHost = "http://127.0.0.1:8000";
const settingsKey = 'dyrwtuaftqSettings';
const storageArea = (chrome.storage && chrome.storage.sync) ? chrome.storage.sync : chrome.storage.local;
const defaultSettings = {
  autoCheck: true,
  forceConfirm: true,
  disableGoogleAi: true,
};

function normalizeHost(host) {
  const value = (host || "").trim();
  if (!value) return "http://127.0.0.1:8000";
  if (value.startsWith("http://") || value.startsWith("https://")) {
    return value.replace(/\/$/, "");
  }
  return `http://${value.replace(/\/$/, "")}`;
}

function ensureDefaultSettings() {
  storageArea.get(settingsKey, (data) => {
    const existing = data[settingsKey] || {};
    const merged = { ...defaultSettings, ...existing };
    const hasMissingDefaults = Object.keys(defaultSettings).some((key) => typeof existing[key] === 'undefined');

    if (hasMissingDefaults) {
      storageArea.set({ [settingsKey]: merged });
    }
  });
}

chrome.runtime.onInstalled.addListener(() => {
  ensureDefaultSettings();
});

chrome.runtime.onStartup.addListener(() => {
  ensureDefaultSettings();
});

ensureDefaultSettings();

const backendHostReady = fetch(chrome.runtime.getURL('settings.json'))
  .then(r => r.json())
  .then(data => {
    if (data.backendHost) {
      backendHost = normalizeHost(data.backendHost);
    }
  })
  .catch(err => {
    console.error("Failed to load settings.json", err);
  });

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== "check_prompt") {
    return false;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 12000);

  (async () => {
    try {
      await backendHostReady;

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
      console.error("DYRWTUAFTQ backend request failed", { backendHost, detail });
      sendResponse({ error: "backend_unreachable", detail });
    } finally {
      clearTimeout(timeoutId);
    }
  })();

  return true;
});
