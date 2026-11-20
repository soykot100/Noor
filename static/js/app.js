/* Noor — shared client utilities.
   - Loads/saves preferences to localStorage (truly anonymous, server has nothing).
   - Applies theme + language.
   - Wires the mobile nav toggle.
   - Syncs all [data-persist] selects to the saved value.
*/
(function () {
  "use strict";
  var NS = "noor.";   // namespace prefix to avoid colliding with other apps
  var KEYS = {
    language: NS + "language",
    mode: NS + "mode",
    faith: NS + "faith",
    theme: NS + "theme",
    chats: NS + "chats",
    mood: NS + "mood",
  };

  function get(key, fallback) {
    try {
      var v = localStorage.getItem(key);
      return v === null ? fallback : v;
    } catch (e) { return fallback; }
  }
  function set(key, val) {
    try { localStorage.setItem(key, val); } catch (e) {}
  }
  function del(key) {
    try { localStorage.removeItem(key); } catch (e) {}
  }

  function applyTheme() {
    var theme = get(KEYS.theme, "system");
    var dark;
    if (theme === "system") {
      dark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    } else {
      dark = (theme === "dark");
    }
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }

  function applyLang() {
    var lang = get(KEYS.language, "auto");
    if (lang === "auto") {
      // Heuristic: if browser language starts with bn, prefer Bangla.
      var bl = (navigator.language || "en").toLowerCase();
      document.documentElement.setAttribute("data-lang", bl.indexOf("bn") === 0 ? "bn" : "en");
    } else {
      document.documentElement.setAttribute("data-lang", lang);
    }
    document.documentElement.setAttribute("lang", lang === "bn" ? "bn" : "en");
  }

  function syncPersistControls() {
    var nodes = document.querySelectorAll("[data-persist]");
    nodes.forEach(function (el) {
      var key = KEYS[el.getAttribute("data-persist")];
      if (!key) return;
      var saved = get(key, null);
      if (saved !== null) {
        // Only set if the option exists.
        var exists = Array.prototype.some.call(el.options, function (o) { return o.value === saved; });
        if (exists) el.value = saved;
      }
      el.addEventListener("change", function () {
        set(key, el.value);
        if (el.getAttribute("data-persist") === "theme") applyTheme();
        if (el.getAttribute("data-persist") === "language") applyLang();
      });
    });
  }

  function wireNav() {
    var toggle = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");
    if (!toggle || !links) return;
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close on link click (mobile).
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        links.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Public API used by chat.js / mood.js.
  window.NoorStore = {
    KEYS: KEYS,
    get: get, set: set, del: del,
    applyTheme: applyTheme, applyLang: applyLang,
    clearChats: function () { del(KEYS.chats); },
    clearMood: function () { del(KEYS.mood); },
    clearAll: function () {
      Object.keys(KEYS).forEach(function (k) { del(KEYS[k]); });
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    applyTheme();
    applyLang();
    syncPersistControls();
    wireNav();
    // If system theme, listen for OS change.
    if (window.matchMedia) {
      try {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
          if (get(KEYS.theme, "system") === "system") applyTheme();
        });
      } catch (e) {}
    }
  });
})();
