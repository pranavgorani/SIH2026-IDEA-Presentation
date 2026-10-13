# Nyaya-Tula AI — Ethics & Human-in-the-Loop Principles

## 1. Human-in-the-Loop Mandate

- Nyaya-Tula AI is an **assistive forensic screening instrument**, not an autonomous border clearance authority.
- The system flags potential anomalies and computes explainable evidence; final adverse immigration or legal decisions require authorized human inspector confirmation.

## 2. Preventing False Accusations of Fraud

1. **Blurry Images vs. Counterfeiting**:
   - A blurry, poorly lit, or low-resolution image must trigger `NEEDS_RESCAN` or `NEEDS_REVIEW`, never `HIGH RISK` or `FRAUD`.
2. **Missing Optional Fields**:
   - Lack of optional fields (e.g. father's name on a newer format card) is not evidence of fraud.
3. **No Fabricated Risk Scores**:
   - When a document cannot be classified or recognized, the risk score is marked `N/A` (null), rather than populating an arbitrary score (e.g. 35.0).
