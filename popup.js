const settingsKey = 'dyrwtuaftqSettings';
const latestInferenceKey = 'dyrwtuaftqLatestInference';
const defaultSettings = {
  autoCheck: true,
  forceConfirm: true,
  disableGoogleAi: true,
};

const storageArea = (chrome.storage && chrome.storage.sync) ? chrome.storage.sync : chrome.storage.local;
const inferenceStorage = (chrome.storage && chrome.storage.local) ? chrome.storage.local : storageArea;

const autoCheck = document.getElementById('auto-check');
const forceConfirm = document.getElementById('force-confirm');
const disableGoogleAi = document.getElementById('disable-google-ai');
const settingsStatus = document.getElementById('settings-status');

const feedbackPrompt = document.getElementById('feedback-prompt');
const feedbackPredicted = document.getElementById('feedback-predicted');
const feedbackExpected = document.getElementById('feedback-expected');
const feedbackNotes = document.getElementById('feedback-notes');
const feedbackStatus = document.getElementById('feedback-status');
const latestInference = document.getElementById('latest-inference');
const submitFeedbackButton = document.getElementById('submit-feedback');

function flashStatus(node, message, isError = false) {
  if (!node) return;
  node.textContent = message;
  node.style.color = isError ? '#8A1F12' : '#000000';
  node.classList.add('visible');
  setTimeout(() => {
    node.classList.remove('visible');
  }, 2000);
}

function loadSettings() {
  storageArea.get(settingsKey, (data) => {
    const settings = { ...defaultSettings, ...(data[settingsKey] || {}) };
    autoCheck.checked = settings.autoCheck !== false;
    forceConfirm.checked = settings.forceConfirm !== false;
    disableGoogleAi.checked = settings.disableGoogleAi !== false;
  });
}

function saveSettings() {
  const settings = {
    autoCheck: autoCheck.checked,
    forceConfirm: forceConfirm.checked,
    disableGoogleAi: disableGoogleAi.checked,
  };

  storageArea.set({ [settingsKey]: settings }, () => {
    flashStatus(settingsStatus, 'SAVED.');
  });
}

function setLatestInferencePreview(payload) {
  if (!payload || !payload.prompt) {
    latestInference.textContent = '';
    latestInference.classList.add('empty');
    return;
  }

  const previewText = payload.prompt.length > 160
    ? `${payload.prompt.slice(0, 160)}...`
    : payload.prompt;

  const summary = [
    `Latest decision: ${payload.decision_level || 'unknown'}`,
    payload.ib_label ? `IB: ${payload.ib_label}` : '',
    payload.ic_label ? `IC: ${payload.ic_label}` : '',
    payload.submitted_at ? `At: ${new Date(payload.submitted_at).toLocaleString()}` : '',
    `Prompt: ${previewText}`,
  ].filter(Boolean).join('\n');

  latestInference.textContent = summary;
  latestInference.classList.remove('empty');
}

function loadLatestInference() {
  inferenceStorage.get(latestInferenceKey, (data) => {
    const payload = data[latestInferenceKey];
    setLatestInferencePreview(payload);

    if (!payload) return;
    if (!feedbackPrompt.value.trim()) {
      feedbackPrompt.value = payload.prompt || '';
    }
    if (!feedbackPredicted.value && payload.decision_level) {
      feedbackPredicted.value = payload.decision_level;
    }
  });
}

function sendRuntimeMessage(message) {
  return new Promise((resolve) => {
    try {
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          resolve({ ok: false, error: 'runtime_error', detail: chrome.runtime.lastError.message });
          return;
        }
        resolve(response || { ok: false, error: 'empty_response' });
      });
    } catch (err) {
      resolve({ ok: false, error: 'runtime_error', detail: err?.message || String(err) });
    }
  });
}

async function submitFeedback() {
  const prompt = feedbackPrompt.value.trim();
  if (!prompt) {
    flashStatus(feedbackStatus, 'PROMPT IS REQUIRED.', true);
    return;
  }

  submitFeedbackButton.disabled = true;
  submitFeedbackButton.textContent = 'SENDING...';

  const payload = {
    prompt,
    predicted_decision: feedbackPredicted.value || '',
    actual_label: feedbackExpected.value,
    notes: feedbackNotes.value.trim(),
  };

  const result = await sendRuntimeMessage({ type: 'submit_feedback', payload });

  if (result && result.ok) {
    flashStatus(feedbackStatus, 'FEEDBACK SENT.');
    feedbackNotes.value = '';
  } else {
    const detail = result?.detail || result?.error || 'unknown';
    flashStatus(feedbackStatus, `FAILED: ${detail}`, true);
  }

  submitFeedbackButton.disabled = false;
  submitFeedbackButton.textContent = 'SEND FEEDBACK';
}

document.getElementById('save-settings').addEventListener('click', saveSettings);
submitFeedbackButton.addEventListener('click', () => {
  submitFeedback();
});

loadSettings();
loadLatestInference();
