(function () {

  const wiz = document.getElementById("bookingWizard");
  if (!wiz) return;

  let step = 1;
  let selectedVehicle = null;
  let rate = 0;
  let extrasTotal = 0;

  /* =========================
     Step Navigation
     ========================= */
  function showStep(s) {
    step = s;

    document.querySelectorAll(".ds-step").forEach(el => {
      el.classList.toggle("is-active", el.dataset.step == s);
    });

    document.querySelectorAll(".ds-wizard__section").forEach(sec => {
      sec.classList.toggle("is-active", sec.dataset.section == s);
    });
  }

  wiz.querySelectorAll("[data-next]").forEach(btn => {
    btn.addEventListener("click", () => {
      const section = wiz.querySelector(`.ds-wizard__section[data-section="${step}"]`);
      if (section && !DS_UI.validateRequired(section)) return;
      showStep(step + 1);
    });
  });

  wiz.querySelectorAll("[data-back]").forEach(btn => {
    btn.addEventListener("click", () => showStep(step - 1));
  });

  /* =========================
     Customer search
     ========================= */
  const custSearch = document.getElementById("custSearch");
  const custResults = document.getElementById("custResults");

  if (custSearch && custResults) {
    custSearch.addEventListener("input", async () => {
      const q = custSearch.value.trim();
      if (!q) {
        custResults.innerHTML = "";
        return;
      }

      try {
        const res = await DS_API.get(`/api/customers/?search=${encodeURIComponent(q)}`);
        if (!res.ok) return;

        custResults.innerHTML = res.results.map(c => `
          <tr data-name="${c.name}" data-phone="${c.phone}" data-id="${c.id_number}">
            <td>${c.name}</td>
            <td>${c.phone}</td>
            <td>${c.id_number}</td>
          </tr>
        `).join("");

      } catch {
        custResults.innerHTML = "";
      }
    });

    custResults.addEventListener("click", e => {
      const row = e.target.closest("tr");
      if (!row) return;

      document.getElementById("custName").value = row.dataset.name || "";
      document.getElementById("custPhone").value = row.dataset.phone || "";
      document.getElementById("custId").value = row.dataset.id || "";
    });
  }

  /* =========================
     Vehicle availability
     ========================= */
  const pickupInput = document.getElementById("pickupDate");
  const returnInput = document.getElementById("returnDate");
  const vehicleResults = document.getElementById("vehicleResults");

  async function loadVehicles() {
    if (!pickupInput.value || !returnInput.value) return;

    try {
      const res = await DS_API.get(`/api/availability/?pickup=${pickupInput.value}&return=${returnInput.value}`);
      if (!res.ok) return;

      vehicleResults.innerHTML = res.vehicles.map(v => `
        <tr data-id="${v.id}" data-rate="${v.rate}">
          <td>${v.brand} ${v.model}</td>
          <td>${v.plate}</td>
          <td>${v.rate}</td>
          <td><button class="ds-btn ds-btn--small selectVehicle">Select</button></td>
        </tr>
      `).join("");

    } catch {
      vehicleResults.innerHTML = "";
    }
  }

  pickupInput?.addEventListener("change", loadVehicles);
  returnInput?.addEventListener("change", loadVehicles);

  vehicleResults?.addEventListener("click", e => {
    if (!e.target.classList.contains("selectVehicle")) return;

    const row = e.target.closest("tr");
    selectedVehicle = row.dataset.id;
    rate = parseFloat(row.dataset.rate || 0);

    vehicleResults.querySelectorAll("tr").forEach(r => r.classList.remove("is-selected"));
    row.classList.add("is-selected");
  });

  /* =========================
     Extras calculation
     ========================= */
  document.querySelectorAll(".extra").forEach(el => {
    el.addEventListener("change", () => {
      extrasTotal = 0;
      document.querySelectorAll(".extra:checked").forEach(x => {
        extrasTotal += parseFloat(x.dataset.price || 0);
      });
      const out = document.getElementById("extrasTotal");
      if (out) out.textContent = extrasTotal;
    });
  });

  /* =========================
     Pricing summary
     ========================= */
  function calcSummary() {
    const p = new Date(pickupInput.value);
    const r = new Date(returnInput.value);
    const days = Math.max(1, Math.ceil((r - p) / 86400000));

    document.getElementById("sumDays").textContent = days;
    document.getElementById("sumRate").textContent = rate;
    document.getElementById("sumExtras").textContent = extrasTotal;
    document.getElementById("sumTotal").textContent = (days * rate) + extrasTotal;
  }

  document.querySelector('[data-section="6"]')?.addEventListener("mouseenter", calcSummary);

  /* =========================
     Signature
     ========================= */
  const canvas = document.getElementById("signCanvas");
  let signatureData = null;

  if (canvas) {
    const ctx = canvas.getContext("2d");
    let draw = false;

    canvas.addEventListener("mousedown", () => draw = true);
    canvas.addEventListener("mouseup", () => draw = false);
    canvas.addEventListener("mousemove", e => {
      if (!draw) return;
      ctx.lineTo(e.offsetX, e.offsetY);
      ctx.stroke();
    });

    document.getElementById("clearSign")?.addEventListener("click", () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      signatureData = null;
    });
  }

  /* =========================
     Finish booking
     ========================= */
  document.getElementById("finishBooking")?.addEventListener("click", async () => {

    if (!selectedVehicle) {
      DS_UI.toast("Vehicle", "Select vehicle first");
      return;
    }

    const btn = document.getElementById("finishBooking");
    btn.disabled = true;

    const payload = {
      customer_name: custName.value,
      phone: custPhone.value,
      id_number: custId.value,
      vehicle_id: selectedVehicle,
      pickup: pickupInput.value,
      return: returnInput.value,
      extras_total: extrasTotal,
      rate: rate,
      odo_out: odoOut.value,
      fuel_out: fuelOut.value,
      signature: canvas ? canvas.toDataURL() : null
    };

    try {
      const res = await DS_API.post("/api/bookings/create/", payload);
      if (res.ok) {
        DS_UI.toast("Booking", "Created successfully");
        showStep(9);
      } else {
        DS_UI.toast("Booking", "Failed to save");
      }
    } catch {
      DS_UI.toast("Booking", "Server error");
    }

    btn.disabled = false;
  });

})();