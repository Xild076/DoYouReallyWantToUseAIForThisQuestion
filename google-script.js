const handledQueriesKey = 'dyrwtuaftqHandledGoogleQueries';
const storageArea = (chrome.storage && chrome.storage.sync) ? chrome.storage.sync : chrome.storage.local;

function normalizeQuery(query) {
  return (query || '').trim().replace(/\s+/g, ' ').toLowerCase();
}

function getHandledQueries() {
  try {
    const raw = sessionStorage.getItem(handledQueriesKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_err) {
    return [];
  }
}

function hasHandledQuery(query) {
  const handled = getHandledQueries();
  return handled.includes(query);
}

function markHandledQuery(query) {
  const handled = getHandledQueries();
  if (handled.includes(query)) return;

  handled.push(query);
  if (handled.length > 100) {
    handled.splice(0, handled.length - 100);
  }

  sessionStorage.setItem(handledQueriesKey, JSON.stringify(handled));
}

storageArea.get('dyrwtuaftqSettings', (data) => {
  const settings = { disableGoogleAi: true, ...(data['dyrwtuaftqSettings'] || {}) };
  if (settings.disableGoogleAi === false) return;

  const url = new URL(window.location.href);
  if (url.pathname !== '/search') return;

  const query = normalizeQuery(url.searchParams.get('q'));
  if (!query) return;
  if (hasHandledQuery(query)) return;

  if (url.searchParams.get('udm') !== '14') {
    markHandledQuery(query);
    url.searchParams.set('udm', '14');
    window.location.replace(url.toString());
    return;
  }

  markHandledQuery(query);
});