(function () {
  const root = document.getElementById("ds-booking-return");
  if (!root) return;

  const bookingId = root.getAttribute("data-booking-id");
  const btnSubmit = document.getElementById("r-submit");
  const btnReport = document.getElementById("r-report");
  const extraKmInput = document.getElementById("r-extra-km");
  const odoInInput = document.getElementById("r-odo");
  const odoOutInput = document.getElementById("r-odo-out");
  const includedKmInput = document.getElementById("r-included-km");
  const paymentAmountInput = document.getElementById("r-payment-amount");

  let paymentAmountManual = false;

  let extraKmManual = false;

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  const CSRF = getCookie("csrftoken");

  function val(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
  }

  function numberVal(id) {
    const n = parseFloat(val(id) || "0");
    return Number.isNaN(n) ? 0 : n;
  }

  function parseYmd(value) {
    if (!value) return null;
    const parts = String(value).split("-");
    if (parts.length !== 3) return null;
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const d = parseInt(parts[2], 10);
    if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) return null;
    return new Date(y, m - 1, d);
  }

  function dayDiff(start, end) {
    if (!start || !end) return 1;
    const ms = end.getTime() - start.getTime();
    const days = Math.floor(ms / (24 * 60 * 60 * 1000));
    return Math.max(days, 1);
  }

  function updateSummary() {
    const days = parseInt(root.getAttribute("data-days") || "1", 10) || 1;
    const includedPerDay = parseInt(root.getAttribute("data-included-km-per-day") || "200", 10) || 200;
    const bookedDays = Math.max(days, 1);

    const pickupDate = parseYmd(root.getAttribute("data-pickup-date"));
    const plannedReturnDate = parseYmd(root.getAttribute("data-planned-return-date"));
    const actualReturnDate = parseYmd(val("r-date"));
    let usedDays = bookedDays;
    if (pickupDate && plannedReturnDate && actualReturnDate && actualReturnDate < plannedReturnDate) {
      usedDays = dayDiff(pickupDate, actualReturnDate);
    }
    usedDays = Math.min(Math.max(usedDays, 1), bookedDays);

    const includedTotal = usedDays * Math.max(includedPerDay, 0);

    const odoOut = numberVal("r-odo-out");
    const odoIn = numberVal("r-odo");
    const totalKm = Math.max(0, odoIn - odoOut);

    if (includedKmInput) includedKmInput.value = String(includedTotal);

    if (!extraKmManual && extraKmInput) {
      extraKmInput.value = String(Math.max(0, totalKm - includedTotal));
    }

    const extraKm = numberVal("r-extra-km");
    const rate = numberVal("r-rate");
    const extraCharge = extraKm * rate;
    const extraChargeEl = document.getElementById("r-extra-charge");
    if (extraChargeEl) extraChargeEl.value = extraCharge.toFixed(3);

    const total = parseFloat(root.getAttribute("data-total") || "0") || 0;
    const dailyRate = parseFloat(root.getAttribute("data-daily-rate") || "0") || 0;
    const extrasTotal = parseFloat(root.getAttribute("data-extras-total") || "0") || 0;
    const vatRate = parseFloat(root.getAttribute("data-vat-rate") || "0") || 0;
    const proratedSubtotal = dailyRate * usedDays + extrasTotal;
    const proratedTotal = proratedSubtotal + (proratedSubtotal * vatRate);
    const earlyReturnCredit = usedDays < bookedDays ? Math.max(0, total - proratedTotal) : 0;
    const creditEl = document.getElementById("r-early-credit");
    if (creditEl) creditEl.textContent = earlyReturnCredit.toFixed(3);

    const additions = extraCharge
      + numberVal("r-fuel-charge")
      + numberVal("r-late-fee")
      + numberVal("r-damage-fee")
      + numberVal("r-other-fee")
      - earlyReturnCredit;
    const addEl = document.getElementById("r-additions");
    if (addEl) addEl.textContent = additions.toFixed(3);

    const alreadyPaid = parseFloat(root.getAttribute("data-already-paid") || "0") || 0;
    const alreadyPaidEl = document.getElementById("r-already-paid");
    if (alreadyPaidEl) alreadyPaidEl.textContent = alreadyPaid.toFixed(3);

    const deposit = parseFloat(root.getAttribute("data-deposit") || "0") || 0;
    const finalEl = document.getElementById("r-final");
    const payable = total + additions - deposit;
    const balanceDue = (payable - alreadyPaid).toFixed(3);
    if (finalEl) finalEl.textContent = balanceDue;

    if (paymentAmountInput && !paymentAmountManual) {
      paymentAmountInput.value = Math.max(parseFloat(balanceDue), 0).toFixed(3);
    }
  }

  ["r-date", "r-extra-km", "r-fuel-charge", "r-late-fee", "r-damage-fee", "r-other-fee", "r-odo", "r-odo-out"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", updateSummary);
  });

  if (extraKmInput) {
    extraKmInput.addEventListener("input", () => {
      extraKmManual = true;
    });
  }

  if (paymentAmountInput) {
    paymentAmountInput.addEventListener("input", () => {
      paymentAmountManual = true;
    });
  }

  async function submitReturn(preOpen) {
    if (!bookingId) return;
    const payload = {
      date: val("r-date"),
      odo: val("r-odo"),
      fuel: val("r-fuel"),
      extra_km: val("r-extra-km"),
      fuel_charge: val("r-fuel-charge"),
      late_fee: val("r-late-fee"),
      damage_fee: val("r-damage-fee"),
      other_fee: val("r-other-fee"),
      damage: val("r-damage"),
      signature: val("returnSignatureData"),
      inspector_name: val("r-inspector-name"),
      payment_amount: val("r-payment-amount"),
      payment_method: val("r-payment-method"),
      payment_notes: val("r-payment-notes"),
    };

    const resp = await fetch(`/api/bookings/${bookingId}/return/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": CSRF,
      },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();
    if (!data.ok) {
      if (preOpen && !preOpen.closed) preOpen.close();
      alert(data.error || "Failed");
      return;
    }

    const finalEl = document.getElementById("r-final");
    if (finalEl) finalEl.textContent = String(data.balance_due ?? data.due ?? "0");
    const creditEl = document.getElementById("r-early-credit");
    if (creditEl) creditEl.textContent = String(data.early_return_credit || "0");
    if (typeof data.already_paid !== "undefined") {
      root.setAttribute("data-already-paid", String(data.already_paid));
      const alreadyPaidEl = document.getElementById("r-already-paid");
      if (alreadyPaidEl) alreadyPaidEl.textContent = String(data.already_paid);
    }

    const url = `/print/bookings/${bookingId}/invoice/`;
    if (preOpen && !preOpen.closed) {
      preOpen.location = url;
    } else {
      window.open(url, "_blank");
    }

    window.location.href = "/bookings/";
  }

  if (btnSubmit) {
    btnSubmit.addEventListener("click", function (e) {
      e.preventDefault();
      const preOpen = window.open("", "_blank");
      submitReturn(preOpen);
    });
  }

  if (btnReport) {
    btnReport.addEventListener("click", function (e) {
      e.preventDefault();
      if (bookingId) window.open(`/print/bookings/${bookingId}/return-report/`, "_blank");
    });
  }

  // Damage photo uploads
  const photoInput = document.getElementById("r-photo-files");
  const photoUpload = document.getElementById("r-photo-upload");
  const photoGrid = document.getElementById("r-photo-grid");

  async function loadPhotos() {
    if (!photoGrid || !bookingId) return;
    const res = await fetch(`/api/bookings/${bookingId}/return/photos/`, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });
    const data = await res.json();
    if (!data.ok) {
      photoGrid.innerHTML = "";
      return;
    }
    const items = data.results || [];
    photoGrid.innerHTML = items.map((p) => `
      <div class="ds-photoCard" data-photo="${p.id}">
        <img src="${p.url}" alt="Damage Photo">
        <button class="ds-photoCard__delete" data-photo-del="${p.id}">Delete</button>
      </div>
    `).join("") || "<div class=\"ds-empty\">No Photos</div>";

    photoGrid.querySelectorAll("[data-photo-del]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-photo-del");
        if (!id) return;
        const resp = await fetch(`/api/bookings/${bookingId}/return/photos/${id}/delete/`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": CSRF,
          }
        });
        const out = await resp.json();
        if (!out.ok) return alert(out.error || "Failed");
        loadPhotos();
      });
    });
  }

  if (photoUpload && photoInput) {
    photoUpload.addEventListener("click", async (e) => {
      e.preventDefault();
      if (!bookingId) return;
      if (!photoInput.files || photoInput.files.length === 0) return;
      const fd = new FormData();
      Array.from(photoInput.files).forEach((f) => fd.append("files", f));
      const resp = await fetch(`/api/bookings/${bookingId}/return/photos/upload/`, {
        method: "POST",
        body: fd,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": CSRF,
        }
      });
      const out = await resp.json();
      if (!out.ok) return alert(out.error || "Failed");
      photoInput.value = "";
      loadPhotos();
    });
  }

  updateSummary();
  loadPhotos();
})();
