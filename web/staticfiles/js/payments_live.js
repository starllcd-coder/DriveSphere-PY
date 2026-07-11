(function () {
  const root = document.getElementById("ds-payments");
  if (!root) return;

  const card = document.getElementById("p-tableCard");
  const body = document.getElementById("p-body");

  const booking = document.getElementById("p-booking");
  const customer = document.getElementById("p-customer");
  const from = document.getElementById("p-from");
  const to = document.getElementById("p-to");
  const method = document.getElementById("p-method");

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
  }

  function render(list) {
    if (!Array.isArray(list) || list.length === 0) {
      body.innerHTML = `<tr><td colspan="9" class="ds-empty">No payments</td></tr>`;
      return;
    }

    body.innerHTML = list.map(p => `
      <tr>
        <td>${esc(p.date || "-")}</td>
        <td>${esc(p.receipt_number || "-")}</td>
        <td>#${esc(String(p.booking_id || "-"))}</td>
        <td>${esc(p.customer_name || "-")}</td>
        <td>${esc(p.method || "-")}</td>
        <td>${esc(p.currency || "")} ${esc(p.amount || "0.000")}</td>
        <td><span class="ds-badge ds-badge--paid">${esc(p.status || "PAID")}</span></td>
        <td>${esc(p.notes || "")}</td>
        <td class="ds-ta-right">
          <a class="ds-btn ds-btn--small" href="/api/payments/${esc(p.id)}/receipt.pdf" target="_blank">Receipt</a>
        </td>
      </tr>
    `).join("");
  }

  async function load() {
    try {
      DS_UI.setLoading(card, true);

      const qs = new URLSearchParams();
      if (booking.value) qs.set("booking_id", booking.value);

      // Note: API may not support customer filter directly; keep UI filter for Phase 2 server-side enhancements.
      if (method.value) qs.set("method", method.value);
      if (from.value) qs.set("from", from.value);
      if (to.value) qs.set("to", to.value);

      const data = await DS_API.get(`/api/payments/?${qs.toString()}`);
      if (!data.ok) throw new Error(data.error || "Payments failed");

      // client-side filter by customer if backend doesn't support
      let list = data.results || [];
      if (customer.value) {
        const q = customer.value.toLowerCase();
        list = list.filter(p => String(p.customer_name || "").toLowerCase().includes(q));
      }

      render(list);
      DS_UI.setLoading(card, false);
    } catch (e) {
      DS_UI.setLoading(card, false);
      DS_UI.toast("Payments", e.message || "Failed to load payments");
      body.innerHTML = `<tr><td colspan="9" class="ds-empty">Failed to load</td></tr>`;
    }
  }

  [booking, customer, from, to].forEach(inp => inp.addEventListener("input", debounce(load, 350)));
  method.addEventListener("change", load);

  function debounce(fn, ms) {
    let t = null;
    return function () {
      clearTimeout(t);
      t = setTimeout(fn, ms);
    };
  }

  load();
})();