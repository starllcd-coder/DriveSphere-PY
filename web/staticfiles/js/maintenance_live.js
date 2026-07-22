(function () {
  const root = document.getElementById("ds-maintenance");
  if (!root) return;

  const canUpdate = root.dataset.canUpdate === "1";
  const canDelete = root.dataset.canDelete === "1";
  const canReport = root.dataset.canReport === "1";

  const card = document.getElementById("m-tableCard");
  const body = document.getElementById("m-body");
  const markDoneBtn = document.getElementById("m-mark-done");

  const vehicle = document.getElementById("m-vehicle");
  const plate = document.getElementById("m-plate");
  const type = document.getElementById("m-type");
  const priority = document.getElementById("m-priority");

  let selectedId = null;

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    }[m]));
  }

  function isArabicClient() {
    return document.documentElement.lang === 'ar' || document.documentElement.dir === 'rtl';
  }

  function tr(en, ar) {
    return isArabicClient() ? ar : en;
  }

  function render(list) {
    if (!Array.isArray(list) || list.length === 0) {
      body.innerHTML = `<tr><td colspan="10" class="ds-empty">${isArabicClient() ? 'لا توجد مهام' : 'No tasks'}</td></tr>`;
      selectedId = null;
      if (markDoneBtn) markDoneBtn.disabled = true;
      return;
    }

    body.innerHTML = list.map(task => {
      const actions = [];
      if (canUpdate) actions.push(`
        <button
          class="ds-actionBtn ds-actionBtn--done"
          data-task-done="${esc(task.id)}"
          title="${esc(tr('Mark task done', 'وضع كمكتملة'))}">
          <span class="ds-actionBtn__icon" aria-hidden="true">✓</span>
          <span class="ds-actionBtn__label">${esc(tr('Mark Done', 'كمكتملة'))}</span>
        </button>
      `);
      if (canReport) actions.push(`
        <a
          class="ds-actionBtn ds-actionBtn--print"
          target="_blank"
          href="/api/maintenance/report.pdf"
          title="${esc(tr('Print maintenance report', 'طباعة تقرير الصيانة'))}">
          <span class="ds-actionBtn__icon" aria-hidden="true">🖨</span>
          <span class="ds-actionBtn__label">${esc(tr('Print', 'طباعة'))}</span>
        </a>
      `);
      if (canDelete) actions.push(`
        <button
          class="ds-actionBtn ds-actionBtn--delete"
          data-task-delete="${esc(task.id)}"
          title="${esc(tr('Delete task', 'حذف المهمة'))}">
          <span class="ds-actionBtn__icon" aria-hidden="true">🗑</span>
          <span class="ds-actionBtn__label">${esc(tr('Delete', 'حذف'))}</span>
        </button>
      `);
      return `
      <tr data-task-id="${esc(task.id)}">
        <td>${esc(task.date || task.task_date || "-")}</td>
        <td>${esc(task.vehicle || task.vehicle_name || "-")}</td>
        <td>${esc(task.plate || task.plate_number || "-")}</td>
        <td>${esc(task.type || task.task_type || "-")}</td>
        <td>${esc(task.priority || "-")}</td>
        <td>${esc(task.assignee || "-")}</td>
        <td>${esc(task.due || task.due_date || "-")}</td>
        <td>${esc(task.est_cost || "0.000")}</td>
        <td>${esc(task.notes || "")}</td>
        <td class="ds-actions-col">
          <div class="ds-actionGroup">
            ${actions.join("")}
          </div>
        </td>
      </tr>
    `;
    }).join("");

    body.querySelectorAll("tr[data-task-id]").forEach((row) => {
      const id = row.getAttribute("data-task-id");
      if (selectedId && id === String(selectedId)) row.classList.add("is-selected");
      row.addEventListener("click", () => {
        selectedId = id;
        body.querySelectorAll("tr[data-task-id]").forEach((r) => r.classList.remove("is-selected"));
        row.classList.add("is-selected");
        if (markDoneBtn) markDoneBtn.disabled = false;
      });
    });

    const hasSelected = selectedId && body.querySelector(`tr[data-task-id="${selectedId}"]`);
    if (!hasSelected) {
      selectedId = null;
      if (markDoneBtn) markDoneBtn.disabled = true;
    } else if (markDoneBtn) {
      markDoneBtn.disabled = false;
    }

    if (canUpdate) {
      body.querySelectorAll("[data-task-done]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-task-done");
        try {
          const data = await DS_API.post(`/api/maintenance/${id}/done/`, {});
          if (!data.ok) return alert(data.error || "Failed");
        } catch (err) {
          return alert(err.message || "Failed");
        }
        load();
      });
      });
    }

    if (canDelete) {
      body.querySelectorAll("[data-task-delete]").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute("data-task-delete");
        if (!confirm("Delete this task?")) return;
        try {
          const data = await DS_API.post(`/api/maintenance/${id}/delete/`, {});
          if (!data.ok) return alert(data.error || "Failed");
        } catch (err) {
          return alert(err.message || "Failed");
        }
        load();
      });
      });
    }
  }

  async function load() {
    try {
      DS_UI.setLoading(card, true);

      const qs = new URLSearchParams();
      if (type.value) qs.set("type", type.value);
      if (priority.value) qs.set("priority", priority.value);

      const data = await DS_API.get(`/api/maintenance/?${qs.toString()}`);
      if (!data.ok) throw new Error(data.error || "Maintenance failed");

      // client-side filters if backend doesn't support these query params yet
      let list = data.results || [];
      if (plate.value) {
        const q = plate.value.toLowerCase();
        list = list.filter(t => String(t.plate || t.plate_number || "").toLowerCase().includes(q));
      }
      if (vehicle.value) {
        const q = vehicle.value.toLowerCase();
        list = list.filter(t => String(t.vehicle || t.vehicle_name || "").toLowerCase().includes(q));
      }

      render(list);
      DS_UI.setLoading(card, false);
    } catch (e) {
      DS_UI.setLoading(card, false);
      DS_UI.toast("Maintenance", e.message || "Failed to load maintenance");
      body.innerHTML = `<tr><td colspan="10" class="ds-empty">Failed to load</td></tr>`;
    }
  }

  [vehicle, plate].forEach(inp => inp.addEventListener("input", debounce(load, 350)));
  type.addEventListener("change", load);
  priority.addEventListener("change", load);

  if (markDoneBtn) {
    markDoneBtn.addEventListener("click", async () => {
      if (!selectedId) {
        DS_UI.toast("Maintenance", "Select a task first");
        return;
      }
      try {
        const data = await DS_API.post(`/api/maintenance/${selectedId}/done/`, {});
        if (!data.ok) return alert(data.error || "Failed");
      } catch (err) {
        return alert(err.message || "Failed");
      }
      load();
    });
  }

  function debounce(fn, ms) {
    let t = null;
    return function () {
      clearTimeout(t);
      t = setTimeout(fn, ms);
    };
  }

  load();
})();
