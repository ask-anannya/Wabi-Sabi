# Grounding, not hallucination detection

## Why this was redesigned

The original build was a text chatbot. The only signal it had was its own
output: a keyword prefilter (`api/llm/prefilter.py`) flagged responses that
*sounded* risky, and a judge LLM (`api/llm/hallucination.py`) scored how much
a response deviated from plausible, policy-compliant language. That is a
reasonable design when text is the only input — but it is fundamentally a
proxy. It measures whether the model's *language* looks safe, not whether
its *claims* are true.

Wabi-Sabi's scan path changes what's available: `POST /scan` gives the
pipeline real numeric skin measurements from YouCam Skin AI
(`api/services/youcam_client.py`) before the LLM ever generates a word. Once
real measurements exist, "does this sound hallucinated?" is the wrong
question. The right question is: **does this advice trace back to a metric
we actually measured?** That's grounding, not hallucination detection, and
it's checkable in a way free-text plausibility never was.

## The three components (`api/llm/grounding.py`)

1. **Claim grounding** — a cheap deterministic keyword pass (absolute
   language, unsupported-cause terms — the direct descendants of the old
   prefilter's `ABSOLUTE_TERMS`/`MEDICAL_TERMS`) catches the obvious cases
   for free. Anything that survives goes to one LLM judge call
   (`prompts/grounding_check.prompt`) that checks each claim against the
   measured metrics and their bands.
2. **Directional consistency** — fully deterministic, no LLM. Checks
   generated advice categories against the static `ADVICE_BANDS` lookup
   (`api/domain/advice_bands.py`): recommending something on the `avoid`
   list for the measured severity band is a consistency failure. This is
   the part a judge can verify is real just by reading the config.
3. **Metric ambiguity** — the direct conceptual replacement for the old
   `HallucinationScore`. Instead of scoring the *model's* uncertainty, it
   scores the *measurement's* uncertainty: a reading sitting near a band
   boundary (`band_distance`) is genuinely uncertain regardless of how well
   the advice is written, and lowers confidence accordingly.

These combine into a `TrustScore`, divided by a persona risk multiplier
(`PERSONA_RISK_WEIGHTS`, reused unchanged from `api/services/
user_persona_metrics.py`) — so the same measured severity yields a lower
stated confidence, and an earlier dermatologist referral, for
higher-risk personas (sensitive skin, acne, teen age bucket).

## The hard rule

If grounding or consistency fails, the pipeline does not attach a
low-confidence caveat to an ungrounded claim and speak it anyway — it strips
the offending claim before the result is spoken (`analyse_and_advise` in
`api/services/llm_service.py`). A claim either traces to a measurement or it
isn't said.

## What stayed the same, and why

`POST /llm/chat` still runs the old prefilter/hallucination pipeline
unchanged. It has no photo, no measurements — grounding has nothing to
verify against there, so the old free-text approach remains the right tool
for that path.
