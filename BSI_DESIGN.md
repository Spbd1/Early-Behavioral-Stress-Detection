# Behavioral Stress Index (BSI) Design

**Status:** Design-only specification. Do not interpret this document as an implemented model. The current code implementation is an **MVP BSI** in `src/behavioral_stress/alerting/bsi.py`; it implements a bounded heuristic score, conservative bands, an uncertainty band, a reliability proxy, top contributors, limitations, and safety warnings, while deferring local baselines, seasonality/event adjustment, calibrated uncertainty, volume-aware reliability, and full lineage/version metadata.

**Safety framing:** The Behavioral Stress Index (BSI) is **not a recession predictor** and must not be presented as a deterministic economic forecast. It is an **experimental behavioral stress monitoring indicator** intended to summarize abnormal, stress-related changes in aggregate digital traces relative to each geography's own historical baseline.

The BSI is designed to be understandable to researchers, analysts, journalists, policymakers, and non-technical dashboard users while remaining mathematically grounded enough for audit, calibration, and uncertainty reporting.

---

## 1. Purpose and Non-Goals

### 1.1 What the BSI Measures

The BSI summarizes the degree to which current collective behavior appears abnormal and stress-related compared with the historical baseline of the same geography.

It combines evidence from:

1. Hidden Markov Model (HMM) stress-regime posterior probabilities.
2. Breadth across ontology categories and signal families.
3. Persistence of stress-related signals over time.
4. Local anomaly strength.
5. Trend acceleration or deceleration.
6. Concept-drift penalties.
7. Data quality.
8. Geographic confidence.
9. Cross-signal agreement.

### 1.2 What the BSI Does Not Measure

The BSI must not be described as directly measuring:

- GDP.
- Unemployment.
- Recession probability.
- Poverty.
- Individual psychological stress.
- Causal effects of specific events unless separately validated.

### 1.3 Plain-Language Definition

> **BSI score:** A 0-100 experimental score estimating how abnormal and behaviorally stress-related current collective activity appears relative to the historical baseline of the same geography.

---

## 2. Conceptual Pipeline

```text
Raw aggregate signals
        |
        v
Local geographic normalization
        |
        v
Seasonality / holiday / event adjustment
        |
        v
Robust anomaly and trend features
        |
        v
HMM regime inference + signal-family aggregation
        |
        v
Breadth, persistence, agreement, acceleration
        |
        v
Quality, drift, and geographic confidence adjustment
        |
        v
BSI score + confidence + uncertainty interval + explanations
```

The most important design principle is that the BSI should be **relative within geography**, not a naive comparison of raw search or platform metrics across countries, regions, or cities.

---

## 3. Notation

Let:

- `g` denote a geography, such as country, region, province, metro area, or city.
- `t` denote a time period, such as day or week.
- `i` denote an individual signal, keyword group, metric, or feature.
- `c` denote an ontology category, such as debt anxiety, discount seeking, job insecurity, discretionary travel pullback, housing stress, or general economic concern.
- `f` denote a broader signal family, such as Google Trends, social content, labor-market queries, financial hardship terms, mobility-like proxies, or news-adjusted behavioral signals.
- `x_{i,g,t}` denote the raw or preprocessed value of signal `i` in geography `g` at time `t`.
- `z_{i,g,t}` denote the local normalized anomaly score.
- `a_{i,g,t}` denote a bounded anomaly-strength score in `[0, 1]`.
- `w_i` denote the base weight for signal `i`.
- `q_{i,g,t}` denote a data-quality score in `[0, 1]`.
- `d_{i,g,t}` denote a drift penalty in `[0, 1]`, where higher means more drift risk.
- `P(S_k | X_{g,1:t})` denote the HMM posterior probability of regime `k` given observations through time `t`.

Suggested HMM regimes:

- `S_0`: baseline / normal behavioral state.
- `S_1`: elevated monitoring / early stress.
- `S_2`: sustained behavioral stress.
- `S_3`: contraction-like behavioral state.

`S_3` should not be named “recession” in public dashboards. Safer labels are **contraction-like behavioral regime**, **high-stress behavioral regime**, or **severe stress-related activity regime**.

---

## 4. Geographic Normalization

### 4.1 Why Raw Google Trends Scores Are Not Directly Comparable

Raw Google Trends values are commonly scaled relative to the highest point in the selected query, geography, and time window. This means that a value of `80` in one region is not necessarily the same absolute search volume, population-adjusted search intensity, or behavioral intensity as a value of `80` in another region. Direct comparison is dangerous because:

- Scaling is relative to the selected geography and time range.
- Low-volume regions may have noisier or suppressed values.
- Query sampling and normalization can vary across requests.
- A small city can show a high relative spike from a low baseline.
- National data often aggregates enough volume to be more stable than city-level data.
- Search behavior differs culturally, linguistically, and demographically across geographies.

Therefore, BSI should compare each geography primarily against its **own historical baseline**.

### 4.2 Local Rolling Baselines

