/* Noor — chat logic.
   - Maintains conversation history in localStorage (anonymous, server has no copy).
   - Sends only the trimmed recent history with each request.
   - Renders bot reply, optional passage label, and the crisis banner
     whenever the safety layer asks for it.
*/
(function () {
  "use strict";
  if (!window.NoorStore) return;
  var store = window.NoorStore;
  var KEY = store.KEYS.chats;

  var form = document.getElementById("chatForm");
  var input = document.getElementById("msgInput");
  var log = document.getElementById("chatLog");
  var typing = document.getElementById("typing");
  var banner = document.getElementById("crisisBanner");
  var phones = document.getElementById("crisisPhones");
  var sendBtn = document.getElementById("sendBtn");
  var actionBtn = document.getElementById("actionPlanBtn");
  var clearBtn = document.getElementById("clearChatBtn");

  if (!form || !input || !log) return;

  // In-memory mirror of the history (sent to the server each turn).
  // Each item: { role: "user"|"assistant", content: "..." }
  var history = [];

  // The very first bot greeting (in the HTML) is NOT counted as history
  // for the API; we keep it only for display.

  function loadHistory() {
    try {
      var raw = localStorage.getItem(KEY);
      if (raw) history = JSON.parse(raw) || [];
    } catch (e) { history = []; }
  }
  function saveHistory() {
    try { localStorage.setItem(KEY, JSON.stringify(history.slice(-24))); } catch (e) {}
  }

  function scrollBottom() {
    log.scrollTop = log.scrollHeight;
  }

  function addUserMsg(text) {
    var row = document.createElement("div");
    row.className = "msg msg-user";
    row.innerHTML =
      '<div class="msg-bubble"></div>';
    row.querySelector(".msg-bubble").textContent = text;
    log.appendChild(row);
    scrollBottom();
  }

  function addBotMsg(replyText, passage) {
    var row = document.createElement("div");
    row.className = "msg msg-bot";
    var avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = "🕊️";
    var bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    // replyText may contain \n\n — preserve via CSS white-space: pre-wrap.
    bubble.textContent = replyText;

    if (passage) {
      var label = document.createElement("span");
      label.className = "passage-label";
      var lang = (document.documentElement.getAttribute("data-lang") || "en");
      label.textContent = lang === "bn"
        ? ("একটি প্রতিফলন — " + (passage.tradition || ""))
        : ("A reflection from " + (passage.tradition || ""));
      var cite = document.createElement("span");
      cite.className = "passage-cite";
      cite.textContent = passage.source + " — " + passage.citation;
      bubble.appendChild(label);
      // The quote text is already in the reply (verified by the server).
      bubble.appendChild(cite);
    }
    row.appendChild(avatar);
    row.appendChild(bubble);
    log.appendChild(row);
    scrollBottom();
  }

  function showCrisis(helplines) {
    if (!banner || !phones) return;
    phones.innerHTML = "";
    (helplines || []).forEach(function (h) {
      var a = document.createElement("a");
      var phonesList = h.phones || [];
      a.href = "tel:" + (phonesList[0] || "");
      a.textContent = h.name + ": " + phonesList.join(" · ");
      phones.appendChild(a);
    });
    banner.hidden = false;
    banner.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function setTyping(on) {
    if (!typing) return;
    typing.hidden = !on;
    if (on) scrollBottom();
  }

  function setLoading(on) {
    sendBtn.disabled = on;
    input.disabled = on;
    if (on) setTyping(true); else setTyping(false);
  }

  async function send(text) {
    addUserMsg(text);
    history.push({ role: "user", content: text });
    saveHistory();
    setLoading(true);

    var payload = {
      message: text,
      history: history.slice(-24).filter(function (h) {
        return h && h.content && (h.role === "user" || h.role === "assistant");
      }),
      language: store.get(store.KEYS.language, "auto"),
      mode: store.get(store.KEYS.mode, "holistic"),
      faith: store.get(store.KEYS.faith, "none"),
    };

    try {
      var resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      var data = await resp.json();
      setLoading(false);

      var reply = data.reply || data.reply_en || data.reply_bn || "…";
      addBotMsg(reply, data.used_passage || null);
      history.push({ role: "assistant", content: reply });
      saveHistory();

      if (data.show_help) {
        showCrisis(data.helplines || []);
      }
    } catch (err) {
      setLoading(false);
      addBotMsg(
        "আমার একটু সমস্যা হলো। একটু পরে আবার চেষ্টা করুন।\n" +
        "I had a small problem. Please try again in a moment."
      );
    }
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = (input.value || "").trim();
    if (!text) return;
    input.value = "";
    send(text);
  });

  // Enter to send (Shift+Enter for newline)
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event("submit"));
    }
  });

  // Clear chat
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      if (!confirm("সব কথা মুছে ফেলবেন? · Delete the whole conversation?")) return;
      history = [];
      try { localStorage.removeItem(KEY); } catch (e) {}
      // Keep the first greeting, drop everything else.
      var first = log.querySelector(".msg-bot");
      log.innerHTML = "";
      if (first) log.appendChild(first);
      banner.hidden = true;
    });
  }

  // Action plan / summary
  if (actionBtn) {
    actionBtn.addEventListener("click", function () {
      if (history.length === 0) {
        addBotMsg("আগে একটু কথা বলুন, তারপর সারাংশ দিতে পারব। · Talk a little first, then I can summarize.");
        return;
      }
      var summaryReq =
        "আমাদের এই কথার একটি সংক্ষিপ্ত সারাংশ দিন এবং আগামী কয়েক দিনের জন্য " +
        "তিনটি ছোট, বাস্তবায়নযোগ্য পদক্ষেপ দিন। " +
        "Please give a brief summary of our conversation and three small, " +
        "doable next steps for the next few days.";
      send(summaryReq);
    });
  }

  // Restore banner if last turn was a crisis (best-effort).
  loadHistory();
})();
