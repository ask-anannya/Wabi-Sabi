# Wabi-Sabi: honest skincare shopping, measured by YouCam

**Tagline:** Shop only what your skin needs and can actually handle, at an honest price. No influencer hype.

## Inspiration
Skincare shopping is driven by hype. A serum goes viral, and thousands of people buy it on the strength of someone else's skin. Retinoids show the damage most clearly: the market is full of different forms (HPR, retinol, retinal, adapalene) at very different strengths, and people with sensitive skin regularly burn their faces by jumping straight to a 1% retinol they were never ready for. Meanwhile, the same active at the same strength can cost 2× to 20× more depending on the logo.

We wanted an assistant that does what a friend with a dermatology degree and no affiliate links would do: look at your actual skin, remember what your skin has tolerated, and tell you honestly whether a product is worth it **for you**.

## What it does
1. **Scan.** A selfie goes to the **YouCam AI Skin Analysis API**, which measures 11 concerns: moisture, wrinkles, redness, dark spots, acne, pores, oiliness, radiance, texture, firmness and eye bags. It also returns a skin score and a skin age. From these readings Wabi-Sabi detects your skin type and what your skin needs right now.
2. **Learn your tolerance.** Each active (retinoids, AHAs, BHAs, vitamin C, benzoyl peroxide, niacinamide, azelaic acid) has a strength ladder.
   - You can only climb **one step** above what you've proven.
   - A strength that irritated you is blocked for good.
   - The ladder learns from an onboarding quiz ("this burned me", "this worked"), quick check-ins (fine / tingling / redness / peeling), and **repeat YouCam scans**. If redness, texture or dryness gets measurably worse after you start a new active, the app asks whether that product caused it.
3. **Honest picks.** Every product gets an Honest Score with plain-language reasons:
   - **Need:** does it address what your scan found?
   - **Tolerance (hard gate):** is it within your ladder, and free of ingredients you react to?
   - **Value:** price per ml against products doing the same job at the same strength, with an **"Overpriced"** flag that names the cheaper equivalent.
   - **Hype gap:** how heavily the brand is marketed (an editorial buzz tier) against what's actually in the bottle.
   - **People like you?:** what other users with your skin type and experience level actually logged after using it, because what worked for an influencer doesn't predict your skin.
   - **Honest dupe / Try this instead:** the same strength for less, or, when a product is too strong for you, the strongest version you *can* handle.
4. **Hype check.** Search any product you saw on your feed and get the honest verdict for your skin.
5. **Voice-first and grounded.** Scan advice is spoken aloud, and every claim is checked against the measured YouCam scores before it's voiced. Unsupported claims are removed, not softened.

## How we use the YouCam API
We use **YouCam AI Skin Analysis (S2S API v2)**, entirely server-side:
1. `POST /s2s/v2.0/file` creates the upload, and the image goes to the pre-signed URL.
2. `POST /s2s/v2.0/task/skin-analysis` runs with 11 concerns.
3. `GET /s2s/v2.0/task/skin-analysis/{task_id}` is polled asynchronously until the task succeeds.
4. The result zip is downloaded. From `score_info.json` we read every concern's `ui_score`, `skin_age` and `all.score`, and we display YouCam's annotated mask image for each concern.

The scores power the whole product:
- They set the **needs**: severity bands map to ingredient categories.
- They **detect skin type** from oiliness, moisture and redness.
- They set the **safety filters**: for example, moderate redness rules out fragrance, and significant dryness blocks retinoid escalation.
- They **verify tolerance on rescan**: a worsening in redness, texture or moisture after starting an active raises an alert.
- They track **progress**: changes count only when they're above a noise threshold.
- They **ground the spoken advice**.

## How we built it
- **Backend:** FastAPI (Python).
  - YouCam client with retries and a mock mode.
  - Deterministic trust engine: tolerance ladders, value math, hype gap, dupes.
  - SQLAlchemy store (SQLite / Postgres) for profiles, product usage, reactions and scan history.
- **Curated catalog:** about 60 real products with active ingredients, concentrations (with undisclosed strengths flagged and treated as potentially strong), and prices.
- **Gemini:** writes the spoken advice and the voice, behind a grounding checker. Product claims never come from the LLM.
- **Frontend:** React 19, TypeScript, Vite, Tailwind, framer-motion.
- **Tests:** about 60 pytest tests for the tolerance rules, the trust engine, YouCam parsing and the endpoints.

## Challenges
- Turning YouCam's 0–100 health scores into consistent severity bands, then into advice that never contradicts the measurement.
- Designing tolerance rules strict enough to prevent burns but flexible enough to let people progress, while treating undisclosed concentrations honestly.
- Keeping recommendations honest: popularity and style can break ties, but they can never outrank substance or override your tolerance.

## What we learned
Measurement changes the conversation. Once you have real skin scores, you can check advice against them, catch irritation that a person might dismiss, and say "no, not for you" with evidence.

## What's next
- YouCam AI Makeup and Skin VTO, so users can try tinted sunscreens and foundations before buying.
- A larger catalog through retailer feeds, with live prices.
- Using the community reaction data to recommend starting strengths for each skin type.

## Built with
YouCam AI Skin Analysis API · FastAPI · Python · SQLAlchemy · Gemini · React · TypeScript · Vite · Tailwind CSS
