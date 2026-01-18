# Bayesian Probability Update Methodology for Project Likelihood

## Overview

This document defines a systematic, defensible approach for updating project probabilities as new evidence emerges during business development. The methodology uses Bayesian inference to incorporate observations (positive or negative signals) and their strength (Low, Medium, or High likelihood) into probability estimates.

## Purpose

In business development and innovation portfolio management, project probabilities are inherently uncertain and change as new information becomes available. This methodology provides:

1. **Objectivity**: A consistent framework for updating probabilities
2. **Transparency**: Clear reasoning for why probabilities changed
3. **Auditability**: Full history of updates and evidence
4. **Team Alignment**: Structured way to incorporate diverse perspectives

## Theoretical Foundation

### Bayes' Theorem

The core principle is Bayes' Theorem, which describes how to update beliefs given new evidence:

```
P(H|E) = [P(E|H) × P(H)] / P(E)
```

Where:
- P(H|E) = Posterior probability (updated belief after evidence)
- P(H) = Prior probability (current belief before evidence)
- P(E|H) = Likelihood (probability of observing evidence if hypothesis is true)
- P(E) = Marginal probability of evidence

### Odds Form (More Practical)

For sequential updates, the **odds form** is more intuitive:

```
Posterior Odds = Likelihood Ratio × Prior Odds
```

