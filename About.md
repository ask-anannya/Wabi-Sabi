# Wabi-Sabi

## Inspiration

Skincare shopping is driven by hype. A serum goes viral, and thousands of people buy it on the strength of someone else's skin. Retinoids show the damage most clearly: there are many forms (HPR, retinol, retinal, adapalene) at very different strengths, and people with sensitive skin regularly burn their faces by jumping straight to a 1% retinol they were never ready for. Meanwhile, the same active at the same strength can cost 2× to 20× more depending on the logo.

**Something that worked for someone else is not evidence that it'll work for you.** Wabi-Sabi is built around that idea: look at *your* skin, remember what *your* skin has tolerated, and tell you honestly whether a product is worth it for you.

## What it does

- **Scans your skin with YouCam AI Skin Analysis.** It measures 11 concerns (moisture, wrinkles, redness, dark spots, acne, pores, oiliness, radiance, texture, firmness, eye bags) and returns a skin age and overall score. Your skin type is detected from the scan.
- **Learns your tolerance.** Each active ingredient has a strength ladder. You climb one careful step at a time; anything that irritated you is blocked for good. The ladder learns from an onboarding quiz, quick check-ins, and repeat scans that catch rising redness, texture or dryness after a new product.
- **Recommends honestly.** Every product gets an Honest Score with plain-language reasons: does it address what your scan found, is it within your tolerance, is it fairly priced per ml, and is its buzz backed by substance. It flags overpriced products and names an honest dupe, or, when something is too strong for you, the version you *can* handle.
- **Hype check.** Search any product you saw on your feed and get the verdict for your skin.
- **Grounded, voice-first advice.** The scan result is spoken aloud, and every claim is checked against the measured scores before it's voiced.

## How we built it

- **FastAPI (Python) backend**:
  - a YouCam S2S v2 client (upload → task → poll → results zip);
  - a deterministic Honest Match trust engine and tolerance model;
  - a grounding engine for the spoken advice;
  - SQLAlchemy storage on SQLite or Postgres.
- **Curated catalog** of about 60 real products with actives, concentrations (undisclosed ones flagged and treated as strong) and prices, plus editorial brand signals.
- **Gemini** for spoken advice, the grounding judge and text-to-speech. Product claims never come from the LLM.
- **React 19 + TypeScript + Vite + Tailwind** frontend.
- **pytest**: 60 tests covering tolerance rules, the trust engine, YouCam parsing, grounding and the endpoints.
- **Datadog** for metrics and tracing across the chat and scan paths.

## How it got here

Wabi-Sabi started as a text skincare chatbot with an LLM-observability layer. That layer is still running on the chat path: a risk-based prefilter that decides *when* to run hallucination evaluation, and a persona-weighted "hallucination blast radius" built from atomic Datadog metrics (see `Metrics.md` and `Datadog-metrics.md`).

For the first YouCam hackathon it was rebuilt into a photo-scan product with a grounding engine. Once real skin measurements exist, the question changes from "does this *sound* hallucinated?" to "does this advice trace back to something we measured?" (see `GROUNDING.md`).

For the YouCam Skin AI & eCommerce VTO Hackathon it became an honest shopping assistant: the Honest Match engine, tolerance ladders, 11-concern analysis, and the Honest picks, Hype check and Tolerance screens.

## Challenges

- Turning YouCam's 0–100 health scores into consistent severity bands, then into advice and product needs that never contradict the measurement.
- Making tolerance rules strict enough to prevent burns but flexible enough to let people progress, and handling undisclosed concentrations honestly.
- Keeping recommendations honest: popularity and style can break ties, but they can never outrank substance or override your tolerance.
- Live-testing surprises, like a dropped Gemini connection silently turning a clean reading "uncertain" (now retried).

## What we learned

Measurement changes the conversation. With real skin scores you can check advice against them, catch irritation a person might dismiss, and say "no, not for you" with evidence instead of vibes.

## What's next

- YouCam AI Makeup and Skin VTO, to try tinted sunscreens and foundations before buying.
- A larger catalog from retailer feeds, with live prices.
- Using community reaction data to suggest starting strengths for each skin type.