For each signal `i`, geography `g`, and time `t`, define a baseline window `B(g,t)` that excludes the current evaluation period and includes comparable historical observations.

Recommended baseline choices:

- **Daily MVP:** previous 180-365 days, excluding the most recent 7-14 days.
- **Weekly MVP:** previous 52-156 weeks, excluding the current and prior week.
- **Production:** multi-year seasonal baseline using same week-of-year or same day-of-week windows.

Robust baseline statistics:

```text
median_{i,g,t} = median(x_{i,g,s}) for s in B(g,t)
MAD_{i,g,t}    = median(|x_{i,g,s} - median_{i,g,t}|) for s in B(g,t)
```

Robust z-score:

```text
z_{i,g,t} = (x_{i,g,t} - median_{i,g,t}) / (1.4826 * MAD_{i,g,t} + epsilon)
```

where `epsilon` prevents division by very small values.

For signals where decreases indicate stress, such as discretionary travel or luxury spending interest, invert the sign:

```text
z^stress_{i,g,t} = direction_i * z_{i,g,t}
```

where:

```text
direction_i = +1  if increases imply more stress
direction_i = -1  if decreases imply more stress
```

### 4.3 Bounded Anomaly Strength

Convert robust anomalies into bounded scores:

```text
a_{i,g,t} = sigmoid(alpha_i * (z^stress_{i,g,t} - tau_i))
```

where:

- `a_{i,g,t}` is in `[0, 1]`.
- `tau_i` is the anomaly threshold where the signal begins contributing materially.
- `alpha_i` controls steepness.

A robust default is:

```text
a_{i,g,t} = clamp((z^stress_{i,g,t} - 0.5) / 3.0, 0, 1)
```

This simpler transformation is easier to explain and avoids overconfidence from extreme z-scores.

### 4.4 Low-Volume Geography Treatment

Low-volume regions should not be forced into false precision. Each geography should receive a geographic confidence score:

```text
G_{g,t} = min(1, sqrt(effective_volume_{g,t} / target_volume_level)) * coverage_{g,t} * stability_{g,t}
```

Where possible, `effective_volume` should reflect available platform volume, number of valid signals, query stability, and sampling consistency. If true volume is unavailable, use proxies such as non-zero observation rate, missingness, variance stability, and API retry consistency.

Recommended handling:

- Suppress city-level BSI if `G_{g,t}` is below a hard minimum.
- Display score with low reliability if `G_{g,t}` is marginal.
- Roll sparse geographies up to region/province/state when necessary.
- Avoid ranking low-volume regions against high-volume regions.

---

## 5. Component Scores

The BSI should combine interpretable component scores. Each component is normalized to `[0, 1]` before final scaling.

### 5.1 HMM Stress Posterior Component

Let the HMM produce posterior probabilities for stress-related regimes:

```text
p_{early,g,t}       = P(S_1 | X_{g,1:t})
p_{stress,g,t}      = P(S_2 | X_{g,1:t})
p_{contraction,g,t} = P(S_3 | X_{g,1:t})
```

Define:

```text
H_{g,t} = lambda_1 * p_{early,g,t}
        + lambda_2 * p_{stress,g,t}
        + lambda_3 * p_{contraction,g,t}
```

with:

```text
lambda_1 < lambda_2 < lambda_3
lambda_1 + lambda_2 + lambda_3 = 1
```

Example:

```text
H_{g,t} = 0.20 * p_{early,g,t}
        + 0.35 * p_{stress,g,t}
        + 0.45 * p_{contraction,g,t}
```

This component reflects inferred behavioral-regime state, not recession probability.

### 5.2 Signal Breadth Component

Breadth captures how many ontology categories and independent signal families are moving in a stress-consistent direction.

Category activation:

```text
A_{c,g,t} = weighted_mean(a_{i,g,t} for i in category c)
```

A category is active when:

```text
A_{c,g,t} >= theta_c
```

Breadth:

```text
B_{g,t} = sum_c rho_c * I(A_{c,g,t} >= theta_c) / sum_c rho_c
```

where `rho_c` are category weights and `I(.)` is an indicator function.

A smoother version avoids hard thresholds:

```text
B_{g,t} = sum_c rho_c * sigmoid(beta * (A_{c,g,t} - theta_c)) / sum_c rho_c
```

### 5.3 Signal Persistence Component

Persistence differentiates a one-day spike from sustained behavioral change.

For a lookback window `W_p`, such as 14 or 28 days:

```text
P_{g,t} = sum_{k=0}^{W_p-1} omega_k * CoreAnomaly_{g,t-k} / sum_{k=0}^{W_p-1} omega_k
```

where `omega_k` is a decay weight, for example:

```text
omega_k = exp(-k / half_life)
```

`CoreAnomaly` can be the weighted average anomaly across active, quality-adjusted signals. Production systems should require a minimum run length:

```text
persistent_flag_{g,t} = I(number of days with CoreAnomaly > theta_p in last W_p days >= m)
```

