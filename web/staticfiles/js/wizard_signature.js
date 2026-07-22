(function () {
  function initSignature(canvasId, clearId, outputId) {
    const canvas = document.getElementById(canvasId);
    const clearBtn = document.getElementById(clearId);
    const output = document.getElementById(outputId);

    if (!canvas || !output) return;

    const ctx = canvas.getContext("2d");
    ctx.lineWidth = 2;
    ctx.lineCap = "round";

    const blankDataUrl = canvas.toDataURL("image/png");

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

    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        output.value = "";
      });
    }

    const form = canvas.closest("form");
    if (form) {
      form.addEventListener("submit", function () {
        const dataUrl = canvas.toDataURL("image/png");
        if (output.value && dataUrl === blankDataUrl) return;
        output.value = dataUrl;
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSignature("customerSignature", "signatureClear", "signatureData");
    initSignature("inspectorSignature", "inspectorSignatureClear", "inspectorSignatureData");
    initSignature("returnSignature", "returnSignatureClear", "returnSignatureData");
  });
})();
