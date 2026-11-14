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
  var SESSION_CHANGED = "Your session changed. Reload the page and try again.";

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
      var detail = event.detail || {};
      if (detail.xhr && detail.xhr.status === 403) {
        toast(SESSION_CHANGED, "error");
        return;
      }
      var verb = (detail.requestConfig && detail.requestConfig.verb) || "get";
      toast(verb === "get" ? LOAD_ERROR : SAVE_ERROR, "error");
    }
    document.body.addEventListener("htmx:responseError", onFailure);
    document.body.addEventListener("htmx:sendError", onFailure);

    // Session ended (the request was redirected to the login page): go to a real login
    // page instead of swapping the login form into the list.
    document.body.addEventListener("htmx:beforeSwap", function (event) {
      var xhr = event.detail && event.detail.xhr;
      if (xhr && xhr.responseURL && xhr.responseURL.indexOf("/login/") !== -1) {
        event.detail.shouldSwap = false;
        window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname + window.location.search);
      }
    });

    // After an inline stage change, put focus back on the same stage control,
    // so keyboard users don't restart from the top of the page.
    var refocusId = null;
    document.body.addEventListener("htmx:beforeRequest", function (event) {
      var form = event.detail && event.detail.elt;
      var host = form && form.closest && form.closest(".stage-popover") && form.closest(".contact-row, .stage-panel");
      refocusId = host ? host.id : null;
    });
    document.body.addEventListener("htmx:afterSettle", function () {
      if (!refocusId) return;
      var host = document.getElementById(refocusId);
      refocusId = null;
      var trigger = host && host.querySelector("summary.stage-trigger");
      if (trigger) trigger.focus();
    });

    // On touch devices, hide the bottom tab bar while the on-screen keyboard is up
    // (a text field has focus), so it doesn't cover what you're typing.
    var coarse = window.matchMedia && window.matchMedia("(pointer: coarse)");
    var TYPING = "input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=submit]), textarea";
    document.addEventListener("focusin", function (event) {
      if (coarse && coarse.matches && event.target.matches(TYPING)) document.body.classList.add("kbd-open");
    });
    document.addEventListener("focusout", function () {
      setTimeout(function () {
        var active = document.activeElement;
        if (!active || !active.matches(TYPING)) document.body.classList.remove("kbd-open");
      }, 60);
    });

    // Drop any htmx history snapshots when logging out (belt and braces; the cache is off).
    document.addEventListener("submit", function (event) {
      var action = event.target.getAttribute("action") || "";
      if (/\/logout\/$/.test(action)) {
        try { window.localStorage.removeItem("htmx-history-cache"); } catch (e) { /* storage blocked */ }
      }
    });

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
