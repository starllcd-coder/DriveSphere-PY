(function () {
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
})();