# Noor — নূর 🕊️

> _Where Science Meets Compassion, and Every Faith Finds a Place._
> _যেখানে সায়েন্স আর সহানুভূতি মেলে — আর প্রতিটি ধর্ম নিজের জায়গা পায়।_

Noor is a **free, anonymous, web-based AI companion** that gives people in
Bangladesh a private first step toward mental wellness — in **Bangla or
English**, with optional spiritual comfort from their own faith.

It is **not** a therapist, not a diagnostic tool, and never a replacement
for emergency services. It is a calm, judgment-free space to be heard, to
find a small coping step, and — only if the user wants — a reflection
from Islam, Hinduism, Buddhism, or Christianity (or none).

---

## ⚠️ Before you launch to real users

This build ships with **sample** scripture passages marked
`"SAMPLE — Pending Scholar Review"`. The blueprint is explicit:

> _"Each faith has at least two qualified reviewers: a scholar or clergy
> member plus a mental-health-literate reviewer. Nothing goes live
> without sign-off."_

**Before public launch you MUST:**

1. Have each faith's library reviewed and signed off by qualified scholars.
2. Have a psychologist review all content for clinical safety.
3. Re-review every library quarterly.

Until then, keep the app in pilot/demo mode with a small trusted group.

---

## What's in this build (the 11 MVP features)

| #   | Feature                                   | Where                             |
| --- | ----------------------------------------- | --------------------------------- |
| 1   | AI companion chat (Bangla + English)      | `/chat`                           |
| 2   | Science-only and Holistic modes           | top strip on `/chat`              |
| 3   | Four-faith + no-faith selection           | top strip on `/chat`, `/settings` |
| 4   | Anonymous access (no accounts, no PII)    | everywhere                        |
| 5   | Bangla + English full UI                  | auto-detect, switchable           |
| 6   | Crisis detection + 3-tier safety protocol | `app/safety.py`                   |
| 7   | Breathing + CBT exercises (8 curated)     | `/exercises`                      |
| 8   | Action plan at end of conversation        | "Summarize & next steps" button   |
| 9   | Mood check-in (stored on device)          | `/mood`                           |
| 10  | Delete-my-data controls                   | `/settings`                       |
| 11  | Verified helpline directory               | `/resources`                      |

---

## Quick start (local)

### 1. Install Python

Python 3.10 or newer. Check with `python --version`.

### 2. (Recommended) make a virtual environment

```bash
python -m venv venv
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your environment

```bash
cp .env.example .env
```

**মুখ্য: ফ্রি AI key নেওয়ার নিয়ম (Groq — ৩০ সেকেন্ড, সম্পূর্ণ ফ্রি):**

1. <https://console.groq.com/keys> এ যান।
2. ফ্রি account বানান (Google login — কোনো ক্রেডিট কার্ড লাগে না)।
3. **Create API Key** চাপুন → key কপি করুন।
4. `.env` ফাইলে বসান:
   ```
   LLM_PROVIDER=groq
   LLM_API_KEY=gsk_...আপনার_কপি_করা_key...
   ```
5. `SECRET_KEY` — একটা লম্বা random string বসান:
   `python -c "import secrets; print(secrets.token_hex(32))"`

**Groq কেন?** সম্পূর্ণ ফ্রি tier, OpenAI SDK-র সাথে 100% compatible, খুব দ্রুত,
বাংলা+English দুটোতেই ভালো। ডিফল্ট মডেল: `openai/gpt-oss-120b`
(Groq-এর বর্তমান ফ্রি-টিয়ার মডেল, দিনে ~১৪৪০ requests)।

> ⚠️ **গুরুত্বপূর্ণ:** আগের `llama-3.3-70b-versatile` মডেলটি ২০২৬-০৮-১৬ তে Groq-এর
> ফ্রি/dev tier থেকে **বন্ধ** হয়ে গেছে — এটা ব্যবহার করলে `404 model_not_found` আসবে
> এবং app DEMO-তে পড়ে যাবে (একই উত্তর বারবার)। এই build-এ ডিফল্ট `openai/gpt-oss-120b`
> বসানো আছে। অন্য ফ্রি alt: `qwen/qwen3-32b` (তেজি, ভালো Bangla)।

> **OpenAI চাইলে:** `LLM_PROVIDER=openai` দিন এবং `LLM_API_KEY`-তে OpenAI key বসান।
> অন্য কোনো OpenAI-compatible provider (Together AI, OpenRouter) ও চলবে।
>
> **কোনো key না দিলে:** app DEMO mode-এ চলে — rule-based empathetic fallback,
> পুরো app কাজ করে, শুধু আসল AI ছাড়া।

### 5. Run

```bash
python run.py
```

Open <http://127.0.0.1:5000>.

---

## Deploy to Render

The repo includes `render.yaml` (a Render Blueprint).

### Steps

1. Push this project to a GitHub repo (e.g. `noor`).
   ```bash
   git init
   git add .
   git commit -m "Initial Noor build"
   git branch -M main
   git remote add origin https://github.com/<you>/noor.git
   git push -u origin main
   ```
2. Go to <https://render.com> → **New** → **Blueprint**.
3. Select your `noor` repo. Render reads `render.yaml` and proposes the service.
4. In the **Environment** tab, set:
   - `LLM_PROVIDER` = `groq`
   - `LLM_API_KEY` = your free Groq key from <https://console.groq.com/keys>
     (or leave empty for DEMO mode).
   - `SECRET_KEY` = a long random string.
5. Click **Apply**. Render builds and deploys. The first deploy takes ~2 min.
6. Your app is live at `https://noor.onrender.com` (or your custom subdomain).

