(function () {
  function isArabicClient() {
    return document.documentElement.lang === "ar" || document.documentElement.dir === "rtl";
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  const CSRF = getCookie("csrftoken");

  function jsonFetch(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": CSRF,
      },
      body: JSON.stringify(payload || {}),
    }).then((r) => r.json());
  }

  function openModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.add("is-open");
  }

  function closeModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.remove("is-open");
  }

  document.addEventListener("click", function (e) {
    const open = e.target.closest("[data-open]");
    if (open) openModal(open.getAttribute("data-open"));

    const close = e.target.closest("[data-close]");
    if (close) closeModal(close.getAttribute("data-close"));
  });

  const npSave = document.getElementById("np-save");
  const npId = document.getElementById("np-id");
  const npBooking = document.getElementById("np-booking");
  const npAmount = document.getElementById("np-amount");
  const npMethod = document.getElementById("np-method");
  const npNotes = document.getElementById("np-notes");

  const rfSave = document.getElementById("rf-save");
  const rfPayment = document.getElementById("rf-payment");
  const rfAmount = document.getElementById("rf-amount");
  const rfMethod = document.getElementById("rf-method");
  const rfNotes = document.getElementById("rf-notes");

  if (npSave) {
    npSave.addEventListener("click", async () => {
      const payload = {
        booking_id: npBooking.value,
        amount: npAmount.value,
        method: npMethod.value || "CASH",
        notes: npNotes.value,
      };

      let data;
      if (npId.value) {
        payload.payment_id = npId.value;
        data = await jsonFetch(`/api/payments/${npId.value}/update/`, payload);
      } else {
        data = await jsonFetch("/api/payments/create/", payload);
      }

      if (!data.ok) {
        alert(data.error || "Failed");
        return;
      }
      closeModal("newPayment");
      window.location.reload();
    });
  }

  if (rfSave) {
    rfSave.addEventListener("click", async () => {
      const payload = {
        payment_id: rfPayment.value,
        amount: rfAmount.value,
        method: rfMethod.value || "CASH",
        notes: rfNotes.value,
      };
      const data = await jsonFetch("/api/refunds/create/", payload);
      if (!data.ok) {
        alert(data.error || "Failed");
        return;
      }
      closeModal("refund");
      window.location.reload();
    });
  }

  document.addEventListener("click", function (e) {
    const edit = e.target.closest("[data-payment-edit]");
    if (!edit) return;
    const row = edit.closest("tr");
    if (!row) return;

    npId.value = edit.getAttribute("data-payment-edit") || "";
    npBooking.value = row.getAttribute("data-booking") || "";
    npAmount.value = row.getAttribute("data-amount") || "";
    npMethod.value = row.getAttribute("data-method") || "CASH";
    npNotes.value = row.getAttribute("data-notes") || "";
    openModal("newPayment");
  });

  document.addEventListener("click", async function (e) {
    const del = e.target.closest("[data-payment-delete]");
    if (!del) return;
    if (!confirm(isArabicClient() ? "هل تريد إلغاء هذه الدفعة؟" : "Void this payment?")) return;
    const id = del.getAttribute("data-payment-delete");
    const data = await jsonFetch(`/api/payments/${id}/void/`, {});
    if (!data.ok) {
      alert(data.error || "Failed");
      return;
    }
    window.location.reload();
  });
})();
