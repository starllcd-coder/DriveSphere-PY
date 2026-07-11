(function () {

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  async function getJson(url) {
    const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
    return res.json();
  }

  async function postJson(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(payload || {}),
    });
    return res.json();
  }

  function isArabic() {
    return (document.documentElement.getAttribute("lang") || "").toLowerCase() === "ar";
  }

  /* =========================
     Clock (top bar)
     ========================= */
  function formatNow() {
    const now = new Date();
    const locale = document.documentElement.getAttribute("lang") || undefined;
    const date = now.toLocaleDateString(locale, {
      year: "numeric",
      month: "short",
      day: "2-digit"
    });
    const time = now.toLocaleTimeString(locale, {
      hour: "2-digit",
      minute: "2-digit"
    });
    return `${date} Â· ${time}`;
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
     Topbar dropdowns
     ========================= */
  function bindTopbarDropdowns() {
    const dropdowns = Array.from(document.querySelectorAll("[data-dropdown]"));
    if (!dropdowns.length) return;

    function closeAll() {
      dropdowns.forEach(d => {
        d.classList.remove("is-open");
        const toggle = d.querySelector("[data-dropdown-toggle]");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
      });
    }

    document.addEventListener("click", e => {
      const toggle = e.target.closest("[data-dropdown-toggle]");
      if (!toggle) {
        if (!e.target.closest("[data-dropdown]")) closeAll();
        return;
      }

      const dropdown = toggle.closest("[data-dropdown]");
      const isOpen = dropdown.classList.contains("is-open");
      closeAll();
      if (!isOpen) {
        dropdown.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
        if (toggle.getAttribute("data-dropdown-toggle") === "notify") {
          loadNotifications();
        }
      }
    });

    document.addEventListener("keydown", e => {
      if (e.key === "Escape") closeAll();
    });
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function bindGlobalSearch() {
    const form = document.querySelector("[data-global-search-form]");
    const input = document.querySelector("[data-global-search-input]");
    const results = document.querySelector("[data-global-search-results]");
    if (!form || !input || !results) return;

    const endpoint = form.getAttribute("data-search-endpoint") || "/api/search/";
    let timer = null;

    function renderMessage(message) {
      results.innerHTML = `<div class="ds-empty">${escapeHtml(message)}</div>`;
    }

    function renderGroups(groups) {
      if (!Array.isArray(groups) || !groups.length) {
        renderMessage(isArabic() ? "\u0644\u0627 \u062a\u0648\u062c\u062f \u0646\u062a\u0627\u0626\u062c \u0645\u0637\u0627\u0628\u0642\u0629." : "No matching results.");
        return;
      }

      results.innerHTML = groups.map(group => `
        <div class="ds-searchGroup">
          <div class="ds-searchGroup__label">${escapeHtml(group.label)}</div>
          ${(group.items || []).map(item => `
            <a class="ds-searchItem" href="${escapeHtml(item.url)}">
              <div class="ds-searchItem__title">${escapeHtml(item.title)}</div>
              <div class="ds-searchItem__sub">${escapeHtml(item.subtitle)}</div>
              ${item.meta ? `<div class="ds-searchItem__meta">${escapeHtml(item.meta)}</div>` : ""}
            </a>
          `).join("")}
        </div>
      `).join("");
    }

    async function runSearch() {
      const q = input.value.trim();
      if (q.length < 2) {
        renderMessage(isArabic() ? "\u0627\u0643\u062a\u0628 \u062d\u0631\u0641\u064a\u0646 \u0639\u0644\u0649 \u0627\u0644\u0623\u0642\u0644 \u0644\u0644\u0628\u062d\u062b." : "Type at least 2 characters to search.");
        return;
      }

      renderMessage(isArabic() ? "\u062c\u0627\u0631\u064d \u0627\u0644\u0628\u062d\u062b..." : "Searching...");
      try {
        const data = await getJson(`${endpoint}?q=${encodeURIComponent(q)}`);
        renderGroups(data.groups || []);
      } catch (e) {
        renderMessage(isArabic() ? "\u062a\u0639\u0630\u0631 \u062a\u0646\u0641\u064a\u0630 \u0627\u0644\u0628\u062d\u062b \u062d\u0627\u0644\u064a\u0627\u064b." : "Search is unavailable right now.");
      }
    }

    input.addEventListener("input", () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(runSearch, 220);
    });

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      await runSearch();
    });
  }

  let notificationsLoaded = false;
  function setNotifyUi(count) {
    const dot = document.getElementById("ds-notify-dot");
    const clearBtn = document.getElementById("ds-notify-clear");
    const hasItems = Number(count || 0) > 0;
    if (dot) dot.style.display = hasItems ? "block" : "none";
    if (clearBtn) clearBtn.style.display = hasItems ? "inline-flex" : "none";
  }
  async function dismissNotification(id) {
    const res = await postJson("/settings/api/notifications/dismiss/", { id });
    if (!res.ok) throw new Error(res.error || "Failed");
  }

  async function snoozeNotification(id, days) {
    const res = await postJson("/settings/api/notifications/snooze/", { id, days });
    if (!res.ok) throw new Error(res.error || "Failed");
  }
  async function loadNotifications(force) {
    if (notificationsLoaded && !force) return;
    const list = document.getElementById("ds-notify-list");
    if (!list) return;
    try {
      const data = await getJson("/settings/api/notifications/");
      const items = Array.isArray(data.results) ? data.results.slice(0, 6) : [];
      setNotifyUi(data.count || 0);

      if (items.length === 0) {
        list.innerHTML = `<div class="ds-empty">${isArabic() ? "\u0644\u0627 \u062a\u0648\u062c\u062f \u0625\u0634\u0639\u0627\u0631\u0627\u062a" : "No notifications"}</div>`;
        notificationsLoaded = true;
        return;
      }

      list.innerHTML = items.map(item => `
        <div class="ds-notifyItem ds-notifyItem--interactive">
          <a class="ds-notifyItem__body" href="/settings/general/?tab=notifications">
            <div class="ds-notifyItem__title">${item.title}</div>
            <div class="ds-notifyItem__meta">${item.detail}</div>
          </a>
          <div class="ds-notifyItem__actions">
            <button class="ds-notifyAction" type="button" data-notify-snooze="${item.id}" data-days="1">${isArabic() ? "\u063a\u062f\u0627\u064b" : "1d"}</button>
            <button class="ds-notifyAction" type="button" data-notify-dismiss="${item.id}">${isArabic() ? "\u0625\u062e\u0641\u0627\u0621" : "Hide"}</button>
          </div>
        </div>
      `).join("");

      list.querySelectorAll("[data-notify-dismiss]").forEach(btn => {
        btn.addEventListener("click", async (e) => {
          e.preventDefault();
          e.stopPropagation();
          await dismissNotification(btn.getAttribute("data-notify-dismiss"));
          notificationsLoaded = false;
          loadNotifications(true);
        });
      });

      list.querySelectorAll("[data-notify-snooze]").forEach(btn => {
        btn.addEventListener("click", async (e) => {
          e.preventDefault();
          e.stopPropagation();
          await snoozeNotification(btn.getAttribute("data-notify-snooze"), Number(btn.getAttribute("data-days") || 1));
          notificationsLoaded = false;
          loadNotifications(true);
        });
      });

      notificationsLoaded = true;
    } catch (e) {
      setNotifyUi(0);
      list.innerHTML = `<div class="ds-empty">${isArabic() ? "\u062a\u0639\u0630\u0631 \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u0625\u0634\u0639\u0627\u0631\u0627\u062a" : "Failed to load notifications"}</div>`;
    }
  }

  async function clearNotifications() {
    const list = document.getElementById("ds-notify-list");
    if (!list) return;
    try {
      const res = await postJson("/settings/api/notifications/clear/", {});
      if (!res.ok) throw new Error(res.error || "Failed");
      notificationsLoaded = false;
      setNotifyUi(0);
      list.innerHTML = `<div class="ds-empty">${isArabic() ? "\u0644\u0627 \u062a\u0648\u062c\u062f \u0625\u0634\u0639\u0627\u0631\u0627\u062a" : "No notifications"}</div>`;
    } catch (e) {
      list.innerHTML = `<div class="ds-empty">${isArabic() ? "\u062a\u0639\u0630\u0631 \u0645\u0633\u062d \u0627\u0644\u0625\u0634\u0639\u0627\u0631\u0627\u062a" : "Failed to clear notifications"}</div>`;
    }
  }

  /* =========================
     Language toggle
     ========================= */
  function bindLanguageToggle() {
    const buttons = Array.from(document.querySelectorAll(".ds-lang-toggle__btn[data-lang]"));
    if (!buttons.length) return;

    buttons.forEach(btn => {
      btn.addEventListener("click", async () => {
        const lang = btn.getAttribute("data-lang");
        if (!lang || btn.classList.contains("is-active")) return;
        try {
          const res = await postJson("/settings/api/language/", { language: lang });
          if (!res.ok) throw new Error(res.error || "Failed");
          window.location.reload();
        } catch (e) {
          // Keep silent; user can retry
        }
      });
    });
  }

  /* =========================
     Init
     ========================= */
  document.addEventListener("DOMContentLoaded", () => {
    const headerTitle = document.getElementById("ds-page-header-title");
    const headerSub = document.getElementById("ds-page-header-sub");
    const topbarTitle = document.querySelector(".ds-page-title");
    const main = document.querySelector("main");

    if (headerTitle && topbarTitle) {
      headerTitle.textContent = topbarTitle.textContent.trim();
    }

    if (headerSub && main) {
      const subtitle = (main.getAttribute("data-page-subtitle") || "").trim();
      if (subtitle) {
        headerSub.textContent = subtitle;
      }

      if (headerSub.textContent.trim()) {
        headerSub.style.display = "block";
      } else {
        headerSub.style.display = "none";
      }
    }

    updateClock();
    bindPasswordToggle();
    bindSidebarToggle();
    bindRowSelection();
    setActiveSidebar();
    bindTopbarDropdowns();
    bindGlobalSearch();
    bindLanguageToggle();
    document.getElementById("ds-notify-clear")?.addEventListener("click", clearNotifications);
    setNotifyUi(0);
    loadNotifications(true);
    setInterval(updateClock, 30000);
  });

})();
