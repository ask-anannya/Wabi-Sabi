# How we built it: tech stack

**Wabi-Sabi** is a web app with a React front end and a Python (FastAPI) back end. **YouCam AI Skin Analysis** provides the skin measurements, and a deterministic trust engine turns them into honest product recommendations. Gemini voices the advice, but no product claim ever comes from an LLM.

**Live demo:** https://frontend-two-blush-t4kahgjhky.vercel.app

## YouCam API (the core input)

**YouCam AI Skin Analysis, S2S API v2**, is called server-side so the API key never reaches the browser:
1. `POST /s2s/v2.0/file` returns a file id and a pre-signed upload URL; the photo is uploaded exactly as instructed.
2. `POST /s2s/v2.0/task/skin-analysis` runs with **11 concerns**: moisture, wrinkle, redness, age spot, acne, pore, oiliness, radiance, texture, firmness, eye bag.
3. `GET /s2s/v2.0/task/skin-analysis/{task_id}` is polled asynchronously until the task succeeds.
4. The result zip is downloaded and parsed. `score_info.json` gives a 0–100 score per concern plus **skin age** and the **overall skin score**, and each concern's **annotated mask image** is shown over the user's own photo.

What the scores drive:
- **Needs:** each score becomes a severity band (clear / mild / moderate / significant), and each band maps to ingredient categories to recommend and avoid.
- **Skin type detection:** oily, dry, combination, normal or sensitive, inferred from oiliness, moisture and redness.
- **Safety filters:** for example, moderate redness rules out fragrance, and significant dryness blocks any retinoid step-up.
- **Reaction detection:** a measurable rise in redness, texture or dryness after starting a new product triggers an alert for the user to confirm.
- **Progress tracking** between scans, with a noise threshold so tiny changes aren't reported as improvement.
- **Grounding:** every spoken claim is checked against these measurements.

## Back end

| Technology | What we use it for |
|---|---|
| **Python 3.13 + FastAPI** | API server: scan orchestration, profile, matches, check-ins, chat, voice |
| **httpx** (async) | YouCam client with retry on network errors and non-blocking polling |
| **Pillow** | Validating and resizing images to YouCam's size limits |
| **Honest Match trust engine** (plain Python) | Scores every product: scan need × tolerance gate × value per ml × hype gap, plus honest dupes and safer alternatives. Deterministic: no AI, no network calls |
| **Tolerance model** (plain Python) | Per-ingredient strength ladders (retinoids, AHAs, BHAs, vitamin C, benzoyl peroxide, niacinamide, azelaic acid) that learn from a quiz, check-ins and rescans |
| **Curated catalog** (JSON) | About 60 real products with actives, concentrations (undisclosed ones flagged), prices and sizes, plus editorial brand buzz tiers |
| **SQLAlchemy** | Scans, users, skin profiles, product usage and reactions; SQLite by default, Postgres when `DATABASE_URL` is set |
| **google-auth** | Server-side verification of Google Sign-In tokens (optional accounts) |

## AI

| Technology | What we use it for | What it's *not* used for |
|---|---|---|
| **Gemini 2.5 Flash** (`google-genai`) | Writing the spoken scan advice, limited to ingredient categories allowed for the measured bands; the chat assistant | Recommending or describing specific products |
| **Gemini 2.5 Flash** as a grounding judge | Checking each advice claim against the measured YouCam scores before it's spoken (retries once on a dropped connection) | Scoring products |
| **Gemini TTS** | Reading the result aloud, with the browser's own speech as a fallback | |

All product scoring, tolerance rules, price comparisons and dupes are ordinary, testable code.

## Front end

| Technology | What we use it for |
|---|---|
| **React 19 + TypeScript 5.9** | Screens: Scan, Honest picks, Hype check, Tolerance, Chat, History |
| **Vite 7** | Dev server and production build |
| **Tailwind CSS 3** | Dark theme and design tokens; responsive down to phone width |
| **Framer Motion** | Screen transitions |
| **lucide-react** | Icons; every icon-only control has a screen-reader label |
| **axios** | API client |
| **Google Identity Services** | Optional sign-in |

## Infrastructure and quality

| Technology | What we use it for |
|---|---|
| **Vercel** | Hosting: the FastAPI backend as a Python serverless function and the React front end as a static build |
| **Docker Compose + nginx** | Local and self-hosted setup (API, built front end, reverse proxy) |
| **pytest** | 61 tests for tolerance rules, the trust engine, YouCam parsing (including a mock built from a real captured result), grounding and HTTP endpoints; they run without any real keys |
| **Datadog** (`datadog`, `ddtrace`, browser RUM) | Metrics and tracing: scan volume, grounding scores, trust bands, YouCam latency and failures |
| **GitHub** | Source control |

## Architecture in one line

Photo → **YouCam Skin Analysis** (11 concerns, skin age, score, masks) → severity bands → **Gemini** advice → **grounding check** → spoken result, *and* → **Honest Match engine** (your tolerance ladder + catalog facts + buzz tier + community reports) → honest picks, hype checks and alerts.

## Built with

`youcam-api` · `perfect-corp` · `python` · `fastapi` · `httpx` · `sqlalchemy` · `sqlite` · `gemini` · `google-genai` · `react` · `typescript` · `vite` · `tailwindcss` · `framer-motion` · `vercel` · `docker` · `nginx` · `pytest` · `datadog`
