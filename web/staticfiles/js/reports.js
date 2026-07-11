(function () {
  document.querySelectorAll(".ds-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-tab");

      document.querySelectorAll(".ds-tab").forEach(t => t.classList.remove("is-active"));
      tab.classList.add("is-active");

      document.querySelectorAll(".ds-tabPanel").forEach(p => {
        p.classList.toggle("is-active", p.getAttribute("data-panel") === target);
      });
    });
  });
})();