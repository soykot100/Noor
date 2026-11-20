"""Project Noor — OpenAI LLM service.

This module builds the system prompt, calls OpenAI when an API key is
present, and falls back to a warm rule-based responder when there is no
key (DEMO MODE) so the whole app is testable locally for free.

LAYERED REPLY (blueprint, "How the AI separates science from faith"):
    1. A science + compassion core is ALWAYS generated, inside safety
       constraints.
    2. A spiritual layer is added ONLY if the user opted in. It is the
       EXACT passage from rag_service — never paraphrased, never from
       model memory — and labeled "A reflection from [tradition]".
    3. If nothing suitable exists, Noor says so and offers a secular
       alternative.

The chat route (routes.py) is responsible for:
    - calling safety.assess() BEFORE this module
    - prepending the crisis/watch message when level != "none"
    - calling rag_service.retrieve() and passing the passage here
    - verifying the passage text appears UNMODIFIED in the final reply
"""
from __future__ import annotations
import json
import logging
from typing import List, Dict, Optional
from flask import current_app

log = logging.getLogger("noor.llm")

# ---------------------------------------------------------------------------
# System prompt. This is the heart of the AI's behaviour. It encodes every
# non-negotiable rule from the blueprint so the model cannot drift.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_EN = """\
You are Noor, a free, anonymous web companion for young people in
Bangladesh who feel anxious, lonely, or overwhelmed. You are NOT a
therapist, you do NOT diagnose, and you never replace professional help.

YOUR THREE PILLARS:
1. Science — offer evidence-based, CBT-inspired coping: name the feeling,
   breathing, grounding (5-4-3-2-1), gentle reframing, behavioural steps.
2. Compassion — warm, plain language, validating, non-judgmental. Listen
   before you advise. Never dismiss, never preach.
3. Spirituality — OPTIONAL, only when the user has chosen a faith. The
   passage provided to you in this turn is the ONLY scripture you may use.
   Quote it EXACTLY, word for word, in the user's chosen language, then
   add a short, gentle reflection that connects it to what they said.

NON-NEGOTIABLE RULES:
- Never invent or paraphrase scripture. If no passage was provided, do
  NOT quote any scripture from memory. Say instead: "I don't have a
  fitting reflection for that right now — here is a small step instead."
- Never infer religion from a person's name, language, or location.
- Never imply that distress reflects weak faith, sin, or punishment.
- Never mix two faith traditions in one reply.
- Never diagnose ("you have depression"). Describe, don't label.
- Never promise cure. Offer comfort and a small next step.
- If the user shows crisis signs, you have ALREADY been given a crisis
  message to lead with — start your reply with that message verbatim,
  then continue gently. Never tell the user to calm down. Never leave.

