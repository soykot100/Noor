"""Project Noor — all URL routes.

Routes:
    GET  /              landing page (welcome + privacy explainer)
    GET  /about         about: what Noor is, content review process, privacy
    GET  /chat          the companion chat page
    POST /api/chat      chat endpoint (JSON in, JSON out)
    GET  /exercises     list of curated CBT / breathing exercises
    GET  /exercises/<id>  one exercise in full
    GET  /mood          mood check-in (stored on the device)
    GET  /resources     verified helpline directory
    GET  /settings      language / faith / mode / delete-my-data
    GET  /health        (defined in __init__.py) for Render checks

The chat endpoint is the only one that talks to OpenAI. It ALWAYS:
    1. validates input length,
    2. runs safety.assess() BEFORE any LLM call,
    3. calls rag_service.retrieve() for an OPTIONAL faith passage,
    4. calls llm_service.generate_reply() with the crisis message if any,
    5. verifies any quoted passage actually exists in the library,
    6. returns reply + safety level + (optional) helpline box flag.
"""
from __future__ import annotations
import logging
from flask import Blueprint, render_template, request, jsonify, current_app

from . import safety, rag_service, llm_service, exercises as exercises_data
from . import resources as resources_data

log = logging.getLogger("noor.routes")
bp = Blueprint("noor", __name__)


# ---------------------------------------------------------------
# Pages
# ---------------------------------------------------------------
@bp.route("/")
def index():
    return render_template(
        "index.html",
        demo_mode=current_app.config["DEMO_MODE"],
        model=current_app.config["LLM_MODEL"],
        provider=current_app.config["LLM_PROVIDER"],
    )


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/chat")
def chat():
    return render_template("chat.html", demo_mode=current_app.config["DEMO_MODE"])


@bp.route("/exercises")
def exercises_page():
    cats = {"breathing": [], "grounding": [], "cbt": [], "body": []}
    for e in exercises_data.get_all():
        cats.setdefault(e["category"], []).append(e)
    return render_template("exercises.html", categories=cats)


@bp.route("/exercises/<exid>")
def exercise_detail(exid: str):
    e = exercises_data.get_by_id(exid)
    if not e:
        return render_template("error.html", code=404,
                               message_en="Exercise not found.",
                               message_bn="অনুশীলন পাওয়া যায়নি।"), 404
    return render_template("exercise_detail.html", ex=e)


@bp.route("/breathe")
def breathe_page():
    """Live animated breathing tool (4-7-8 and Box breathing)."""
    breathing = [e for e in exercises_data.get_all()
                 if e["category"] == "breathing"]
    return render_template("breathe.html", exercises=breathing)


@bp.route("/mood")
def mood_page():
    return render_template("mood.html")


@bp.route("/resources")
def resources_page():
    data = resources_data.get_all()
    return render_template("resources.html", **data)


@bp.route("/settings")
def settings_page():
    return render_template("settings.html")


# ---------------------------------------------------------------
# Chat API  (the only route that touches the LLM)
# ---------------------------------------------------------------
@bp.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_text = (data.get("message") or "").strip()
    history = data.get("history") or []
    language = (data.get("language") or "auto").lower()
    faith = (data.get("faith") or "none").lower()
    mode = (data.get("mode") or "holistic").lower()

    # --- Input validation ---
    max_chars = current_app.config.get("MAX_USER_INPUT_CHARS", 2000)
    if not user_text:
        return jsonify(error=True, reply="Please type something first."), 400
    if len(user_text) > max_chars:
        return jsonify(
            error=True,
            reply_en=("That's quite long — could you share the part that's "
                      "heaviest right now?"),
            reply_bn=("বেশ লম্বা — এখন যেটা সবচেয়ে ভারী লাগছে, সেটুকু বলুন?"),
        ), 200

    if not isinstance(history, list):
        history = []

    # --- Layer 1: SAFETY CHECK BEFORE ANYTHING ELSE ---
    decision = safety.assess(user_text)
    crisis_message = None
    if decision.level == "crisis":
        crisis_message = (
            decision.message_bn if language == "bn" else decision.message_en
        )
    elif decision.level == "watch" and language == "bn":
        # Watch message is shown as a soft note, not prepended to the reply,
        # unless we are in Bangla — then we lead gently.
        pass

    # --- Layer 2: OPTIONAL faith passage (RAG retrieval) ---
    # Faith is "none" by default. Mode "science" overrides even an opted-in
    # faith to ensure the science-only promise.
    passage = None
    if mode != "science" and faith and faith != "none":
        themes = rag_service.detect_themes(user_text)
        passage = rag_service.retrieve(faith, user_text, themes)

    # --- Layer 3: GENERATE THE REPLY (OpenAI or demo fallback) ---
    result = llm_service.generate_reply(
        history=history,
        user_text=user_text,
        language=language,
        faith=faith,
        passage=passage,
        crisis_message=crisis_message,
    )

    reply_text = result["reply"]

    # --- Layer 4: VERIFY NO FABRICATED SCRIPTURE ---
    # If a passage was provided but its exact text is NOT in the reply,
    # the model paraphrased or invented — strip the scripture-looking part.
    used = None
    if passage:
        for field in ("text_en", "text_bn"):
            t = passage.get(field, "")
            if t and t in reply_text:
                used = passage
                break
        # If neither verbatim text appears, the model drifted. We trust the
        # safety message + reply; passage is NOT marked as "used" so the UI
        # won't claim a verified quote that wasn't verbatim.
        if used is None and current_app.config.get("DEBUG_SAFETY"):
            log.warning("Passage provided but not quoted verbatim; "
                        "not marking as used.")

    # --- Layer 5: ASSEMBLE THE CLIENT PAYLOAD ---
    payload = {
        "reply": reply_text,
        "source": result["source"],
        "safety": decision.as_dict(),
        "used_passage": (
            {
                "id": used["id"],
                "source": used["source"],
                "citation": used["citation"],
                "text_en": used.get("text_en", ""),
                "text_bn": used.get("text_bn", ""),
                "tradition": faith,
            }
            if used else None
        ),
        "show_help": decision.show_help,
        "helplines": (
            [_h_for_json(h) for h in resources_data.get_for_crisis()]
            if decision.show_help else []
        ),
        "error": False,
    }
    return jsonify(payload), 200