### 5.4 Anomaly Strength Component

The anomaly strength component summarizes robust local anomalies:

```text
A_{g,t} = sum_i w_i * q_{i,g,t} * (1 - d_{i,g,t}) * a_{i,g,t}
        / sum_i w_i * q_{i,g,t} * (1 - d_{i,g,t})
```

Signals with high missingness, instability, or drift contribute less.

### 5.5 Trend Acceleration Component

Acceleration captures whether stress-related activity is worsening or stabilizing.

Let `M_{g,t}` be a smoothed core stress signal, such as exponentially weighted mean anomaly:

```text
Delta_{g,t}  = M_{g,t} - M_{g,t-h}
Accel_{g,t}  = Delta_{g,t} - Delta_{g,t-h}
```

Convert to bounded score:

```text
T_{g,t} = sigmoid(gamma * Accel_{g,t})
```

Because acceleration can be noisy, it should receive a smaller weight than anomaly, breadth, or persistence. It should explain directional change, not dominate the index.

### 5.6 Drift Penalty Component

Concept drift occurs when the meaning, behavior, or data-generating process of a signal changes. Examples include keyword semantic drift, platform UI changes, API changes, or sudden query normalization shifts.

Signal-level drift estimates may use:

- Population Stability Index (PSI).
- Jensen-Shannon divergence between recent and baseline distributions.
- Change-point detection.
- Keyword co-occurrence shifts.
- Volume-normalization instability.

Aggregate drift risk:

```text
D_{g,t} = sum_i w_i * drift_score_{i,g,t} / sum_i w_i
```

Drift should reduce confidence and may dampen the score:

```text
score_dampener_{g,t} = 1 - eta_D * D_{g,t}
```

where `eta_D` is in `[0, 1]`. Recommended: drift should primarily affect confidence, not silently erase real stress signals.

### 5.7 Data Quality Component

Data quality should be separately displayed and also used in uncertainty estimates.

Signal quality:

```text
q_{i,g,t} = completeness_{i,g,t}
          * stability_{i,g,t}
          * volume_score_{i,g,t}
          * api_consistency_{i,g,t}
          * normalization_reliability_{i,g,t}
```

Aggregate data quality:

```text
Q_{g,t} = sum_i w_i * q_{i,g,t} / sum_i w_i
```

Quality dimensions:

- Missing data.
- Sparse regional coverage.
- Low-volume keywords.
- Google Trends normalization instability.
- API inconsistencies.
- Duplicate or stale data.
- Unusual platform sampling changes.

### 5.8 Geographic Confidence Component

Geographic confidence indicates how trustworthy a score is for a given geographic level.

```text
G_{g,t} = level_prior_g * coverage_{g,t} * volume_stability_{g,t} * historical_depth_{g,t}
```

Suggested level priors before empirical calibration:

| Geography level | Suggested prior |
|---|---:|
| National | 0.90-1.00 |
| Large region / state / province | 0.70-0.90 |
| Metro area | 0.55-0.80 |
| City / small local area | 0.35-0.70 |

These priors should be calibrated using observed stability and validation data, not treated as universal constants.

### 5.9 Cross-Signal Agreement Component

Agreement captures whether independent signal families corroborate the same stress-related direction.

Family activation:

```text
F_{f,g,t} = weighted_mean(a_{i,g,t} for i in family f)
```

Agreement can be measured as weighted activation across families:

```text
C_{g,t} = sum_f phi_f * I(F_{f,g,t} >= theta_f) / sum_f phi_f
```

A stronger agreement formulation rewards diverse confirmation and penalizes isolated movement:

```text
C_{g,t} = mean(F_{f,g,t}) * (1 - normalized_entropy_gap)
```

Where high agreement occurs when several independent families are simultaneously elevated. In dashboard language:

- Travel decline alone is weak evidence.
- Travel decline plus discount-seeking, layoff searches, debt terms, and housing stress is stronger evidence.

---

## 6. Recommended Composite Formulation

### 6.1 Raw Composite Score

Define the normalized component vector:

```text
V_{g,t} = [H_{g,t}, B_{g,t}, P_{g,t}, A_{g,t}, T_{g,t}, C_{g,t}]
```

The primary raw BSI is:

```text
R_{g,t} = w_H H_{g,t}
        + w_B B_{g,t}
        + w_P P_{g,t}
        + w_A A_{g,t}
        + w_T T_{g,t}
        + w_C C_{g,t}
```

with:

```text
w_H + w_B + w_P + w_A + w_T + w_C = 1
```

Recommended MVP weights:

| Component | Symbol | MVP weight | Reason |
|---|---:|---:|---|
| HMM posterior | `H` | 0.25 | Regime context, but not sole driver |
| Anomaly strength | `A` | 0.25 | Direct abnormality measure |
| Breadth | `B` | 0.15 | Protects against one-signal spikes |
| Persistence | `P` | 0.15 | Rewards sustained transitions |
| Cross-signal agreement | `C` | 0.15 | Rewards independent corroboration |
| Trend acceleration | `T` | 0.05 | Useful but noisy |

