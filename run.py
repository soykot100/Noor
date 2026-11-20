"""Project Noor — local entry point.

Run locally:
    pip install -r requirements.txt
    cp .env.example .env       # then edit .env (or leave key empty for DEMO mode)
    python run.py

Then open http://127.0.0.1:5000

On Render this file is NOT used — Render runs:
    gunicorn "app:create_app()" --workers 2 --threads 4 --timeout 60
(see render.yaml)
"""
from app import create_app

app = create_app()


if __name__ == "__main__":
    # debug=True only when running locally via `python run.py`.
    app.run(host="0.0.0.0", port=5000, debug=True)
