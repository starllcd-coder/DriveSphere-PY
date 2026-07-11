(function () {

  /* =========================
     Clock (top bar)
     ========================= */
  function formatNow() {
    const now = new Date();
    const date = now.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit"
    });
    const time = now.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit"
    });
    return `${date} · ${time}`;
  }

  function updateClock() {
    const el = document.getElementById("dsClock");
    if (el) el.textContent = formatNow();
  }

  /* =========================
     Password toggle
     ========================= */
  function bindPasswordToggle() {
    document.querySelectorAll("[data-toggle='password']").forEach(btn => {
      btn.addEventListener("click", () => {
        const wrap = btn.closest(".ds-inputWrap");
        if (!wrap) return;
        const input = wrap.querySelector("input");
        if (!input) return;
        input.type = input.type === "password" ? "text" : "password";
      });
    });
  }

  /* =========================
     Mobile sidebar toggle
     ========================= */
  function bindSidebarToggle() {
    const toggle = document.getElementById("sidebarToggle");
    const sidebar = document.querySelector(".ds-sidebar");
    if (!toggle || !sidebar) return;

    toggle.addEventListener("click", () => {
      sidebar.classList.toggle("is-open");
    });
  }

  /* =========================
     Table row selection
     ========================= */
  function bindRowSelection() {
    document.addEventListener("click", e => {
      const row = e.target.closest("tbody tr");
      if (!row) return;

      const tbody = row.parentElement;
      tbody.querySelectorAll("tr").forEach(r => r.classList.remove("is-selected"));
      row.classList.add("is-selected");
    });
  }

  /* =========================
     Active sidebar highlight
     ========================= */
  function setActiveSidebar() {
    const path = window.location.pathname;
    document.querySelectorAll(".ds-sidebar a").forEach(a => {
      const href = a.getAttribute("href");
      if (!href) return;
      if (path.startsWith(href)) {
        a.classList.add("is-active");
      }
    });
  }

  /* =========================
     Init
     ========================= */
  document.addEventListener("DOMContentLoaded", () => {
    updateClock();
    bindPasswordToggle();
    bindSidebarToggle();
    bindRowSelection();
    setActiveSidebar();
    setInterval(updateClock, 30000);
  });

})();