### 6.2 Quality- and Drift-Aware Adjustment

Quality and drift should be visible rather than hidden. The public score may be lightly adjusted, while confidence carries most of the quality burden.

```text
R^*_{g,t} = R_{g,t} * (1 - eta_D D_{g,t})
```

Recommended:

```text
eta_D = 0.10 to 0.25
```

Avoid large score suppression from quality penalties because that can hide real stress during messy data periods. Instead, surface uncertainty clearly.

### 6.3 Scaling to 0-100

Simple scaling:

```text
BSI_{g,t} = round(100 * clamp(R^*_{g,t}, 0, 1))
```

Calibrated scaling:

```text
BSI_{g,t} = 100 * empirical_CDF_g(R^*_{g,t})
```

Tradeoff:

- Linear scaling is easy to explain and stable for MVP.
- Empirical CDF scaling better reflects local historical rarity but can make scores less comparable across time if recalibrated too often.

Recommended production compromise:

```text
BSI_{g,t} = 100 * calibrated_monotone_transform_g(R^*_{g,t})
```

where the transform is fitted on a fixed calibration period and updated only on a controlled schedule.

---

## 7. Confidence, Reliability, and Uncertainty

### 7.1 Confidence Score

Confidence should be reported separately from the BSI score.

```text
Conf_{g,t} = Q_{g,t}^{alpha_Q}
           * G_{g,t}^{alpha_G}
           * (1 - D_{g,t})^{alpha_D}
           * model_stability_{g,t}^{alpha_M}
           * coverage_balance_{g,t}^{alpha_C}
```

Default exponents:

```text
alpha_Q = 0.35
alpha_G = 0.25
alpha_D = 0.20
alpha_M = 0.10
alpha_C = 0.10
```

`Conf_{g,t}` should be displayed as a percentage or as a reliability level.

### 7.2 Reliability Levels

| Confidence | Reliability label | Dashboard behavior |
|---:|---|---|
| `>= 0.80` | High | Show score and normal explanations |
| `0.60-0.79` | Moderate | Show score with uncertainty note |
| `0.40-0.59` | Low | Show warning, suppress rankings |
| `< 0.40` | Very low | Consider suppressing score or showing only qualitative note |

### 7.3 Uncertainty Propagation

Uncertainty should reflect both statistical variability and data reliability.

Signal-level variance estimate:

```text
Var(a_{i,g,t}) = bootstrap_or_delta_variance(a_{i,g,t})
```

Composite variance approximation:

```text
Var(R_{g,t}) ≈ sum_i effective_weight_{i,g,t}^2 * Var(a_{i,g,t})
              + Var_HMM_{g,t}
              + Var_smoothing_{g,t}
              + Var_calibration_{g,t}
```

Inflate uncertainty under low confidence:

```text
Var_adjusted(BSI_{g,t}) = 100^2 * Var(R_{g,t}) / max(Conf_{g,t}, c_min)
```

A 90% interval:

```text
Lower_{g,t} = clamp(BSI_{g,t} - 1.645 * sqrt(Var_adjusted), 0, 100)
Upper_{g,t} = clamp(BSI_{g,t} + 1.645 * sqrt(Var_adjusted), 0, 100)
```

Production systems should prefer block bootstrap or Bayesian posterior simulation:

1. Resample time blocks to preserve autocorrelation.
2. Resample signals within ontology families.
3. Draw HMM regime probabilities from posterior uncertainty.
4. Recompute BSI for each draw.
5. Report the 5th and 95th percentiles.

### 7.4 Required Output Fields

Every BSI output should include:

```json
{
  "geography": "example-region",
  "date": "YYYY-MM-DD",
  "score": 64,
  "severity_band": "significant behavioral stress",
  "confidence": 0.72,
  "reliability": "moderate",
  "uncertainty_interval_90": [54, 73],
  "experimental_label": true,
  "not_recession_prediction": true,
  "top_contributors": [],
  "drift_warnings": [],
  "data_quality_notes": []
}
```

---

## 8. Temporal Smoothing and Anti-Spike Protections

### 8.1 Smoothing Windows

Recommended smoothing:

- Daily dashboard: 7-day median or exponentially weighted moving average.
- Weekly dashboard: 4-week exponentially weighted moving average.
- Research mode: unsmoothed and smoothed series shown together.

EWMA:

```text
S_{g,t} = lambda_s * BSI_raw_{g,t} + (1 - lambda_s) * S_{g,t-1}
```

where `lambda_s` is typically `0.20-0.35` for daily data.

### 8.2 Persistence Logic

A stress band should not be escalated based on a single spike unless the anomaly is extreme and corroborated.

Recommended escalation conditions:

```text
Escalate if:
  BSI_smoothed >= band_threshold
  AND persistence_score >= theta_p
  AND cross_signal_agreement >= theta_c
  AND confidence >= theta_conf
```

