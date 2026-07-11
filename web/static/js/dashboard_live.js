(function () {
  const root = document.getElementById("ds-dashboard");
  if (!root) return;

  const kpisWrap = document.getElementById("dash-kpis");
  const overviewCard = document.getElementById("dash-overview");
  const bookingsBody = document.getElementById("dash-bookings-body");
  const paymentsBody = document.getElementById("dash-payments-body");
  const miniWrap = document.getElementById("dash-mini");

  let period = "today";

  function setKPIs(overview) {
    const cards = kpisWrap.querySelectorAll(".ds-kpiCard");
    if (cards.length < 4) return;

    cards[0].querySelector(".ds-kpiCard__value").textContent = overview.bookings_count ?? "—";
    cards[1].querySelector(".ds-kpiCard__value").textContent = overview.active_customers ?? "—";
    cards[2].querySelector(".ds-kpiCard__value").textContent = overview.fleet_vehicles ?? "—";
    cards[3].querySelector(".ds-kpiCard__value").textContent = overview.revenue_net ?? "—";
  }

  function setMini(overview) {
    const vals = miniWrap.querySelectorAll(".ds-miniKpi__value");
    if (vals.length < 4) return;
    vals[0].textContent = overview.active_rentals ?? "—";
    vals[1].textContent = overview.upcoming_bookings ?? "—";
    vals[2].textContent = overview.overdue_rentals ?? "—";
    vals[3].textContent = overview.maintenance_open ?? "—";
  }

  function renderBookings(list) {
    if (!Array.isArray(list) || list.length === 0) {
      bookingsBody.innerHTML = `<tr><td colspan="5" class="ds-empty">No reservations</td></tr>`;
      return;
    }

    bookingsBody.innerHTML = list.slice(0, 6).map(b => `
      <tr>
        <td>${escapeHtml(b.customer?.name || "-")}</td>
        <td>${escapeHtml((b.vehicle?.plate || "-"))}</td>
        <td>${escapeHtml(b.pickup_date || "-")}</td>
        <td>${escapeHtml(b.return_date || "-")}</td>
        <td><span class="ds-badge ds-badge--${String(b.status||"").toLowerCase()}">${escapeHtml(b.status||"-")}</span></td>
      </tr>
    `).join("");
  }

  function renderPayments(list) {
    if (!Array.isArray(list) || list.length === 0) {
      paymentsBody.innerHTML = `<div class="ds-empty">No payments</div>`;
      return;
    }

    paymentsBody.innerHTML = `<div class="ds-list">` + list.slice(0, 6).map(p => `
      <div class="ds-listRow">
        <div class="ds-listRow__left">
          <div class="ds-listRow__icon">💳</div>
          <div>
            <div class="ds-listRow__title">${escapeHtml(p.customer_name || "-")}</div>
            <div class="ds-listRow__sub">Receipt ${escapeHtml(p.receipt_number || "-")} · Booking #${escapeHtml(String(p.booking_id || "-"))}</div>
          </div>
        </div>
        <div class="ds-listRow__right">
          <div class="ds-listRow__amount">${escapeHtml(p.currency || "")} ${escapeHtml(p.amount || "0.000")}</div>
          <div class="ds-listRow__sub">${escapeHtml(p.date || "-")}</div>
        </div>
      </div>
    `).join("") + `</div>`;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
  }

  async function load() {
    try {
      DS_UI.setLoading(overviewCard, true);

      const overview = await DS_API.get(`/api/reports/overview/?period=${encodeURIComponent(period)}`);
      if (!overview.ok) throw new Error(overview.error || "Overview failed");

      setKPIs(overview.data);
      setMini(overview.data);

      const bookings = await DS_API.get(`/api/bookings/?status=`);
      renderBookings(bookings.results || []);

      const payments = await DS_API.get(`/api/payments/`);
      renderPayments(payments.results || []);

      DS_UI.setLoading(overviewCard, false);
    } catch (e) {
      DS_UI.setLoading(overviewCard, false);
      DS_UI.toast("Dashboard", e.message || "Failed to load dashboard data");
      bookingsBody.innerHTML = `<tr><td colspan="5" class="ds-empty">Failed to load</td></tr>`;
      paymentsBody.innerHTML = `<div class="ds-empty">Failed to load</div>`;
    }
  }

  // Period buttons
  overviewCard.querySelectorAll("[data-period]").forEach(btn => {
    btn.addEventListener("click", () => {
      overviewCard.querySelectorAll("[data-period]").forEach(b => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      period = btn.getAttribute("data-period") || "today";
      load();
    });
  });

  load();
})();