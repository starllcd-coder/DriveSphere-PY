/* DriveSphere - Customers list + selection */

(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function safeText(v) {
    return v === null || v === undefined ? "" : String(v);
  }

  function isArabicClient() {
    return document.documentElement.lang === "ar" || document.documentElement.dir === "rtl";
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

  const root = $("#ds-customers");
  if (!root) return;

  const elName = $("#c-name");
  const elPhone = $("#c-phone");
  const elId = $("#c-id");
  const elBody = $("#c-body");

  const btnDocsUpload = $("#c-docs-upload");
  const btnDocsView = $("#c-docs-view");
  const btnAdd = $("#c-add");
  const btnEdit = $("#c-edit");
  const btnDel = $("#c-del");

  let selectedCustomerId = null;

  const API = { list: "/api/customers/" };

  async function jsonFetch(url) {
    const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
  }

  function setSelected(id) {
    selectedCustomerId = id;
    if (btnDocsUpload) btnDocsUpload.disabled = !id;
    if (btnDocsView) btnDocsView.disabled = !id;
    if (btnEdit) btnEdit.disabled = !id;
    if (btnDel) btnDel.disabled = !id;

    $$("tr[data-id]", elBody).forEach((tr) => {
      tr.classList.toggle("is-selected", String(tr.getAttribute("data-id")) === String(id));
    });
  }

  function renderCustomers(rows) {
    if (!rows || rows.length === 0) {
      elBody.innerHTML = `<tr><td colspan="4" class="ds-empty">${isArabicClient() ? "لا يوجد عملاء" : "No customers found"}</td></tr>`;
      setSelected(null);
      return;
    }

    elBody.innerHTML = rows
      .map(
        (c) => `<tr data-id="${c.id}">
        <td>${safeText(c.name)}</td>
        <td>${safeText(c.phone_number)}</td>
        <td>${safeText(c.id_number)}</td>
        <td>${safeText(c.address)}</td>
      </tr>`,
      )
      .join("");

    $$("tr[data-id]", elBody).forEach((tr) => {
      tr.addEventListener("click", () => setSelected(tr.getAttribute("data-id")));
      tr.style.cursor = "pointer";
    });

    setSelected(null);
  }

  async function loadCustomers() {
    const params = new URLSearchParams();
    if (elName.value.trim()) params.set("name", elName.value.trim());
    if (elPhone.value.trim()) params.set("phone", elPhone.value.trim());
    if (elId.value.trim()) params.set("id_number", elId.value.trim());

    elBody.innerHTML = `<tr><td colspan="4" class="ds-empty">${isArabicClient() ? "جارٍ التحميل..." : "Loading..."}</td></tr>`;
    const data = await jsonFetch(`${API.list}?${params.toString()}`);
    renderCustomers(data.results || []);
  }

  function wireFilters() {
    const handler = () => loadCustomers().catch((e) => toast(e.message));
    [elName, elPhone, elId].forEach((el) => {
      el.addEventListener("input", debounce(handler, 250));
    });
  }

  function wireButtons() {
    if (btnAdd) {
      btnAdd.addEventListener("click", () => {
        window.location.href = "/customers/new/";
      });
    }

    if (btnEdit) {
      btnEdit.addEventListener("click", () => {
        if (!selectedCustomerId) return;
        window.location.href = `/customers/${selectedCustomerId}/edit/`;
      });
    }

    if (btnDocsUpload) {
      btnDocsUpload.addEventListener("click", () => {
        if (!selectedCustomerId) return;
        window.location.href = `/customers/${selectedCustomerId}/documents/`;
      });
    }

    if (btnDocsView) {
      btnDocsView.addEventListener("click", () => {
        if (!selectedCustomerId) return;
        window.location.href = `/customers/${selectedCustomerId}/documents/`;
      });
    }

    if (btnDel) {
      btnDel.addEventListener("click", () => {
        if (!selectedCustomerId) return;
        // eslint-disable-next-line no-alert
        if (!confirm(isArabicClient() ? "هل تريد حذف هذا العميل؟ لا يمكن التراجع عن ذلك." : "Delete this customer? This cannot be undone.")) return;
        window.location.href = `/customers/${selectedCustomerId}/delete/`;
      });
    }
  }

  function init() {
    wireFilters();
    wireButtons();
    loadCustomers().catch((e) => toast(e.message));
  }

  init();
})();
