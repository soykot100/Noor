"""Unit tests for the safety layer — the most critical module.

Run with:  pytest tests/test_safety.py
(or without pytest:  python -m unittest tests.test_safety)
"""
import os
import sys

# Make the `app` package importable when run from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.safety import assess  # noqa: E402


def _crisis_inputs():
    return [
        "I want to kill myself",
        "I'm going to end my life tonight",
        "i'd rather be dead",
        "suicide",
        "I have a plan to hurt myself",
        "ami morbo",
        "bancha chai na",
        "nijake mere felbo",
        "atma hatya",
        "bish khabo",
        "no reason to live anymore",
    ]


def _watch_inputs():
    return [
        "I feel so hopeless lately",
        "nobody cares about me",
        "I'm so alone",
        "ami eka, keu nai",
        "khub kosto pacchi",
        "tired of living like this",
    ]


def _safe_inputs():
    return [
        "I'm excited about my exam",
        "today was a good day",
        "ami valo achi",
        "can you teach me breathing",
        "I want to learn CBT",
        "thanks for being here",
    ]


def test_crisis_inputs_trigger_crisis():
    for text in _crisis_inputs():
        d = assess(text)
        assert d.level == "crisis", f"expected crisis for: {text!r}, got {d.level}"
        assert d.tier == 2
        assert d.show_help is True
        assert d.message_en and d.message_bn


def test_watch_inputs_trigger_watch_or_higher():
    for text in _watch_inputs():
        d = assess(text)
        assert d.level in ("watch", "crisis"), (
            f"expected watch+ for: {text!r}, got {d.level}"
        )
        assert d.show_help is True


def test_safe_inputs_do_not_trigger():
    for text in _safe_inputs():
        d = assess(text)
        assert d.level == "none", f"expected none for: {text!r}, got {d.level}"
        assert d.show_help is False


def test_empty_is_safe():
    assert assess("").level == "none"
    assert assess("   ").level == "none"


if __name__ == "__main__":
    # Allow running without pytest.
    test_crisis_inputs_trigger_crisis()
    test_watch_inputs_trigger_watch_or_higher()
    test_safe_inputs_do_not_trigger()
    test_empty_is_safe()
    print("All safety tests passed.")
