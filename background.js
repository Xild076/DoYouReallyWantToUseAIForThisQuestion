let backendHost = "http://127.0.0.1:8000";
const settingsKey = 'dyrwtuaftqSettings';
const latestInferenceKey = 'dyrwtuaftqLatestInference';
const storageArea = (chrome.storage && chrome.storage.sync) ? chrome.storage.sync : chrome.storage.local;
const inferenceStorage = (chrome.storage && chrome.storage.local) ? chrome.storage.local : storageArea;
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

function storeLatestInference(message, payload, sender) {
  const latest = {
    submitted_at: new Date().toISOString(),
    prompt: (message.text || '').trim(),
    model_type: message.mode || 'ic',
    decision_level: payload.decision_level || '',
    ib_label: payload.ib_label || '',
    ic_label: payload.ic_label || '',
    source_url: sender?.tab?.url || '',
  };

  inferenceStorage.set({ [latestInferenceKey]: latest });
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
  if (message.type === "check_prompt") {
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
        storeLatestInference(message, payload, sender);
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
  }

  if (message.type === "submit_feedback") {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);

    (async () => {
      try {
        await backendHostReady;

        const incoming = (message && message.payload) || {};
        const mergedMetadata = {
          ...(incoming.metadata || {}),
          extension_version: chrome.runtime.getManifest().version,
          submitted_from: 'extension_popup',
        };

        const payload = {
          ...incoming,
          source_url: incoming.source_url || sender?.tab?.url || '',
          submitted_at: incoming.submitted_at || new Date().toISOString(),
          metadata: mergedMetadata,
        };

        const response = await fetch(`${backendHost}/feedback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        if (!response.ok) {
          const errText = await response.text();
          sendResponse({ ok: false, error: "feedback_error", status: response.status, detail: errText });
          return;
        }

        const data = await response.json();
        sendResponse({ ok: true, data });
      } catch (err) {
        const detail = err?.message || String(err);
        console.error("DYRWTUAFTQ feedback request failed", { backendHost, detail });
        sendResponse({ ok: false, error: "feedback_unreachable", detail });
      } finally {
        clearTimeout(timeoutId);
      }
    })();

    return true;
  }

  return false;
});
