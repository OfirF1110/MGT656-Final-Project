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

  var SAVE_ERROR = "Couldn't save. Check your connection and try again.";
  var LOAD_ERROR = "Couldn't load results. Check your connection and try again.";

  function closeStageMenus(except) {
    document.querySelectorAll("details.stage-menu[open]").forEach(function (menu) {
      if (menu !== except) menu.removeAttribute("open");
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("#toast-stack .oc-toast").forEach(function (el) {
      setTimeout(function () { dismiss(el); }, TOAST_MS);
    });

    // Server-sent toasts: HX-Trigger: {"toast": "Stage updated"}
    document.body.addEventListener("toast", function (event) {
      toast(event.detail && event.detail.value);
    });

    // Failed htmx requests leave the page as it was and say so.
    function onFailure(event) {
      var verb = (event.detail && event.detail.requestConfig && event.detail.requestConfig.verb) || "get";
      toast(verb === "get" ? LOAD_ERROR : SAVE_ERROR, "error");
    }
    document.body.addEventListener("htmx:responseError", onFailure);
    document.body.addEventListener("htmx:sendError", onFailure);

    // Stage menus: one open at a time; close on outside click or Escape.
    document.addEventListener("toggle", function (event) {
      var menu = event.target;
      if (menu.matches && menu.matches("details.stage-menu") && menu.open) closeStageMenus(menu);
    }, true);
    document.addEventListener("click", function (event) {
      // Outside a menu, or on the phone sheet's backdrop (the <details> itself): close.
      var menu = event.target.closest("details.stage-menu");
      if (!menu || event.target === menu) closeStageMenus(null);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      var open = document.querySelector("details.stage-menu[open]");
      if (open) {
        open.removeAttribute("open");
        var summary = open.querySelector("summary");
        if (summary) summary.focus();
      }
    });
  });
})();