**Notes:**

- The free plan sleeps after 15 min of inactivity; the first request after
  sleep takes ~30 s to wake. For production, use a paid plan.
- No database is needed for the MVP — chat history and mood live in the
  user's browser (truly anonymous).
- `singapore` region is set in `render.yaml` as the closest to Bangladesh;
  change it if needed.

---

## How the AI works (and stays safe)

Every reply is built in layers:

1. **Safety first.** Before the LLM is called, `app/safety.py` runs a
   layered check (rule-based keywords in **Bangla + English**, phrase
   patterns, conservative thresholds). If a crisis signal fires, a warm
   "I'm staying with you" message is prepared and the helpline box is
   flagged to appear.
2. **Optional faith retrieval.** Only if the user opted into a faith AND
   mode is not "science-only", `app/rag_service.py` retrieves **one**
   matching passage from the verified library. The LLM is given the
   passage and instructed to quote it **verbatim**.
3. **LLM call.** `app/llm_service.py` calls the LLM (Groq's
   `openai/gpt-oss-120b` by default — free and fast) with a strict
   system prompt encoding every non-negotiable rule. If no key is set or
   the call fails, a rule-based empathetic responder takes over so the
   user is never left hanging. (The footer shows ✓ LIVE or ⚠️ DEMO;
   `/api/debug` shows config status, `/api/llm-test` makes one real
   call to surface any error.)
