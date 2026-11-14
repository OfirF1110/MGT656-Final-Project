// OfferChat client helpers. Pages work without this file; it only adds feedback.
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  var TOAST_MS = 4000;

  function dismiss(el) {
    el.classList.add("is-leaving");
    setTimeout(function () { el.remove(); }, 220);
  }

  function toast(message, kind) {
    var stack = document.getElementById("toast-stack");
    if (!stack || !message) return;
    var el = document.createElement("div");
    el.className = "oc-toast" + (kind === "error" ? " oc-toast--error" : "");
    el.setAttribute("role", kind === "error" ? "alert" : "status");
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(function () { dismiss(el); }, TOAST_MS);
  }

  window.OfferChat = { toast: toast };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("#toast-stack .oc-toast").forEach(function (el) {
      setTimeout(function () { dismiss(el); }, TOAST_MS);
    });
  });
})();
