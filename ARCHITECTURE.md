# Wabi-Sabi — Architecture

Technical deep-dive. For the product pitch see [`README.md`](README.md); for the grounding-engine design rationale see [`GROUNDING.md`](GROUNDING.md). This document assumes familiarity with both.

## Contents
- [System overview](#system-overview)
- [Deployment topology](#deployment-topology)
- [Backend layout](#backend-layout)
- [Frontend layout](#frontend-layout)
- [Scan flow (sequence)](#scan-flow-sequence)
- [Chat flow (sequence)](#chat-flow-sequence)
- [Grounding engine internals](#grounding-engine-internals)
- [Auth flow (sequence)](#auth-flow-sequence)
- [Voice / TTS flow (sequence)](#voice--tts-flow-sequence)
- [Frontend screen state machine](#frontend-screen-state-machine)
- [Data model](#data-model)
- [Configuration reference](#configuration-reference)
- [Known limitations / unverified assumptions](#known-limitations--unverified-assumptions)

---

## System overview

```mermaid
flowchart TB
    subgraph Client["Browser"]
        FE["React SPA<br/>(Vite build)"]
    end

    subgraph Edge["nginx"]
        NX["Reverse proxy +<br/>static file serving"]
    end

    subgraph Backend["FastAPI (single process)"]
        API["api/main.py<br/>routers: llm · scan · auth · tts · health"]
    end

    subgraph External["External services"]
        GEMINI["Gemini API<br/>chat · scan advice · grounding judge · TTS"]
        YOUCAM["YouCam Skin AI API<br/>file upload · task · poll · results zip"]
        GOOGLE["Google Identity Services<br/>ID token issuance + verification keys"]
        DD["Datadog Agent<br/>StatsD + APM"]
    end

    subgraph Storage["Storage"]
        SQLITE[("SQLite<br/>scans · users")]
    end

    FE -->|HTTPS| NX --> API
    API --> GEMINI
    API --> YOUCAM
    API -.verifies token against.-> GOOGLE
    API --> SQLITE
    API -->|UDP, fire-and-forget| DD

    style API fill:#1c1a1f,stroke:#5fb4d9,color:#fff
    style FE fill:#1c1a1f,stroke:#b8a9c9,color:#fff
    style SQLITE fill:#1c1a1f,stroke:#88d4ab,color:#fff
```

Single FastAPI process, single SQLite file, no message queue, no separate auth server. Deliberately minimal — every external dependency is either optional (Datadog, YouCam via mock mode, Google Sign-In) or degrades gracefully (TTS → browser voice).

---

## Deployment topology

```mermaid
flowchart LR
    subgraph Compose["docker compose"]
        DG["datadog<br/>(datadog/agent image)"]
        A["api<br/>(FastAPI + ddtrace)"]
        FEB["frontend<br/>(one-shot: vite build → copy to shared volume)"]
        N["nginx<br/>(serves the copied build, proxies /api)"]
    end
    U(("User's browser")) --> N
    N -->|static files| FEB
    N -->|/api/v1/*| A
    A --> DG

    style A fill:#1c1a1f,stroke:#5fb4d9,color:#fff
```

All four services read the **same** `env/app.env` via `env_file:` in `docker-compose*.yml` — each ignores whatever variables it doesn't need. One exception: Vite's `VITE_*` variables are baked in at **build time**, before the container ever reads `env_file:`, so they must live in `frontend/.env.local` instead (see [Configuration reference](#configuration-reference)).

`frontend`'s container doesn't run a server — its only job is `cp -a /app/. /frontend/`, copying the Vite build output into a volume that `nginx` serves directly.

---

## Backend layout

```
api/
├── main.py                 FastAPI app, CORS, exception handler, router mounts
├── llm/
│   ├── __init__.py         LLM wrapper around google-genai; two module-level
│   │                       instances: wabi_sabi_llm (chat), wabi_sabi_scan_llm (scan advice)
│   ├── grounding.py        Grounding engine — see below
│   ├── prefilter.py        Chat-path keyword risk prefilter (unchanged, pre-existing)
│   └── hallucination.py    Chat-path judge-LLM scorer (unchanged, pre-existing)
├── domain/advice_bands.py  Static band → advice-category lookup (the deterministic backbone)
├── models/                 Pydantic: llm_response, grounding, user, hallucination
├── services/
│   ├── llm_service.py      llm_chat() [chat path] + analyse_and_advise() [scan path]
│   ├── youcam_client.py    File upload → task creation → poll → results zip → parse
│   ├── scan_store.py       SQLite: scans table (save/get/delete/deltas)
│   ├── auth_store.py       SQLite: users table (upsert on sign-in)
│   ├── tts_service.py      Gemini TTS → WAV
│   ├── user_persona_metrics.py   PERSONA_RISK_WEIGHTS (reused by grounding.py)
│   └── llm_datadog_metrics.py
├── routers/                llm.py (/llm/chat), scan.py (/scan, /scan/history[/{id}]),
│                            auth.py (/auth/google), tts.py (/tts), health.py (/health)
├── prompts/                 wabi-sabi_v1/v2 (chat), wabi_sabi_scan (scan advice),
│                            hallucination_detection (chat judge), grounding_check (scan judge)
└── webhooks/, datadog_agent/, utils/
```

Root path is `/api/v1` (set in `main.py`), so every endpoint above is actually under that prefix — e.g. `POST /api/v1/scan`.

---

## Frontend layout

```
frontend/src/
├── App.tsx                 Screen state machine + top-level data (auth user, chat messages)
├── components/
│   ├── NavBar.tsx           Persistent top bar: logo, Scan/Chat/History tabs, AuthButton
│   ├── AuthButton.tsx        Google Identity Services button ↔ signed-in avatar/menu
│   ├── LandingScreen.tsx    Full-viewport-per-section descriptive landing page
│   ├── ScanScreen.tsx        Capture/upload → poll → results → voice playback → chat handoff
│   ├── ChatbotScreen.tsx, ChatBubble.tsx, TypingIndicator.tsx
│   ├── RoutineDisplay.tsx, RoutineStepCard.tsx, RoutineDetailModal.tsx   (chat-path routines)
│   ├── HistoryScreen.tsx    Scan history list + delete
│   ├── TrustLine.tsx         Confidence band — icon + text + colour, never colour alone
│   ├── ProgressView.tsx      Scan-to-scan deltas, same icon+text principle
│   └── ui/                  Button, Card, Blob, SectionHeading — shared design-token primitives
├── services/
│   ├── api.ts                axios client: chatLLM, postScan, getScanHistory,
│   │                          deleteScanHistoryEntry, signInWithGoogle, synthesizeSpeech
│   └── speech.ts             Voice controller: Gemini TTS primary, browser SpeechSynthesis fallback
└── entities/types.tsx        Shared TypeScript types (mirrors backend Pydantic models)
```

---

## Scan flow (sequence)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as ScanScreen
    participant API as FastAPI /scan
    participant YC as YouCam API
    participant G as Gemini

    U->>FE: submits/captures photo
    FE->>FE: client-side resize (long side ≤ 4096)
    FE->>API: POST /scan (multipart)
    API->>YC: POST /s2s/v2.0/file (upload URL request)
    YC-->>API: pre-signed S3 URL + file_id
    API->>YC: PUT image bytes
    API->>YC: POST /s2s/v2.0/task/skin-analysis
    YC-->>API: task_id
    loop poll until success/error
        API->>YC: GET task status
    end
    YC-->>API: results.url (zip: score_info.json + per-metric PNGs)
    API->>API: download zip, parse ui_scores, normalise + band
    API->>G: generate advice (measured metrics + allowed categories + persona)
    G-->>API: advice JSON
    API->>API: grounding check (deterministic + judge), consistency, ambiguity, trust
    API->>API: strip any failing claims, build spoken_script
    API->>API: save_scan() [metrics minus output_image]
    API-->>FE: ScanResponse (metrics incl. output_image, advice, trust, progress)
    FE->>API: POST /tts (spoken_script)
    API->>G: synthesize speech
    G-->>API: raw PCM
    API-->>FE: WAV audio
    FE->>U: plays narration
```

Key detail: **`output_image` (the annotated per-metric PNGs, base64) is only ever in the live response — never persisted.** `analyse_and_advise()` builds a separate `metrics_for_storage` list with that field excluded before calling `scan_store.save_scan()`, both to keep the SQLite file lean and to avoid sending ~1MB of image data into the Gemini prompt unnecessarily.

---

## Chat flow (sequence)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as ChatbotScreen
    participant API as FastAPI /llm/chat
    participant G as Gemini

    U->>FE: sends message
    FE->>API: POST /llm/chat {messages}
    API->>G: wabi_sabi_llm.vertex_chat(payload)
    G-->>API: raw JSON (chat or routine)
    API->>API: wabi_sabi_prefilter() — cheap keyword risk scan
    alt risk_score >= threshold
        API->>G: hallucination_detector judge call
        G-->>API: hallucination_score + category
        API->>API: log persona-weighted risk metrics
    end
    API-->>FE: {result: text or routine JSON}
```

This path is untouched by the grounding-engine rebuild — no photo, no measurements, so there's nothing for grounding to check against. The original prefilter → selective-judge-call design (cheap-first, only escalate on risk signal) remains the right tool here.

---

## Grounding engine internals

```mermaid
flowchart LR
    subgraph Input
        M["Measured SkinMetric[]<br/>name, band, normalised, band_distance"]
        ADV["Generated advice text<br/>+ recommend/avoid categories"]
    end

    subgraph Deterministic["No LLM"]
        DET["4a-1: keyword pass<br/>ABSOLUTE_TERMS + UNSUPPORTED_TERMS"]
        CONS["4b: check_consistency()<br/>vs ADVICE_BANDS avoid-lists"]
        AMB["4c: compute_ambiguity()<br/>from band_distance"]
    end

    subgraph Judge["One LLM call, only if needed"]
        LLM["4a-2: grounding_check.prompt<br/>claim-by-claim vs metrics"]
    end

    ADV --> DET
    DET -->|survives| LLM
    DET -->|hard-fail term found| FAIL1["grounding_score = 0"]
    ADV --> CONS
    M --> AMB

    LLM --> COMP["4d: compose_trust()<br/>w1·grounding + w2·consistency + w3·(1-ambiguity)<br/>÷ persona_risk_multiplier"]
    FAIL1 --> COMP
    CONS --> COMP
    AMB --> COMP

    COMP --> BAND{"score bucket"}
    BAND -->|≥0.8| CONFIDENT["confident"]
    BAND -->|≥0.6| FAIRLY["fairly_confident"]
    BAND -->|≥0.4| UNCERTAIN["uncertain"]
    BAND -->|<0.4| DERM["see_a_dermatologist"]

    style COMP fill:#1c1a1f,stroke:#5fb4d9,color:#fff
    style DERM fill:#1c1a1f,stroke:#d4807a,color:#f88
```

- **`w1, w2, w3`** — `TRUST_WEIGHTS` env var, default `0.4, 0.4, 0.2`.
- **`persona_risk_multiplier`** — mean of `PERSONA_RISK_WEIGHTS[concern]` across the user's stated concerns (`acne: 1.5, sensitive: 2.0, teen: 2.0, normal: 1.0`), reused unchanged from the original chat-path persona metrics.
- **Hard rule** — any claim that fails 4a or lands a 4b violation is removed from the `advice` list entirely in `analyse_and_advise()` before the spoken script is assembled. It is never spoken with a "might not be accurate" caveat attached.

---

## Auth flow (sequence)

```mermaid
sequenceDiagram
    participant U as User
    participant FE as AuthButton
    participant GIS as Google Identity Services
    participant API as FastAPI /auth/google
    participant DB as SQLite users

    FE->>GIS: initialize({client_id, callback})
    GIS->>FE: renders official Google button
    U->>GIS: clicks, picks account
    GIS-->>FE: credential (signed ID token)
    FE->>API: POST /auth/google {credential}
    API->>API: id_token.verify_oauth2_token(credential, aud=GOOGLE_CLIENT_ID)
    Note over API: Verifies signature against Google's public<br/>keys directly — no code exchange, no client secret
    API->>DB: upsert_user(sub, email, name, picture)
    API-->>FE: {user_id, email, name, picture}
    FE->>FE: store in localStorage,<br/>swap active user_id from anon UUID to Google sub
```

No session cookie, no server-side session store — the frontend just holds the returned `user_id` and passes it as a plain field on every `/scan` and `/scan/history` call, exactly as it already did for the anonymous local ID. Signing in changes *which* id is used; it doesn't change how any other endpoint works.

---

## Voice / TTS flow (sequence)

```mermaid
sequenceDiagram
    participant FE as speech.ts
    participant API as FastAPI /tts
    participant G as Gemini TTS

    FE->>API: POST /tts {text, style}
    API->>G: generate_content(model=gemini-2.5-flash-preview-tts,<br/>voice=Kore, response_modalities=[AUDIO])
    G-->>API: raw PCM (16-bit, 24kHz, mono)
    API->>API: wrap in WAV container
    API-->>FE: audio/wav bytes
    FE->>FE: play via <audio> element

    alt request fails or times out (>45s)
        FE->>FE: fall back to window.speechSynthesis
    end
```

Measured latency: **~25s for a ~100-word scan narration.** This is real Gemini TTS generation time, not a bug — the frontend timeout (45s) and a visible "Preparing your voice…" state are both sized around that measurement rather than assuming it's fast.

---

## Frontend screen state machine

```mermaid
stateDiagram-v2
    [*] --> landing
    landing --> scan: Start Scan
    landing --> chat: Ask Wabi a question
    scan --> chat: Talk to Wabi (scan summary seeded as first message)
    chat --> scan: nav tab
    scan --> history: nav tab
    chat --> history: nav tab
    history --> scan: nav tab
    history --> chat: nav tab
    landing --> history: nav tab
    note right of landing
        NavBar (logo, Scan/Chat/History
        tabs, AuthButton) is persistent
        across all four states
    end note
```

Single `screen: "landing" | "scan" | "chat" | "history"` state in `App.tsx` (a deliberate refactor from three separate booleans once a fourth screen was added). `AnimatePresence mode="wait"` handles the cross-fade between screens.

---

## Data model

```mermaid
erDiagram
    USERS {
        string id PK "Google sub claim"
        string email
        string name
        string picture
        datetime created_at
    }
    SCANS {
        int id PK
        string user_id FK "Google sub, or anonymous local UUID"
        datetime created_at
        json metrics_json "SkinMetric[] minus output_image"
        float trust_score
        json advice_json
    }
    USERS ||--o{ SCANS : "may own (loosely — no real FK constraint)"
```

Both tables live in one SQLite file (`SCAN_DB_PATH`, default `/app/data/scan_history.db` in the container, mounted as a named Docker volume so it survives container recreation). There's no foreign-key constraint between them — `SCANS.user_id` is just a string that happens to equal a `USERS.id` when the scanning user was signed in, or an anonymous client-generated UUID otherwise.

---

## Configuration reference

All variables live in one file, `env/app.env` (copy from `env_samples/.env.samples`), read by every container via `env_file:` — **except** `VITE_*` variables, which Vite bakes in at build time and must instead live in `frontend/.env.local`.

| Variable | Required | Purpose |
|:---|:---|:---|
| `GEMINI_API_KEY` | **Yes** | Chat, scan advice, grounding judge, TTS — everything LLM-related |
| `LLM_MODEL`, `JUDGE_MODEL`, `GROUNDING_MODEL` | Yes (have defaults) | Which Gemini model each role uses |
| `TTS_MODEL`, `TTS_VOICE` | Yes (have defaults) | `gemini-2.5-flash-preview-tts`, prebuilt voice name (`Kore` by default) |
| `TRUST_WEIGHTS` | Yes (has default) | `w1,w2,w3` for trust composition, default `0.4,0.4,0.2` |
| `YOUCAM_API_KEY` | No | Real scans; leave unset with `YOUCAM_MOCK_MODE=true` |
| `YOUCAM_API_BASE`, `YOUCAM_TIER`, `YOUCAM_MOCK_MODE`, `YOUCAM_MAX_UNITS_PER_SESSION` | Yes (have defaults) | YouCam client config |
| `SCAN_DB_PATH` | Yes (has default) | SQLite file path |
| `GOOGLE_CLIENT_ID` | No | Backend-side token audience check for Sign-In |
| `VITE_GOOGLE_CLIENT_ID` | No | **Frontend `.env.local` only** — same value as above, build-time |
| `DD_*` | No | Datadog agent connection + APM/RUM config |
| `CORS_ALLOW_ORIGINS` | Yes (has default `*`) | CORS |

---

