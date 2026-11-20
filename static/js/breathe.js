/* Noor — live breathing animation.
   Patterns:
     478  : inhale 4, hold 7, exhale 8          (good for panic / sleep)
     box  : inhale 4, hold 4, exhale 4, hold 4  (steady, grounding)
     calm : inhale 4, exhale 6                  (gentle, easy)
*/
(function () {
  "use strict";

  var PATTERNS = {
    "478": [
      { phase: "inhale",  label_bn: "শ্বাস নিন",  label_en: "Breathe in",  scale: 1,   dur: 4 },
      { phase: "hold",    label_bn: "ধরে রাখুন", label_en: "Hold",        scale: 1,   dur: 7 },
      { phase: "exhale",  label_bn: "ছাড়ুন",    label_en: "Breathe out", scale: 0.4, dur: 8 },
    ],
    "box": [
      { phase: "inhale",  label_bn: "শ্বাস নিন",  label_en: "Breathe in",  scale: 1,   dur: 4 },
      { phase: "hold",    label_bn: "ধরে রাখুন", label_en: "Hold",        scale: 1,   dur: 4 },
      { phase: "exhale",  label_bn: "ছাড়ুন",    label_en: "Breathe out", scale: 0.4, dur: 4 },
      { phase: "hold",    label_bn: "ফাঁকা ধরুন", label_en: "Hold empty", scale: 0.4, dur: 4 },
    ],
    "calm": [
      { phase: "inhale",  label_bn: "শ্বাস নিন",  label_en: "Breathe in",  scale: 1,   dur: 4 },
      { phase: "exhale",  label_bn: "ছাড়ুন",    label_en: "Breathe out", scale: 0.4, dur: 6 },
    ],
  };

  var circle = document.getElementById("breathCircle");
  var hint = document.getElementById("breathHint");
  var labelPhase = null;
  var labelCount = document.getElementById("breathCount");
  var startBtn = document.getElementById("breatheStart");
  var stopBtn = document.getElementById("breatheStop");
  var roundsEl = document.getElementById("breatheRounds");
  var roundsEnEl = document.getElementById("breatheRoundsEn");
  var pick = document.getElementById("breathePick");

  if (!circle) return;

  var pattern = PATTERNS["478"];
  var stepIndex = 0;
  var rounds = 0;
  var running = false;
  var phaseTimer = null;
  var countTimer = null;
  var reduced = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function lang() {
    return document.documentElement.getAttribute("data-lang") || "en";
  }

  function setPhaseText(step) {
    // Hide the "Press start" hint once running.
    if (hint) hint.style.display = "none";
    var labelEl = document.getElementById("breathLabel");
    if (!labelEl) return;
    var phaseSpans = labelEl.querySelectorAll(".phase");
    phaseSpans.forEach(function (s) { s.classList.add("hidden"); });
    var bn = labelEl.querySelector(".phase.bn");
    var en = labelEl.querySelector(".phase.en");
    var txt = (lang() === "bn") ? step.label_bn : step.label_en;
    // Replace text in the matching language span.
    if (lang() === "bn" && bn) { bn.classList.remove("hidden"); bn.textContent = txt; }
    else if (en) { en.classList.remove("hidden"); en.textContent = txt; }
  }

  function setRoundDisplay() {
    if (roundsEl) roundsEl.textContent = rounds;
    if (roundsEnEl) roundsEnEl.textContent = rounds;
  }

  function applyScale(step) {
    // Match the CSS transition duration to this phase's duration so the
    // circle grows/shrinks in sync with the count.
    var dur = reduced ? 0 : step.dur;
    circle.style.transitionDuration = dur + "s";
    // Force reflow so the new transition-duration takes effect before
    // the class/scale change.
    void circle.offsetWidth;
    circle.classList.remove("inhale", "hold", "exhale", "idle");
    if (step.phase === "inhale") circle.classList.add("inhale");
    else if (step.phase === "exhale") circle.classList.add("exhale");
    else circle.classList.add("hold"); // hold works for both full & empty
  }

  function runCountdown(seconds, onDone) {
    var left = seconds;
    if (labelCount) labelCount.textContent = String(left);
    clearInterval(countTimer);
    countTimer = setInterval(function () {
      left -= 1;
      if (labelCount) labelCount.textContent = left > 0 ? String(left) : "";
      if (left <= 0) {
        clearInterval(countTimer);
        onDone();
      }
    }, 1000);
  }

  function nextStep() {
    if (!running) return;
    var step = pattern[stepIndex];
    setPhaseText(step);
    applyScale(step);
    runCountdown(step.dur, function () {
      stepIndex += 1;
      if (stepIndex >= pattern.length) {
        stepIndex = 0;
        rounds += 1;
        setRoundDisplay();
      }
      // small breath between phases
      setTimeout(nextStep, 150);
    });
  }

  function start() {
    if (running) return;
    running = true;
    stepIndex = 0;
    rounds = 0;
    setRoundDisplay();
    startBtn.disabled = true;
    stopBtn.disabled = false;
    if (pick) pick.querySelectorAll(".btn").forEach(function (b) { b.disabled = true; });
    nextStep();
  }

  function stop() {
    running = false;
    clearInterval(phaseTimer);
    clearInterval(countTimer);
    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (pick) pick.querySelectorAll(".btn").forEach(function (b) { b.disabled = false; });
    // Reset circle to idle.
    circle.classList.remove("inhale", "hold", "exhale");
    circle.classList.add("idle");
    circle.style.transitionDuration = "0s";
    if (hint) hint.style.display = "";
    var labelEl = document.getElementById("breathLabel");
    if (labelEl) {
      var bn = labelEl.querySelector(".phase.bn");
      var en = labelEl.querySelector(".phase.en");
      if (bn) { bn.textContent = "প্রস্তুত"; bn.classList.remove("hidden"); }
      if (en) { en.textContent = "Ready"; en.classList.add("hidden"); }
      if (lang() === "en") { if (bn) bn.classList.add("hidden"); if (en) en.classList.remove("hidden"); }
    }
    if (labelCount) labelCount.textContent = "";
  }

  if (startBtn) startBtn.addEventListener("click", start);
  if (stopBtn) stopBtn.addEventListener("click", stop);

  if (pick) {
    pick.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-pattern]");
      if (!btn) return;
      if (running) return; // don't switch mid-session
      pick.querySelectorAll(".btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      var name = btn.getAttribute("data-pattern");
      if (PATTERNS[name]) pattern = PATTERNS[name];
    });
  }
})();
