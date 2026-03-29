const targetSelector = "textarea";
const userInputSelectors = ["textarea", "[contenteditable=\"true\"]", "[role=\"textbox\"]", "input:not([type=hidden])"];
let autoCheckEnabled = true;
let requireConfirmation = true;
let disableGoogleAi = true;
let guardBypass = false;
let lastFocusedPrompt = null;
const settingsKey = 'dyrwtuaftqSettings';
const storageAreaName = (chrome.storage && chrome.storage.sync) ? 'sync' : 'local';
const storageArea = chrome.storage[storageAreaName];
const defaultSettings = {
  autoCheck: true,
  forceConfirm: true,
  disableGoogleAi: true,
};

function ensureModalStyles() {
  if (document.getElementById('dyrwtuaftq-modal-style')) return;
  const style = document.createElement('style');
  style.id = 'dyrwtuaftq-modal-style';
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@700&family=Space+Mono:wght@400;700&display=swap');
    
    .ps-overlay {
      position: fixed;
      inset: 0;
      background: rgba(17, 17, 17, 0.85);
      backdrop-filter: blur(2px);
      z-index: 2147483646;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .ps-modal {
      width: min(520px, 100%);
      background: #F5F3EC;
      border: 4px solid #111111;
      border-bottom-width: 8px;
      box-shadow: 12px 12px 0px #E3381B;
      overflow: hidden;
      color: #111111;
      font-family: 'Space Mono', Courier, monospace;
      padding: 0;
    }
    .ps-head {
      font-family: 'Libre Baskerville', serif;
      padding: 24px 24px 16px 24px;
      font-size: 28px;
      font-weight: 700;
      border-bottom: 4px solid #111111;
      background: #F5F3EC;
      color: #E3381B;
      line-height: 1.1;
      text-transform: uppercase;
      letter-spacing: -1.5px;
    }
    .ps-body {
      padding: 24px;
      font-size: 14px;
      line-height: 1.5;
      font-weight: 700;
      white-space: pre-wrap;
      text-transform: uppercase;
    }
    .ps-actions {
      display: flex;
      gap: 16px;
      justify-content: flex-end;
      padding: 0 24px 24px 24px;
    }
    .ps-btn {
      border: 2px solid #111111;
      background: #F5F3EC;
      color: #111111;
      font-family: 'Space Mono', Courier, monospace;
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      padding: 12px 20px;
      cursor: pointer;
      box-shadow: 4px 4px 0px #E3381B;
      transition: all 0.1s ease;
    }
    .ps-btn:hover {
      transform: translate(-2px, -2px);
      box-shadow: 6px 6px 0px #E3381B;
    }
    .ps-btn:active {
      transform: translate(2px, 2px);
      box-shadow: 0px 0px 0px #E3381B;
    }
    .ps-btn.primary {
      background: #111111;
      color: #F5F3EC;
    }
    .ps-btn.warn {
      background: #E3381B;
      border-color: #111111;
      color: #F5F3EC;
      box-shadow: 4px 4px 0px #111111;
    }
    .ps-btn.warn:hover {
      box-shadow: 6px 6px 0px #111111;
    }
    .ps-btn.warn:active {
      box-shadow: 0px 0px 0px #111111;
    }
  `;
  document.documentElement.appendChild(style);
}

function showDecisionModal({ title, message, actions, dismissAction }) {
  ensureModalStyles();
  return new Promise((resolve) => {
    const overlay = document.createElement('div');
    overlay.className = 'ps-overlay';

    const modal = document.createElement('div');
    modal.className = 'ps-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');

    const head = document.createElement('div');
    head.className = 'ps-head';
    head.textContent = title;

    const body = document.createElement('div');
    body.className = 'ps-body';
    body.textContent = message;

    const actionsWrap = document.createElement('div');
    actionsWrap.className = 'ps-actions';

    const cleanup = (result) => {
      document.removeEventListener('keydown', escHandler, true);
      overlay.remove();
      resolve(result);
    };

    const escHandler = (event) => {
      if (event.key === 'Escape' && dismissAction) {
        event.preventDefault();
        cleanup(dismissAction.value);
      }
    };

    actions.forEach((actionDef) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = `ps-btn${actionDef.kind ? ` ${actionDef.kind}` : ''}`;
      btn.textContent = actionDef.label;
      btn.addEventListener('click', () => cleanup(actionDef.value));
      actionsWrap.appendChild(btn);
    });

    overlay.addEventListener('click', (event) => {
      if (event.target === overlay && dismissAction) {
        cleanup(dismissAction.value);
      }
    });

    modal.appendChild(head);
    modal.appendChild(body);
    modal.appendChild(actionsWrap);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    document.addEventListener('keydown', escHandler, true);
  });
}

async function checkPrompt(text, mode = "ic") {
  if (!autoCheckEnabled) {
    return { decision_level: "allow" };
  }
  try {
    const response = await chrome.runtime.sendMessage({ type: "check_prompt", text, mode });
    return response || null;
  } catch (err) {
    return { error: "extension_unreachable", detail: err?.message || String(err) };
  }
}

function refreshSettings() {
  storageArea.get(settingsKey, (data) => {
    const settings = { ...defaultSettings, ...(data[settingsKey] || {}) };
    autoCheckEnabled = settings.autoCheck !== false;
    requireConfirmation = settings.forceConfirm !== false;
    disableGoogleAi = settings.disableGoogleAi !== false;
  });
}

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === storageAreaName && changes[settingsKey]) {
    refreshSettings();
  }
});

refreshSettings();

function isSendButton(el) {
  if (!el) return false;
  if (el.closest && el.closest('.ps-overlay')) return false;
  if (el.getAttribute('type') === 'submit') return true;
  const aria = (el.getAttribute('aria-label') || '').toLowerCase();
  const text = (el.innerText || '').toLowerCase();
  return (aria.includes('send') || text.includes('send') || text.includes('submit'));
}

function getPromptValue(el) {
  if (!el) return '';
  if ('value' in el) return el.value;
  return el.innerText || el.textContent || '';
}

function clearPrompt(el) {
  if (!el) return;
  if ('value' in el) {
    el.value = '';
  } else {
    el.textContent = '';
    el.innerHTML = '';
  }
  // React/Angular require native event firing to detect changes
  el.dispatchEvent(new Event('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}

function openGoogleSearch(query) {
  let googleUrl = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
  if (disableGoogleAi) {
    googleUrl += `&udm=14`;
  }
  window.open(googleUrl, "_blank");
}

function submitPrompt(promptEl, preferredButton = null) {
  const sendButton = preferredButton && preferredButton.isConnected ? preferredButton : findSendButton();
  if (sendButton) {
    sendButton.click();
    return;
  }
  if (promptEl?.form && typeof promptEl.form.requestSubmit === 'function') {
    promptEl.form.requestSubmit();
    return;
  }
  if (promptEl?.form) {
    promptEl.form.submit();
  }
}

async function guardedAction(promptEl, action) {
  const textValue = getPromptValue(promptEl);
  const verdict = await checkPrompt(textValue, "ic");
  if (!verdict) {
    await showDecisionModal({
      title: 'DYRWTUAFTQ',
      message: 'DYRWTUAFTQ could not validate this prompt (no response from extension).',
      actions: [{ label: 'Send Anyway', value: 'send', kind: 'primary' }, { label: 'Cancel', value: 'cancel' }],
      dismissAction: { value: 'cancel' },
    }).then((choice) => {
      if (choice === 'send') {
        guardBypass = true;
        action();
      }
    });
    return;
  }

  if (verdict.error === "extension_unreachable") {
    const decision = await showDecisionModal({
      title: 'DYRWTUAFTQ Extension Error',
      message: `Extension communication failed.\n\n${verdict.detail || 'Unknown error.'}`,
      actions: [{ label: 'Send Anyway', value: 'send', kind: 'primary' }, { label: 'Cancel', value: 'cancel' }],
      dismissAction: { value: 'cancel' },
    });
    if (decision === 'send') {
      guardBypass = true;
      action();
    }
    return;
  }

  if (verdict.error === "backend_unreachable") {
    const detail = verdict.detail ? `\n\nDetail: ${verdict.detail}` : "";
    const decision = await showDecisionModal({
      title: 'Backend Unreachable',
      message: `DYRWTUAFTQ backend unreachable.${detail}`,
      actions: [{ label: 'Send Anyway', value: 'send', kind: 'primary' }, { label: 'Cancel', value: 'cancel' }],
      dismissAction: { value: 'cancel' },
    });
    if (decision === 'send') {
      guardBypass = true;
      action();
    }
    return;
  }

  if (verdict.error === "backend_error") {
    const decision = await showDecisionModal({
      title: 'Backend Error',
      message: `DYRWTUAFTQ backend error (${verdict.status || "unknown"}).`,
      actions: [{ label: 'Send Anyway', value: 'send', kind: 'primary' }, { label: 'Cancel', value: 'cancel' }],
      dismissAction: { value: 'cancel' },
    });
    if (decision === 'send') {
      guardBypass = true;
      action();
    }
    return;
  }

  switch (verdict.decision_level) {
    case "allow":
      guardBypass = true;
      action();
      return;
    case "maybe": {
      const userStillWantsAi = requireConfirmation
        ? (await showDecisionModal({
          title: 'PROMPT INTERCEPT',
          message: 'Can you answer this question yourself?\n\nIf it’s a generic query, use a standard search engine instead of wasting AI inferences.',
          actions: [{ label: 'REJECT', value: 'cancel' }, { label: 'PROCEED', value: 'send', kind: 'warn' }],
          dismissAction: { value: 'cancel' },
        })) === 'send'
        : true;
      if (userStillWantsAi) {
        guardBypass = true;
        action();
      } else {
        openGoogleSearch(textValue);
        clearPrompt(promptEl);
      }
      return;
    }
    case "no-ai": {
      openGoogleSearch(textValue);
      clearPrompt(promptEl);
      return;
    }
    default:
      guardBypass = true;
      action();
  }
}

function findSendButton() {
  const candidates = Array.from(document.querySelectorAll('button, [role="button"]'));
  return candidates.find((el) => isSendButton(el));
}

function findPromptElement(source) {
  let current = source;
  while (current && current !== document.body) {
    if (current.matches) {
      if (userInputSelectors.some((sel) => current.matches(sel))) {
        return current;
      }
    }
    if (current.isContentEditable) {
      return current;
    }
    current = current.parentElement;
  }
  if (lastFocusedPrompt && lastFocusedPrompt.isConnected) {
    return lastFocusedPrompt;
  }
  if (document.activeElement && document.activeElement !== document.body) {
    const active = document.activeElement;
    if (active.matches) {
      if (userInputSelectors.some((sel) => active.matches(sel)) || active.isContentEditable) {
        return active;
      }
    }
  }
  return null;
}

document.addEventListener('focusin', (event) => {
  const el = event.target;
  if (!el || !el.matches) return;
  if (userInputSelectors.some((sel) => el.matches(sel)) || el.isContentEditable) {
    lastFocusedPrompt = el;
  }
});

document.addEventListener('focusout', (event) => {
  if (event.target === lastFocusedPrompt) {
    lastFocusedPrompt = null;
  }
});

document.addEventListener("submit", async (event) => {
  if (event.target && event.target.closest && event.target.closest('.ps-overlay')) return;
  if (guardBypass) {
    guardBypass = false;
    return;
  }
  const promptEl = findPromptElement(event.target);
  if (!promptEl) return;
  const text = getPromptValue(promptEl).trim();
  if (!text) return;
  event.preventDefault();
  event.stopImmediatePropagation();

  await guardedAction(promptEl, () => {
    submitPrompt(promptEl);
  });
}, true);

document.addEventListener("keydown", async (event) => {
  if (event.target && event.target.closest && event.target.closest('.ps-overlay')) return;
  if (guardBypass) {
    guardBypass = false;
    return;
  }
  const promptEl = findPromptElement(event.target);
  if (!promptEl) return;
  if (event.key !== "Enter" || event.shiftKey) return;
  const text = getPromptValue(promptEl).trim();
  if (!text) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  await guardedAction(promptEl, () => {
    submitPrompt(promptEl);
  });
}, true);

document.addEventListener('click', async (event) => {
  if (event.target && event.target.closest && event.target.closest('.ps-overlay')) return;
  if (guardBypass) {
    guardBypass = false;
    return;
  }
  const button = event.target.closest('button, [role="button"]');
  if (!button || !isSendButton(button)) return;
  const promptEl = findPromptElement(button);
  if (!promptEl) return;
  const text = getPromptValue(promptEl).trim();
  if (!text) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  await guardedAction(promptEl, () => submitPrompt(promptEl, button));
}, true);
