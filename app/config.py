"""Project Noor configuration.

All settings are read from environment variables so the same code
runs locally (with .env) and on Render (with env vars in the dashboard).

LLM PROVIDER: the app is provider-agnostic. Any OpenAI-compatible API
works — Groq (FREE, recommended), OpenAI, Together AI, OpenRouter.
Set LLM_PROVIDER + LLM_API_KEY and you're done. See .env.example.
"""
import os
from dotenv import load_dotenv

# Load .env file when running locally. On Render env vars already exist.
load_dotenv()

# Per-provider defaults so the user only needs to set the KEY.
_DEFAULT_BASE_URLS = {
    "groq":        "https://api.groq.com/openai/v1",
    "openai":      None,                                   # OpenAI SDK default
    "together":    "https://api.together.xyz/v1",
    "openrouter":  "https://openrouter.ai/api/v1",
}
_DEFAULT_MODELS = {
    # NOTE: "llama-3.3-70b-versatile" was RETIRED on Groq's free/dev tier
    # on 2026-08-16 and now returns 404 model_not_found. The official
    # successor is openai/gpt-oss-120b. A faster alt is qwen/qwen3-32b.
    "groq":        "openai/gpt-oss-120b",
    "openai":      "gpt-4o-mini",
    "together":    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "openrouter":  "meta-llama/llama-3.3-70b-instruct",
}


class Config:
    # --- Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me-in-production")

    # --- LLM provider (Groq by default — FREE, OpenAI-compatible, very fast) ---
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "groq").lower().strip()

    # The API key. We accept several env names for convenience:
    #   LLM_API_KEY  (preferred)
    #   GROQ_API_KEY (if provider is groq)
    #   OPENAI_API_KEY (legacy / if provider is openai)
    LLM_API_KEY = (
        os.environ.get("LLM_API_KEY", "").strip()
        or os.environ.get("GROQ_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
    )

    # Base URL: explicit override wins, else per-provider default.
    _explicit_base = os.environ.get("LLM_BASE_URL", "").strip()
    LLM_BASE_URL = _explicit_base or _DEFAULT_BASE_URLS.get(LLM_PROVIDER)

    # Model: explicit override wins, else per-provider default.
    _explicit_model = os.environ.get("LLM_MODEL", "").strip()
    LLM_MODEL = _explicit_model or _DEFAULT_MODELS.get(LLM_PROVIDER, "gpt-4o-mini")

    # --- App behaviour ---
    # When no LLM key is set, the app runs in DEMO mode: it uses a
    # rule-based empathetic responder instead of calling the LLM.
    # This lets you test the whole app locally with zero setup.
    DEMO_MODE = (LLM_API_KEY == "")

    DEBUG_SAFETY = os.environ.get("DEBUG_SAFETY", "0") == "1"

    # Safety: hard limits on conversation length to protect the model.
    MAX_HISTORY_TURNS = 24          # 12 user + 12 assistant messages
    MAX_USER_INPUT_CHARS = 2000     # reject extremely long messages

    # Name shown in the UI.
    APP_NAME = "Noor"
    APP_TAGLINE_BN = "আপনার মন আজ কেমন?"   # "How is your heart today?"
    APP_TAGLINE_EN = "How is your heart today?"
