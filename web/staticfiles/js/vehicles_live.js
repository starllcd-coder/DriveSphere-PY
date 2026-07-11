(function () {
  const root = document.getElementById("ds-vehicles");
  if (!root) return;

  const card = document.getElementById("v-tableCard");
  const body = document.getElementById("v-body");

  const plate = document.getElementById("v-plate");
  const brand = document.getElementById("v-brand");
  const model = document.getElementById("v-model");
  const status = document.getElementById("v-status");

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
  }

  function render(list) {
    if (!Array.isArray(list) || list.length === 0) {
      body.innerHTML = `<tr><td colspan="9" class="ds-empty">No vehicles</td></tr>`;
      return;
    }

    body.innerHTML = list.map(v => `
      <tr>
        <td>${esc(v.plate_number || v.plate || "-")}</td>
        <td>${esc((v.brand_name || v.brand || "-") + " " + (v.model_name || v.model || ""))}</td>
        <td>${esc(v.year || "-")}</td>
        <td>${esc(v.category || "-")}</td>
        <td>${esc(v.transmission || "-")}</td>
        <td>${esc(v.fuel || "-")}</td>
        <td>${esc(v.color || "-")}</td>
        <td><span class="ds-badge ds-badge--${esc(String(v.status||"").toLowerCase())}">${esc(v.status || "-")}</span></td>
        <td>${esc(v.daily_rate || "-")}</td>
      </tr>
    `).join("");
  }

  async function load() {
    try {
      DS_UI.setLoading(card, true);

      const qs = new URLSearchParams();
      if (plate.value) qs.set("plate", plate.value);
      if (brand.value) qs.set("brand", brand.value);
      if (model.value) qs.set("model", model.value);
      if (status.value) qs.set("status", status.value);

      const data = await DS_API.get(`/api/vehicles/?${qs.toString()}`);
      if (!data.ok) throw new Error(data.error || "Vehicles failed");
      render(data.results || []);

      DS_UI.setLoading(card, false);
    } catch (e) {
      DS_UI.setLoading(card, false);
      DS_UI.toast("Vehicles", e.message || "Failed to load vehicles");
      body.innerHTML = `<tr><td colspan="9" class="ds-empty">Failed to load</td></tr>`;
    }
  }

  [plate, brand, model].forEach(inp => inp.addEventListener("input", debounce(load, 350)));
  status.addEventListener("change", load);

  function debounce(fn, ms) {
    let t = null;
    return function () {
      clearTimeout(t);
      t = setTimeout(fn, ms);
    };
  }

  load();
})();