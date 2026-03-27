chrome.storage.sync.get('dyrwtuaftqSettings', (data) => {
  const settings = data['dyrwtuaftqSettings'] || {};
  // If the toggle is ON, forcefully ensure Google search is "Web" mode (udm=14)
  if (settings.disableGoogleAi === true) {
    const url = new URL(window.location.href);
    if (url.pathname === '/search' && url.searchParams.get('udm') !== '14') {
      url.searchParams.set('udm', '14');
      window.location.replace(url.toString());
    }
  }
});