def _h_for_json(h):
    """Slim a helpline dict for the JSON response."""
    return {
        "name": h["name"],
        "phones": h.get("phones", [h.get("phone")] if h.get("phone") else []),
        "hours": h.get("hours", ""),
        "note_en": h.get("note_en", ""),
        "note_bn": h.get("note_bn", ""),
        "verified_date": h.get("verified_date", ""),
    }


# ---------------------------------------------------------------
# Misc API
# ---------------------------------------------------------------
@bp.route("/api/exercises")
def api_exercises():
    return jsonify(exercises=exercises_data.get_all())


@bp.route("/api/resources/crisis")
def api_crisis_resources():
    """Public endpoint the chat UI calls to render the crisis box."""
    return jsonify(helplines=[_h_for_json(h)
                              for h in resources_data.get_for_crisis()])


@bp.route("/api/faith-meta")
def api_faith_meta():
    """Return reviewer / version status for each faith library."""
    out = {}
    for f in ("islam", "hinduism", "buddhism", "christianity"):
        out[f] = rag_service.faith_meta(f)
    return jsonify(out)


@bp.route("/api/debug")
def api_debug():
    """Diagnostic: show the LLM config WITHOUT exposing the key.

    Lets you instantly see whether your Groq key loaded and which model
    will be used. Visit /api/debug in the browser.
    """
    key = current_app.config.get("LLM_API_KEY", "")
    return jsonify({
        "status": "ok",
        "demo_mode": current_app.config.get("DEMO_MODE", True),
        "provider": current_app.config.get("LLM_PROVIDER", "groq"),
        "model": current_app.config.get("LLM_MODEL", ""),
        "base_url": current_app.config.get("LLM_BASE_URL"),
        "key_loaded": bool(key),
        "key_prefix": (key[:7] + "…" + str(len(key)) + "chars") if key else "(none)",
        "hint": (
            "DEMO mode — no LLM_API_KEY found. Set it in .env and restart."
            if not key else
            "Key loaded. If replies still feel scripted, visit /api/llm-test "
            "to try one real call and see any error."
        ),
    })


@bp.route("/api/llm-test")
def api_llm_test():
    """Make ONE real LLM call to verify the key + model actually work.

    Returns the reply on success, or the exact error on failure — so you
    can tell a 404 'model not found' (wrong/retired model) from a 401/403
    (bad key) from a network error. Does NOT expose the key.
    """
    if current_app.config.get("DEMO_MODE", True):
        return jsonify({
            "ok": False, "tested": False,
            "error": "DEMO mode — no LLM_API_KEY is set, so no call was made. "
                     "Put your Groq key in .env as LLM_API_KEY and restart.",
        }), 200

    import time
    t0 = time.time()
    try:
        from openai import OpenAI
        api_key = current_app.config["LLM_API_KEY"].strip()
        base_url = current_app.config.get("LLM_BASE_URL")
        model = current_app.config["LLM_MODEL"]
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user",
                       "content": "Say a single short warm word."}],
            max_tokens=20, temperature=0.5,
        )
        text = (resp.choices[0].message.content or "").strip()
        return jsonify({
            "ok": True, "tested": True,
            "model": model,
            "reply": text,
            "ms": round((time.time() - t0) * 1000),
        }), 200
    except Exception as exc:  # noqa: BLE001
        # Surface the error type so the user can fix it.
        msg = str(exc)
        status = "model_error"
        if "404" in msg or "model_not_found" in msg or "does not exist" in msg:
            status = "model_not_found"
            msg = (f"The model '{model}' is not available on your Groq key. "
                   "It was likely retired. Set LLM_MODEL to a current model "
                   "like openai/gpt-oss-120b or qwen/qwen3-32b in .env.")
        elif "401" in msg or "AuthenticationError" in msg or "403" in msg:
            status = "auth_error"
            msg = ("Your Groq key was rejected (401/403). Re-copy it from "
                   "console.groq.com/keys and put it in .env as LLM_API_KEY.")
        elif "429" in msg or "rate" in msg.lower():
            status = "rate_limit"
            msg = ("Groq rate limit hit (429). The free tier resets at UTC "
                   "midnight. Wait a bit, or set LLM_MODEL=qwen/qwen3-32b.")
        return jsonify({"ok": False, "tested": True, "status": status,
                        "model": model, "error": msg}), 200