Where:
- **Odds** = P / (1 - P)
- **Likelihood Ratio** = P(E|Deal Happens) / P(E|Deal Doesn't Happen)

This form allows us to apply multiple updates sequentially and naturally handles both positive and negative evidence.

## Implementation for Startup/BD Context

### Stage-Based Prior Probabilities

Each project starts with a **prior probability** based on its stage:

| Stage | Default Probability | Rationale |
|-------|---------------------|-----------|
| **Signed** | 95% | Contract executed; only exceptional circumstances prevent |
| **Close to Signing** | 70% | Verbal commitment, scope defined, awaiting final approval |
| **Interested** | 40% | Mutual interest, scope being defined, budget uncertain |
| **Frontier** | 15% | Early conversations, concept stage, high uncertainty |

These priors are configurable by the organization based on historical conversion rates.

### Likelihood Ratios for Observations

When an observation is recorded, we apply a **likelihood ratio** based on its type and strength:

#### Positive Evidence Likelihood Ratios

| Likelihood Tag | Likelihood Ratio | Effect on Probability | Example |
|----------------|------------------|----------------------|---------|
| **High** | 2.0 | Strong increase | "Contract signed", "Budget approved" |
| **Medium** | 1.5 | Moderate increase | "Proposal accepted", "Key stakeholder committed" |
| **Low** | 1.2 | Slight increase | "Positive initial meeting", "Some interest expressed" |

#### Negative Evidence Likelihood Ratios

| Likelihood Tag | Likelihood Ratio | Effect on Probability | Example |
|----------------|------------------|----------------------|---------|
| **High** | 0.5 | Strong decrease | "Budget cut", "Key stakeholder left", "Competing solution chosen" |
| **Medium** | 0.67 | Moderate decrease | "Timeline slipped", "Budget concerns raised" |
| **Low** | 0.83 | Slight decrease | "Minor technical concern", "One stakeholder hesitant" |

### Rationale for Likelihood Ratios

These ratios are calibrated to be:

1. **Symmetric in log-space**: Positive High (2.0) and Negative High (0.5) are inverses, providing balanced updates
2. **Conservative**: Changes are meaningful but not extreme, preventing overreaction to single data points
3. **Multiplicative**: Sequential updates compound appropriately
4. **Bounded**: Impossible to reach exactly 0% or 100% (maintains uncertainty)

### Update Algorithm

When a new observation is added:

```
Step 1: Convert current probability to odds
  Odds_prior = P_current / (1 - P_current)

Step 2: Apply likelihood ratio
  Odds_posterior = Odds_prior × LikelihoodRatio

Step 3: Convert back to probability
  P_new = Odds_posterior / (1 + Odds_posterior)

Step 4: Apply bounds (1% minimum, 99% maximum)
  P_final = max(1, min(99, P_new))
```

### Worked Example

**Scenario**: "Close to Signing" project at 70% probability

**Observation Added**: "Budget concerns raised in Q4" (Negative, Medium)

```
Step 1: Convert to odds
  Odds_prior = 0.70 / (1 - 0.70) = 0.70 / 0.30 = 2.33

Step 2: Apply likelihood ratio (Negative Medium = 0.67)
  Odds_posterior = 2.33 × 0.67 = 1.56

Step 3: Convert to probability
  P_new = 1.56 / (1 + 1.56) = 1.56 / 2.56 = 0.61 = 61%

Step 4: Result
  Probability updated from 70% → 61%
```

**Second Observation**: "Verbal commitment received from sponsor" (Positive, High)

```
Step 1: Start from 61%
  Odds = 0.61 / 0.39 = 1.56

Step 2: Apply LR = 2.0
  Odds = 1.56 × 2.0 = 3.12

Step 3: Convert
  P = 3.12 / 4.12 = 0.76 = 76%

Step 4: Result
  Probability updated from 61% → 76%
```

### Calibration to Historical Data

Organizations should calibrate likelihood ratios to their own historical data:

1. **Track outcomes**: Record which projects closed vs. failed
2. **Analyze signals**: What observations correlated with success/failure?
3. **Adjust ratios**: If "budget approved" projects close 90% of the time vs. 50% base rate, the LR should be ~9.0
4. **Iterate**: Refine ratios quarterly based on new data

Example calibration calculation:

```
If "Budget Approved" observation:
- Appears in 80% of deals that close
- Appears in 20% of deals that don't close

Likelihood Ratio = 0.80 / 0.20 = 4.0
```

## Special Scenarios

### Conflicting Evidence

When observations point in different directions:

- **Bayesian approach naturally handles this**: Each observation updates sequentially
- **Net effect depends on strength**: Two Medium positives can offset one High negative
- **Transparency**: Full observation history shows the reasoning

### Stage Changes

When a project moves to a new stage:

**Option 1: Reset to stage default (Recommended for major transitions)**
```
Example: "Interested" → "Close to Signing"
- Reset to 70% (new stage default)
- Previous observations archived
- Rationale: Major milestone changes the context
```

**Option 2: Continue updating from current probability**
```
Example: "Interested" → "Close to Signing"
- Keep current probability (e.g., 55%)
- Continue applying observations
- Rationale: Preserves accumulated evidence
```

Recommendation: **Option 1** for stage progressions (Frontier → Interested → Close to Signing → Signed), **Option 2** for lateral changes (e.g., source changes).

### Manual Overrides

Users may manually adjust probability:

- **Flag the override**: Mark that it's not purely Bayesian
- **Require justification**: Capture why manual adjustment was needed
- **Resume Bayesian updates**: Future observations update from the manually-set value
- **Review regularly**: Check if systematic biases suggest recalibration needed

### Multiple Decision Makers

When different stakeholders provide observations:

1. **Independent observations**: Each person's observation updates the probability
2. **Tag with source**: Track who provided each observation
3. **Aggregate transparently**: All updates are visible in history
4. **Resolve conflicts**: If observations directly contradict, facilitate discussion

Example:
- Sales Lead adds: "Budget approved" (Positive, High) → 45% to 64%
- Technical Lead adds: "Major technical risks identified" (Negative, Medium) → 64% to 55%
- Net: Started at 45%, ended at 55% after incorporating both perspectives

## User Interface Guidelines

### Displaying Updates

When an observation is added, show:

```
┌─────────────────────────────────────────────────────────┐
│ Observation Added: "Budget approved"                    │
│ Type: Positive | Likelihood: High                       │
│                                                         │
│ Bayesian Update:                                        │
│ Previous: 45%                                           │
│ Likelihood Ratio: 2.0x                                  │
│ New Probability: 64%                                    │
│                                                         │
│ [Accept Update] [Adjust Manually]                       │
└─────────────────────────────────────────────────────────┘
```

### Probability History

Show a timeline of changes:

```
Project: Alpha Basin Analysis

Probability History:
─────────────────────────────────────────────────────────
Jan 5   | 40% | Created (Stage: Interested)
Jan 10  | 55% | ⬆ "Scope meeting very positive" (Positive, Medium)
Jan 12  | 45% | ⬇ "Competing vendor in play" (Negative, Medium)
Jan 15  | 64% | ⬆ "Budget approved" (Positive, High)
Jan 18  | 70% | ⬆ Stage changed to "Close to Signing"
─────────────────────────────────────────────────────────
```

### Bulk Observations

For projects with many observations, show:

- **Net effect**: "6 observations: 4 positive, 2 negative"
- **Summary**: "Starting: 40% → Ending: 67%"
- **Expandable detail**: Click to see each update step-by-step

## Best Practices

### When to Add Observations

✅ **DO add observations for:**
- Concrete events: "Contract signed", "Budget cut", "Key hire joined"
- Stakeholder actions: "Sponsor committed", "Decision maker left"
- External factors: "Market conditions improved", "Regulations changed"
- Milestone outcomes: "Pilot successful", "Proposal rejected"

❌ **DON'T add observations for:**
- Routine status updates: "Had weekly meeting"
- Vague feelings: "I have a good feeling about this"
- Duplicate information: Same signal reported twice
- Speculation: "I think they might be interested"

### Choosing Likelihood Levels

**High**: The observation is a strong, reliable signal with clear implications
- Example: "Contract executed" (Positive), "Client went bankrupt" (Negative)

**Medium**: The observation is meaningful but not definitive
- Example: "Proposal accepted" (Positive), "Timeline slipped" (Negative)

**Low**: The observation provides some signal but has limited predictive power
- Example: "Meeting went well" (Positive), "One stakeholder had questions" (Negative)

### Review Cadence

1. **Weekly**: Review projects with recent observations
2. **Monthly**: Calibrate probabilities across portfolio
3. **Quarterly**: Analyze closed deals to refine likelihood ratios
4. **Annually**: Update stage-based priors based on historical conversion rates

### Red Flags (When to Investigate)

- **Flat probability with many observations**: May indicate neutral/conflicting evidence or need to adjust LRs
- **Wild swings**: Probabilities changing >30% frequently may indicate overreaction
- **Stuck at extremes**: Probabilities consistently at 5% or 95% may indicate broken calibration
- **Observation fatigue**: No observations added for weeks may indicate process breakdown

## Mathematical Properties

### Why This Approach Works

1. **Proper probability**: Always produces valid probabilities (0-100%)
2. **Commutative**: Order of observations doesn't matter for final probability
3. **Coherent**: Satisfies probability axioms
4. **Reversible**: Positive and negative evidence with same strength are inversely related
5. **Conservative**: Bounded away from 0% and 100% to maintain uncertainty

### Limitations

1. **Independence assumption**: Assumes observations are conditionally independent
   - In practice: Observations may be correlated
   - Mitigation: Group related observations or adjust LRs for correlated events

2. **Linear pooling**: Sequential updates assume simple multiplicative effects
   - In practice: Some observations may be redundant
   - Mitigation: Avoid recording duplicate information

3. **Static likelihood ratios**: LRs don't adapt based on context
   - In practice: A "budget approved" signal may mean different things in different contexts
   - Mitigation: Periodic recalibration, context-specific observation types

4. **No confidence intervals**: Single point estimate, not a distribution
   - In practice: 70% could mean high confidence or high uncertainty
   - Mitigation: Track number and diversity of observations as proxy for confidence

## Advanced Topics

### Sensitivity Analysis

Test how sensitive forecasts are to probability assumptions:

```
Scenario: Change all "Interested" projects by ±10%
- Expected Case changes from 234 person-weeks to [210-258]
- Sensitivity: Moderate
- Action: Focus on clarifying these projects' true likelihood
```

### Ensemble Forecasting

Generate multiple scenarios with different probability assumptions:

- **Optimistic**: Apply +20% to all unscheduled projects
- **Pessimistic**: Apply -20% to all non-Signed projects
- **Realistic**: Use current Bayesian probabilities

Compare resource needs across scenarios.

### Confidence Scoring

Augment probabilities with confidence based on:

```
Confidence = f(
  number_of_observations,
  diversity_of_observation_types,
  recency_of_observations,
  stage_duration
)
```

Example:
- Project at 70% with 1 observation: Low confidence
- Project at 70% with 8 diverse observations over 3 months: High confidence

## Appendix: Lookup Tables

### Quick Reference: Probability Changes

Starting from **40%** (Interested stage):

| Observation | Likelihood | New Probability | Change |
|-------------|-----------|-----------------|--------|
| Positive | High | 57% | +17% |
| Positive | Medium | 50% | +10% |
| Positive | Low | 44% | +4% |
| Negative | High | 25% | -15% |
| Negative | Medium | 32% | -8% |
| Negative | Low | 36% | -4% |

Starting from **70%** (Close to Signing stage):

| Observation | Likelihood | New Probability | Change |
|-------------|-----------|-----------------|--------|
| Positive | High | 82% | +12% |
| Positive | Medium | 78% | +8% |
| Positive | Low | 73% | +3% |
| Negative | High | 54% | -16% |
| Negative | Medium | 61% | -9% |
| Negative | Low | 66% | -4% |

### Likelihood Ratio Quick Reference

| Type | Likelihood | Ratio | Interpretation |
|------|-----------|-------|----------------|
| Positive | High | 2.0 | Doubles the odds |
| Positive | Medium | 1.5 | Increases odds by 50% |
| Positive | Low | 1.2 | Increases odds by 20% |
| Negative | High | 0.5 | Halves the odds |
| Negative | Medium | 0.67 | Reduces odds by 1/3 |
| Negative | Low | 0.83 | Reduces odds by 1/6 |

---

## References & Further Reading

1. **Frequentist vs Bayesian**: While frequentist approaches focus on long-run frequencies, Bayesian approaches update beliefs based on evidence—more appropriate for unique BD opportunities.

2. **Calibration Research**: Studies show that humans are typically overconfident (assign 80% to events that occur ~60%). Bayesian frameworks can help combat this bias.

3. **Forecasting Best Practices**: Superforecasters (top 1% of predictors) update beliefs incrementally and weight evidence appropriately—this methodology codifies that approach.

4. **Business Applications**: Similar Bayesian approaches are used in credit scoring, insurance underwriting, and venture capital deal screening.

---

**Version**: 1.0
**Last Updated**: January 18, 2026
**Author**: Project Scheduling Toolkit Team
**Status**: Approved for Implementation
