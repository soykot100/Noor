"""Project Noor — Safety layer.

This is the single most important module in the app. The blueprint's
two critical risks are:
    1. a missed crisis signal (someone in danger gets no help)
    2. an invented scripture quotation

This module handles risk #1. The strategy is LAYERED and CONSERVATIVE
(favouring false positives over false negatives):

    Layer 1: rule-based keyword matching (Bangla + English)
             — instant, deterministic, never skipped.
    Layer 2: phrase-pattern matching for subtler suicidal ideation.
    Layer 3: optional LLM self-check flag (set by the classifier).

Output: a SafetyDecision with:
    - level:    "none" | "watch" | "crisis"
    - tier:     1 (watch) | 2 (crisis)
    - matched:  list of triggers that fired (for the action plan)
    - message:  a warm, non-abandoning message shown to the user
    - show_help: whether the crisis banner / helpline box must appear

The chat route ALWAYS calls assess() BEFORE the LLM, and the crisis
message is layered INTO the AI reply so the AI never "leaves" the user
(blueprint rule: AI stays present while surfacing human help).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


# ------------------------------------------------------------------
# Crisis keyword bank.
# These are deliberately broad. A false positive only costs the user
# a gentle "here are helplines" line; a false negative can cost a life.
# ------------------------------------------------------------------

# Direct, high-confidence crisis words (Bangla + English).
CRISIS_KEYWORDS = [
    # English
    "kill myself", "killing myself", "kill me",
    "suicide", "suicidal", "end my life", "end it all",
    "end my suffering", "want to die", "wishing i was dead",
    "wishing i were dead", "i want to die", "i'd rather be dead",
    "better off dead", "no reason to live", "no point living",
    "cant go on", "can't go on", "cant live", "can't live",
    "take my own life", "taking my own life",
    "hurt myself", "harming myself", "self harm", "self-harm",
    "cut myself", "cutting myself",
    "overdose", "jump off", "hang myself", "hanging myself",
    "not worth living", "dont want to live", "don't want to live",
    "suicide plan", "how to kill", "ways to die",

    # Bangla (romanized common spellings)
    "atma hatya", "atmahatya", "atma-hatya",        # suicide
    "nijake mere felbo", "nijake mere fellam",      # kill myself
    "nijake maramu", "nijake mere felmu",
    "morbo", "morte chai", "morte chay",             # want to die
    "morle valo hoto", "morle valo hobe",            # better if i die
    "morle santi", "morle shanti",                   # peace in death
    "bancha chai na", "banchte chai na",             # don't want to live
    "jibon ta sesh", "jibon sesh korechi",           # life is over
    "jibon ta noy", "jibon bekaar",                  # life worthless
    "kete felbo", "kete fellam", "katbo",            # cut myself
    "bish khabo", "bish kheyechi",                   # take poison
    "jhule morbo", "jhap diye morbo",               # hang myself
    "chyasha boshi", "chyasha bosbo",                # sit for suicide
]

# Lower-confidence but still concerning — escalate to "watch" tier.
WATCH_KEYWORDS = [
    # English
    "hopeless", "helpless", "worthless", "useless",
    "no one cares", "nobody cares", "no one would miss me",
    "empty inside", "numb", "i give up", "giving up",
    "can't take it", "cant take it anymore", "too much pain",
    "tired of living", "tired of life",
    "depressed", "severe depression", "panic attack",
    "crying all the time", "cant stop crying",
    "alone", "so alone", "lonely and scared",
    "abused", "being abused", "was abused",
    "hurting", "in pain",

    # Bangla (romanized)
    "asha nai", "asha chere dilam", "asha nai kono",  # hopeless
    "kono valo lage na", "kichu valo lage na",        # nothing feels good
    "eka", "ektai", "keu nai", "keu asen na",          # alone
    "jibon ta bekaar", "jibon bekaar",                 # life worthless
    "kandte pari na", "kanna parchi", "kanna thik",    # crying
    "jibon ta keu", "keu kichu bolbe na",
    "bhoy lagche", "panic", "voy lagche",              # scared
    "khub kosto", "kosto pacchi", "kosto",             # pain
    "valo lagche na", "valo lagche na ekta",           # not feeling well
]

# Phrases that suggest someone is PLANNING (highest urgency).
PLANNING_PHRASES = [
    "i have a plan", "i've decided", "i have decided",
    "goodbye", "bye forever", "final goodbye",
    "tonight i will", "tomorrow i will", "going to do it tonight",
    "this is my last", "last message",
    "nijake marte chaitam", "ajke ratri", "kalke",     # Bangla
]


# ------------------------------------------------------------------
# Data class returned to the chat route.
# ------------------------------------------------------------------
@dataclass
class SafetyDecision:
    level: str = "none"          # "none" | "watch" | "crisis"
    tier: int = 0                # 0 none, 1 watch, 2 crisis
    matched: List[str] = field(default_factory=list)
    show_help: bool = False      # show helpline box / crisis banner
    block_llm: bool = False      # (reserved) hard-block LLM call
    message_bn: str = ""
    message_en: str = ""

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "tier": self.tier,
            "matched": self.matched,
            "show_help": self.show_help,
            "message_bn": self.message_bn,
            "message_en": self.message_en,
        }


# ------------------------------------------------------------------
# The messages shown when a crisis or watch signal fires.
# Tone: warm, present, non-judgmental, NOT clinical, NOT abandoning.
# The AI itself keeps talking — this message is PREPENDED to its reply
# so the user never feels the app "stopped responding".
# ------------------------------------------------------------------
CRISIS_MESSAGE_EN = (
    "I hear you, and I'm staying right here with you. What you're "
    "carrying is heavy, and reaching out — even to a screen — took "
    "courage. You do not have to face this alone. Please, in this "
    "moment, let a real human being help carry it. The numbers below "
    "are free, confidential, and trained for exactly this.\n\n"
    "I'll keep talking with you too. You are not a burden."
)

CRISIS_MESSAGE_BN = (
    "আমি আপনার কথা শুনছি, আর আমি এখানে আছি — যাচ্ছি না। যা আপনি "
    "বহন করছেন সেটা ভারী, আর বলা যত কঠিন হোক, এই একটা কথা বলতে "
    "পেরেছেন সেটাই অনেক। এই মুহূর্তে একজন সত্যিকারের মানুষের কাছে "
    "সাহায্য নিন — নিচের নম্বরগুলো ফ্রি, গোপনীয়, আর ঠিক এমন "
    "মুহূর্তের জন্যই তৈরি।\n\n"
    "আমি আপনার সাথে আছি। আপনি কারো বোঝা নন।"
)

WATCH_MESSAGE_EN = (
    "That sounds really painful, and I'm glad you told me. I'm here. "
    "If at any point you feel unsafe, the helplines below are free "
    "and confidential — you can save them now even if you don't "
    "need them today."
)

WATCH_MESSAGE_BN = (
    "কষ্টের কথাটা আমাকে বললেন, ধন্যবাদ। আমি আপনার পাশে আছি। যদি "
    "কখনো মনে হয় আর সহ্য হচ্ছে না, নিচের ফ্রি হেল্পলাইনগুলো "
    "এখনই সেভ রাখতে পারেন — আজ না লাগলেও কাল লাগতে পারে।"
)


def _normalize(text: str) -> str:
    """Lowercase + collapse spaces so matching is forgiving."""
    return " ".join((text or "").lower().split())


def assess(user_text: str) -> SafetyDecision:
    """Assess a single user message. Conservative: any hit = at least watch."""
    norm = _normalize(user_text)
    if not norm:
        return SafetyDecision()

    matched = []

    # --- Layer 1: planning phrases → crisis, highest urgency ---
    for p in PLANNING_PHRASES:
        if p in norm:
            matched.append(p)

    # --- Layer 2: direct crisis keywords → crisis ---
    for k in CRISIS_KEYWORDS:
        if k in norm:
            matched.append(k)

    if matched:
        return SafetyDecision(
            level="crisis",
            tier=2,
            matched=matched,
            show_help=True,
            message_bn=CRISIS_MESSAGE_BN,
            message_en=CRISIS_MESSAGE_EN,
        )

    # --- Layer 3: watch keywords → watch tier ---
    for k in WATCH_KEYWORDS:
        if k in norm:
            matched.append(k)

    if matched:
        return SafetyDecision(
            level="watch",
            tier=1,
            matched=matched,
            show_help=True,
            message_bn=WATCH_MESSAGE_BN,
            message_en=WATCH_MESSAGE_EN,
        )

    return SafetyDecision()
