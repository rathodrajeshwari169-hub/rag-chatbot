# D2C Fashion Customer Intelligence — Final Report

**Project:** Decoding Customer Value | **Dataset:** Dataset.csv (3,900 transactions)  
**Date:** May 2026 | **Status:** Complete

---

## Executive Summary

This report delivers a full customer intelligence analysis of a D2C fashion brand's transaction dataset. Using 3,900 purchase records across 18 attributes, we built two competing loyalty definitions, segmented customers into five actionable groups, identified geographic and category opportunities, and designed a promotional sunset plan with traceable business logic.

**Top 5 findings:**

| # | Finding |
|---|---|
| 1 | **14.1% of customers are High-Value Loyal (S1)** — they spend $90.89 avg with zero discount dependency and drive ~$49,900 in revenue proxy |
| 2 | **Loyalty Score B (Commercial) is the superior definition** — it shows a $30 spend gradient across tiers vs Score A's flat $0.57 gap |
| 3 | **Promo-Habituated Spenders (S4) represent the biggest opportunity** — $90.48 avg spend + 100% promo use; these buyers can be weaned off discounts |
| 4 | **Outerwear shows the strongest retention signal** — highest avg repeats (28.4), strong loyalty, indicating it is the brand's retention anchor |
| 5 | **The ideal customer** is a 44-year-old, mid-age or senior, primarily male, buying in Clothing/Accessories, paying digitally, with 30+ previous purchases and no promo dependency |

---

## 1. Dataset Audit

### 1.1 Structure

| Property | Value |
|---|---|
| Rows | 3,900 |
| Columns | 18 |
| Missing values | Review Rating: 37 rows (0.9%) |
| Duplicates | 0 |
| Time series | None — cross-sectional snapshot only |
| Margin/cost data | None — profit estimates are scenario-based |

### 1.2 Data Dictionary

| Column | Type | Business Meaning |
|---|---|---|
| Customer ID | int | Unique identifier per transaction |
| Age | int (18–70) | Customer age at time of record |
| Gender | string | Male / Female |
| Item Purchased | string | Specific SKU purchased |
| Category | string | Clothing, Accessories, Footwear, Outerwear |
| Purchase Amount (USD) | int (20–100) | Transaction value in USD |
| Location | string | US state |
| Size | string | S / M / L / XL |
| Color | string | Product color |
| Season | string | Season of purchase |
| Review Rating | float (2.5–5.0) | Customer satisfaction (post-purchase) |
| Subscription Status | Yes/No | Whether customer has a subscription |
| Shipping Type | string | Standard, Express, Next Day Air, etc. |
| Discount Applied | Yes/No | Whether a discount was applied |
| Promo Code Used | Yes/No | Whether a promo code was used |
| Previous Purchases | int (1–50) | Proxy for historical repeat behavior |
| Payment Method | string | Credit Card, Venmo, PayPal, etc. |
| Frequency of Purchases | string | Self-reported purchase frequency |

### 1.3 Key Data Quality Notes

- **Review Rating imputed** (37 rows, 0.9%) → median value 3.80 used. Rows flagged with `review_imputed=1`.
- **Structural split observed**: All rows with Subscription=Yes also have Discount=Yes and Promo=Yes (1,053 rows). All Subscription=No rows have Discount=No and Promo=No (2,847 rows). This appears to be an assembly artifact from two source files. This split was documented, not treated as an organic signal.
- **No timestamps**: Cannot compute true CLV, churn rate, or trend metrics. `spend_x_frequency` used as an annualised value proxy.
- **Single transaction per customer**: All repeat behavior measured through `Previous Purchases` proxy.

---

## 2. Engineered Features

### 2.1 Value Features

| Feature | Formula | Business Purpose |
|---|---|---|
| `purchase_amount` | Raw transaction value | Direct spend signal |
| `spend_x_frequency` | `purchase_amount × purchases_per_year` | Annualised value proxy |
| `high_value_flag` | `purchase_amount ≥ Q75 ($81)` | Top-quartile spender |
| `purchases_per_year` | Mapped from frequency string | Purchase cadence |

### 2.2 Loyalty Features

| Feature | Formula | Notes |
|---|---|---|
| `loyalty_score_A` | 0.30×norm(prev) + 0.25×sub + 0.25×norm(freq) + 0.20×norm(rating) | Behavioral definition |
| `loyalty_score_B` | 0.35×norm(spend) + 0.25×norm(prev) + 0.25×(1−promo) + 0.15×norm(rating) | Commercial definition |
| `loyalty_tier_A/B` | Low/Medium/High by tercile | Segmentation-ready |

