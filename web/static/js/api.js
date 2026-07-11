(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  function buildHeaders(extra) {
    const headers = Object.assign(
      { "X-Requested-With": "XMLHttpRequest" },
      extra || {}
    );

    const csrf = getCookie("csrftoken");
    if (csrf) headers["X-CSRFToken"] = csrf;

    return headers;
  }

  async function request(method, url, body, opts) {
    const options = opts || {};
    const headers = buildHeaders(options.headers);

    const init = {
      method,
      headers
    };

    if (body !== undefined && body !== null) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }

    const resp = await fetch(url, init);

    let data = null;
    const ct = resp.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      data = await resp.json();
    } else {
      data = { ok: resp.ok, text: await resp.text() };
    }

    if (!resp.ok) {
      const msg = (data && (data.error || data.message)) || `Request failed (${resp.status})`;
      const err = new Error(msg);
      err.status = resp.status;
      err.data = data;
      throw err;
    }

    return data;
  }

  window.DS_API = {
    get: (url, opts) => request("GET", url, null, opts),
    post: (url, body, opts) => request("POST", url, body, opts),
  };
})();