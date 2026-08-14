# D2C Fashion Customer Intelligence Project

## Project Summary

End-to-end customer analytics pipeline for a D2C fashion brand. Built from a single transaction dataset (`Dataset.csv`, 3,900 rows), this project produces customer segmentation, two competing loyalty definitions, SQL analysis, charts, and a promo sunset recommendation — all traceable to raw data.

---

## Quick Start (Reproduce Everything)

### Prerequisites
- Python 3.8+ with `pandas`, `numpy`, `matplotlib`
- Install: `pip install pandas numpy matplotlib`

### Run the full pipeline

```bash
# From the project root directory:
python src/data_cleaning.py
python src/feature_engineering.py
python src/segmentation.py
python src/sql_builder.py
python src/visualization.py
```

On Windows if `python` isn't in PATH, use the full path:
```powershell
$py = "C:\Users\praga\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$env:PYTHONIOENCODING = "utf-8"
& $py src/data_cleaning.py
& $py src/feature_engineering.py
& $py src/segmentation.py
& $py src/sql_builder.py
& $py src/visualization.py
```

**Total runtime: ~60 seconds**

---

## File Structure

```
Decoding customer value/
├── data/
│   ├── raw/
│   │   └── Dataset.csv                  ← Source of truth (do not modify)
│   └── processed/
│       ├── cleaned_data.csv             ← Phase 2 output (21 columns)
│       └── feature_table.csv            ← Phase 3 output (39 columns)
├── src/
│   ├── data_cleaning.py                 ← Phase 2: Clean + standardize
│   ├── feature_engineering.py           ← Phase 3: Build features
│   ├── segmentation.py                  ← Phase 4: Assign segments
│   ├── sql_builder.py                   ← Phase 5: SQLite DB + queries
│   └── visualization.py                 ← Phase 6: Charts + dashboard export
├── sql/
│   └── customer_segmentation.sql        ← 7 analytical SQL queries
├── outputs/
│   ├── customer_level_table.csv         ← Full feature + segment table
│   ├── segment_summary.csv              ← 5-row segment profile
│   ├── kpi_summary.csv                  ← Business KPIs by segment
│   ├── dashboard_data.csv               ← BI-ready wide table (30 cols)
│   ├── customer_intelligence.db         ← SQLite database
│   └── figures/
│       ├── 00_founder_dashboard.png     ← 4-panel executive dashboard
│       ├── 01_value_pyramid.png
│       ├── 02_promo_vs_loyalty.png
│       ├── 03_geo_opportunity.png
│       ├── 04_category_funnel.png
│       ├── 05_loyalty_comparison.png
│       ├── 06_segment_profiles.png
│       └── 07_age_analysis.png
├── report/
│   └── final_report.md                  ← Full business report
├── slides/
│   └── deck_outline.md                  ← 15-slide deck outline
└── README.md                            ← This file
```

---

## Dataset Overview

| Property | Value |
|---|---|
| Source | `Dataset.csv` (original, unmodified) |
| Rows | 3,900 |
| Columns | 18 |
| Missing values | `Review Rating`: 37 rows (0.9%) |
| Time series | None — cross-sectional snapshot |
| Margins/Costs | Not present |

### Column Reference

| Column | Type | Description |
|---|---|---|
| Customer ID | int | Unique per row |
| Age | int 18–70 | Customer age |
| Gender | string | Male / Female |
| Item Purchased | string | SKU name |
| Category | string | Clothing, Accessories, Footwear, Outerwear |
| Purchase Amount (USD) | int 20–100 | Transaction value |
| Location | string | US State |
| Size | string | S / M / L / XL |
| Color | string | Product colour |
| Season | string | Fall / Winter / Spring / Summer |
| Review Rating | float 2.5–5.0 | Post-purchase satisfaction |
| Subscription Status | Yes/No | Brand subscription |
| Shipping Type | string | 6 options |
| Discount Applied | Yes/No | Discount on this transaction |
| Promo Code Used | Yes/No | Promo code used |
| Previous Purchases | int 1–50 | Historical purchase count proxy |
| Payment Method | string | 7 options |
| Frequency of Purchases | string | Purchase cadence |

---

## Assumptions & Proxies