### 2.3 Promo Features

| Feature | Formula | Notes |
|---|---|---|
| `promo_dependency_score` | `(discount_applied + promo_code_used) / 2` | 0=none, 0.5=one, 1.0=both |
| `promo_flag` | `promo_dependency_score > 0` | Binary indicator |

### 2.4 Satisfaction Features

| Feature | Rule | Notes |
|---|---|---|
| `satisfaction_flag` | `review_rating ≥ 4.0` | Satisfied customer proxy |
| `high_satisfaction` | `review_rating ≥ 4.5` | Highly satisfied |
| `low_satisfaction` | `review_rating < 3.0` | At-risk signal |

---

## 3. Loyalty Definition Analysis

### 3.1 Definition A — Behavioral Loyalty

**Formula:** `0.30×prev_purchases + 0.25×subscription + 0.25×frequency + 0.20×rating`

- Captures *engagement behavior*: how often someone buys and whether they've committed to a subscription
- Avg spend by tier: Low=$59.99 | Medium=$59.42 | High=$59.88
- **Problem**: Virtually no spend differentiation across tiers ($0.57 range)
- Reason: In this dataset, subscription_status and discount_applied are perfectly correlated, meaning high-behavioral-loyalty customers are also heavy discount users — which suppresses commercial differentiation

### 3.2 Definition B — Commercial Loyalty

**Formula:** `0.35×spend + 0.25×prev_purchases + 0.25×(1−promo_dependency) + 0.15×rating`

- Captures *commercial value*: how much someone spends, how often they repeat, and whether they do so organically
- Avg spend by tier: Low=$45.81 | Medium=$57.74 | High=$75.27
- **Strong gradient**: $29.46 spread across tiers
- Correlation with Score A: r = −0.016 (near-zero — they measure fundamentally different things)

### 3.3 Winner: Definition B (Commercial Loyalty)

| Criterion | Score A | Score B | Winner |
|---|---|---|---|
| Internal consistency | Medium | High | **B** |
| Spend gradient | $0.57 | $29.46 | **B** |
| Interpretability | Medium | High | **B** |
| Business usefulness | Low | High | **B** |
| Segment stability | Medium | High | **B** |

**Verdict**: Score B is the recommended loyalty definition. It directly maps to revenue and can guide acquisition targeting, retention investment, and promotional strategy. Score A is useful for engagement tracking but should not drive commercial decisions.

---

## 4. Customer Segmentation

### 4.1 Segment Rules and Sizes

| Code | Label | Rule | Count | % |
|---|---|---|---|---|
| S1 | High-Value Loyal | `high_value_flag=1 AND loyalty_tier_B=High AND promo_flag=0` | 549 | 14.1% |
| S4 | Promo-Habituated Spenders | `promo_flag=1 AND high_value_flag=1` | 402 | 10.3% |
| S2 | Promo-Dependent Buyers | `promo_flag=1 AND spend < median AND repeats < median` | 395 | 10.1% |
| S5 | Low-Value Occasional | `low_value_flag=1 AND low_repeat_flag=1` | 154 | 3.9% |
| S0 | General Buyers | All remaining | 2,400 | 61.5% |

*Note: S3 (Emerging Loyalists) returned 0 members — because in this dataset, all subscription=1 rows also have promo_flag=1, making the S3 rule (sub=1 AND promo=0) impossible to satisfy. This confirms the dataset assembly artifact.*

### 4.2 Segment Profiles

| Segment | Avg Spend | Avg Repeats | Discount % | Loyalty B | Avg Rating | Annual Value Proxy |
|---|---|---|---|---|---|---|
| S1 High-Value Loyal | $90.89 | 26.1 | 0% | 0.768 | 3.83 | $1,533 |
| S4 Promo-Habituated | $90.48 | 26.4 | 100% | 0.514 | 3.76 | $1,535 |
| S0 General Buyers | $52.86 | 28.3 | 36.7% | 0.515 | 3.73 | $945 |
| S2 Promo-Dependent | $39.05 | 12.7 | 100% | 0.218 | 3.75 | $637 |
| S5 Low-Value Occasional | $29.33 | 7.2 | 0% | 0.401 | 3.81 | $473 |

### 4.3 Business Actions by Segment

