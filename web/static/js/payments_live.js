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

  const btnNew = document.getElementById("p-new");
  const btnRefund = document.getElementById("p-refund");
  const btnEdit = document.getElementById("p-edit");
  const btnDelete = document.getElementById("p-delete");

  let selectedPaymentId = null;

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
  }

  function isArabicClient() {
    return document.documentElement.lang === 'ar' || document.documentElement.dir === 'rtl';
  }

  function setSelected(id) {
    selectedPaymentId = id;
    const hasSelection = Boolean(id);
    if (btnEdit) btnEdit.disabled = !hasSelection;
    if (btnDelete) btnDelete.disabled = !hasSelection;

    Array.from(body.querySelectorAll("tr[data-id]")).forEach((tr) => {
      tr.classList.toggle("is-selected", String(tr.getAttribute("data-id")) === String(id));
    });
  }

  function render(list) {
    if (!Array.isArray(list) || list.length === 0) {
      body.innerHTML = `<tr><td colspan="8" class="ds-empty">${isArabicClient() ? 'لا توجد مدفوعات' : 'No payments'}</td></tr>`;
      setSelected(null);
      return;
    }

    body.innerHTML = list.map(p => `
      <tr data-id="${esc(p.id)}">
        <td>${esc(p.date || "-")}</td>
        <td>${esc(p.receipt_number || "-")}</td>
        <td>#${esc(String(p.booking_id || "-"))}</td>
        <td>${esc(p.customer_name || "-")}</td>
        <td>${esc(p.method || "-")}</td>
        <td>${esc(p.currency || "")} ${esc(p.amount || "0.000")}</td>
        <td><span class="ds-badge ds-badge--paid">${esc(p.status || "PAID")}</span></td>
        <td>${esc(p.notes || "")}</td>
      </tr>
    `).join("");

    Array.from(body.querySelectorAll("tr[data-id]")).forEach((tr) => {
      tr.addEventListener("click", () => setSelected(tr.getAttribute("data-id")));
      tr.style.cursor = "pointer";
    });

    setSelected(null);
  }

  function normalizePaymentsResponse(data) {
    if (Array.isArray(data)) {
      return data.map((item) => ({
        id: item.id,
        receipt_number: item.receipt_number,
        date: item.date || item.payment_date,
        booking_id: item.booking_id,
        customer_name: item.customer_name,
        method: item.method,
        amount: item.amount,
        currency: item.currency || item.currency_code,
        status: item.status,
        notes: item.notes,
      }));
    }

    if (data && Array.isArray(data.results)) {
      return data.results;
    }

    return [];
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

      const data = await DS_API.get(`/web-api/payments/?${qs.toString()}`);
      if (!Array.isArray(data) && !data.ok) throw new Error(data.error || "Payments failed");

      // client-side filter by customer if backend doesn't support
      let list = normalizePaymentsResponse(data);
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

  function wireButtons() {
    if (btnNew) {
      btnNew.addEventListener("click", () => {
        window.location.href = "/payments/new/";
      });
    }

    if (btnRefund) {
      btnRefund.addEventListener("click", () => {
        window.location.href = "/payments/refund/";
      });
    }

    if (btnEdit) {
      btnEdit.addEventListener("click", () => {
        if (!selectedPaymentId) return;
        window.location.href = `/payments/${selectedPaymentId}/edit/`;
      });
    }

    if (btnDelete) {
      btnDelete.addEventListener("click", () => {
        if (!selectedPaymentId) return;
        // eslint-disable-next-line no-alert
        if (!confirm(isArabicClient() ? "هل تريد حذف هذه الدفعة؟ سيتم إلغاؤها." : "Delete this payment? This will void the payment.")) return;
        window.location.href = `/payments/${selectedPaymentId}/delete/`;
      });
    }
  }

  wireButtons();
  load();
})();
