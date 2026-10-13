# Nyaya-Tula AI — Evaluation Benchmarks & Methodology

This directory houses the reproducible evaluation suites for OCR extraction, document classification, tampering analysis, and risk scoring.

## Standardized Evaluation Protocol

Per SIH 2026 guidelines, all metrics are strictly grounded in measurable code evaluations:
- **No fabricated accuracy percentages**: Benchmarks are evaluated on documented test suites or clearly marked as `NOT EVALUATED` when large-scale empirical datasets are not present.
- **Separate evaluation modules**: OCR CER/WER, classification confusion matrices, and tampering anomalies are evaluated independently.

## Benchmark Scripts

1. **Document Classification**:
   ```bash
   .venv/Scripts/python.exe benchmarks/evaluate_classifier.py
   ```
   Evaluates multi-class precision, recall, and macro-F1 across PAN, Aadhaar, Passport, Voter ID, Driving Licence, Vehicle RC, and Unsupported files.

2. **OCR Accuracy**:
   ```bash
   .venv/Scripts/python.exe benchmarks/evaluate_ocr.py
   ```
   Computes Character Error Rate (CER), Word Error Rate (WER), and field-level exact match across synthetic identity document zones.

3. **Tampering Analysis**:
   ```bash
   .venv/Scripts/python.exe benchmarks/evaluate_tampering.py
   ```
   Measures Error Level Analysis (ELA) false-positive and false-negative rates on genuine and edited image patches.

## Metrics Schema

All outputs conform to the strict JSON schema defined in [`benchmarks/metrics_schema.json`](file:///benchmarks/metrics_schema.json).