**S1 — High-Value Loyal**: No discount needed. Reward with exclusive early access, free premium shipping, VIP status. Upsell to higher-margin Outerwear and Accessories. These are the brand's most valuable customers — protect them at all costs.

**S4 — Promo-Habituated Spenders**: The highest commercial opportunity. Spend matches S1 but 100% promo-dependent. Initiate a phased sunset plan (see Section 6). Focus on product storytelling and brand-value messaging to reduce discount reliance.

**S0 — General Buyers**: The largest segment (61.5%). Target with personalization to move members into S1 or S3 over time. Test subscription offers. Moderate discount use (36.7%) — partially manageable.

**S2 — Promo-Dependent Buyers**: Low spend, low repeats, 100% promo-driven. High risk: removing discounts may cause churn. Do not sunset immediately — test gently with loyalty reward substitution.

**S5 — Low-Value Occasional**: Evaluate acquisition cost. If CAC is high relative to $473 annual value proxy, reduce spend on this segment. Test re-engagement with content-first approach.

---

## 5. Business Questions — Answered

### Q1: Who are the most valuable customers?

**High-Value Loyal (S1)** — 549 customers, avg spend $90.89, zero discount dependency, loyalty score 0.768.

**Profile**: Senior (50–70) or Mid-Age (35–49) customers, primarily Male, purchasing Clothing or Accessories in any season, using digital payment methods, with 25+ previous purchases and no promo reliance.

### Q2: Who buys only because of promotions?

**Promo-Dependent Buyers (S2)** — 395 customers, 100% discount rate, avg spend $39.05, avg 12.7 previous purchases.

**Profile**: Cross-age, sub-median spend, low repeat history. These customers are price-sensitive new or occasional buyers attracted by discounts. Removing discounts abruptly risks losing them entirely.

### Q3: Which geographies are underlevered organic demand pockets?

From the geographic analysis, states with the highest organic (no-promo) demand rate include those in the midwest and northeastern US. States with high organic_avg_spend AND high loyalty_score_B represent natural targets for upsell campaigns without promotional spend.

**Key insight**: States with pct_organic > 70% and avg_spend > $60 represent the most valuable geographic pockets for organic growth investment.

### Q4: Which categories and seasons are entry-point vs retention?

| Category | Avg Repeats | Role | Action |
|---|---|---|---|
| Outerwear | 28.4 | Retention | Protect with loyalty programs |
| Accessories | 27.3 | Retention/Transition | Cross-sell into Clothing |
| Clothing | 25.0 | Transition | Drive repeat; entry + retention |
| Footwear | 24.0 | Entry-Point/Transition | Use as acquisition hook |

*Note: SQL Query Q4 was expanded to analyze the cross-section of Season and Category to uncover further retention patterns, identifying that Outerwear in Fall/Winter yields the highest historical repeat count.*

**Outerwear is the retention anchor** — customers who buy Outerwear have the highest repeat history. It should be positioned as a loyalty category, not a discount driver.

### Q5: What does the ideal customer profile look like?

*(Full profile in Section 7)*

### Q6: How should promotions change?

*(Full plan in Section 6)*

---

## 6. Promotional Sunset Plan

### 6.1 Target Segment: S4 — Promo-Habituated Spenders

**Why S4?** These 402 customers match S1 on spend ($90.48) and repeat behavior (26.4 prev purchases), but use discounts on every transaction. Converting even 50% to organic buyers would protect ~$18,200 in revenue while eliminating discount cost.

### 6.2 Trigger Behavior Definition

A customer qualifies for the sunset program if ALL of the following are true:
- `purchase_amount ≥ $81` (Q75 threshold — confirmed high spender)
- `promo_flag = 1` (currently discount-dependent)
- `review_rating ≥ 4.0` (satisfied — unlikely to churn on principle)
- `previous_purchases ≥ 20` (established history — not a one-time buyer)

### 6.3 Phased Rollout

| Phase | Duration | Action | Monitoring KPI |
|---|---|---|---|
| Phase 0: Baseline | 4 weeks | No change; collect current purchase rate | Baseline purchase frequency |
| Phase 1: Pilot | 8 weeks | Remove discount for 10% of qualifying S4 (40 customers) | Purchase rate, revenue, satisfaction |
| Phase 2: Expand | 8 weeks | If churn rate < 15%, expand to 40% | Same as Phase 1 |
| Phase 3: Full Rollout | 12 weeks | Apply to remaining 50%; introduce loyalty points substitution | Revenue retention rate |

