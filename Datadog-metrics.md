# Dashboard: *Selective Hallucination Observability & Blast Radius*
### Our dashboards observe not just hallucinations, but the decision to evaluate them and the persona-weighted blast radius they create in production.


## GROUP 1 — Evaluation Decision Observability

> *Observability of **when and why** hallucination evaluation happens*

### Panel 1.1 — Evaluation Coverage Over Time

* **Chart type:** Time Series (Line)
* **Metrics:**

  * `llm.chats.total`
  * `llm.hallucination.evaluated.count`
* **Purpose:** Proves hallucination evaluation is **selective**, not always-on

---

### Panel 1.2 — Evaluation Trigger Rate

* **Chart type:** Time Series (Line / Area)
* **Metrics:**

  * `llm.hallucination.evaluation_rate`

    ```
    = evaluated_chats / total_chats
    ```
* **Purpose:** Shows cost-aware gating behavior

---

### Panel 1.3 — Prefilter Risk Classification Distribution

* **Chart type:** Stacked Bar (or Area)
* **Metrics:**

  * `llm.prefilter.trigger.medical_claim.count`
  * `llm.prefilter.trigger.absolute_claim.count`
  * `llm.prefilter.trigger.brand_violation.count`
  * `llm.prefilter.trigger.unsafe_ingredient.count`
  * `llm.prefilter.trigger.premature_routine.count`
  * `llm.prefilter.trigger.json_format_violation.count`
* **Purpose:** Explains *why* certain prompts enter evaluation

---

## GROUP 2 — Hallucination Detection Metrics

### Panel 2.1 — Hallucination Score Over Time

* **Chart type:** Time Series (Line)
* **Metrics:**

  * `llm.hallucination.score.avg`
* **Thresholds:**

  * Warning: `> 0.6`
  * Critical: `> 0.8`

---

### Panel 2.2 — Hallucination Severity Distribution

* **Chart type:** Histogram
* **Metrics:**

  * `llm.hallucination.score`
* **Purpose:** Shows whether hallucinations are marginal or severe

---

### Panel 2.3 — Evaluated vs Non-Evaluated Outcomes

* **Chart type:** Stacked Bar
* **Metrics:**

  * `llm.hallucination.clean.count`
  * `llm.hallucination.flagged.count`
* **Purpose:** Justifies selectivity accuracy

---

## GROUP 3 — Hallucination Blast Radius

### Panel 3.1 — Hallucination Blast Radius Index (HBRS)

* **Chart type:** Time Series (Line)
* **Metric:**
  * `llm.hallucination.blast_radius.index`
  * `llm.hallucination.score`
  * `llm.chats.total`
  * `llm.hallucination.persona_risk_weight`

    ```
    = hallucination_score × chat_volume × persona_risk_weight
    ```
* **Purpose:** Single metric that defines incident severity

---

### Panel 3.2 — Exposure vs Hallucination Correlation

* **Chart type:** Dual-Axis Time Series
* **Metrics:**

  * Left axis: `llm.chats.total`
  * Right axis: `llm.hallucination.score.avg`
* **Purpose:** Separates “bad but harmless” from “bad and widespread”

---

### Panel 3.3 — Blast Radius Heatmap by User Persona

* **Chart type:** Heatmap
* **Metrics:**

  * `llm.hallucination.score.avg`
* **Dimensions (Y-axis):**

  * `user.age_bucket`
  * `user.skin_concern`
  * `user.skin_type`
* **Purpose:** Shows propagation across vulnerable cohorts

---

## GROUP 4 — SLOs, Alerts & Runbooks

### Panel 4.1 — Hallucination Blast Radius SLO

* **Chart type:** SLO Status Widget
* **Metric:**

  * `llm.hallucination.blast_radius.index`
* **SLO Example:**

  ```
  HBRS < threshold for 99% of evaluated windows
  ```

---

### Panel 4.2 — Incident Timeline

* **Chart type:** Event Stream
* **Events:**

  * `hallucination_detected`
  * `blast_radius_threshold_breached`
  * `runbook_triggered`
* **Purpose:** Ties detection → response → resolution

---

### Panel 4.3 — Runbook Execution Status

* **Chart type:** Table
* **Metrics:**

  * `runbook.id`
  * `runbook.status`
  * `runbook.execution_time`
* **Purpose:** Shows closed-loop observability

---

## GROUP 5 — Executive Summary

### Panel 5.1 — KPI Tiles

* **Chart type:** Value / Query Value
* **Metrics:**

  * `llm.hallucination.score.peak`
  * `llm.hallucination.blast_radius.peak`
  * `llm.users.affected.count`
  * `llm.evaluation.coverage.rate`
  * `runbook.triggered.count`

---