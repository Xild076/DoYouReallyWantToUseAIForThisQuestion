const storageKey = 'dyrwtuaftqSettings';
const defaultSettings = {
  autoCheck: true,
  forceConfirm: true,
  disableGoogleAi: true
};
const storageArea = (chrome.storage && chrome.storage.sync) ? chrome.storage.sync : chrome.storage.local;
const autoCheck = document.getElementById('auto-check');
const forceConfirm = document.getElementById('force-confirm');
const disableGoogleAi = document.getElementById('disable-google-ai');
const status = document.getElementById('settings-status');

function loadSettings() {
  storageArea.get(storageKey, (data) => {
    const settings = { ...defaultSettings, ...(data[storageKey] || {}) };
    autoCheck.checked = settings.autoCheck !== false;
    forceConfirm.checked = settings.forceConfirm !== false;
    disableGoogleAi.checked = settings.disableGoogleAi !== false;
  });
}

function saveSettings() {
  const settings = {
    autoCheck: autoCheck.checked,
    forceConfirm: forceConfirm.checked,
    disableGoogleAi: disableGoogleAi.checked
  };
  storageArea.set({ [storageKey]: settings }, () => {
    status.textContent = 'SAVED.';
    status.classList.add('visible');
    setTimeout(() => {
      status.classList.remove('visible');
    }, 1500);
  });
}

document.getElementById('save-settings').addEventListener('click', saveSettings);
loadSettings();
