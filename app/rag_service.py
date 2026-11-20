"""Project Noor — RAG service: faith-filtered content retrieval.

BLUEPRINT RULE (non-negotiable):
    "Never generate scripture: retrieve it or decline."

This module is the ONLY place that decides what scripture, if any,
appears in a reply. The LLM never quotes from its own memory — it can
only wrap a passage this module hands it (and the chat route verifies
the exact string is in the library after generation).

Flow:
    1. User has a faith (or "none"). If "none", retrieve() returns []
       and the reply is purely science + compassion.
    2. For a faith, we match the user's message against theme tags
       (hope, patience, grief, anxiety, forgiveness, gratitude, fear,
       loneliness, anger).
    3. We return at most ONE passage per reply (blueprint: never mix
       traditions, and keep replies focused).
    4. If nothing matches, retrieve() returns [] and the LLM is told
       to say "I don't have a fitting reflection for that right now"
       and offer a secular coping step instead.

The JSON files under app/content/ are SAMPLE content marked
"PENDING REVIEW". Real launch requires scholar + psychologist sign-off
(see README → Content Review Process).
"""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Optional

CONTENT_DIR = Path(__file__).parent / "content"
SUPPORTED_FAITHS = ("islam", "hinduism", "buddhism", "christianity", "none")

# Theme → keywords (Bangla romanized + English). Used for retrieval.
THEME_KEYWORDS = {
    "anxiety":     ["anxious", "anxiety", "worry", "worried", "tense", "nervous",
                    "chinta", "chintaa", "voy", "bhoy", "tension", "stress"],
    "grief":       ["grief", "loss", "lost", "died", "death", "mourning",
                    "mritu", "mrityu", "haralam", "hoye gelo", "chilo na"],
    "hope":        ["hopeless", "no hope", "give up", "future", "ashay",
                    "asha nai", "ashari", "bhabte pari na"],
    "patience":    ["patience", "tired", "waiting", "how long", "sabr",
                    "dhairjo", "dhairya", "koto din", "ar koto"],
    "loneliness":  ["alone", "lonely", "no one", "nobody", "isolated",
                    "eka", "ektai", "keu nai", "ekla"],
    "fear":        ["afraid", "scared", "fear", "terrified", "panic",
                    "bhoy", "voy", "voy lagche", "bhoy lagche"],
    "forgiveness": ["guilt", "guilty", "mistake", "regret", "sorry",
                    "doa", "pap", "paap", "ghrina", "ghrinna"],
    "gratitude":   ["grateful", "thankful", "blessing", "shukr",
                    "krithaggho", "dondo", "dhonnobad"],
    "anger":       ["angry", "rage", "furious", "hate",
                    "rag", "ragi", "ghrina", "kichuta"],
}


@lru_cache(maxsize=8)
def _load_faith(faith: str) -> List[Dict]:
    """Load a faith's content library once and cache it."""
    if faith in ("", "none", None):
        return []
    path = CONTENT_DIR / f"{faith}.json"
    if not path.exists():
        return []
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    # The JSON is {"meta": {...}, "passages": [...]}
    return data.get("passages", [])


def faith_meta(faith: str) -> Dict:
    """Return the metadata block (name, reviewers, version, status) for a faith."""
    if faith in ("", "none", None):
        return {}
    path = CONTENT_DIR / f"{faith}.json"
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f).get("meta", {})
    except (json.JSONDecodeError, OSError):
        return {}


def detect_themes(user_text: str) -> List[str]:
    """Map a user message to 0..N theme tags."""
    norm = " " + (user_text or "").lower() + " "
    themes = []
    for theme, words in THEME_KEYWORDS.items():
        if any(w in norm for w in words):
            themes.append(theme)
    return themes


def retrieve(faith: str, user_text: str, themes: Optional[List[str]] = None) -> Optional[Dict]:
    """Return at most ONE passage matching the themes, or None.

    Selection rule: pick the passage whose theme tags overlap most with
    the detected themes; break ties by a fixed 'priority' field (lower
    first) so the choice is deterministic across restarts.
    """
    if faith in ("", "none", None):
        return None
    if themes is None:
        themes = detect_themes(user_text)
    if not themes:
        return None

    passages = _load_faith(faith)
    if not passages:
        return None

    best = None
    best_score = 0
    for p in passages:
        tags = set(p.get("themes", []))
        score = len(tags & set(themes))
        if score > best_score or (
            score == best_score and best is not None
            and p.get("priority", 99) < best.get("priority", 99)
        ):
            best = p
            best_score = score

    if best is None or best_score == 0:
        return None
    return best


def get_passage_by_text(faith: str, exact_text: str) -> Optional[Dict]:
    """Verify a quoted passage REALLY exists in the library.

    Used after the LLM produces its reply: if the model quoted something,
    we check that exact substring is present in some passage. If not, we
    strip the quote (this enforces the 'no fabricated scripture' rule).
    """
    if faith in ("", "none", None) or not exact_text:
        return None
    passages = _load_faith(faith)
    for p in passages:
        if exact_text in (p.get("text_en", "") + " " + p.get("text_bn", "")):
            return p
    return None