| Assumption | Rationale |
|---|---|
| `Review Rating` imputed with **median (3.80)** | Median is robust to the bimodal distribution; imputed rows flagged with `review_imputed=1` |
| `purchases_per_year` mapped from frequency string | Fortnightly=26, Bi-Weekly=26, Monthly=12, Quarterly=4, Every 3 Months=4, Annually=1, Weekly=52 |
| `spend_x_frequency` = purchase_amount × purchases_per_year | Proxy for annualised customer value; NOT true CLV (no cost data or timestamps) |
| `Previous Purchases` = lifetime repeat count proxy | Assumed to represent historical total purchases; no confirmation available |
| Discount rate assumption of 20% in scenario modeling | Industry norm for D2C fashion; clearly labeled as assumption |
| Structural data split (rows 1–1053 all Yes/Yes/Yes) | Treated as assembly artifact; documented but NOT used as a segment trigger |

---

## Methodology

### Phase 2 — Data Cleaning (`src/data_cleaning.py`)
- Column names standardized to snake_case
- Yes/No columns binary-encoded (1/0)
- Missing Review Rating imputed with median
- Frequency mapped to purchases-per-year
- Dataset structural split flagged

### Phase 3 — Feature Engineering (`src/feature_engineering.py`)
- 18 new features engineered from 21 cleaned columns (39 total)
- Two loyalty scores built (A=behavioral, B=commercial)
- Promo dependency scored (0, 0.5, 1.0)
- Satisfaction flags (≥4.0, ≥4.5, <3.0)
- Age bands (Teen, Young Adult, Mid-Age, Senior)

### Phase 4 — Segmentation (`src/segmentation.py`)
- Rule-based (not clustering) for full traceability
- 5 segments + General Buyers
- Priority-ordered assignment (S1 > S3 > S4 > S2 > S5 > S0)
- Segment business actions documented

### Phase 5 — SQL (`src/sql_builder.py`)
- SQLite database created from customer_level_table.csv
- 7 queries answering 5 business questions + 2 supplementary
- SQL file also written to `sql/customer_segmentation.sql`
- KPI summary exported as CSV

### Phase 6 — Visualization (`src/visualization.py`)
- 8 PNG charts generated (120 DPI, publication-quality)
- `dashboard_data.csv` exported (30 columns, BI-ready)
- Founder dashboard (4-panel) saved as `00_founder_dashboard.png`

---

## Key Findings

### Loyalty Definition Winner: Score B (Commercial)

Score A (behavioral) shows no spend differentiation across loyalty tiers ($0.57 range).  
Score B (commercial) shows a $29.46 gradient: Low=$45.81 → Medium=$57.74 → High=$75.27.  
**Use Score B for all commercial decisions.**

### Segments

| Segment | Count | Avg Spend | Discount % | Action |
|---|---|---|---|---|
| S1 High-Value Loyal | 549 | $90.89 | 0% | Protect; VIP treatment |
| S4 Promo-Habituated | 402 | $90.48 | 100% | Phased sunset plan |
| S0 General Buyers | 2,400 | $52.86 | 37% | Personalize; upsell |
| S2 Promo-Dependent | 395 | $39.05 | 100% | Gentle substitution |
| S5 Low-Value Occasional | 154 | $29.33 | 0% | Re-engage or deprioritize |

### Ideal Customer Profile
> A 40–55 year old buyer, purchasing Clothing or Accessories at full price 12–26 times per year, with 30+ previous purchases, no promo dependency, and a review rating ≥ 4.0.

---

## Dashboard (Power BI / Tableau)

Load `outputs/dashboard_data.csv` into Power BI or Tableau.

**Recommended 4 panels:**

| Panel | Chart Type | Measure | Filter |
|---|---|---|---|
| Customer Pyramid | Donut + bar | Count + avg spend by segment | All / by gender |
| Promo vs Revenue | Scatter | promo_rate vs avg_spend (bubble=count) | Segment |
| Geographic Map | Choropleth / bar | pct_organic, avg_spend | Min 20 customers |
| Category Funnel | Bar + line | avg_repeats + avg_spend | Category |

---

## Limitations

- No timestamps → no true CLV, no churn rate, no time trends
- No margin/cost data → no true profit calculation
- One transaction per customer → no direct repeat observation
- Dataset assembly artifact (subscription perfectly correlates with promo usage)
- Gender skew (68% Male) — female-specific insights are preliminary
- All monetary impact estimates are scenario-based assumptions

---

## Contact / Reproduction

All code is pure Python (no proprietary dependencies).  
To reproduce: install `pandas numpy matplotlib` and run the 5 scripts in order.  
SQLite database is pre-built at `outputs/customer_intelligence.db`.
