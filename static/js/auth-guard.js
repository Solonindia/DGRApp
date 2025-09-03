// demoapp/static/demoapp/js/auth-guard.js
// -----------------------------------------------------------
// Purpose: After logout, if the user hits the browser Back button
// and a protected page is restored from history/BFCache, this script
// quickly checks the session and sends them back to the correct login.
// -----------------------------------------------------------

(function () {
  // You can override these from the template *before* you include this file:
  //   <script>window.LOGIN_PATH = '/superuser/login/';</script>
  //   <script>window.PING_URL   = '/auth/ping/';</script>
  const LOGIN_PATH = window.LOGIN_PATH || '/user/login/';
  const PING_URL   = window.PING_URL   || '/auth/ping/';

  async function ensureLoggedIn() {
    try {
      const resp = await fetch(PING_URL, {
        method: 'GET',
        credentials: 'include',
        cache: 'no-store',
        headers: { 'Accept': 'application/json' }
      });

      if (!resp.ok) {
        // If server errors, be safe and go to login
        return location.replace(LOGIN_PATH);
      }

      const data = await resp.json();
      if (!data || !data.authenticated) {
        // Session not authenticated anymore → go to login
        return location.replace(LOGIN_PATH);
      }
    } catch (_) {
      // Network error → go to login
      return location.replace(LOGIN_PATH);
    }
  }

  // If page was restored from the browser's back/forward cache, verify session.
  window.addEventListener('pageshow', function (e) {
    const nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    const cameFromBF = e.persisted || (nav && nav.type === 'back_forward');
    if (cameFromBF) {
      ensureLoggedIn();
    }
  });

  // Verify again whenever the tab becomes visible (user switches back to this tab).
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
      ensureLoggedIn();
    }
  });

  // Extra safety: check on window focus (covers some cases).
  window.addEventListener('focus', ensureLoggedIn);

  // Hint some browsers not to BFCache this page.
  window.addEventListener('unload', function () { /* noop */ });

  // Optional: uncomment to also check on every normal load.
  // ensureLoggedIn();
})();
