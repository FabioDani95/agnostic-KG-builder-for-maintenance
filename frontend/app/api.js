(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  root.api = async function api(path, options) {
    const init = { ...(options || {}) };
    if (init.body && !(init.body instanceof FormData)) {
      init.headers = { "Content-Type": "application/json", ...(init.headers || {}) };
      init.body = JSON.stringify(init.body);
    }
    const response = await fetch(path, init);
    const payload = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) {
      const detail = payload && payload.detail;
      const error = new Error(
        typeof detail === "string"
          ? detail
          : (detail && detail.title) || `HTTP ${response.status}`
      );
      error.detail = detail;
      throw error;
    }
    return payload;
  };
})();