Recommended de-escalation should be gradual:

```text
De-escalate if:
  BSI_smoothed < lower_band_threshold for n consecutive periods
```

This hysteresis prevents dashboard flicker.

### 8.3 Anti-Spike Protections

Use at least three of the following before public alerting:

- Robust z-scores rather than mean-standard-deviation z-scores.
- Winsorization of extreme normalized values.
- Minimum breadth requirement.
- Minimum persistence requirement.
- News-shock detection.
- Holiday and seasonality adjustment.
- Viral/trending-topic suppression.
- Confidence downgrade for isolated platform spikes.

---

## 9. Severity Bands

### 9.1 Recommended Bands

| BSI range | Label | Interpretation |
|---:|---|---|
| 0-20 | Normal | Behavior is close to local historical baseline. |
| 20-40 | Elevated monitoring | Some stress-related changes are visible but limited or uncertain. |
| 40-60 | Mild behavioral stress | Multiple signals show abnormal stress-related behavior. |
| 60-80 | Significant behavioral stress | Broad, persistent, and corroborated stress-related behavior. |
| 80-100 | Extreme behavioral stress | Highly abnormal, broad, persistent stress-related behavior; requires careful uncertainty review. |

### 9.2 Why Bands Exist

Bands help non-technical users understand score ranges without overinterpreting point estimates. They should be framed as communication aids, not hard scientific boundaries.

### 9.3 Threshold Calibration

Thresholds should be calibrated using:

- Historical percentiles within geography.
- Known stress episodes, annotated carefully without assuming causality.
- Stability testing across rolling windows.
- False-positive review by analysts.
- Cross-validation across geographies and time.
- User research on dashboard interpretability.

Example calibration rule:

```text
Normal:                  below local 60th percentile
Elevated monitoring:      local 60th-75th percentile
Mild behavioral stress:   local 75th-90th percentile
Significant stress:       local 90th-97.5th percentile
Extreme stress:           above local 97.5th percentile
```

The published 0-20, 20-40, 40-60, 60-80, and 80-100 bands can remain fixed for readability, while the transform from raw composite to BSI should be locally calibrated.

### 9.4 Geography-Specific Thresholds

Thresholds may vary by geography because:

- Baseline search behavior differs.
- Seasonality differs.
- Data volume differs.
- Local holidays differ.
- Platform adoption differs.
- Urban and rural behavioral traces differ.

Any geography-specific calibration must be documented to avoid misleading rankings.

---

## 10. Explainability Design

Each BSI score should include explanations at four levels.

### 10.1 Top Contributing Signals

Contribution of signal `i`:

```text
contribution_{i,g,t} = effective_weight_{i,g,t} * a_{i,g,t}
```

where:

```text
effective_weight_{i,g,t} = w_i * q_{i,g,t} * (1 - d_{i,g,t})
```

Report top contributors with direction and confidence:

```text
- Discount-seeking searches: elevated, persistent, high confidence.
- Debt relief terms: elevated, moderate confidence.
- Discretionary travel interest: declining, low confidence due to holiday adjustment.
```

### 10.2 Ontology Category Contribution

Category contribution:

```text
category_contribution_{c,g,t} = sum_{i in c} contribution_{i,g,t}
```

Display as a stacked bar or table:

| Category | Contribution | Direction | Reliability |
|---|---:|---|---|
| Debt anxiety | 24% | Up | Moderate |
| Discount seeking | 18% | Up | High |
| Discretionary travel | 12% | Down | Moderate |

### 10.3 Regional Breakdown

For parent geographies, show child-region contributions only when child data reliability is sufficient. Do not rank cities if confidence is low.

Parent aggregation:

```text
BSI_parent = sum_g population_or_signal_weight_g * BSI_g * Conf_g
             / sum_g population_or_signal_weight_g * Conf_g
```

Use population weighting only if the signal methodology supports it. Otherwise, label as signal-weighted or coverage-weighted.

### 10.4 Trend Explanation

Trend explanations should be template-based and uncertainty-aware:

```text
"BSI increased from 48 to 57 over the last 14 days. The increase was mainly associated with broader activation in debt-related searches and discount-seeking behavior. Confidence is moderate because two smaller regions have sparse data. This is not a recession forecast."
```

### 10.5 Drift Warnings

Examples:

- "Keyword meaning may have shifted due to viral media usage."
- "Google Trends normalization was unstable across repeated pulls."
- "City-level volume is sparse; interpret with caution."
- "One signal family dominates this movement; agreement is low."

---

## 11. False-Positive Suppression

### 11.1 Seasonality Handling

Use seasonal baselines that account for:

- Day of week.
- Week of year.
- Month.
- School calendar effects where relevant.
- Tax season and shopping seasons.
- Weather-sensitive behavior if applicable.

Seasonal robust z-score:

```text
z_{seasonal,i,g,t} = (x_{i,g,t} - median_same_season_{i,g,t})
                     / (1.4826 * MAD_same_season_{i,g,t} + epsilon)
```

