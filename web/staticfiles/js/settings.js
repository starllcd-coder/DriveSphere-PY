(function () {
  const root = document.getElementById("ds-settings");
  if (!root) return;

  const canSettings = root.dataset.canSettings === "1";
  const canEmployees = root.dataset.canEmployees === "1";

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return "";
  }

  const CSRF = getCookie("csrftoken");
  const INTEGRATION_TYPES = [
    { key: "ACCOUNTING_QUICKBOOKS", label: "QuickBooks", syncKind: "accounting" },
    { key: "ACCOUNTING_ZOHO", label: "Zoho Books", syncKind: "accounting" },
    { key: "TELEMATICS_PROVIDER_A", label: "Telematics Provider A", syncKind: "telematics" },
    { key: "TELEMATICS_PROVIDER_B", label: "Telematics Provider B", syncKind: "telematics" },
  ];

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function isArabicClient() {
    try {
      if (typeof isArabic === "function") return isArabic();
    } catch (e) {}
    return document.documentElement.lang === "ar" || document.documentElement.dir === "rtl";
  }

  function docLabel(type) {
    const en = {
      AGREEMENT: 'Agreement',
      CONFIRMATION: 'Confirmation',
      HANDOVER: 'Handover',
      INVOICE: 'Invoice',
      QUOTATION: 'Quotation',
      RECEIPT: 'Receipt',
      REPORT: 'Report',
      RETURN_REPORT: 'Return Report',
    };
    const ar = {
      AGREEMENT: '\u0627\u0644\u0627\u062a\u0641\u0627\u0642\u064a\u0629',
      CONFIRMATION: '\u062a\u0623\u0643\u064a\u062f',
      HANDOVER: '\u062a\u0633\u0644\u064a\u0645',
      INVOICE: '\u0641\u0627\u062a\u0648\u0631\u0629',
      QUOTATION: '\u0639\u0631\u0636 \u0633\u0639\u0631',
      RECEIPT: '\u0625\u064a\u0635\u0627\u0644',
      REPORT: '\u062a\u0642\u0631\u064a\u0631',
      RETURN_REPORT: '\u062a\u0642\u0631\u064a\u0631 \u0627\u0644\u0625\u0631\u062c\u0627\u0639',
    };
    if (isArabicClient()) return ar[type] || type;
    return en[type] || type;
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
        "X-CSRFToken": CSRF,
      },
      body: JSON.stringify(payload || {}),
    });
    return res.json();
  }

  function activateTab(target) {
    document.querySelectorAll(".ds-tab").forEach((t) => t.classList.remove("is-active"));
    document.querySelectorAll(".ds-tabPanel").forEach((p) => p.classList.remove("is-active"));
    document.querySelector(`.ds-tab[data-tab='${target}']`)?.classList.add("is-active");
    document.querySelector(`[data-panel='${target}']`)?.classList.add("is-active");
  }

  // Tabs
  document.querySelectorAll(".ds-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");
      activateTab(target);
      if (target === "notifications") loadNotifications();
      if (target === "integrations") {
        loadIntegrationProfiles();
        loadIntegrationLogs();
      }
      if (target === "audit") loadAuditLogs();
    });
  });

  // General
  const businessFields = {
    business_name: document.getElementById("s-business-name"),
    short_code: document.getElementById("s-company-code"),
    business_name_ar: document.getElementById("s-business-name-ar"),
    commercial_registration_number: document.getElementById("s-cr"),
    vat_no: document.getElementById("s-vat"),
    address: document.getElementById("s-address"),
    address_ar: document.getElementById("s-address-ar"),
    phone_number: document.getElementById("s-phone"),
    phone_number_ar: document.getElementById("s-phone-ar"),
    email: document.getElementById("s-email"),
    email_ar: document.getElementById("s-email-ar"),
    website: document.getElementById("s-website"),
    website_ar: document.getElementById("s-website-ar"),
    currency_code: document.getElementById("s-currency-code"),
    currency_symbol: document.getElementById("s-currency-symbol"),
  };

  const logoInput = document.getElementById("s-logo-input");
  const logoPreview = document.getElementById("s-logo-preview");
  const logoUploadBtn = document.getElementById("s-logo-upload");

  async function loadBusiness() {
    if (!canSettings) return;
    const data = await getJson("/settings/api/business/");
    if (!data.ok) return;
    Object.keys(businessFields).forEach((k) => {
      if (businessFields[k]) businessFields[k].value = data.data[k] || "";
    });

    if (logoPreview) {
      const url = data.data.logo_url || "";
      if (url) {
        logoPreview.src = url;
        logoPreview.hidden = false;
      } else {
        logoPreview.hidden = true;
      }
    }
  }

  if (logoInput && logoPreview) {
    logoInput.addEventListener("change", () => {
      const file = logoInput.files && logoInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        logoPreview.src = reader.result;
        logoPreview.hidden = false;
      };
      reader.readAsDataURL(file);
    });
  }

  async function uploadLogo() {
    if (!logoInput || !logoInput.files || !logoInput.files[0]) {
      throw new Error("Please choose a logo file first.");
    }
    const formData = new FormData();
    formData.append("logo", logoInput.files[0]);

    const res = await fetch("/settings/api/business/logo/", {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": CSRF,
      },
      body: formData,
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "Upload failed");
    if (logoPreview && data.logo_url) {
      logoPreview.src = data.logo_url;
      logoPreview.hidden = false;
    }
  }

  logoUploadBtn?.addEventListener("click", async () => {
    try {
      await uploadLogo();
      alert("Logo updated");
    } catch (e) {
      alert(e.message || "Failed");
    }
  });

  async function saveBusiness() {
    if (!canSettings) return;
    const payload = {};
    Object.keys(businessFields).forEach((k) => payload[k] = businessFields[k]?.value || "");
    const res = await postJson("/settings/api/business/save/", payload);
    if (!res.ok) throw new Error(res.error || "Failed");
  }

  document.getElementById("s-save-business")?.addEventListener("click", async () => {
    try {
      await saveBusiness();
      alert("Saved");
    } catch (e) {
      alert(e.message || "Failed");
    }
  });

  async function loadBranches() {
    if (!canSettings) return;
    const data = await getJson("/settings/api/branches/");
    const body = document.getElementById("s-branches-body");
    if (!body) return;
    if (!data.ok) {
      body.innerHTML = `<tr><td colspan="4" class="ds-empty">Failed</td></tr>`;
      return;
    }
    body.innerHTML = (data.results || []).map((b) => `
      <tr>
        <td>${b.name}</td>
        <td><input class="ds-input ds-input--small" value="${b.code || ""}" data-branch-code></td>
        <td>${b.is_active ? "Active" : "Inactive"}</td>
        <td>
          ${canSettings ? `<button class="ds-btn ds-btn--small" data-branch-save="${b.id}">Save</button>
          <button class="ds-btn ds-btn--small ds-btn--danger" data-branch-del="${b.id}">Delete</button>` : ""}
        </td>
      </tr>
    `).join("") || `<tr><td colspan="4" class="ds-empty">${isArabicClient() ? '\u0644\u0627 \u062a\u0648\u062c\u062f \u0641\u0631\u0648\u0639' : 'No Branches'}</td></tr>`;

    body.querySelectorAll("[data-branch-save]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-branch-save");
        const row = btn.closest("tr");
        const code = row.querySelector("[data-branch-code]")?.value || "";
        const res = await postJson(`/settings/api/branches/${id}/update/`, { code });
        if (!res.ok) return alert(res.error || "Failed");
        loadBranches();
      });
    });

    body.querySelectorAll("[data-branch-del]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-branch-del");
        if (!confirm("Delete this branch?")) return;
        const res = await postJson(`/settings/api/branches/${id}/delete/`, {});
        if (!res.ok) return alert(res.error || "Failed");
        loadBranches();
      });
    });
  }

  document.getElementById("s-branch-add")?.addEventListener("click", async () => {
    const name = document.getElementById("s-branch-name")?.value || "";
    const res = await postJson("/settings/api/branches/create/", { name });
    if (!res.ok) return alert(res.error || "Failed");
    document.getElementById("s-branch-name").value = "";
    loadBranches();
  });

  function buildDocPreview(d) {
    const companyCode = (businessFields.short_code?.value || d.prefix || "DS").trim().toUpperCase() || "DS";
    const branchCode = "BR";
    const docCode = (d.doc_code || d.doc_type || "DOC").toString().trim().toUpperCase().slice(0, 4) || "DOC";
    const date = new Date();
    const dateStr = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, "0")}${String(date.getDate()).padStart(2, "0")}`;
    const seq = String(d.next_number || 1).padStart(Number(d.padding || 0), "0");
    return [companyCode, branchCode, docCode, dateStr, seq].join(d.separator || "-");
  }

  async function loadDocNumbering() {
    if (!canSettings) return;
    const data = await getJson("/settings/api/doc-numbering/");
    const body = document.getElementById("s-docs-body");
    if (!body) return;
    if (!data.ok) {
      body.innerHTML = `<tr><td colspan="8" class="ds-empty">Failed</td></tr>`;
      return;
    }
    body.innerHTML = (data.results || []).map((d) => `
      <tr data-doc="${d.doc_type}">
        <td>${docLabel(d.doc_type)}</td>
        <td><input class="ds-input ds-input--small" value="${d.doc_code || ""}" data-field="doc_code"></td>
        <td><input class="ds-input ds-input--small" value="${d.prefix || ""}" data-field="prefix"></td>
        <td><input class="ds-input ds-input--small" value="${d.separator || ""}" data-field="separator"></td>
        <td><input class="ds-input ds-input--small" value="${d.padding}" data-field="padding"></td>
        <td><input class="ds-input ds-input--small" value="${d.next_number}" data-field="next_number"></td>
        <td class="ds-muted" data-doc-preview>${buildDocPreview(d)}</td>
        <td>${canSettings ? `<button class="ds-btn ds-btn--small" data-doc-save="${d.doc_type}">${isArabicClient() ? '\u062d\u0641\u0638' : 'Save'}</button>` : ""}</td>
      </tr>
    `).join("") || `<tr><td colspan="8" class="ds-empty">No Docs</td></tr>`;

    body.querySelectorAll("[data-doc-save]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const row = btn.closest("tr");
        const docType = btn.getAttribute("data-doc-save");
        const payload = {
          doc_type: docType,
          doc_code: row.querySelector("[data-field='doc_code']").value,
          prefix: row.querySelector("[data-field='prefix']").value,
          separator: row.querySelector("[data-field='separator']").value,
          padding: row.querySelector("[data-field='padding']").value,
          next_number: row.querySelector("[data-field='next_number']").value,
        };
        const res = await postJson("/settings/api/doc-numbering/save/", payload);
        if (!res.ok) return alert(res.error || "Failed");
        alert("Saved");
      });
    });
  }

  async function saveDocNumberingAll() {
    if (!canSettings) return;
    const rows = document.querySelectorAll("#s-docs-body tr[data-doc]");
    for (const row of rows) {
      const docType = row.getAttribute("data-doc");
      const payload = {
        doc_type: docType,
        doc_code: row.querySelector("[data-field='doc_code']")?.value || "",
        prefix: row.querySelector("[data-field='prefix']")?.value || "",
        separator: row.querySelector("[data-field='separator']")?.value || "",
        padding: row.querySelector("[data-field='padding']")?.value || "0",
        next_number: row.querySelector("[data-field='next_number']")?.value || "0",
      };
      const res = await postJson("/settings/api/doc-numbering/save/", payload);
      if (!res.ok) throw new Error(res.error || "Failed to save document numbering");
    }
  }

  // Exchange rates
  const exchangeTable = document.getElementById("s-exchange-table");
  const exchangeUpdated = document.getElementById("s-exchange-updated");
  const exchangeUpdateBtn = document.getElementById("s-exchange-update");

  function renderRates(base, rates) {
    if (!exchangeTable) return;
    const body = exchangeTable.querySelector("tbody");
    if (!body) return;

    const list = [
      base,
      "USD",
      "EUR",
      "AED",
      "SAR",
      "BHD",
      "KWD",
      "QAR",
    ];
    const rows = list.map((code) => {
      const rate = (code === base) ? 1 : (rates[code] || "-");
      return `<tr><td>${code}</td><td>${rate}</td></tr>`;
    });
    body.innerHTML = rows.join("") || `<tr><td colspan="2" class="ds-empty">${isArabicClient() ? '\u0644\u0627 \u062a\u0648\u062c\u062f \u0623\u0633\u0639\u0627\u0631' : 'No Rates'}</td></tr>`;
  }

  async function loadExchangeRates() {
    if (!canSettings) return;
    const data = await getJson("/settings/api/exchange-rates/");
    if (!data.ok) return;
    renderRates(data.data.base || "USD", data.data.rates || {});
    if (exchangeUpdated) {
      const updatedLabel = isArabicClient()
        ? "\u0622\u062e\u0631 \u062a\u062d\u062f\u064a\u062b"
        : "Last Updated";
      exchangeUpdated.textContent = data.data.updated_at
        ? `${updatedLabel}: ${new Date(data.data.updated_at).toLocaleString()}`
        : `${updatedLabel}: -`;
    }
  }

  exchangeUpdateBtn?.addEventListener("click", async () => {
    const res = await postJson("/settings/api/exchange-rates/update/", {});
    if (!res.ok) return alert(res.error || (isArabicClient() ? '\u0641\u0634\u0644' : 'Failed'));
    loadExchangeRates();
  });

  // Backup & Restore
  const backupExportBtn = document.getElementById("backup-export");
  const backupFileInput = document.getElementById("backup-file");
  const backupRestoreBtn = document.getElementById("backup-restore");
  const backupResetBtn = document.getElementById("backup-reset");

  backupExportBtn?.addEventListener("click", () => {
    window.location.href = "/settings/api/backup/export/";
  });

  backupRestoreBtn?.addEventListener("click", async () => {
    const file = backupFileInput?.files?.[0];
    if (!file) return alert(isArabicClient() ? "\u0627\u062e\u062a\u0631 \u0645\u0644\u0641 \u0627\u0644\u0646\u0633\u062e \u0627\u0644\u0627\u062d\u062a\u064a\u0627\u0637\u064a .zip \u0623\u0648\u0644\u0627\u064b." : "Choose a backup .zip file first.");
    const confirmText = prompt(
      isArabicClient()
        ? "\u0627\u0643\u062a\u0628 RESTORE \u0644\u062a\u0623\u0643\u064a\u062f \u0627\u0644\u0627\u0633\u062a\u0639\u0627\u062f\u0629. \u0633\u064a\u062a\u0645 \u0627\u0633\u062a\u0628\u062f\u0627\u0644 \u062c\u0645\u064a\u0639 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a."
        : "Type RESTORE to confirm restore. This will overwrite all data."
    );
    if (confirmText !== "RESTORE") return;

    const formData = new FormData();
    formData.append("backup", file);
    formData.append("confirm", confirmText);

    const res = await fetch("/settings/api/backup/restore/", {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": CSRF,
      },
      body: formData,
    });
    const data = await res.json();
    if (!data.ok) return alert(data.error || (isArabicClient() ? "\u0641\u0634\u0644\u062a \u0627\u0644\u0627\u0633\u062a\u0639\u0627\u062f\u0629" : "Restore failed"));
    alert(isArabicClient() ? "\u0627\u0643\u062a\u0645\u0644\u062a \u0627\u0644\u0627\u0633\u062a\u0639\u0627\u062f\u0629. \u0633\u064a\u062a\u0645 \u0625\u0639\u0627\u062f\u0629 \u062a\u062d\u0645\u064a\u0644 \u0627\u0644\u0635\u0641\u062d\u0629." : "Restore completed. The page will reload.");
    window.location.reload();
  });

  backupResetBtn?.addEventListener("click", async () => {
    const confirmText = prompt(
      isArabicClient()
        ? "\u0627\u0643\u062a\u0628 RESET \u0644\u0625\u0639\u0627\u062f\u0629 \u0636\u0628\u0637 \u0627\u0644\u0645\u0635\u0646\u0639. \u0633\u064a\u062a\u0645 \u062d\u0630\u0641 \u062c\u0645\u064a\u0639 \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a."
        : "Type RESET to factory reset. This will delete all data."
    );
    if (confirmText !== "RESET") return;
    const username = prompt(
      isArabicClient()
        ? "\u0627\u0633\u0645 \u0645\u0633\u062a\u062e\u062f\u0645 \u0627\u0644\u0645\u062f\u064a\u0631 \u0627\u0644\u0630\u064a \u0633\u064a\u062a\u0645 \u0627\u0644\u0625\u0628\u0642\u0627\u0621 \u0639\u0644\u064a\u0647 (\u0633\u064a\u062a\u0645 \u0625\u0646\u0634\u0627\u0624\u0647 \u0645\u0646 \u062c\u062f\u064a\u062f):"
        : "Admin username to keep (will be recreated):"
    );
    if (!username) return alert(isArabicClient() ? "\u0627\u0633\u0645 \u0645\u0633\u062a\u062e\u062f\u0645 \u0627\u0644\u0645\u062f\u064a\u0631 \u0645\u0637\u0644\u0648\u0628." : "Admin username is required.");
    const password = prompt(
      isArabicClient()
        ? "\u0643\u0644\u0645\u0629 \u0645\u0631\u0648\u0631 \u0627\u0644\u0645\u062f\u064a\u0631:"
        : "Admin password to set:"
    );
    if (!password) return alert(isArabicClient() ? "\u0643\u0644\u0645\u0629 \u0645\u0631\u0648\u0631 \u0627\u0644\u0645\u062f\u064a\u0631 \u0645\u0637\u0644\u0648\u0628\u0629." : "Admin password is required.");
    const res = await postJson("/settings/api/backup/reset/", {
      confirm: confirmText,
      admin_username: username,
      admin_password: password,
    });
    if (!res.ok) return alert(res.error || (isArabicClient() ? "\u0641\u0634\u0644\u062a \u0625\u0639\u0627\u062f\u0629 \u0627\u0644\u0636\u0628\u0637" : "Reset failed"));
    alert(isArabicClient() ? "\u0627\u0643\u062a\u0645\u0644\u062a \u0625\u0639\u0627\u062f\u0629 \u0636\u0628\u0637 \u0627\u0644\u0645\u0635\u0646\u0639. \u064a\u0631\u062c\u0649 \u062a\u0633\u062c\u064a\u0644 \u0627\u0644\u062f\u062e\u0648\u0644 \u0645\u0631\u0629 \u0623\u062e\u0631\u0649." : "Factory reset completed. Please log in again.");
    window.location.href = "/login/";
  });

  // Employees
  let editUserId = "";
  async function loadEmployees() {
    if (!canEmployees) return;
    const data = await getJson("/settings/api/employees/");
    const body = document.getElementById("e-body");
    if (!body) return;
    if (!data.ok) {
      body.innerHTML = `<tr><td colspan="5" class="ds-empty">Failed</td></tr>`;
      return;
    }
    body.innerHTML = (data.results || []).map((u) => `
      <tr data-user="${u.id}">
        <td>${u.email}</td>
        <td>${u.username || ""}</td>
        <td>${u.role || ""}</td>
        <td>${u.is_active ? "Active" : "Inactive"}</td>
        <td>
          ${canEmployees ? `<button class="ds-btn ds-btn--small" data-emp-edit="${u.id}">Edit</button>
          <button class="ds-btn ds-btn--small ds-btn--danger" data-emp-del="${u.id}">Delete</button>` : ""}
        </td>
      </tr>
    `).join("") || `<tr><td colspan="5" class="ds-empty">No Employees</td></tr>`;

    body.querySelectorAll("[data-emp-edit]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const row = btn.closest("tr");
        editUserId = btn.getAttribute("data-emp-edit");
        document.getElementById("e-email").value = row.children[0].textContent || "";
        document.getElementById("e-username").value = row.children[1].textContent || "";
        document.getElementById("e-role").value = row.children[2].textContent || "ADMIN";
        document.getElementById("e-password").value = "";
      });
    });

    body.querySelectorAll("[data-emp-del]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this employee?")) return;
        const id = btn.getAttribute("data-emp-del");
        const res = await postJson(`/settings/api/employees/${id}/delete/`, {});
        if (!res.ok) return alert(res.error || "Failed");
        loadEmployees();
      });
    });
  }

  document.getElementById("e-save")?.addEventListener("click", async () => {
    if (!canEmployees) return;
    const payload = {
      username: document.getElementById("e-username").value,
      email: document.getElementById("e-email").value,
      password: document.getElementById("e-password").value,
      role: document.getElementById("e-role").value,
    };
    let res;
    if (editUserId) {
      res = await postJson(`/settings/api/employees/${editUserId}/update/`, payload);
    } else {
      res = await postJson("/settings/api/employees/create/", payload);
    }
    if (!res.ok) return alert(res.error || "Failed");
    alert(res.message || "User saved");
    editUserId = "";
    document.getElementById("e-password").value = "";
    loadEmployees();
  });

  // Database
  async function loadDbProfile() {
    if (!canSettings) return;
    const data = await getJson("/settings/api/db/profile/");
    if (!data.ok) return;
    document.getElementById("db-provider").value = data.data.provider || "POSTGRES";
    document.getElementById("db-host").value = data.data.host || "";
    document.getElementById("db-port").value = data.data.port || "";
    document.getElementById("db-name").value = data.data.database_name || "";
    document.getElementById("db-user").value = data.data.username || "";
    document.getElementById("db-pass").value = data.data.password || "";
    document.getElementById("db-ssl").value = data.data.sslmode || "";
  }

  document.getElementById("db-save")?.addEventListener("click", async () => {
    if (!canSettings) return;
    const payload = {
      provider: document.getElementById("db-provider").value,
      host: document.getElementById("db-host").value,
      port: document.getElementById("db-port").value,
      database_name: document.getElementById("db-name").value,
      username: document.getElementById("db-user").value,
      password: document.getElementById("db-pass").value,
      sslmode: document.getElementById("db-ssl").value,
    };
    const res = await postJson("/settings/api/db/profile/save/", payload);
    if (!res.ok) return alert(res.error || "Failed");
    alert("Saved");
  });

  document.getElementById("db-test")?.addEventListener("click", async () => {
    if (!canSettings) return;
    const res = await postJson("/settings/api/db/test/", {});
    alert(res.message || "Done");
  });

  document.getElementById("db-migrate")?.addEventListener("click", async () => {
    if (!canSettings) return;
    const res = await postJson("/settings/api/db/migrate/", {});
    alert(res.message || "Done");
  });

  // Notifications
  async function loadNotifications() {
    const list = document.getElementById("s-notify-list");
    if (!list) return;
    const data = await getJson("/settings/api/notifications/");
    if (!data.ok) {
      list.innerHTML = `<div class="ds-empty">${isArabicClient() ? '\u062a\u0639\u0630\u0631 \u0627\u0644\u062a\u062d\u0645\u064a\u0644' : 'Failed'}</div>`;
      return;
    }
    if (!data.results || data.results.length === 0) {
      list.innerHTML = `<div class="ds-empty">${isArabicClient() ? '\u0644\u0627 \u062a\u0648\u062c\u062f \u0625\u0634\u0639\u0627\u0631\u0627\u062a' : 'No notifications'}</div>`;
      return;
    }
    list.innerHTML = data.results.map((item) => `
      <div class="ds-notifyItem ds-notifyItem--interactive">
        <div class="ds-notifyItem__body">
          <div class="ds-notifyItem__title">${item.title}</div>
          <div class="ds-notifyItem__meta">${item.detail}</div>
        </div>
        <div class="ds-notifyItem__actions">
          <button class="ds-btn ds-btn--small" type="button" data-notify-snooze="${item.id}" data-days="1">${isArabicClient() ? '\u063a\u062f\u0627\u064b' : '1d'}</button>
          <button class="ds-btn ds-btn--small ds-btn--danger" type="button" data-notify-dismiss="${item.id}">${isArabicClient() ? '\u0625\u062e\u0641\u0627\u0621' : 'Hide'}</button>
        </div>
      </div>
    `).join("");

    list.querySelectorAll("[data-notify-dismiss]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const res = await postJson("/settings/api/notifications/dismiss/", { id: btn.getAttribute("data-notify-dismiss") });
        if (!res.ok) return alert(res.error || (isArabicClient() ? '\u0641\u0634\u0644' : 'Failed'));
        loadNotifications();
      });
    });

    list.querySelectorAll("[data-notify-snooze]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const res = await postJson("/settings/api/notifications/snooze/", {
          id: btn.getAttribute("data-notify-snooze"),
          days: Number(btn.getAttribute("data-days") || 1),
        });
        if (!res.ok) return alert(res.error || (isArabicClient() ? '\u0641\u0634\u0644' : 'Failed'));
        loadNotifications();
      });
    });
  }

  document.getElementById("s-notify-clear")?.addEventListener("click", async () => {
    const res = await postJson("/settings/api/notifications/clear/", {});
    if (!res.ok) return alert(res.error || (isArabicClient() ? '\u0641\u0634\u0644' : 'Failed'));
    loadNotifications();
  });

  document.getElementById("s-notify-sync")?.addEventListener("click", async () => {
    const res = await postJson("/settings/api/notifications/sync/", {});
    if (!res.ok) return alert(res.error || (isArabicClient() ? '\u0641\u0634\u0644' : 'Failed'));
    const result = res.result || {};
    alert(
      isArabicClient()
        ? `\u062a\u0645\u062a \u0645\u0632\u0627\u0645\u0646\u0629 \u0627\u0644\u062a\u0630\u0643\u064a\u0631\u0627\u062a. \u062c\u062f\u064a\u062f: ${result.created || 0}\u060c \u0645\u062d\u062f\u062b: ${result.updated || 0}`
        : `Reminder sync completed. Created: ${result.created || 0}, updated: ${result.updated || 0}`
    );
    loadNotifications();
  });

  function getIntegrationCard(type) {
    return document.querySelector(`.ds-integrationCard[data-integration-type="${type}"]`);
  }

  async function saveIntegrationProfile(type) {
    const card = getIntegrationCard(type);
    if (!card) return;

    const metadataRaw = card.querySelector("[data-int-field='metadata']")?.value?.trim() || "";
    let metadata = {};
    if (metadataRaw) {
      try {
        metadata = JSON.parse(metadataRaw);
      } catch (e) {
        throw new Error(`Invalid JSON in ${type} metadata`);
      }
    }

    const payload = {
      integration_type: type,
      base_url: card.querySelector("[data-int-field='base_url']")?.value?.trim() || "",
      client_id: card.querySelector("[data-int-field='client_id']")?.value?.trim() || "",
      org_id: card.querySelector("[data-int-field='org_id']")?.value?.trim() || "",
      metadata,
      is_active: !!card.querySelector("[data-int-field='is_active']")?.checked,
    };

    const clientSecret = card.querySelector("[data-int-field='client_secret']")?.value?.trim() || "";
    const accessToken = card.querySelector("[data-int-field='access_token']")?.value?.trim() || "";
    const refreshToken = card.querySelector("[data-int-field='refresh_token']")?.value?.trim() || "";
    if (clientSecret) payload.client_secret = clientSecret;
    if (accessToken) payload.access_token = accessToken;
    if (refreshToken) payload.refresh_token = refreshToken;

    const res = await postJson("/api/integrations/profiles/", payload);
    if (!res.profile) {
      throw new Error(res.error || "Failed to save integration profile");
    }
  }

  async function runIntegrationSync(type) {
    const card = getIntegrationCard(type);
    if (!card) return;
    const syncKind = card.dataset.integrationSyncKind || "accounting";
    const payload = { integration_type: type };
    if (syncKind === "accounting") {
      payload.period = card.querySelector("[data-int-field='period']")?.value || "monthly";
    } else {
      payload.since_hours = Number(card.querySelector("[data-int-field='since_hours']")?.value || 6);
    }
    const res = await postJson("/api/integrations/sync/run/", payload);
    if (!res.status) {
      throw new Error(res.error || "Sync failed");
    }
    return res;
  }

  function integrationCardTemplate(type, profile) {
    const typeMeta = INTEGRATION_TYPES.find((item) => item.key === type) || { label: type, syncKind: "accounting" };
    const metadataText = JSON.stringify(profile?.metadata || {}, null, 2);
    return `
      <div class="ds-integrationCard" data-integration-type="${type}" data-integration-sync-kind="${typeMeta.syncKind}">
        <div class="ds-integrationCard__head">
          <div class="ds-card__title">${escapeHtml(typeMeta.label)}</div>
          <label class="ds-integrationCard__status">
            <input type="checkbox" data-int-field="is_active" ${profile?.is_active ? "checked" : ""}>
            <span>${isArabicClient() ? "\u0646\u0634\u0637" : "Active"}</span>
          </label>
        </div>
        <div class="ds-formGrid">
          <label class="ds-label">${isArabicClient() ? "Base URL" : "Base URL"}</label>
          <input class="ds-input ds-input--small" data-int-field="base_url" placeholder="https://..." value="${escapeHtml(profile?.base_url || "")}">

          <label class="ds-label">${isArabicClient() ? "Client ID" : "Client ID"}</label>
          <input class="ds-input ds-input--small" data-int-field="client_id" value="${escapeHtml(profile?.client_id || "")}">

          <label class="ds-label">${isArabicClient() ? "Client Secret" : "Client Secret"}</label>
          <input class="ds-input ds-input--small" data-int-field="client_secret" placeholder="${isArabicClient() ? "\u0627\u062a\u0631\u0643\u0647 \u0641\u0627\u0631\u063a\u0627\u064b \u0644\u0639\u062f\u0645 \u0627\u0644\u062a\u063a\u064a\u064a\u0631" : "Leave blank to keep unchanged"}">

          <label class="ds-label">${isArabicClient() ? "Access Token" : "Access Token"}</label>
          <input class="ds-input ds-input--small" data-int-field="access_token" placeholder="${isArabicClient() ? "\u0627\u062a\u0631\u0643\u0647 \u0641\u0627\u0631\u063a\u0627\u064b \u0644\u0639\u062f\u0645 \u0627\u0644\u062a\u063a\u064a\u064a\u0631" : "Leave blank to keep unchanged"}">

          <label class="ds-label">${isArabicClient() ? "Refresh Token" : "Refresh Token"}</label>
          <input class="ds-input ds-input--small" data-int-field="refresh_token" placeholder="${isArabicClient() ? "\u0627\u062a\u0631\u0643\u0647 \u0641\u0627\u0631\u063a\u0627\u064b \u0644\u0639\u062f\u0645 \u0627\u0644\u062a\u063a\u064a\u064a\u0631" : "Leave blank to keep unchanged"}">

          <label class="ds-label">${isArabicClient() ? "Org ID" : "Org ID"}</label>
          <input class="ds-input ds-input--small" data-int-field="org_id" value="${escapeHtml(profile?.org_id || "")}">

          <label class="ds-label">${isArabicClient() ? "Metadata (JSON)" : "Metadata (JSON)"}</label>
          <textarea class="ds-input ds-input--small" data-int-field="metadata" rows="3">${escapeHtml(metadataText)}</textarea>

          ${typeMeta.syncKind === "accounting" ? `
            <label class="ds-label">${isArabicClient() ? "\u0641\u062a\u0631\u0629 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629" : "Sync Period"}</label>
            <select class="ds-input ds-input--small" data-int-field="period">
              <option value="today">${isArabicClient() ? "\u0627\u0644\u064a\u0648\u0645" : "Today"}</option>
              <option value="weekly">${isArabicClient() ? "\u0623\u0633\u0628\u0648\u0639\u064a" : "Weekly"}</option>
              <option value="monthly" selected>${isArabicClient() ? "\u0634\u0647\u0631\u064a" : "Monthly"}</option>
            </select>
          ` : `
            <label class="ds-label">${isArabicClient() ? "\u0639\u062f\u062f \u0627\u0644\u0633\u0627\u0639\u0627\u062a" : "Since Hours"}</label>
            <input type="number" min="1" max="168" class="ds-input ds-input--small" data-int-field="since_hours" value="6">
          `}
        </div>
        <div class="ds-integrationCard__actions">
          <button class="ds-btn ds-btn--small" type="button" data-int-save="${type}">${isArabicClient() ? "\u062d\u0641\u0638" : "Save"}</button>
          <button class="ds-btn ds-btn--small ds-btn--primary" type="button" data-int-sync="${type}">${isArabicClient() ? "\u062a\u0634\u063a\u064a\u0644 \u0627\u0644\u0645\u0632\u0627\u0645\u0646\u0629" : "Run Sync"}</button>
        </div>
      </div>
    `;
  }

  async function loadIntegrationProfiles() {
    if (!canSettings) return;
    const list = document.getElementById("s-integrations-list");
    if (!list) return;

    const data = await getJson("/api/integrations/profiles/");
    if (!data.profiles) {
      list.innerHTML = `<div class="ds-empty">${isArabicClient() ? "\u062a\u0639\u0630\u0631 \u0627\u0644\u062a\u062d\u0645\u064a\u0644" : "Failed to load integrations"}</div>`;
      return;
    }

    const byType = {};
    (data.profiles || []).forEach((item) => {
      byType[item.integration_type] = item;
    });
    list.innerHTML = INTEGRATION_TYPES.map((item) => integrationCardTemplate(item.key, byType[item.key])).join("");

    list.querySelectorAll("[data-int-save]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const type = btn.getAttribute("data-int-save");
        try {
          await saveIntegrationProfile(type);
          alert(isArabicClient() ? "\u062a\u0645 \u062d\u0641\u0638 \u0645\u0644\u0641 \u0627\u0644\u062a\u0643\u0627\u0645\u0644" : "Integration profile saved");
        } catch (e) {
          alert(e.message || "Failed");
        }
      });
    });

    list.querySelectorAll("[data-int-sync]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const type = btn.getAttribute("data-int-sync");
        try {
          const result = await runIntegrationSync(type);
          alert(`${result.status}: ${result.summary || ""}`);
          loadIntegrationLogs();
        } catch (e) {
          alert(e.message || "Failed");
        }
      });
    });
  }

  async function loadIntegrationLogs() {
    if (!canSettings) return;
    const body = document.getElementById("s-int-log-body");
    if (!body) return;
    const integrationType = document.getElementById("s-int-log-type")?.value || "";
    const qs = integrationType ? `?integration_type=${encodeURIComponent(integrationType)}` : "";
    const data = await getJson(`/api/integrations/sync/logs/${qs}`);
    if (!data.logs) {
      body.innerHTML = `<tr><td colspan="5" class="ds-empty">${isArabicClient() ? "\u062a\u0639\u0630\u0631 \u0627\u0644\u062a\u062d\u0645\u064a\u0644" : "Failed to load logs"}</td></tr>`;
      return;
    }
    if (!data.logs.length) {
      body.innerHTML = `<tr><td colspan="5" class="ds-empty">${isArabicClient() ? "\u0644\u0627 \u062a\u0648\u062c\u062f \u0633\u062c\u0644\u0627\u062a" : "No logs yet"}</td></tr>`;
      return;
    }
    body.innerHTML = data.logs.map((item) => `
      <tr>
        <td>${item.created_at ? new Date(item.created_at).toLocaleString() : ""}</td>
        <td>${escapeHtml(item.profile_type || "")}</td>
        <td>${escapeHtml(item.direction || "")}</td>
        <td>${escapeHtml(item.status || "")}</td>
        <td>${escapeHtml(item.summary || "")}</td>
      </tr>
    `).join("");
  }

  async function saveAllIntegrationProfiles() {
    if (!canSettings) return;
    for (const type of INTEGRATION_TYPES.map((item) => item.key)) {
      if (!getIntegrationCard(type)) continue;
      await saveIntegrationProfile(type);
    }
  }

  document.getElementById("s-integrations-refresh")?.addEventListener("click", () => {
    loadIntegrationProfiles();
    loadIntegrationLogs();
  });
  document.getElementById("s-int-log-refresh")?.addEventListener("click", loadIntegrationLogs);
  document.getElementById("s-int-log-type")?.addEventListener("change", loadIntegrationLogs);

  async function loadAuditLogs() {
    if (!canSettings) return;
    const body = document.getElementById("s-audit-body");
    if (!body) return;
    const query = document.getElementById("s-audit-query")?.value || "";
    const data = await getJson(`/settings/api/audit-logs/?q=${encodeURIComponent(query)}`);
    if (!data.ok) {
      body.innerHTML = `<tr><td colspan="5" class="ds-empty">${isArabicClient() ? '\u062a\u0639\u0630\u0631 \u0627\u0644\u062a\u062d\u0645\u064a\u0644' : 'Failed'}</td></tr>`;
      return;
    }
    if (!data.results || data.results.length === 0) {
      body.innerHTML = `<tr><td colspan="5" class="ds-empty">${isArabicClient() ? '\u0644\u0627 \u062a\u0648\u062c\u062f \u0633\u062c\u0644\u0627\u062a' : 'No log entries'}</td></tr>`;
      return;
    }
    body.innerHTML = data.results.map((item) => `
      <tr>
        <td>${item.created_at ? new Date(item.created_at).toLocaleString() : ""}</td>
        <td>${item.action}</td>
        <td>${item.user_email || "System"}</td>
        <td>${item.entity_type || ""} ${item.entity_id || ""}</td>
        <td>${item.message || ""}</td>
      </tr>
    `).join("");
  }

  document.getElementById("s-audit-refresh")?.addEventListener("click", loadAuditLogs);
  document.getElementById("s-audit-query")?.addEventListener("input", () => {
    window.clearTimeout(loadAuditLogs._timer);
    loadAuditLogs._timer = window.setTimeout(loadAuditLogs, 220);
  });

  function activeTab() {
    return document.querySelector(".ds-tab.is-active")?.getAttribute("data-tab") || "general";
  }

  async function applyActiveTab() {
    const tab = activeTab();
    if (tab === "general") {
      if (!canSettings) return;
      await saveBusiness();
      await saveDocNumberingAll();
      return;
    }
    if (tab === "employees") {
      if (!canEmployees) return;
      document.getElementById("e-save")?.click();
      return;
    }
    if (tab === "database") {
      if (!canSettings) return;
      document.getElementById("db-save")?.click();
      return;
    }
    if (tab === "integrations") {
      if (!canSettings) return;
      await saveAllIntegrationProfiles();
    }
  }

  document.getElementById("settings-apply")?.addEventListener("click", async () => {
    try {
      await applyActiveTab();
      alert("Applied");
    } catch (e) {
      alert(e.message || "Failed");
    }
  });

  document.getElementById("settings-save")?.addEventListener("click", async () => {
    try {
      await applyActiveTab();
      alert("Saved");
    } catch (e) {
      alert(e.message || "Failed");
    }
  });

  // Init
  const initialTab = new URLSearchParams(window.location.search || "").get("tab");
  if (initialTab) activateTab(initialTab);
  loadBusiness();
  loadBranches();
  loadDocNumbering();
  loadExchangeRates();
  loadEmployees();
  loadDbProfile();
  if (initialTab === "integrations") {
    loadIntegrationProfiles();
    loadIntegrationLogs();
  }
  if (initialTab === "notifications") loadNotifications();
  if (initialTab === "audit") loadAuditLogs();
})();