### 6.4 Substitution Strategy

Replace discounts with:
- **Early access** to new season collections
- **Free premium shipping** upgrades (Express/Next Day Air)
- **Loyalty points** redeemable for future purchases (not immediate discounts)

### 6.5 Scenario Impact Model

*Assumption: discount = avg 20% of purchase amount ($18.10 per transaction). Proxy only.*

| Scenario | Assumptions | Revenue Impact | Margin Impact |
|---|---|---|---|
| Low (pessimistic) | 50% of S4 churns post-sunset | −$18,200 revenue | Marginal gain from discount removal offset by revenue loss |
| Base | 20% churn, 80% retain organically | +$7,280 margin improvement | Net positive |
| High (optimistic) | 5% churn, 95% retain | +$13,700 margin improvement | Significant positive |

> ⚠️ **Limitation**: These estimates assume a 20% average discount rate derived from industry norms. The dataset contains no margin or cost data. Actual impact requires finance team input.

### 6.6 Success Metrics

- **Primary**: % of S4 customers purchasing within 90 days without discount (target: ≥ 80%)
- **Secondary**: Revenue per customer from ex-S4 group (target: ≥ $80/transaction)
- **Guard**: Overall customer satisfaction score (no decline acceptable)
- **Exit criterion**: If churn rate exceeds 25% in Phase 1, halt and revert

### 6.7 Downside Risks

1. **Churn spike**: S4 customers may be truly price-elastic, not brand-loyal
2. **Competitive substitution**: If competitors continue discounting, customers may switch
3. **Satisfaction drop**: Abrupt discount removal without substitution can damage brand perception

---

## 7. Ideal Customer Profile

*Based on Q5 SQL query: loyalty_tier_B = High, no promo, satisfied (≥4.0 rating), 25+ repeats*

| Attribute | Value |
|---|---|
| **Age** | ~44 years old (mid-age skew) |
| **Gender** | Primarily Male (dataset gender skew noted) |
| **Age Band** | Mid-Age (35–49) or Senior (50–70) |
| **Top Category** | Clothing (highest volume), Accessories (highest loyalty) |
| **Top Season** | Balanced across seasons |
| **Payment Method** | Credit Card / Digital (Venmo, PayPal) |
| **Shipping Preference** | Standard or Express |
| **Purchase Amount** | $75–$100 per transaction |
| **Previous Purchases** | 30+ (high repeat history) |
| **Purchase Frequency** | Monthly to Fortnightly (12–26x/year) |
| **Review Rating** | ≥ 4.0 (satisfied) |
| **Promo Dependency** | None (0) |
| **Loyalty Score B** | ≥ 0.75 |

**One-sentence ideal customer description for marketing:**  
*"A 40–55 year old regular buyer who purchases Clothing or Accessories at full price 12–26 times per year, rates the brand highly, and has 30+ previous transactions — no discount needed."*

---

## 8. Limitations

| Limitation | Impact | Mitigation Used |
|---|---|---|
| No timestamps | Cannot compute true CLV, churn rate, or trend | `spend_x_frequency` proxy; clearly labeled |
| No margin/cost data | Cannot compute true profit impact | Scenario modeling with stated assumptions |
| Single transaction per customer | No true repeat observation | `Previous Purchases` used as proxy |
| Dataset assembly artifact (Yes/Yes/Yes vs No/No/No split) | Subscription & promo perfectly correlated | Documented; S3 segment excluded |
| No causality | Cannot prove discounts cause repeat | Association language used throughout |
| Gender imbalance (68% Male) | Ideal profile skews male | Noted; female analysis conducted separately |
| Review Rating ~1% missing | Minor imputation risk | Median imputation; flagged |

---

## 9. Recommendations Summary

1. **Adopt Loyalty Score B** as the primary customer value metric across all dashboards and targeting decisions
2. **Protect S1** (549 customers, $49.9K revenue proxy) — zero discounts, maximum service investment
3. **Initiate S4 sunset plan** starting with a 10% pilot cohort; replace discounts with shipping upgrades and early access
4. **Do not abruptly cut discounts to S2** — risk of total churn; test loyalty reward substitution first
5. **Invest in Outerwear retention marketing** — it is the highest-repeat category and the brand's loyalty anchor
6. **Geographic targeting**: Identify and prioritise states with pct_organic > 70% for organic growth campaigns
7. **Collect timestamps and cost data** — current dataset limits the depth of actionable insight significantly
