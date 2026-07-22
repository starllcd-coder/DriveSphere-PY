/* DriveSphere - Vehicles list + selection + telematics */

(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function safeText(v) {
    return v === null || v === undefined ? "" : String(v);
  }

  function toast(msg) {
    // eslint-disable-next-line no-alert
    alert(msg);
  }

  function debounce(fn, wait) {
    let t = null;
    return (...args) => {
      if (t) clearTimeout(t);
      t = setTimeout(() => fn(...args), wait);
    };
  }

  const root = $("#ds-vehicles");
  if (!root) return;

  function isArabicClient() {
    return document.documentElement.lang === "ar" || document.documentElement.dir === "rtl";
  }

  const elPlateFilter = $("#v-plate");
  const elBrandFilter = $("#v-brand");
  const elModelFilter = $("#v-model");
  const elStatusFilter = $("#v-status");
  const elBody = $("#v-body");

  const btnDocsAdd = $("#v-docs-add");
  const btnDocsView = $("#v-docs-view");
  const btnPhotosAdd = $("#v-photos-add");
  const btnPhotosView = $("#v-photos-view");
  const btnAdd = $("#v-add");
  const btnEdit = $("#v-edit");
  const btnDel = $("#v-del");

  const telematicsCaption = $("#v-telematics-caption");
  const telematicsDays = $("#v-telematics-days");
  const telematicsRefresh = $("#v-telematics-refresh");
  const tabButtons = $$("[data-telematics-tab]");

  const kpiDistance = $("#v-t-distance");
  const kpiSpeed = $("#v-t-speed");
  const kpiIdle = $("#v-t-idle");
  const kpiFuel = $("#v-t-fuel");
  const kpiFuelUsed = $("#v-t-fuel-used");
  const kpiEfficiency = $("#v-t-efficiency");
  const kpiPings = $("#v-t-pings");

  const latestGps = $("#v-t-latest-gps");
  const mapLink = $("#v-t-map-link");
  const engineText = $("#v-t-engine");
  const engineUpdated = $("#v-t-engine-updated");
  const batteryText = $("#v-t-battery");
  const faultsText = $("#v-t-faults");

  const tripsBody = $("#v-t-trips-body");
  const evOverspeed = $("#v-t-overspeed");
  const evBrake = $("#v-t-brake");
  const evAccel = $("#v-t-accel");
  const evLowBattery = $("#v-t-low-battery");
  const evFaultList = $("#v-t-fault-list");

  let selectedVehicleId = null;

  const API = { list: "/web-api/vehicles/" };

  async function jsonFetch(url) {
    const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
  }

  function formatIdle(seconds) {
    const total = Number(seconds || 0);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    return `${h}h ${m}m`;
  }

  function formatDuration(seconds) {
    const total = Number(seconds || 0);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    return `${h}h ${m}m`;
  }

  function resetTelematics() {
    [kpiDistance, kpiSpeed, kpiIdle, kpiFuel, kpiFuelUsed, kpiEfficiency, kpiPings].forEach((el) => {
      if (el) el.textContent = "--";
    });
    if (latestGps) latestGps.textContent = "--";
    if (mapLink) {
      mapLink.style.display = "none";
      mapLink.href = "#";
    }
    if (engineText) engineText.textContent = "--";
    if (engineUpdated) engineUpdated.textContent = "";
    if (batteryText) batteryText.textContent = "--";
    if (faultsText) faultsText.textContent = "";
    if (tripsBody) tripsBody.innerHTML = `<tr><td colspan="6" class="ds-empty">--</td></tr>`;
    if (evOverspeed) evOverspeed.textContent = "--";
    if (evBrake) evBrake.textContent = "--";
    if (evAccel) evAccel.textContent = "--";
    if (evLowBattery) evLowBattery.textContent = "--";
    if (evFaultList) evFaultList.textContent = "";
    if (telematicsCaption) {
      telematicsCaption.textContent = isArabicClient()
        ? "اختر مركبة من الجدول لعرض مقاييس التتبع."
        : "Select a vehicle from the table to view telematics metrics.";
    }
  }

  function activateTelematicsTab(name) {
    tabButtons.forEach((btn) => btn.classList.toggle("is-active", btn.getAttribute("data-telematics-tab") === name));
    $$("[data-telematics-panel]").forEach((panel) => {
      panel.classList.toggle("is-active", panel.getAttribute("data-telematics-panel") === name);
    });
  }

  async function loadTelematicsMetrics(days) {
    const data = await jsonFetch(`/api/vehicles/${selectedVehicleId}/telematics/metrics/?days=${days}`);
    if (kpiDistance) kpiDistance.textContent = `${safeText(data.distance_km)} km`;
    if (kpiSpeed) kpiSpeed.textContent = `${safeText(data.avg_speed_kmh)} km/h`;
    if (kpiIdle) kpiIdle.textContent = formatIdle(data.idle_seconds);
    if (kpiFuel) kpiFuel.textContent = `${safeText(data.avg_fuel_percent)}%`;
    if (kpiFuelUsed) kpiFuelUsed.textContent = `${safeText(data.fuel_used_liters)} L`;
    if (kpiEfficiency) kpiEfficiency.textContent = `${safeText(data.efficiency_km_per_liter)} km/L`;
    if (kpiPings) kpiPings.textContent = safeText(data.pings_count);
    if (telematicsCaption) {
      telematicsCaption.textContent = isArabicClient()
        ? `المركبة: ${safeText(data.plate_number)} • نافذة ${safeText(data.window_days)} يوم`
        : `Vehicle: ${safeText(data.plate_number)} • ${safeText(data.window_days)} day window`;
    }
  }

  async function loadTelematicsLatest() {
    const data = await jsonFetch(`/api/vehicles/${selectedVehicleId}/telematics/latest/`);
    const latest = data.latest;
    if (!latest) {
      if (latestGps) latestGps.textContent = isArabicClient() ? "لا توجد بيانات GPS" : "No GPS data";
      if (engineText) engineText.textContent = "--";
      if (batteryText) batteryText.textContent = "--";
      return;
    }
    if (latestGps) {
      latestGps.textContent = `${safeText(latest.latitude)}, ${safeText(latest.longitude)}`;
    }
    if (mapLink && latest.google_maps_url) {
      mapLink.style.display = "inline";
      mapLink.href = latest.google_maps_url;
    }
    if (engineText) {
      const engineState = latest.engine_on === null ? "Unknown" : latest.engine_on ? "ON" : "OFF";
      engineText.textContent = `${engineState}${latest.engine_status ? ` • ${latest.engine_status}` : ""}`;
    }
    if (engineUpdated) {
      engineUpdated.textContent = latest.recorded_at
        ? new Date(latest.recorded_at).toLocaleString()
        : "";
    }
    if (batteryText) {
      batteryText.textContent = latest.battery_voltage ? `${latest.battery_voltage} V` : "--";
    }
    if (faultsText) {
      const faults = Array.isArray(latest.fault_codes) ? latest.fault_codes : [];
      faultsText.textContent = faults.length ? `Faults: ${faults.join(", ")}` : "Faults: none";
    }
  }

  async function loadTelematicsTrips(days) {
    const data = await jsonFetch(`/api/vehicles/${selectedVehicleId}/telematics/trips/?days=${days}`);
    const trips = Array.isArray(data.trips) ? data.trips : [];
    if (!trips.length) {
      tripsBody.innerHTML = `<tr><td colspan="6" class="ds-empty">${isArabicClient() ? "لا توجد رحلات" : "No trips found"}</td></tr>`;
      return;
    }
    tripsBody.innerHTML = trips.slice(0, 100).map((trip) => `
      <tr>
        <td>${trip.start_at ? new Date(trip.start_at).toLocaleString() : ""}</td>
        <td>${trip.end_at ? new Date(trip.end_at).toLocaleString() : ""}</td>
        <td>${safeText(trip.distance_km)} km</td>
        <td>${formatDuration(trip.duration_seconds)}</td>
        <td>${safeText(trip.max_speed_kmh)} km/h</td>
        <td>${safeText(trip.fuel_used_liters)} L</td>
      </tr>
    `).join("");
  }

  async function loadTelematicsEvents(days) {
    const data = await jsonFetch(`/api/vehicles/${selectedVehicleId}/telematics/events/?days=${days}`);
    if (evOverspeed) evOverspeed.textContent = safeText(data.overspeed_count);
    if (evBrake) evBrake.textContent = safeText(data.harsh_brake_count);
    if (evAccel) evAccel.textContent = safeText(data.harsh_accel_count);
    if (evLowBattery) evLowBattery.textContent = safeText(data.low_battery_events);
    if (evFaultList) {
      const faults = Array.isArray(data.fault_codes) ? data.fault_codes : [];
      evFaultList.textContent = faults.length
        ? `Fault codes: ${faults.join(", ")}`
        : (isArabicClient() ? "لا توجد أكواد أعطال." : "No fault codes.");
    }
  }

  async function loadTelematics() {
    if (!selectedVehicleId) {
      resetTelematics();
      return;
    }
    const days = Number(telematicsDays?.value || 7);
    if (telematicsCaption) {
      telematicsCaption.textContent = isArabicClient() ? "جارٍ تحميل بيانات التتبع..." : "Loading telematics...";
    }
    await Promise.all([
      loadTelematicsMetrics(days),
      loadTelematicsLatest(),
      loadTelematicsTrips(days),
      loadTelematicsEvents(days),
    ]);
  }

  function setSelected(id) {
    selectedVehicleId = id;
    const hasSelection = Boolean(id);
    if (btnDocsAdd) btnDocsAdd.disabled = !hasSelection;
    if (btnDocsView) btnDocsView.disabled = !hasSelection;
    if (btnPhotosAdd) btnPhotosAdd.disabled = !hasSelection;
    if (btnPhotosView) btnPhotosView.disabled = !hasSelection;
    if (btnEdit) btnEdit.disabled = !hasSelection;
    if (btnDel) btnDel.disabled = !hasSelection;
    if (telematicsRefresh) telematicsRefresh.disabled = !hasSelection;

    $$("tr[data-id]", elBody).forEach((tr) => {
      tr.classList.toggle("is-selected", String(tr.getAttribute("data-id")) === String(id));
    });

    if (hasSelection) {
      loadTelematics().catch((e) => {
        if (telematicsCaption) {
          telematicsCaption.textContent = isArabicClient()
            ? "تعذر تحميل بيانات التتبع."
            : "Failed to load telematics data.";
        }
        toast(e.message);
      });
    } else {
      resetTelematics();
    }
  }

  function renderVehicles(rows) {
    if (!rows || rows.length === 0) {
      elBody.innerHTML = `<tr><td colspan="9" class="ds-empty">${isArabicClient() ? "لا توجد مركبات" : "No vehicles found"}</td></tr>`;
      setSelected(null);
      return;
    }

    elBody.innerHTML = rows.map((v) => {
      const brandModel = `${safeText(v.brand_name)} / ${safeText(v.model_name)}`.trim();
      return `
        <tr data-id="${v.id}">
          <td>${safeText(v.plate_number)}</td>
          <td>${brandModel}</td>
          <td>${safeText(v.year)}</td>
          <td>${safeText(v.category)}</td>
          <td>${safeText(v.transmission)}</td>
          <td>${safeText(v.fuel_type || v.fuel)}</td>
          <td>${safeText(v.color)}</td>
          <td>${safeText(v.status_label || v.status)}</td>
          <td>${safeText(v.daily_rate)}</td>
        </tr>
      `;
    }).join("");

    $$("tr[data-id]", elBody).forEach((tr) => {
      tr.addEventListener("click", () => setSelected(tr.getAttribute("data-id")));
      tr.style.cursor = "pointer";
    });

    setSelected(null);
  }

  async function loadVehicles() {
    const params = new URLSearchParams();
    if (elPlateFilter.value.trim()) params.set("plate", elPlateFilter.value.trim());
    if (elBrandFilter.value.trim()) params.set("brand", elBrandFilter.value.trim());
    if (elModelFilter.value.trim()) params.set("model", elModelFilter.value.trim());
    if (elStatusFilter.value.trim()) params.set("status", elStatusFilter.value.trim());

    elBody.innerHTML = `<tr><td colspan="9" class="ds-empty">${isArabicClient() ? "جارٍ التحميل..." : "Loading..."}</td></tr>`;
    const data = await jsonFetch(`${API.list}?${params.toString()}`);
    const rows = Array.isArray(data) ? data : (data.results || data.data || []);
    renderVehicles(rows);
  }

  function wireFilters() {
    const handler = () => loadVehicles().catch((e) => toast(e.message));
    [elPlateFilter, elBrandFilter, elModelFilter].forEach((el) => {
      el.addEventListener("input", debounce(handler, 250));
    });
    if (elStatusFilter) elStatusFilter.addEventListener("change", handler);
  }

  function wireButtons() {
    if (btnAdd) {
      btnAdd.addEventListener("click", () => {
        window.location.href = "/vehicles/new/";
      });
    }

    if (btnEdit) {
      btnEdit.addEventListener("click", () => {
        if (!selectedVehicleId) return;
        window.location.href = `/vehicles/${selectedVehicleId}/edit/`;
      });
    }

    if (btnDel) {
      btnDel.addEventListener("click", () => {
        if (!selectedVehicleId) return;
        // eslint-disable-next-line no-alert
        if (!confirm(isArabicClient() ? "هل تريد حذف هذه المركبة؟" : "Delete this vehicle?")) return;
        window.location.href = `/vehicles/${selectedVehicleId}/delete/`;
      });
    }

    [btnDocsAdd, btnDocsView].forEach((btn) => {
      if (!btn) return;
      btn.addEventListener("click", () => {
        if (!selectedVehicleId) return;
        window.location.href = `/vehicles/${selectedVehicleId}/documents/`;
      });
    });

    [btnPhotosAdd, btnPhotosView].forEach((btn) => {
      if (!btn) return;
      btn.addEventListener("click", () => {
        if (!selectedVehicleId) return;
        window.location.href = `/vehicles/${selectedVehicleId}/photos/`;
      });
    });

    telematicsRefresh?.addEventListener("click", () => {
      loadTelematics().catch((e) => toast(e.message));
    });
    telematicsDays?.addEventListener("change", () => {
      if (!selectedVehicleId) return;
      loadTelematics().catch((e) => toast(e.message));
    });
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => activateTelematicsTab(btn.getAttribute("data-telematics-tab")));
    });
  }

  function init() {
    wireFilters();
    wireButtons();
    resetTelematics();
    activateTelematicsTab("overview");
    loadVehicles().catch((e) => toast(e.message));
  }

  init();
})();
