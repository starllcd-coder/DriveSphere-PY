(function () {
  const root = document.getElementById("ds-maintenance");
  if (!root) return;

  const card = document.getElementById("m-tableCard");
  const body = document.getElementById("m-body");

  const vehicle = document.getElementById("m-vehicle");
  const plate = document.getElementById("m-plate");
  const type = document.getElementById("m-type");
  const priority = document.getElementById("m-priority");

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
  }

  function render(list) {
    if (!Array.isArray(list) || list.length === 0) {
      body.innerHTML = `<tr><td colspan="9" class="ds-empty">No tasks</td></tr>`;
      return;
    }

    body.innerHTML = list.map(t => `
      <tr>
        <td>${esc(t.date || t.task_date || "-")}</td>
        <td>${esc(t.vehicle || t.vehicle_name || "-")}</td>
        <td>${esc(t.plate || t.plate_number || "-")}</td>
        <td>${esc(t.type || t.task_type || "-")}</td>
        <td>${esc(t.priority || "-")}</td>
        <td>${esc(t.assignee || "-")}</td>
        <td>${esc(t.due || t.due_date || "-")}</td>
        <td>${esc(t.est_cost || "0.000")}</td>
        <td>${esc(t.notes || "")}</td>
      </tr>
    `).join("");
  }

  async function load() {
    try {
      DS_UI.setLoading(card, true);

      const qs = new URLSearchParams();
      if (type.value) qs.set("type", type.value);
      if (priority.value) qs.set("priority", priority.value);

      const data = await DS_API.get(`/api/maintenance/?${qs.toString()}`);
      if (!data.ok) throw new Error(data.error || "Maintenance failed");

      // client-side filters if backend doesn't support these query params yet
      let list = data.results || [];
      if (plate.value) {
        const q = plate.value.toLowerCase();
        list = list.filter(t => String(t.plate || t.plate_number || "").toLowerCase().includes(q));
      }
      if (vehicle.value) {
        const q = vehicle.value.toLowerCase();
        list = list.filter(t => String(t.vehicle || t.vehicle_name || "").toLowerCase().includes(q));
      }

      render(list);
      DS_UI.setLoading(card, false);
    } catch (e) {
      DS_UI.setLoading(card, false);
      DS_UI.toast("Maintenance", e.message || "Failed to load maintenance");
      body.innerHTML = `<tr><td colspan="9" class="ds-empty">Failed to load</td></tr>`;
    }
  }

  [vehicle, plate].forEach(inp => inp.addEventListener("input", debounce(load, 350)));
  type.addEventListener("change", load);
  priority.addEventListener("change", load);

  function debounce(fn, ms) {
    let t = null;
    return function () {
      clearTimeout(t);
      t = setTimeout(fn, ms);
    };
  }

  load();
})();