### 11.2 Holidays

Holidays can distort travel, spending, search, and media behavior. Recommended strategies:

- Maintain country- and region-specific holiday calendars.
- Add pre-holiday and post-holiday windows.
- Compare against prior years' same holiday windows.
- Lower confidence when holiday adjustment is uncertain.

### 11.3 Viral Events and Platform Trends

Viral events can create spikes unrelated to stress. Detect with:

- Sudden single-keyword dominance.
- High social/news co-mentions unrelated to economic concern.
- Abrupt increase in unrelated query context.
- Sharp spike with no category breadth.
- High platform-specific concentration.

Suppression should reduce contribution from affected signals and add an explanation note.

### 11.4 Temporary Media Shocks and News-Driven Search Spikes

News can trigger search spikes without durable behavioral change. Methods:

- News-volume covariates.
- Media-shock flags.
- Same-day spike dampening until persistence is observed.
- Cross-signal confirmation requirements.
- Analyst annotation for major events.

### 11.5 Platform-Specific Artifacts

Examples:

- API outage.
- Sampling change.
- Bot activity.
- Interface redesign.
- Query taxonomy change.

Handling:

- Monitor pull-to-pull stability.
- Compare repeated API requests where possible.
- Downweight affected platforms.
- Increase uncertainty.
- Avoid emitting high-confidence claims.

---

## 12. Comparison Rules

### 12.1 Comparing Countries

Country A's BSI of 70 should not be interpreted as having the same raw search intensity as Country B's BSI of 70. The safer interpretation is:

> Each country is showing a similarly high level of abnormal stress-related behavior relative to its own historical baseline.

Rules:

- Compare normalized BSI, not raw Google Trends values.
- Display confidence intervals.
- Avoid ranking countries when confidence differs substantially.
- Group countries by data quality before comparison.
- Document language and platform coverage differences.

### 12.2 Comparing Regions Within a Country

Regions may be more comparable than countries but still require caution.

Rules:

- Use local baselines for each region.
- Consider population, signal volume, and platform adoption.
- Suppress or qualify sparse regions.
- Do not treat small-region spikes as equivalent to broad regional stress without breadth and persistence.

### 12.3 Comparing Cities

Cities are high risk for noise.

Rules:

- Require higher minimum confidence.
- Use metro-level aggregation where possible.
- Do not produce leaderboards for low-confidence cities.
- Show uncertainty prominently.
- Prefer "monitoring note" over numeric score for sparse cities.

### 12.4 Comparing Time Periods

Time comparisons are valid only when methodology and calibration are stable.

Rules:

- Keep a fixed calibration period for official series.
- Version the index methodology.
- Mark breaks when signal definitions, APIs, ontology, or weights change.
- Compare smoothed scores for trend narratives.
- Keep raw unsmoothed scores available for research diagnostics.

### 12.5 Why Relative Normalization Matters

Relative normalization allows the BSI to answer:

> "Is this geography behaving unusually compared with itself?"

It does not automatically answer:

> "Does this geography have more stress than another geography in absolute human terms?"

The second question requires additional data, validation, and careful demographic adjustment.

---

## 13. Alternative BSI Formulations

### 13.1 Simple Weighted Index

```text
BSI = 100 * weighted_mean([H, A, B, P, C, T])
```

Pros:

- Easy to explain.
- Easy to implement.
- Good MVP baseline.
- Transparent for journalists and policymakers.

Cons:

- Limited uncertainty modeling.
- May miss nonlinear interactions.
- Requires careful hand-tuned weights.

### 13.2 Percentile-Based Local Rarity Index

```text
BSI = 100 * empirical_CDF_g(R_{g,t})
```

Pros:

- Very interpretable as historical rarity.
- Naturally geography-relative.
- Useful for dashboards.

Cons:

- Can hide absolute differences in signal strength.
- Requires stable historical data.
- Recalibration can alter historical interpretation.

### 13.3 Bayesian Latent Stress Index

Assume latent behavioral stress `L_{g,t}`:

```text
L_{g,t} ~ Normal(L_{g,t-1}, sigma_L^2)
z_{i,g,t} ~ Normal(beta_i * L_{g,t}, sigma_i^2)
```

Then:

```text
BSI = 100 * P(L_{g,t} exceeds calibrated baseline quantile)
```

Pros:

- Strong uncertainty propagation.
- Naturally handles missing data.
- Supports hierarchical geographic pooling.

Cons:

- Harder to explain.
- Higher implementation complexity.
- Requires stronger modeling assumptions.

### 13.4 Machine-Learned Ensemble Index

Use supervised or semi-supervised learning against annotated stress periods.

Pros:

- Can capture nonlinear patterns.
- May improve empirical detection of known stress episodes.

Cons:

- Higher overfitting risk.
- Can encourage mistaken prediction framing.
- Harder to explain.
- Requires careful labels and bias audits.

### 13.5 HMM-Centric Index

