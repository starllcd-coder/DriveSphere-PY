(function () {
  // ---------- Actions dropdown ----------
  function initActionMenus() {
    document.querySelectorAll(".ds-actions").forEach((wrap) => {
      const btn = wrap.querySelector(".ds-actions__toggle");
      const menu = wrap.querySelector(".ds-actions__menu");
      if (!btn || !menu) return;

      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const open = wrap.classList.contains("is-open");
        document.querySelectorAll(".ds-actions.is-open").forEach((w) => w.classList.remove("is-open"));
        if (!open) wrap.classList.add("is-open");
      });
    });

    document.addEventListener("click", () => {
      document.querySelectorAll(".ds-actions.is-open").forEach((w) => w.classList.remove("is-open"));
    });
  }

  // ---------- Upcoming activate ----------
  async function activateBooking(id) {
    try {
      const resp = await fetch(`/api/bookings/${id}/activate/`, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const data = await resp.json();
      if (!data.ok) {
        alert(data.error || "Failed");
        return;
      }
      location.reload();
    } catch (e) {
      alert("Network Error");
    }
  }

  function initActivateButtons() {
    document.querySelectorAll("[data-activate]").forEach((btn) => {
      btn.addEventListener("click", () => activateBooking(btn.getAttribute("data-activate")));
    });
  }

  // ---------- Wizard ----------
  function showStep(step) {
    document.querySelectorAll(".ds-step").forEach((s) => {
      s.classList.toggle("is-active", s.getAttribute("data-step") === String(step));
    });

    document.querySelectorAll(".ds-wizard__section").forEach((sec) => {
      sec.classList.toggle("is-active", sec.getAttribute("data-section") === String(step));
    });
  }

  function initWizard() {
    const wizard = document.querySelector(".ds-wizard");
    if (!wizard) return;

    let step = 1;
    showStep(step);

    wizard.querySelectorAll("[data-wiz-next]").forEach((b) => {
      b.addEventListener("click", () => {
        step = Math.min(9, step + 1);
        showStep(step);
      });
    });

    wizard.querySelectorAll("[data-wiz-back]").forEach((b) => {
      b.addEventListener("click", () => {
        step = Math.max(1, step - 1);
        showStep(step);
      });
    });

    wizard.querySelectorAll("[data-wiz-cancel]").forEach((b) => {
      b.addEventListener("click", () => {
        if (confirm("Cancel booking creation?")) {
          window.location.href = "/bookings/";
        }
      });
    });

    const finishBtn = wizard.querySelector("[data-wiz-finish]");
    if (finishBtn) {
      finishBtn.addEventListener("click", () => {
        alert("Wizard UI Ready. Next step: wire to /api/bookings/create/.");
        window.location.href = "/bookings/";
      });
    }
  }

  // ---------- Signature pad ----------
  function initSignatureCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    ctx.lineWidth = 2;
    ctx.lineCap = "round";

    let drawing = false;
    let lastX = 0;
    let lastY = 0;

    function getPos(e) {
      const rect = canvas.getBoundingClientRect();
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      return { x: clientX - rect.left, y: clientY - rect.top };
    }

    function start(e) {
      drawing = true;
      const p = getPos(e);
      lastX = p.x;
      lastY = p.y;
      e.preventDefault();
    }

    function move(e) {
      if (!drawing) return;
      const p = getPos(e);
      ctx.beginPath();
      ctx.moveTo(lastX, lastY);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();
      lastX = p.x;
      lastY = p.y;
      e.preventDefault();
    }

    function end() {
      drawing = false;
    }

    canvas.addEventListener("mousedown", start);
    canvas.addEventListener("mousemove", move);
    document.addEventListener("mouseup", end);

    canvas.addEventListener("touchstart", start, { passive: false });
    canvas.addEventListener("touchmove", move, { passive: false });
    canvas.addEventListener("touchend", end);

    // clear hook
    document.querySelectorAll(`[data-sign-clear="${canvasId}"]`).forEach((btn) => {
      btn.addEventListener("click", () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      });
    });
  }

  function initSignatures() {
    initSignatureCanvas("customerSign");
    initSignatureCanvas("inspectorSign");
  }

  // ---------- Boot ----------
  document.addEventListener("DOMContentLoaded", function () {
    initActionMenus();
    initActivateButtons();
    initWizard();
    initSignatures();
  });
})();