/* Noor — settings page handlers (delete-my-data, etc.). */
(function () {
  "use strict";
  if (!window.NoorStore) return;
  var store = window.NoorStore;
  var status = document.getElementById("delStatus");

  function flash(msg) {
    if (!status) return;
    status.textContent = msg;
    setTimeout(function () { if (status) status.textContent = ""; }, 3000);
  }

  function bind(id, fn, msg) {
    var btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (!confirm(msg)) return;
      fn();
      flash("মুছে ফেলা হয়েছে · Deleted.");
    });
  }

  bind("delChat", function () {
    store.clearChats();
  }, "সব কথা মুছবেন? · Delete all conversations?");

  bind("delMood", function () {
    store.clearMood();
  }, "সব মুড রেকর্ড মুছবেন? · Delete all mood records?");

  bind("delAll", function () {
    store.clearAll();
    // Re-apply defaults so the UI doesn't look stale.
    store.applyTheme();
    store.applyLang();
    // Reset all persisted selects to default.
    document.querySelectorAll("[data-persist]").forEach(function (el) {
      el.value = el.querySelector("option") ? el.querySelector("option").value : "";
    });
  }, "সব মুছবেন — কথা, মুড, পছন্দ? · Delete EVERYTHING — chats, mood, preferences?");
})();