Use regime posterior as the dominant score:

```text
BSI = 100 * H_{g,t}
```

Pros:

- Clean temporal regime interpretation.
- Strong smoothing and persistence behavior.

Cons:

- Too dependent on model specification.
- Less explainable at signal/category level.
- Risk of users interpreting regimes as economic states.

---

## 14. Recommended MVP Formulation

The MVP should be transparent, stable, and conservative.

### 14.1 MVP Inputs

- Robust local anomaly scores by signal.
- Ontology category mapping.
- Basic HMM posterior probabilities.
- Signal quality score.
- Geographic confidence score.
- Simple drift flags.

### 14.2 MVP Formula

```text
R_{g,t} = 0.25 H_{g,t}
        + 0.25 A_{g,t}
        + 0.15 B_{g,t}
        + 0.15 P_{g,t}
        + 0.15 C_{g,t}
        + 0.05 T_{g,t}
```

```text
BSI_{g,t} = round(100 * clamp(R_{g,t} * (1 - 0.15 D_{g,t}), 0, 1))
```

```text
Conf_{g,t} = Q_{g,t}^{0.35}
           * G_{g,t}^{0.25}
           * (1 - D_{g,t})^{0.20}
           * model_stability_{g,t}^{0.10}
           * coverage_balance_{g,t}^{0.10}
```

### 14.3 MVP Pseudo-Code

```python
for geography in geographies:
    for date in evaluation_dates:
        normalized_signals = []

        for signal in signals:
            baseline = rolling_local_baseline(signal, geography, date)
            z = robust_z_score(signal.value, baseline)
            z_stress = signal.direction * z
            anomaly = clamp((z_stress - 0.5) / 3.0, 0.0, 1.0)

            quality = compute_signal_quality(signal, geography, date)
            drift = compute_drift_risk(signal, geography, date)

            normalized_signals.append({
                "signal": signal,
                "anomaly": anomaly,
                "quality": quality,
                "drift": drift,
            })

        H = hmm_stress_posterior_component(geography, date)
        A = quality_weighted_anomaly_strength(normalized_signals)
        B = ontology_breadth(normalized_signals)
        P = persistence_score(geography, date)
        C = cross_signal_agreement(normalized_signals)
        T = trend_acceleration_score(geography, date)
        D = aggregate_drift_risk(normalized_signals)
        Q = aggregate_data_quality(normalized_signals)
        G = geographic_confidence(geography, date)

        raw = 0.25 * H + 0.25 * A + 0.15 * B + 0.15 * P + 0.15 * C + 0.05 * T
        adjusted = raw * (1 - 0.15 * D)
        score = round(100 * clamp(adjusted, 0.0, 1.0))

        confidence = (Q ** 0.35) * (G ** 0.25) * ((1 - D) ** 0.20) \
                     * (model_stability ** 0.10) * (coverage_balance ** 0.10)

        interval = estimate_uncertainty_interval(score, confidence, normalized_signals)
        explanations = compute_explanations(normalized_signals, H, A, B, P, C, T, D)

        emit_bsi_result(score, confidence, interval, explanations)
```

### 14.4 MVP Guardrails

- Do not label HMM regimes as recessions.
- Do not show city scores below minimum confidence.
- Require breadth and persistence before high-severity public alerts.
- Display uncertainty interval beside every score.
- Include "experimental behavioral stress monitoring indicator" label in UI and exports.

---

## 15. Recommended Production-Safe Formulation

A production-safe BSI should retain MVP transparency while improving robustness.

### 15.1 Production Enhancements

1. Hierarchical Bayesian uncertainty model for signals and geographies.
2. Fixed calibration periods with versioned transforms.
3. Seasonal and holiday-adjusted baselines.
4. Block-bootstrap uncertainty intervals.
5. Automated drift detection and analyst review workflow.
6. Cross-platform validation where available.
7. Event annotation layer for news, holidays, platform outages, and viral events.
8. Score versioning and reproducibility metadata.

### 15.2 Production Formula

```text
R_{g,t}^{prod} = monotone_ensemble(
    H_{g,t}, A_{g,t}, B_{g,t}, P_{g,t}, C_{g,t}, T_{g,t};
    constraints = positive_monotonicity
)
```

Then:

```text
BSI_{g,t}^{prod} = 100 * calibrated_monotone_transform_g(R_{g,t}^{prod})
```

Constraints:

- Higher anomaly should not lower BSI when all else is equal.
- Higher persistence should not lower BSI when all else is equal.
- Higher drift should not increase confidence.
- Lower data quality should not increase confidence.

The production model may be more sophisticated, but the dashboard should still expose component-level decomposition.

---

## 16. Calibration and Validation Ideas

Calibration should not convert the BSI into an economic prediction target. Suitable validation questions include:

- Did the BSI rise during historically known periods of broad public anxiety or hardship-related behavior?
- Did it avoid major false positives during holidays and viral media events?
- Are high scores broad and persistent rather than single-signal artifacts?
- Are uncertainty intervals wider for sparse geographies?
- Do analysts agree that top explanations match the underlying signal movements?