4. **No-fabrication guard.** After the reply is generated, the route
   verifies the passage's exact text actually appears in the reply. If
   the model paraphrased or invented, the passage is **not** marked as
   used (so the UI never claims a verified quote that wasn't verbatim).
5. **Crisis surfacing.** If safety flagged it, helplines are attached to
   the response and the banner appears. The AI **never** "ends the chat"
   on a crisis — it stays present while pointing to human help.

---

## Project structure

```
noor/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── config.py          # configuration (env vars)
│   ├── routes.py          # all URL routes + chat API
│   ├── safety.py          # crisis detection (Bangla + English)
│   ├── llm_service.py     # LLM client (Groq/OpenAI/etc.) + demo fallback
│   ├── rag_service.py     # faith-filtered scripture retrieval
│   ├── exercises.py       # curated CBT + breathing exercises
│   ├── resources.py       # verified helpline directory
│   └── content/
│       ├── islam.json
│       ├── hinduism.json
│       ├── buddhism.json
│       └── christianity.json
├── templates/             # Jinja2 HTML pages
├── static/
│   ├── css/style.css
│   ├── js/{app,chat,mood,settings}.js
│   ├── icons/{icon-192,icon-512}.svg
│   └── manifest.json      # PWA
├── run.py                 # local entry point
├── requirements.txt
├── render.yaml            # Render Blueprint
├── .env.example
└── README.md
```

---

## Non-negotiable rules (encoded in the system prompt)

- Never infer religion from name, language, or location.
- Faith is optional, switchable any time, never required.
- Never imply distress reflects weak faith, sin, or punishment.
- Never mix two faith traditions in one reply.
- **Never generate scripture** — quote verbatim or decline.
- Never diagnose. Never promise cure. Never moralize.
- In crisis, the AI **stays present** while surfacing human help.

---

## Privacy

- **No accounts, no email, no phone.** Truly anonymous.
- Chat history and mood data live in the browser's `localStorage` only.
- Each request sends only the trimmed recent conversation (no identifier)
  to generate the next reply. The server stores nothing.
- If the user taps "Delete everything" in Settings, all local data is
  wiped in one click.

---

## Tech stack

- **Backend:** Python Flask 3 (modular app factory, single blueprint).
- **LLM:** Groq `openai/gpt-oss-120b` (FREE, default). Provider-agnostic —
  any OpenAI-compatible API works (OpenAI, Together AI, OpenRouter) by
  setting `LLM_PROVIDER` + `LLM_API_KEY` + optional `LLM_MODEL`.
  Free Groq alternatives: `qwen/qwen3-32b` (faster), `openai/gpt-oss-20b`.
- **Frontend:** Jinja2 templates + vanilla JS + a single CSS file. PWA-ready.
- **Hosting:** Render (gunicorn). No database needed for the MVP.

---

## Troubleshooting

**`python run.py` says "ModuleNotFoundError: flask"**
→ You skipped `pip install -r requirements.txt`, or you're not in the
virtual environment where you installed them.

**The chat gives the SAME / "scripted" answer every time (even with a key)**
→ The app is in DEMO mode. Two possible causes:

1. **No key loaded** — `LLM_API_KEY` is empty in `.env`. Open Settings →
   "AI status" (or visit `/api/debug`) to check `key_loaded`.
2. **The LLM call is failing and silently falling back to demo.** The most
   common cause: a retired model name. Visit `/api/llm-test` (or Settings →
   "Test the LLM") — it makes one real call and shows the exact error.
   - If it says **`model_not_found` / 404**: your `LLM_MODEL` was retired on
     Groq. `llama-3.3-70b-versatile` and `llama-3.1-8b-instant` were both
     shut down on 2026-08-16. Set `LLM_MODEL=openai/gpt-oss-120b` (or
     `qwen/qwen3-32b`) in `.env` and restart.
   - If it says **`auth_error` / 401/403**: bad key — re-copy it.
   - If it says **`rate_limit` / 429**: free daily cap hit — wait till UTC
     midnight, or switch to `qwen/qwen3-32b`.

The footer shows ✓ LIVE (provider/model) when the key loaded, or ⚠️ DEMO
when it did not. But note: a key can be _loaded_ yet the _call_ can still
fail (retired model) — that's why `/api/llm-test` exists.

**`AuthenticationError` / 401 from the LLM**
→ Your `LLM_API_KEY` is wrong, expired, or copied with extra spaces.
Re-copy it from <https://console.groq.com/keys> and put it in `.env`
(local) or Render's Environment tab. Make sure `LLM_PROVIDER=groq`.

**Bangla text shows as boxes / question marks**
→ The browser couldn't load Google Fonts. The CSS falls back to
`Noto Sans Bengali` then `system-ui`; on most modern systems Bangla
renders fine even without the web font.

**Render deploy says "build failed"**
→ Check the build log. Most common cause: `requirements.txt` has a
package your Python version doesn't support. The pinned versions in
`requirements.txt` are tested on Python 3.11.

---

## License & responsibility

This is a mental-health-adjacent product. Use it responsibly:

- Keep the safety layer on. Never deploy a version with crisis detection
  disabled.
- Keep the content-review process. Never publish unverified scripture to
  real users.
- Comply with Bangladesh's relevant regulations on health-adjacent
  digital services and data protection before public launch.
- The authors take no responsibility for clinical outcomes. This is a
  support tool, not a clinical service.

---

_আপনার মন আজ কেমন? — How is your heart today?_
