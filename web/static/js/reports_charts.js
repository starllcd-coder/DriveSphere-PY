(function () {
  const root = document.getElementById("ds-reports");
  if (!root) return;

  const canOverview = root.dataset.canOverview === "1";
  const canRevenue = root.dataset.canRevenue === "1";
  const canFinancial = root.dataset.canFinancial === "1";
  const canFleet = root.dataset.canFleet === "1";
  const canMaintenance = root.dataset.canMaintenance === "1";
  const canCustomers = root.dataset.canCustomers === "1";
  const fromInput = root.querySelector('input[name="from"]');
  const toInput = root.querySelector('input[name="to"]');
  const applyBtn = root.querySelector("[data-filter-apply]");
  const resetBtn = root.querySelector("[data-filter-reset]");

  let period = "today";

  const charts = {};

  function setActivePeriod(btn) {
    document.querySelectorAll("[data-period]").forEach(b => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    period = btn.getAttribute("data-period");
    if (fromInput) fromInput.value = "";
    if (toInput) toInput.value = "";
    updatePrintLinks();
    loadAll();
  }

  document.querySelectorAll("[data-period]").forEach(btn => {
    btn.addEventListener("click", () => setActivePeriod(btn));
  });

  function validateDateRangeOrToast() {
    const from = fromInput?.value?.trim() || "";
    const to = toInput?.value?.trim() || "";
    if ((from && !to) || (!from && to)) {
      DS_UI.toast("Reports", "Select both From and To dates");
      return false;
    }
    return true;
  }

  if (applyBtn) {
    applyBtn.addEventListener("click", () => {
      if (!validateDateRangeOrToast()) return;
      updatePrintLinks();
      loadAll();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (fromInput) fromInput.value = "";
      if (toInput) toInput.value = "";
      const todayBtn = document.querySelector('[data-period="today"]');
      if (todayBtn) {
        setActivePeriod(todayBtn);
        return;
      }
      period = "today";
      updatePrintLinks();
      loadAll();
    });
  }

  document.querySelectorAll(".ds-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");

      document.querySelectorAll(".ds-tab").forEach(t => t.classList.remove("is-active"));
      tab.classList.add("is-active");

      document.querySelectorAll(".ds-tabPanel").forEach(p => {
        p.classList.toggle("is-active", p.getAttribute("data-panel") === target);
      });
    });
  });

  function updatePrintLinks() {
    const from = fromInput?.value?.trim() || "";
    const to = toInput?.value?.trim() || "";

    document.querySelectorAll("[data-print-base]").forEach((link) => {
      const base = link.getAttribute("data-print-base") || "";
      const url = new URL(base, window.location.origin);
      url.searchParams.set("period", period);
      if (from && to) {
        url.searchParams.set("date_from", from);
        url.searchParams.set("date_to", to);
      }
      link.setAttribute("href", url.toString());
    });

    document.querySelectorAll("[data-pdf-base]").forEach((link) => {
      const base = link.getAttribute("data-pdf-base") || "";
      const url = new URL(base, window.location.origin);
      url.searchParams.set("period", period);
      if (from && to) {
        url.searchParams.set("date_from", from);
        url.searchParams.set("date_to", to);
      }
      link.setAttribute("href", url.toString());
    });
  }

  function reportQuery() {
    const params = new URLSearchParams();
    params.set("period", period);
    const from = fromInput?.value?.trim() || "";
    const to = toInput?.value?.trim() || "";
    if (from && to) {
      params.set("date_from", from);
      params.set("date_to", to);
    }
    return params.toString();
  }

  function sumValues(values) {
    return values.reduce((sum, v) => sum + (Number(v) || 0), 0);
  }

  function formatPercent(value, total) {
    if (!total) return "0%";
    return `${((Number(value) || 0) / total * 100).toFixed(1)}%`;
  }

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[m]));
  }

  function makeChart(id, type, labels, data, label) {
    const ctx = document.getElementById(id);
    if (!ctx) return;

    if (charts[id]) charts[id].destroy();

    const total = sumValues(data);

    charts[id] = new Chart(ctx, {
      type,
      data: {
        labels,
        datasets: [{
          label,
          data,
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed;
                const percent = formatPercent(value, total);
                return `${context.dataset.label}: ${value} (${percent})`;
              }
            }
          }
        }
      }
    });
  }

  function renderRevenueTable(rows) {
    const body = document.getElementById("r-revenue-table");
    if (!body) return;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="11" class="ds-empty">No data</td></tr>`;
      return;
    }

    body.innerHTML = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.date)}</td>
        <td>${escapeHtml(row.trip_id)}</td>
        <td>${escapeHtml(row.customer)}</td>
        <td>${escapeHtml(row.vehicle)}</td>
        <td>${escapeHtml(row.distance)}</td>
        <td>${escapeHtml(row.fare)}</td>
        <td>${escapeHtml(row.tax)}</td>
        <td>${escapeHtml(row.discount)}</td>
        <td>${escapeHtml(row.total)}</td>
        <td>${escapeHtml(row.method)}</td>
        <td>${escapeHtml(row.status)}</td>
      </tr>
    `).join("");
  }

  function renderFinancialTable(rows) {
    const body = document.getElementById("r-financial-table");
    if (!body) return;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="7" class="ds-empty">No data</td></tr>`;
      return;
    }

    body.innerHTML = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.date)}</td>
        <td>${escapeHtml(row.revenue)}</td>
        <td>${escapeHtml(row.maintenance_cost)}</td>
        <td>${escapeHtml(row.fuel_cost)}</td>
        <td>${escapeHtml(row.other_expenses)}</td>
        <td>${escapeHtml(row.total_expenses)}</td>
        <td>${escapeHtml(row.net_profit)}</td>
      </tr>
    `).join("");
  }

  function renderFleetTable(rows) {
    const body = document.getElementById("r-fleet-table");
    if (!body) return;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="7" class="ds-empty">No data</td></tr>`;
      return;
    }

    body.innerHTML = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.vehicle_id)}</td>
        <td>${escapeHtml(row.vehicle_name)}</td>
        <td>${escapeHtml(row.trips_completed)}</td>
        <td>${escapeHtml(row.distance_driven)}</td>
        <td>${escapeHtml(row.revenue_generated)}</td>
        <td>${escapeHtml(row.status)}</td>
        <td>${escapeHtml(row.last_service)}</td>
      </tr>
    `).join("");
  }

  function renderMaintenanceTable(rows) {
    const body = document.getElementById("r-maintenance-table");
    if (!body) return;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="7" class="ds-empty">No data</td></tr>`;
      return;
    }

    body.innerHTML = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.date)}</td>
        <td>${escapeHtml(row.vehicle)}</td>
        <td>${escapeHtml(row.service_type)}</td>
        <td>${escapeHtml(row.description)}</td>
        <td>${escapeHtml(row.cost)}</td>
        <td>${escapeHtml(row.mechanic)}</td>
        <td>${escapeHtml(row.status)}</td>
      </tr>
    `).join("");
  }

  function renderCustomersTable(rows) {
    const body = document.getElementById("r-customers-table");
    if (!body) return;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="6" class="ds-empty">No data</td></tr>`;
      return;
    }

    body.innerHTML = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.customer_id)}</td>
        <td>${escapeHtml(row.name)}</td>
        <td>${escapeHtml(row.total_trips)}</td>
        <td>${escapeHtml(row.total_spent)}</td>
        <td>${escapeHtml(row.last_trip)}</td>
        <td>${escapeHtml(row.status)}</td>
      </tr>
    `).join("");
  }

  function renderOverviewTable(rows) {
    const body = document.getElementById("r-overview-table");
    if (!body) return;
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="11" class="ds-empty">No data</td></tr>`;
      return;
    }

    body.innerHTML = rows.map((row) => `
      <tr>
        <td>${escapeHtml(row.period)}</td>
        <td>${escapeHtml(row.new_customers)}</td>
        <td>${escapeHtml(row.total_customers)}</td>
        <td>${escapeHtml(row.revenue)}</td>
        <td>${escapeHtml(row.trips)}</td>
        <td>${escapeHtml(row.active_vehicles)}</td>
        <td>${escapeHtml(row.completed_trips)}</td>
        <td>${escapeHtml(row.cancelled_trips)}</td>
        <td>${escapeHtml(row.collection_rate)}%</td>
        <td>${escapeHtml(row.pending_balance)}</td>
        <td>${escapeHtml(row.fleet_utilization)}%</td>
      </tr>
    `).join("");
  }

  function setOverview(data) {
    const cards = document.querySelectorAll("#r-overview-kpis .ds-kpiCard__value");
    if (!cards.length) return;

    cards[0].textContent = data.bookings_count ?? "—";
    cards[1].textContent = data.revenue_net ?? "—";
    cards[2].textContent = data.active_customers ?? "—";
    cards[3].textContent = data.fleet_vehicles ?? "—";
  }

  function renderOverviewMetrics(data) {
    const root = document.getElementById("r-overview-kpis");
    if (!root) return;

    const metrics = [
      { label: "Bookings", value: data.bookings_count ?? "-" },
      { label: "Net Revenue", value: data.revenue_net ?? "-" },
      { label: "Net Profit", value: data.net_profit ?? "-" },
      { label: "Pending Balance", value: data.pending_balance ?? "-" },
      { label: "Collection Rate", value: `${data.collection_rate ?? 0}%` },
      { label: "Fleet Utilization", value: `${data.fleet_utilization ?? 0}%` },
      { label: "Avg Booking", value: data.avg_booking_value ?? "-" },
      { label: "Maintenance Open", value: data.maintenance_open ?? "-" },
    ];

    root.innerHTML = `
      <div class="ds-grid ds-grid--kpis" style="margin-top:12px;">
        ${metrics.map((item) => `
          <article class="ds-kpi ds-kpi--blue">
            <div class="ds-kpi__meta">
              <div class="ds-kpi__label">${escapeHtml(item.label)}</div>
              <div class="ds-kpi__value">${escapeHtml(item.value)}</div>
            </div>
          </article>
        `).join("")}
      </div>
    `;
  }

  async function loadOverview() {
    if (!canOverview) return;
    const query = reportQuery();
    const res = await DS_API.get(`/api/reports/overview/?${query}`);
    if (res.ok) renderOverviewMetrics(res.data);

    const table = await DS_API.get(`/api/reports/overview/table/?${query}`);
    if (table.ok) renderOverviewTable(table.rows || []);
  }

  async function loadRevenue() {
    if (!canRevenue) return;
    const query = reportQuery();
    const res = await DS_API.get(`/api/reports/revenue/?${query}`);
    if (res.ok) makeChart("chart-revenue", "bar", res.labels, res.data, "Revenue");

    const table = await DS_API.get(`/api/reports/revenue/table/?${query}`);
    if (table.ok) renderRevenueTable(table.rows || []);
  }

  async function loadFinancial() {
    if (!canFinancial) return;
    const query = reportQuery();
    const res = await DS_API.get(`/api/reports/financial/?${query}`);
    if (res.ok) makeChart("chart-financial", "line", res.labels, res.data, "Net Profit");

    const table = await DS_API.get(`/api/reports/financial/table/?${query}`);
    if (table.ok) renderFinancialTable(table.rows || []);
  }

  async function loadFleet() {
    if (!canFleet) return;
    const query = reportQuery();
    const res = await DS_API.get(`/api/reports/fleet/?${query}`);
    if (res.ok) makeChart("chart-fleet", "doughnut", res.labels, res.data, "Fleet");

    const table = await DS_API.get(`/api/reports/fleet/table/?${query}`);
    if (table.ok) renderFleetTable(table.rows || []);
  }

  async function loadMaintenance() {
    if (!canMaintenance) return;
    const query = reportQuery();
    const res = await DS_API.get(`/api/reports/maintenance/?${query}`);
    if (res.ok) makeChart("chart-maintenance", "bar", res.labels, res.data, "Maintenance");

    const table = await DS_API.get(`/api/reports/maintenance/table/?${query}`);
    if (table.ok) renderMaintenanceTable(table.rows || []);
  }

  async function loadCustomers() {
    if (!canCustomers) return;
    const query = reportQuery();
    const res = await DS_API.get(`/api/reports/customers/?${query}`);
    if (res.ok) makeChart("chart-customers", "line", res.labels, res.data, "Customers");

    const table = await DS_API.get(`/api/reports/customers/table/?${query}`);
    if (table.ok) renderCustomersTable(table.rows || []);
  }

  async function loadAll() {
    try {
      const loaders = [
        loadOverview(),
        loadRevenue(),
        loadFinancial(),
        loadFleet(),
        loadMaintenance(),
        loadCustomers(),
      ];
      await Promise.all(loaders);
    } catch (e) {
      DS_UI.toast("Reports", "Failed to load reports");
    }
  }

  updatePrintLinks();
  loadAll();
})();
