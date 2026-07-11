(function () {
  const root = document.getElementById("ds-reports");
  if (!root) return;

  let period = "today";

  const charts = {};

  function setActivePeriod(btn) {
    document.querySelectorAll("[data-period]").forEach(b => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    period = btn.getAttribute("data-period");
    loadAll();
  }

  document.querySelectorAll("[data-period]").forEach(btn => {
    btn.addEventListener("click", () => setActivePeriod(btn));
  });

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

  function makeChart(id, type, labels, data, label) {
    const ctx = document.getElementById(id);
    if (!ctx) return;

    if (charts[id]) charts[id].destroy();

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
      }
    });
  }

  function setOverview(data) {
    const cards = document.querySelectorAll("#r-overview-kpis .ds-kpiCard__value");
    if (!cards.length) return;

    cards[0].textContent = data.bookings ?? "—";
    cards[1].textContent = data.revenue ?? "—";
    cards[2].textContent = data.customers ?? "—";
    cards[3].textContent = data.fleet ?? "—";
  }

  async function loadOverview() {
    const res = await DS_API.get(`/api/reports/overview/?period=${period}`);
    if (res.ok) setOverview(res.data);
  }

  async function loadRevenue() {
    const res = await DS_API.get(`/api/reports/revenue/?period=${period}`);
    if (!res.ok) return;
    makeChart("chart-revenue", "bar", res.labels, res.data, "Revenue");
  }

  async function loadFinancial() {
    const res = await DS_API.get(`/api/reports/financial/?period=${period}`);
    if (!res.ok) return;
    makeChart("chart-financial", "line", res.labels, res.data, "Financial");
  }

  async function loadFleet() {
    const res = await DS_API.get(`/api/reports/fleet/?period=${period}`);
    if (!res.ok) return;
    makeChart("chart-fleet", "doughnut", res.labels, res.data, "Fleet");
  }

  async function loadMaintenance() {
    const res = await DS_API.get(`/api/reports/maintenance/?period=${period}`);
    if (!res.ok) return;
    makeChart("chart-maintenance", "bar", res.labels, res.data, "Maintenance");
  }

  async function loadCustomers() {
    const res = await DS_API.get(`/api/reports/customers/?period=${period}`);
    if (!res.ok) return;
    makeChart("chart-customers", "line", res.labels, res.data, "Customers");
  }

  async function loadAll() {
    try {
      await Promise.all([
        loadOverview(),
        loadRevenue(),
        loadFinancial(),
        loadFleet(),
        loadMaintenance(),
        loadCustomers()
      ]);
    } catch (e) {
      DS_UI.toast("Reports", "Failed to load reports");
    }
  }

  loadAll();
})();