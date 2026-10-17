# Listing Freshness & Persistence Report: Úřad práce ČR (Czech Labour Office) (`uradprace-cz`)

* **Source Slug:** `uradprace-cz`
* **Upstream Endpoint:** [https://data.mpsv.cz/od/soubory/volna-mista/volna-mista.json](https://data.mpsv.cz/od/soubory/volna-mista/volna-mista.json)
* **Monitoring Cadence:** Daily bulk open data
* **Last Checked:** 2026-10-17 (Initial Setup)
* **Status:** 🟢 Baseline Initialized

## 1. Summary Metrics

| Metric | Measured Value | Methodology |
| :--- | :--- | :--- |
| **Total Tracked Listings** | 0 | Cumulative state tracking |
| **Currently Active** | 0 | Present in latest snapshot / active stream |
| **Withdrawn / Closed** | 0 | Observed departures from register |
| **Median Listing Lifetime** | N/A (initial state) | Kaplan-Meier 50% survival threshold |
| **30-Day Survival Probability** | N/A (insufficient sample) | Kaplan-Meier $S(30)$ accounting for right-censoring |
| **60-Day Survival Probability** | N/A (insufficient sample) | Kaplan-Meier $S(60)$ accounting for right-censoring |
| **90-Day Survival Probability** | N/A (insufficient sample) | Kaplan-Meier $S(90)$ accounting for right-censoring |
| **Staleness Ratio** | 0.00% (0 listings) | Active vacancies past stated expiration date |
| **Schema Contract Integrity** | ✅ PASS | Structural validation of upstream response schema |

## Upstream Schema Integrity

No structural schema drift detected. Upstream payload conforms to expected contract.

## 2. Statistical Methodology

* **Right-Censored Survival Analysis:** Listings that remain active at observation time have not completed their full lifecycle. Naive ratio calculations bias survival downwards; this report applies the non-parametric **Kaplan-Meier estimator** ($S(t) = \prod_{t_i \le t} (1 - d_i/n_i)$) treating active vacancies as right-censored at current observation date.
* **Discrete Day Resolution:** Upstream timestamps operate on discrete calendar days (`YYYY-MM-DD`). Lifetimes are bounded to non-negative integer days.
* **State Retention & Pruning:** Active listings are tracked continuously. Closed/withdrawn listings are maintained in compact state for 180 days to compute multi-month persistence curves, after which historical records are pruned to maintain lightweight git repository storage.
* **Raw Logs:** Ephemeral run logs are stored as 90-day GitHub Actions artifacts rather than polluting git history.