STYLE:
- Short paragraphs. Plain words. One idea at a time.
- End with ONE concrete, small next step the user could try today.
- CODE-MIXING IS NORMAL HERE. In Bangladesh people often write in a
  mix of Bangla and English (e.g. "ami khub stressed feel korchi,
  ki korbo?"). Meet them where they are: if they code-mix, you may
  code-mix back naturally — Bangla base with English words where they
  fit, exactly like a friend would. Do NOT force one language.
  If they write pure Bangla, reply mostly in Bangla (a line of
  English is fine). If pure English, reply in English.
- Never use emojis. Never use clinical jargon. Never moralize.
- Keep replies under ~180 words.

You are a calm presence on a hard day. That is enough.
"""

# When the user is in crisis, the system prompt is extended: the AI MUST
# lead with the provided crisis message and stay gentle.
SYSTEM_PROMPT_CRISIS_EXTENSION = """
THIS TURN IS A CRISIS TURN. A crisis message has been prepared for you.
You MUST begin your reply with that message, word for word, then add one
short warm sentence and ONE small grounding step (like a slow breath).
Do NOT lecture. Do NOT ask the person to justify their feelings. Do NOT
end the conversation. Keep it tender and short.
"""

# ---------------------------------------------------------------------------


def _build_messages(
    history: List[Dict],
    user_text: str,
    language: str,
    passage: Optional[Dict],
    faith_label: Optional[str],
    crisis_message: Optional[str],
) -> List[Dict]:
    """Assemble the message list sent to OpenAI.

    `passage` is the verified scripture dict (or None). When present,
    it is fed to the model with strict instructions to quote it exactly.
    """
    sys = SYSTEM_PROMPT_EN
    if crisis_message:
        sys = sys + "\n" + SYSTEM_PROMPT_CRISIS_EXTENSION

    lang_line = (
        f"The user's preferred UI language is {language}. "
        f"Reply primarily in that language, but stay warm and simple."
    )
    sys = sys + "\n\n" + lang_line

    if passage:
        # Feed the passage. The model must quote it VERBATIM.
        passage_block = (
            "A VERIFIED reflection the user opted in to (faith: "
            f"{faith_label}). You MAY use this passage and ONLY this "
            "passage. Quote it EXACTLY as given, then add a brief, "
            "gentle reflection that connects it to what the user said. "
            "Label it: 'A reflection from {faith_label}.'\n\n"
            f"Source: {passage.get('source')} — {passage.get('citation')}\n"
            f"English text: {passage.get('text_en')}\n"
            f"Bangla text: {passage.get('text_bn')}\n"
            f"Context note (for you only, do not recite): "
            f"{passage.get('context_note')}\n"
        )
        sys = sys + "\n\n" + passage_block
    else:
        sys = (
            sys
            + "\n\n"
            + "The user has NOT opted into a faith reflection for this "
            "turn, or no fitting passage exists. Do NOT quote any "
            "scripture. If they asked for one, say gently: 'I don't have "
            "a fitting reflection for that right now — here is a small "
            "step instead.' Then offer a secular coping step."
        )

    if crisis_message:
        sys = (
            sys
            + "\n\n"
            + f"CRISIS MESSAGE TO LEAD WITH (verbatim, then continue):\n"
            f"\"\"\"\n{crisis_message}\n\"\"\"\n"
        )

    # Trim history to last N turns (Config.MAX_HISTORY_TURNS).
    max_turns = current_app.config.get("MAX_HISTORY_TURNS", 24)
    trimmed = history[-max_turns:]

    messages = [{"role": "system", "content": sys}]
    for turn in trimmed:
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})
    return messages


def _call_openai(messages: List[Dict]) -> Optional[str]:
    """Call the LLM chat API. Provider-agnostic: works with Groq (free),
    OpenAI, Together AI, OpenRouter — any OpenAI-compatible endpoint.

    Returns the text, or None on failure (caller falls back to demo mode).
    """
    try:
        from openai import OpenAI
    except ImportError:
        log.warning("openai package not installed; using demo mode")
        return None

    api_key = current_app.config.get("LLM_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = current_app.config.get("LLM_BASE_URL")  # None = OpenAI default
    model = current_app.config.get("LLM_MODEL", "openai/gpt-oss-120b")
    provider = current_app.config.get("LLM_PROVIDER", "groq")

    try:
        # base_url=None lets the SDK use OpenAI's default endpoint.
        client = OpenAI(api_key=api_key, base_url=base_url)
        kwargs = dict(
            model=model,
            messages=messages,
            temperature=0.6,
            max_tokens=500,
            top_p=0.9,
        )
        # Some providers (Together) want a slightly higher max_tokens cap;
        # the values above are safe for Groq's openai/gpt-oss-120b.
        resp = client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content
        if text:
            text = text.strip()
        log.info("LLM reply via %s/%s (%d chars)",
                 provider, model, len(text or ""))
        return text
    except Exception as exc:  # noqa: BLE001
        log.error("LLM call failed [%s/%s]: %s", provider, model, exc)
        return None


# ---------------------------------------------------------------------------
# DEMO MODE — used when there is no OpenAI key, OR when the OpenAI call
# fails. This is rule-based but genuinely warm, so the app never feels
# broken. It also never fabricates scripture (it just presents the
# retrieved passage, if any).
# ---------------------------------------------------------------------------
DEMO_RESPONSES_EN = [
    "I hear you, and thank you for telling me. What you're feeling "
    "makes sense — it doesn't make you weak, it makes you human. "
    "Right now, can we try one slow breath together? In through your "
    "nose for four counts, hold for four, out through your mouth for "
    "six. Even one round can soften the edge.",

    "That sounds heavy, and I'm glad you put it into words. Sometimes "
    "naming the feeling is already a small step away from drowning in "
    "it. If you're willing, tell me one thing that fed this feeling "
    "today — a moment, a thought, a message. Naming it can loosen it.",

    "I'm here. You don't have to figure everything out at once. Let's "
    "pick one small thing: is there a person, a place, or a sound that "
    "has felt safe to you before? Holding that in mind for a few "
    "seconds can be a place to rest.",
]

DEMO_RESPONSES_BN = [
    "আপনার কথা শুনলাম, বলার জন্য ধন্যবাদ। যা আপনি অনুভব করছেন সেটা "
    "স্বাভাবিক — দুর্বলতা নয়, মানুষ হওয়ার লক্ষণ। এখন একটা ধীর শ্বাস "
    "একসাথে নিই? নাক দিয়ে চারে ভরুন, চারে ধরুন, মুখ দিয়ে ছয়ে ছাড়ুন। "
    "একবারেই বুক কিছুটা হালকা লাগতে পারে।",

    "ভারী লাগছে, আর কথায় বলেছেন বলেই হয়তো একটু হালকা হবে। অনুভূতির "
    "নাম বলা মানেই তার ভেতর থেকে একটু বেরিয়ে আসা। যদি রাজি থাকেন, বলুন "
    "আজ একটা জিনিস যা এই অনুভূতিটা বাড়িয়েছে — একটা মুহূর্ত, একটা ভাব, "
    "একটা মেসেজ। নাম দিলে আলাদা হয়।",

    "আমি আছি। সব একসাথে বুঝতে হবে না। একটা ছোট জিনিস বেছে নিই: "
    "আগে কখনো এমন কেউ, জায়গা, বা শব্দ ছিল যা নিরাপদ লেগেছে? সেটা "
    "মনে ধরে কয়েক সেকেন্ড থাকা একটা বিশ্রামের জায়গা হতে পারে।",
]


def _looks_bangla(text: str) -> bool:
    """True if the text contains Bengali script or strong Bangla markers."""
    if not text:
        return False
    # Bengali Unicode block U+0980–U+09FF
    if any("\u0980" <= ch <= "\u09ff" for ch in text):
        return True
    norm = text.lower()
    markers = ["ami", "tumi", "bhalo", "kemon", "kosto", "voy", "chinta",
               "valo", "lagche", "kichu", "bondhu", "ekhon", "ki", "khub"]
    hits = sum(1 for m in markers if m in norm)
    return hits >= 2


def _demo_reply(user_text: str, language: str, passage: Optional[Dict],
                faith_label: Optional[str],
                crisis_message: Optional[str],
                turn_count: int = 0) -> str:
    """Rule-based warm reply when the LLM is unavailable.

    Structure mirrors the real AI:
        [crisis message if any] + [warm validation] + [passage if any] + [step]

    The core response is chosen by ROTATING through the pool based on
    (message hash + turn count), so:
      - consecutive turns in one conversation get DIFFERENT responses
        (turn_count shifts the index by 1 each turn), and
      - different messages also usually land on different responses.
    This avoids the "same answer every time" feeling in demo mode.
    """
    bangla = language == "bn" or (language == "auto" and _looks_bangla(user_text))
    core_pool = DEMO_RESPONSES_BN if bangla else DEMO_RESPONSES_EN
    # Mix a per-message seed with the turn count, then rotate through the
    # pool. Python's % always returns a non-negative result for a positive
    # modulus, so a negative hash is safe here.
    msg_seed = hash(user_text) & 0x7FFFFFFF
    idx = (msg_seed + turn_count) % len(core_pool)
    core = core_pool[idx]

    parts = []
    if crisis_message:
        parts.append(crisis_message)
    parts.append(core)

    if passage and faith_label:
        label_bn = {
            "islam": "ইসলাম", "hinduism": "হিন্দু ধর্ম",
            "buddhism": "বৌদ্ধ ধর্ম", "christianity": "খ্রিস্টধর্ম",
        }.get(faith_label, faith_label)
        label = label_bn if bangla else faith_label.capitalize()
        text = passage.get("text_bn") if bangla else passage.get("text_en")
        cite = passage.get("citation", "")
        if text:
            reflection_intro = (
                "একটি প্রতিফলন — " if bangla else "A reflection from "
            ) + f"{label}:\n"
            parts.append(
                f"{reflection_intro}\"{text}\"\n— {cite}"
            )

    step_bn = (
        "একটা ছোট কদম: আজ রাতে ঘুমানোর আগে এক মিনিট ধীর শ্বাস নিন, "
        "আর যদি খারাপ লাগে, নিচের হেল্পলাইন নম্বরগুলো রাখুন সেভ।"
    )
    step_en = (
        "One small step: tonight before sleep, take one minute of slow "
        "breathing, and if it ever feels too heavy, the helpline numbers "
        "below are free — save them now even if you don't need them today."
    )
    parts.append(step_bn if bangla else step_en)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Public entry point.
# ---------------------------------------------------------------------------
def generate_reply(
    history: List[Dict],
    user_text: str,
    language: str = "auto",
    faith: str = "none",
    passage: Optional[Dict] = None,
    crisis_message: Optional[str] = None,
) -> Dict:
    """Return a dict with keys: reply, source, used_passage, error.

    `source` is one of: "openai" | "demo".
    `used_passage` is the passage dict if quoted, else None.
    """
    faith_label = None
    if passage:
        faith_label = passage.get("source_meta_tradition") or faith

    demo_mode = current_app.config.get("DEMO_MODE", False)

    if demo_mode:
        reply = _demo_reply(user_text, language, passage, faith_label,
                            crisis_message, turn_count=len(history))
        return {"reply": reply, "source": "demo",
                "used_passage": passage, "error": False}

    messages = _build_messages(history, user_text, language, passage,
                               faith_label, crisis_message)
    text = _call_openai(messages)

    if text is None:
        # OpenAI failed — fall back to demo so the user is never left hanging.
        reply = _demo_reply(user_text, language, passage, faith_label,
                            crisis_message, turn_count=len(history))
        return {"reply": reply, "source": "demo-fallback",
                "used_passage": passage, "error": False}

    return {"reply": text, "source": "openai",
            "used_passage": passage, "error": False}
