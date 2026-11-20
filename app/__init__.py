"""Project Noor — Flask application factory.

This package contains the whole app. The entry point is `run.py`,
which calls `create_app()`.

Structure:
    app/__init__.py      -> create_app() factory
    app/config.py        -> configuration
    app/routes.py        -> all URL routes
    app/safety.py        -> crisis detection (Bangla + English)
    app/llm_service.py   -> OpenAI client (with demo-mode fallback)
    app/rag_service.py   -> faith-filtered content retrieval
    app/content/         -> verified scripture libraries (4 faiths)

Templates and static assets live at the project root (next to run.py),
NOT inside the `app/` package, so we point Flask at them explicitly.
"""
import os
from pathlib import Path
from flask import Flask, jsonify
from .config import Config

# Project root = parent of this `app/` package.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE_DIR = _PROJECT_ROOT / "templates"
_STATIC_DIR = _PROJECT_ROOT / "static"


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder=str(_TEMPLATE_DIR),
        static_folder=str(_STATIC_DIR),
        instance_relative_config=False,
    )
    app.config.from_object(config_class)

    # Register the blueprint that holds all routes.
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Make the LLM status available to every template (footer badge).
    @app.context_processor
    def inject_llm_status():
        return {
            "demo_mode": app.config.get("DEMO_MODE", True),
            "llm_provider": app.config.get("LLM_PROVIDER", "groq"),
            "llm_model": app.config.get("LLM_MODEL", ""),
        }

    # Simple health check for Render.
    @app.route("/health")
    def health():
        return jsonify(status="ok", demo_mode=app.config["DEMO_MODE"])

    # Central error handler so the user never sees an ugly stack trace.
    @app.errorhandler(500)
    def internal_error(_exc):
        return (
            jsonify(
                reply=(
                    "I'm sorry — something went wrong on my side. "
                    "Please try again in a moment. "
                    "If you are in crisis right now, please tap the "
                    "red button below to see helplines."
                ),
                error=True,
            ),
            200,  # return 200 so the chat UI still renders the message
        )

    return app
