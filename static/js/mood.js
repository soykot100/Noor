/* Noor — mood check-in.
   All data stays in localStorage. Nothing is sent to the server.
*/
(function () {
  "use strict";
  if (!window.NoorStore) return;
  var store = window.NoorStore;
  var KEY = store.KEYS.mood;

  var scale = document.getElementById("moodScale");
  var note = document.getElementById("moodNote");
  var saveBtn = document.getElementById("moodSave");
  var status = document.getElementById("moodStatus");
  var chart = document.getElementById("moodChart");
  var list = document.getElementById("moodList");
  var expBtn = document.getElementById("moodExport");
  var clrBtn = document.getElementById("moodClear");

  if (!scale) return;

  var selected = null;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); }
    catch (e) { return []; }
  }
  function saveAll(arr) {
    try { localStorage.setItem(KEY, JSON.stringify(arr)); } catch (e) {}
  }

  scale.querySelectorAll(".mood-opt").forEach(function (btn) {
    btn.addEventListener("click", function () {
      scale.querySelectorAll(".mood-opt").forEach(function (b) { b.classList.remove("selected"); });
      btn.classList.add("selected");
      selected = parseInt(btn.getAttribute("data-value"), 10);
    });
  });

  saveBtn.addEventListener("click", function () {
    if (!selected) {
      status.textContent = "একটি মুড বেছে নিন · Pick a mood first.";
      return;
    }
    var arr = load();
    arr.push({
      v: selected,
      note: (note.value || "").trim(),
      t: new Date().toISOString(),
    });
    // Keep last 60 entries to stay light.
    if (arr.length > 60) arr = arr.slice(-60);
    saveAll(arr);
    note.value = "";
    status.textContent = "সেভ হয়েছে · Saved.";
    render();
    setTimeout(function () { if (status) status.textContent = ""; }, 2500);
  });

  function render() {
    var arr = load();
    if (chart) {
      chart.innerHTML = "";
      var recent = arr.slice(-20);
      var max = 5;
      recent.forEach(function (e) {
        var bar = document.createElement("div");
        bar.className = "mood-bar";
        bar.style.height = ((e.v / max) * 100) + "%";
        var d = new Date(e.t);
        bar.title = (d.toLocaleDateString() + " — " + e.v + "/5" + (e.note ? " — " + e.note : ""));
        chart.appendChild(bar);
      });
      if (recent.length === 0) {
        chart.innerHTML = '<p class="muted small" style="width:100%;text-align:center;">' +
          'এখনো কোনো রেকর্ড নেই · No entries yet.</p>';
      }
    }
    if (list) {
      list.innerHTML = "";
      arr.slice(-12).reverse().forEach(function (e) {
        var li = document.createElement("li");
        var d = new Date(e.t);
        var stars = "";
        for (var i = 0; i < e.v; i++) stars += "●";
        for (var j = e.v; j < 5; j++) stars += "○";
        li.innerHTML =
          '<strong>' + stars + ' ' + e.v + '/5</strong> ' +
          '<span class="muted small">· ' + d.toLocaleString() + '</span>' +
          (e.note ? '<br><span class="small">' + escapeHtml(e.note) + '</span>' : '');
        list.appendChild(li);
      });
    }
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }

  if (expBtn) {
    expBtn.addEventListener("click", function () {
      var arr = load();
      var blob = new Blob([JSON.stringify(arr, null, 2)], { type: "application/json" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "noor-mood-" + new Date().toISOString().slice(0, 10) + ".json";
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  if (clrBtn) {
    clrBtn.addEventListener("click", function () {
      if (!confirm("সব মুড রেকর্ড মুছবেন? · Delete all mood records?")) return;
      try { localStorage.removeItem(KEY); } catch (e) {}
      render();
    });
  }

  render();
})();
