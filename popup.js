const storageKey = 'promptSentinelSettings';
const autoCheck = document.getElementById('auto-check');
const forceConfirm = document.getElementById('force-confirm');
const status = document.getElementById('settings-status');

function loadSettings() {
  chrome.storage.sync.get(storageKey, (data) => {
    const settings = data[storageKey] || {
      autoCheck: true,
      forceConfirm: true
    };
    autoCheck.checked = settings.autoCheck;
    forceConfirm.checked = settings.forceConfirm;
  });
}

function saveSettings() {
  const settings = {
    autoCheck: autoCheck.checked,
    forceConfirm: forceConfirm.checked
  };
  chrome.storage.sync.set({ [storageKey]: settings }, () => {
    status.textContent = 'SAVED.';
    status.classList.add('visible');
    setTimeout(() => {
      status.classList.remove('visible');
    }, 1500);
  });
}

document.getElementById('save-settings').addEventListener('click', saveSettings);
loadSettings();