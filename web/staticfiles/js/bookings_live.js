(function () {
  const listBody = document.getElementById("b-body");
  const upcomingBody = document.getElementById("u-body");
  const isMain = !!listBody;
  const isUpcoming = !!upcomingBody;

  const root = document.getElementById("ds-bookings");
  const canExtend = root?.dataset?.canExtend === "1";
  const canReturn = root?.dataset?.canReturn === "1";
  const canCheckout = root?.dataset?.canCheckout === "1";

  const btnEdit = document.getElementById("b-edit");
  const btnDel = document.getElementById("b-del");

  let selectedBookingId = null;

  if (!isMain && !isUpcoming) return;

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  async function post(url, payload) {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(payload || {}),
    });
    return resp.json();
  }

  function actionMenu(row) {
    const isRtl = document.documentElement.dir === 'rtl' || document.body.classList.contains('is-rtl');
    const labels = isRtl
      ? {
          actions: 'الإجراءات',
          invoice: 'فاتورة',
          agreement: 'اتفاقية',
          confirmation: 'تأكيد الحجز',
          quotation: 'عرض أسعار',
          checkout: 'تسليم',
          extend: 'تمديد',
          return: 'إرجاع',
        }
      : {
          actions: 'Actions',
          invoice: 'Invoice',
          agreement: 'Agreement',
          confirmation: 'Confirmation',
          quotation: 'Quotation',
          checkout: 'Checkout',
          extend: 'Extend',
          return: 'Return',
        };

    const isCheckoutEligible = ["CONFIRMED", "UPCOMING"].includes(String(row.status || "").toUpperCase());
    const checkoutLink = (canCheckout && isCheckoutEligible)
      ? `<a href="/bookings/${row.id}/edit/handover/">${labels.checkout}</a>`
      : "";
    const extendButton = canExtend ? `<button data-extend="${row.id}">${labels.extend}</button>` : "";
    const returnLink = canReturn ? `<a href="/bookings/${row.id}/return/">${labels.return}</a>` : "";

    return `
      <div class="ds-actions">
        <button class="ds-actions__toggle">${labels.actions}</button>
        <div class="ds-actions__menu">
          ${checkoutLink}
          <a href="/print/bookings/${row.id}/invoice/" target="_blank">${labels.invoice}</a>
          <a href="/print/bookings/${row.id}/agreement/" target="_blank">${labels.agreement}</a>
          <a href="/print/bookings/${row.id}/confirmation/" target="_blank">${labels.confirmation}</a>
          <a href="/print/bookings/${row.id}/quotation/" target="_blank">${labels.quotation}</a>
          ${extendButton}
          ${returnLink}
        </div>
      </div>
    `;
  }

  function setSelected(id) {
    selectedBookingId = id;
    if (btnEdit) btnEdit.disabled = !id;
    if (btnDel) btnDel.disabled = !id;

    if (!listBody) return;
    listBody.querySelectorAll("tr[data-id]").forEach((tr) => {
      tr.classList.toggle("is-selected", String(tr.getAttribute("data-id")) === String(id));
    });
  }

  function renderMain(rows) {
    listBody.innerHTML = rows.map((r) => `
      <tr data-id="${r.id}">
        <td>#${r.id}</td>
        <td>${r.customer}</td>
        <td>${r.vehicle}</td>
        <td>${r.pickup_date}</td>
        <td>${r.return_date}</td>
        <td>${r.status}</td>
        <td>${r.total}</td>
        <td style="text-align:right;">${actionMenu(r)}</td>
      </tr>
    `).join("");

    listBody.querySelectorAll("tr[data-id]").forEach((tr) => {
      tr.addEventListener("click", (e) => {
        if (e.target.closest(".ds-actions")) return;
        setSelected(tr.getAttribute("data-id"));
      });
      tr.style.cursor = "pointer";
    });

    setSelected(null);

    listBody.querySelectorAll("[data-extend]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-extend");
        const newDate = prompt("New return date (YYYY-MM-DD)");
        if (!newDate) return;
        const data = await post(`/web-api/bookings/${id}/extend/`, { new_return_date: newDate });
        if (!data.ok) alert(data.error || "Failed");
        else load();
      });
    });
  }

  function renderUpcoming(rows) {
    upcomingBody.innerHTML = rows.map((r) => `
      <tr>
        <td>#${r.id}</td>
        <td>${r.customer}</td>
        <td>${r.vehicle}</td>
        <td>${r.pickup_date}</td>
        <td>${r.return_date}</td>
        <td>${r.status}</td>
        <td>${r.total}</td>
        <td style="text-align:right;"><button class="ds-btn ds-btn--small" data-activate="${r.id}">Activate</button></td>
      </tr>
    `).join("");

    upcomingBody.querySelectorAll("[data-activate]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-activate");
        const data = await post(`/web-api/bookings/${id}/activate/`, {});
        if (!data.ok) alert(data.error || "Failed");
        else load();
      });
    });
  }

  function wireActionButtons() {
    const isRtl = document.documentElement.dir === "rtl" || document.body.classList.contains("is-rtl");
    const deletePrompt = isRtl
      ? "هل تريد حذف هذا الحجز؟ لا يمكن التراجع عن ذلك."
      : "Delete this booking? This cannot be undone.";

    if (btnEdit) {
      btnEdit.addEventListener("click", () => {
        if (!selectedBookingId) return;
        window.location.href = `/bookings/${selectedBookingId}/edit/`;
      });
    }

    if (btnDel) {
      btnDel.addEventListener("click", () => {
        if (!selectedBookingId) return;
        if (!confirm(deletePrompt)) return;
        window.location.href = `/bookings/${selectedBookingId}/delete/`;
      });
    }
  }

  function normalizeBookingsResponse(data) {
    if (Array.isArray(data)) {
      return data.map((item) => ({
        id: item.id,
        customer: item.customer || item.customer_name || "-",
        vehicle: item.vehicle || item.vehicle_display || "-",
        pickup_date: item.pickup_date || "-",
        return_date: item.return_date || "-",
        status: item.status || "-",
        total: item.total || item.total_amount || "0.000",
      }));
    }

    if (data && Array.isArray(data.results)) {
      return data.results;
    }

    return [];
  }

  async function load() {
    const q = document.getElementById("b-q")?.value || document.getElementById("u-q")?.value || "";
    const status = document.getElementById("b-status")?.value || "";
    const url = new URL("/web-api/bookings/", window.location.origin);
    if (q) url.searchParams.set("q", q);
    if (status) url.searchParams.set("status", status);
    if (isUpcoming && !status) url.searchParams.set("status", "UPCOMING");

    const resp = await fetch(url.toString(), { headers: { "X-Requested-With": "XMLHttpRequest" } });
    const data = await resp.json();
    if (!Array.isArray(data) && !data.ok) return;

    const rows = normalizeBookingsResponse(data);

    if (isMain) renderMain(rows);
    if (isUpcoming) renderUpcoming(rows);
  }

  document.getElementById("b-upcoming")?.addEventListener("click", () => {
    window.location.href = "/bookings/upcoming/";
  });

  const params = new URLSearchParams(window.location.search || "");
  const initialQ = params.get("q") || "";
  const initialStatus = params.get("status") || "";
  if (initialQ) {
    const input = document.getElementById("b-q") || document.getElementById("u-q");
    if (input) input.value = initialQ;
  }
  if (initialStatus && document.getElementById("b-status")) {
    document.getElementById("b-status").value = initialStatus;
  }

  document.getElementById("b-q")?.addEventListener("input", load);
  document.getElementById("b-status")?.addEventListener("change", load);
  document.getElementById("u-q")?.addEventListener("input", load);

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".ds-actions")) {
      document.querySelectorAll(".ds-actions.is-open").forEach((el) => el.classList.remove("is-open"));
    }
  });

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".ds-actions__toggle");
    if (!btn) return;
    e.preventDefault();
    const wrap = btn.closest(".ds-actions");
    const open = wrap.classList.contains("is-open");
    document.querySelectorAll(".ds-actions.is-open").forEach((el) => el.classList.remove("is-open"));
    if (!open) wrap.classList.add("is-open");
  });

  wireActionButtons();
  load();
})();
