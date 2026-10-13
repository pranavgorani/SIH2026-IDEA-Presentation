# Nyaya-Tula AI — Model Cards

## 1. Document Classifier (Heuristic & Layout Engine)
- **Model Type**: Multi-tier regex, layout structure, and optical keyword analyzer.
- **Inputs**: Extracted OCR text string, image dimensions, MRZ existence flag.
- **Outputs**: Document type (`PAN`, `AADHAAR`, `PASSPORT`, `VOTER_ID`, `DRIVING_LICENCE`, `VEHICLE_RC`, `VISA`, `UNSUPPORTED`), confidence score [0.0 - 1.0].
- **Limitations**: Requires at least 15 legible characters or an MRZ structure. Returns `NEEDS_RESCAN` on blurred or low-contrast inputs.

## 2. Optical Character Recognition (RapidOCR / PP-OCRv4)
- **Model Type**: ONNX-based lightweight detection and recognition model.
- **Execution Target**: Local CPU / Local CUDA.
- **Inputs**: Preprocessed document images (deskewed, contrast-normalized, multi-orientation).
- **Outputs**: Text bounding boxes, recognized strings, per-token confidence.

## 3. Forensic Tampering Detection (OpenCV & ELA)
- **Model Type**: Error Level Analysis (ELA) compression differential and Laplacian edge gradient analyzer.
- **Outputs**: Compression anomaly score, boundary splice indicators.
- **Limitations**: ELA scores indicate localized compression discontinuities; they are evidentiary indicators, not proof of forgery.