Potential calibration artifacts:

- Annotated stress periods.
- Holiday calendars.
- Major news-event calendars.
- Platform outage logs.
- Synthetic spike tests.
- Backtests across multiple countries and regions.

Avoid optimizing directly for recession dates, GDP changes, or unemployment releases unless clearly framed as a separate research analysis and not as the BSI's operational purpose.

---

## 17. Failure Modes and Risks

### 17.1 Unreliable Index Conditions

The BSI becomes unreliable when:

- Data quality is low across many signal families.
- Geographic confidence is low.
- One platform dominates the score.
- Drift warnings are widespread.
- Historical baseline is too short or structurally different.
- A major holiday, crisis, viral event, or media shock overwhelms normal behavior.
- Signal coverage changes abruptly.

### 17.2 Geographic Sparsity Risks

Sparse geographies may show exaggerated changes due to low baseline volume. The system should suppress or heavily qualify low-confidence city or small-region estimates.

### 17.3 Keyword Drift Risks

Keywords change meaning. A term associated with financial hardship can become a meme, brand, song title, political slogan, or news phrase. Drift monitoring and ontology review are required.

### 17.4 Platform Manipulation Risks

Digital traces can be manipulated by bots, coordinated campaigns, SEO behavior, or platform recommendation systems. Cross-signal agreement and platform diversity reduce but do not eliminate this risk.

### 17.5 Economic Interpretation Risks

Users may incorrectly interpret a high BSI as proof of recession, poverty, unemployment, or economic decline. Every output should include explicit caveats and avoid deterministic wording.

### 17.6 Overfitting Risks

Overly complex scoring systems may fit historical narratives but fail in future periods. Prefer interpretable constraints, out-of-sample validation, versioning, and conservative public labels.

### 17.7 Causal Interpretation Risks

The BSI is observational. It can indicate that stress-related aggregate behaviors changed, but it cannot prove why they changed without additional causal analysis.

---

## 18. Dashboard and Reporting Guidance

### 18.1 Required Labels

Every dashboard and export should include:

```text
Experimental Behavioral Stress Monitoring Indicator.
Not a recession prediction. Not a measure of individual psychological stress.
Scores are relative to each geography's historical baseline and include uncertainty.
```

### 18.2 Recommended Public Wording

Safe:

- "Behavioral stress signals are elevated relative to the region's baseline."
- "Multiple categories show persistent abnormal movement."
- "Confidence is moderate due to sparse local data."
- "This score is not a recession forecast."

Unsafe:

- "This region is entering a recession."
- "The BSI proves economic decline."
- "Residents are psychologically stressed."
- "City A is objectively more stressed than City B" without careful caveats.

---

## 19. Future Extension Ideas

1. Hierarchical pooling so sparse regions borrow strength from parent geographies while preserving local baselines.
2. Multilingual ontology expansion with region-specific terminology.
3. Human-in-the-loop analyst annotations for viral events and major news shocks.
4. Counterfactual seasonal adjustment models.
5. Robust ensemble methods with monotonic constraints.
6. Public methodology cards for each geography.
7. Versioned index releases with reproducibility manifests.
8. Sensitivity analysis showing how scores change under alternative weights.
9. Independent external audit of false positives and uncertainty coverage.
10. Separate research-only modules for comparing BSI with macroeconomic variables without changing the BSI's public purpose.

---

## 20. Implementation Readiness Checklist

Before implementation, confirm:

- [ ] Ontology categories and stress directions are documented.
- [ ] Signal-level quality metrics are defined.
- [ ] Local baseline windows are selected by data frequency.
- [ ] Holiday and seasonal adjustment strategy is available.
- [ ] HMM regime names avoid deterministic economic labels.
- [ ] Confidence and uncertainty outputs are mandatory.
- [ ] Low-volume geography suppression rules are defined.
- [ ] Drift warnings are exposed in outputs.
- [ ] Severity thresholds are calibrated and versioned.
- [ ] Dashboard copy labels the BSI as experimental and not predictive of recession.

---

## 21. Recommended Default Design

For initial implementation planning, use the **MVP weighted index**:

```text
BSI = round(100 * clamp((0.25H + 0.25A + 0.15B + 0.15P + 0.15C + 0.05T) * (1 - 0.15D), 0, 1))
```

Expose alongside:

```text
confidence = Q^0.35 * G^0.25 * (1 - D)^0.20 * model_stability^0.10 * coverage_balance^0.10
```

and a 90% uncertainty interval computed through bootstrap or variance approximation.

This design is recommended because it is:

- Mathematically explicit.
- Explainable to non-technical users.
- Conservative against single-signal spikes.
- Compatible with HMM regime inference.
- Adaptable to geographic normalization.
- Honest about uncertainty and failure modes.
- Clearly framed as an experimental behavioral stress monitoring indicator rather than an economic forecast.
