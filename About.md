# Wabi-Sabi

## Inspiration

Wabi-Sabi was inspired by a simple but serious problem: **people increasingly rely on AI for skincare advice**, yet skincare guidance directly affects real human bodies. Unlike casual chatbots, incorrect or hallucinated skincare recommendations can lead to irritation, long-term skin damage, or loss of trust.

While building AI-driven skincare experiences, we realized that **traditional LLM observability treats hallucinations as a binary correctness issue**, often evaluating every prompt uniformly. This approach is expensive, noisy, and fails to answer a more important question:

> *If a hallucination occurs, how many users does it actually affect, and who are they?*

This insight led us to design Wabi-Sabi not just as an AI skincare assistant, but as a **production-grade system where AI reliability, risk, and impact are observable**.



## What We Built

Wabi-Sabi is an AI-powered skincare assistant that:
- Provides **personalized skincare routines**
- Explains **ingredients and formulations**
- Answers **skin concern–specific questions**
- Tailors responses using **user attributes** such as age, skin type, and skin concern

On top of this user-facing functionality, we built a **novel LLM observability layer** focused on **selective hallucination evaluation and hallucination blast radius measurement**.



## How We Built It

### System Architecture

- **Google Cloud**  
  Used for LLM inference and backend infrastructure to ensure scalability and reliability, Metric emission through Dataflow and BigQuery.
- **Python + FastAPI**  
  Handles request orchestration, persona enrichment, and metric emission.
- **React + Vite**
  Facilitates the seamless user interface.
- **Datadog**  
  Used as the central observability platform for metrics, dashboards, alerts, and runbooks.


### Selective Hallucination Evaluation

Instead of evaluating hallucinations for every prompt, Wabi-Sabi introduces a **risk-based prefilter** that assigns a risk score.
Only prompts with risk score more than 0.25 are evaluated for hallucination. Importantly, **the decision to evaluate is itself observable**.

This allows us to track:
- How often evaluation is triggered
- Why it was triggered
- Affected users along with Pre-filter accuracy

### Hallucination Blast Radius

Detecting a hallucination alone is not enough. We wanted to understand **real-world impact**.

We introduced the **Hallucination Blast Radius Index (HBRS)**, derived inside Datadog using observable signals:

```
HBRS = HallucinationScore * ChatVolume * UserPersonaRiskWeight
```

Where:
- Hallucination Score measures semantic deviation [ Score : 0-1 ]
- Chat Volume represents real user exposure
- Persona Risk Weight reflects sensitivity based on age group and skin concern  [  Score : 1-2 ]

By emitting **atomic metrics** and deriving impact dynamically, we keep the system transparent, tunable, and production-realistic.

### Persona-Aware Impact Visualization

User attributes such as:
- `user.age_bucket`
- `user.skin_type`
- `user.skin_concern`

are emitted as **low-cardinality Datadog tags**.

This enables heatmaps and breakdowns that show:
- Which user personas are affected
- How hallucinations propagate across cohorts
- Why the same hallucination can be low-risk or high-risk depending on audience



## Challenges we ran into

### 1. Avoiding Metric Noise  
Evaluating hallucinations everywhere creates alert fatigue. Designing a selective pipeline required careful prefiltering without missing critical cases.

### 2. Balancing Simplicity and Novelty  
We had to ensure the system was explainable to judges while still demonstrating deep SRE and AI reliability thinking.

### 3. Designing Judge-Safe Observability  
We avoided black-box scores and sensitive logic by emitting only atomic, auditable metrics and deriving insights transparently in Datadog.

### 4. Mapping AI Safety to Business Impact  
Translating hallucination scores into something operationally meaningful required rethinking traditional LLM monitoring approaches.

### 5. GCP Hallucination compatibility :
Since Datadog doesn't have native integration of GCP LLMs such as VertexAI for Hallucination evaluation, we had to 
create an LLM to evaluate the hallucination.



## Accomplishments We’re Proud Of

### 1. Designed selective hallucination evaluation
Instead of evaluating every LLM response, we built a risk-based prefilter that decides when and why hallucination evaluation happens — and made that decision itself observable.

### 2. Turned hallucinations into measurable impact
We moved beyond raw hallucination scores by computing a hallucination blast radius, correlating severity with real traffic and user personas to understand who was affected and how far issues spread.

### 3. Built end-to-end AI observability with Datadog
We integrated Datadog across APM, infrastructure, AI observability, and custom hallucination metrics to create a single, coherent operational view of the system.

### 4. Defined SLOs for AI behavior, not just uptime
We established SLOs around hallucination impact, allowing AI reliability to be measured and enforced like any other production service.

### 5. Implemented actionable detection, alerts, and runbooks
Detection rules trigger Slack alerts when blast radius thresholds are breached, each linked to a runbook that guides engineers through assessment and mitigation steps.

### 6. Delivered a production-grade reliability pattern
Wabi-Sabi demonstrates a reusable approach for operating LLMs safely at scale — where hallucinations are managed as incidents with clear signals, thresholds, and response workflows.



## What We Learned

- **Not all hallucinations matter equally** — exposure and user context define risk
- Observability should measure **impact**, not just model behavior
- Making *evaluation decisions observable* is as important as evaluating outcomes
- Domain-aware personas dramatically improve interpretability of AI incidents
- Separating raw signals from derived metrics increases flexibility and trust


## What's next for Wabi-Sabi - AI Skincare assitant
### Adaptive risk-aware evaluation
- Evolve selective hallucination evaluation by dynamically adjusting prefilter thresholds based on live SLO health, traffic patterns, and incident history.

### Feedback-driven reliability loops
- Use post-incident data and runbook outcomes to continuously refine detection rules, persona risk weights, and evaluation strategies.

### Deeper integration with Datadog AI features
- Expand use of Datadog’s AI Observability to track prompt patterns, response drift, and long-term hallucination trends across model versions.

### Proactive user impact prevention
- Introduce automated mitigation actions, such as safe-response fallbacks or response throttling, before blast radius thresholds are breached.

### Model and prompt version observability
- Compare hallucination behavior across model and prompt versions to support safer rollouts and controlled experimentation.