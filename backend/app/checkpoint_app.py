"""
AI Border Security & Checkpoint Screening System (AG-IDFSE)
Standalone zero-cost checkpoint screening application.
Supports running via:
1. Streamlit: `streamlit run backend/app/checkpoint_app.py`
2. CLI / Script: `python -m backend.app.checkpoint_app [options]`
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
_current = Path(__file__).resolve()
_backend_dir = _current.parent.parent
_project_dir = _backend_dir.parent
for p in [str(_project_dir), str(_backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.services.ag_idfse import ag_idfse_engine


def run_cli_scan(doc_path: str, live_path: str = None, mrz: str = None, hint: str = None):
    print("\n" + "=" * 70)
    print(" AI BORDER SECURITY & DOCUMENT FORENSIC SCREENING ENGINE (AG-IDFSE)")
    print("=" * 70)

    mrz_lines = [l.strip() for l in mrz.splitlines() if l.strip()] if mrz else None

    result = ag_idfse_engine.screen_document(
        image_input=doc_path if doc_path else None,
        live_person_input=live_path if live_path else None,
        mrz_override=mrz_lines,
        document_type_hint=hint
    )

    print(json.dumps(result, indent=2))
    return result


def run_streamlit_app():
    try:
        import streamlit as st
    except ImportError:
        print("Streamlit is not installed in the environment. Install with 'pip install streamlit' to run the GUI.")
        return

    st.set_page_config(
        page_title="AI Border Security & Checkpoint Screening",
        page_icon="🛡️",
        layout="wide"
    )

    st.title("🛡️ AI Border Security & Document Screening Engine")
    st.caption("Zero-Cost Real-Time Checkpoint Screening & Forensic Tampering Detection")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. Credential Ingestion")
        doc_file = st.file_uploader("Upload Identity / Travel Document (Passport, Visa, ID, DL)", type=["jpg", "jpeg", "png", "webp"])
        doc_hint = st.selectbox("Document Taxonomy Hint", ["AUTO_DETECT", "PASSPORT", "VISA", "NATIONAL_ID", "DRIVING_LICENSE"])

    with col2:
        st.subheader("2. Checkpoint Biometric Presenter")
        live_file = st.file_uploader("Live Webcam Presenter Portrait (Optional)", type=["jpg", "jpeg", "png"])
        raw_mrz = st.text_area("Manual MRZ Override (Optional)", placeholder="P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10")

    if st.button("🚀 Execute Forensic Inspection & Screen Credential", type="primary"):
        doc_bytes = doc_file.read() if doc_file else None
        live_bytes = live_file.read() if live_file else None
        mrz_lines = [l.strip() for l in raw_mrz.splitlines() if l.strip()] if raw_mrz else None
        hint = None if doc_hint == "AUTO_DETECT" else doc_hint

        with st.spinner("Executing 4-Module Forensic Inspection Pipeline..."):
            result = ag_idfse_engine.screen_document(
                image_input=doc_bytes,
                live_person_input=live_bytes,
                mrz_override=mrz_lines,
                document_type_hint=hint
            )

        if result.get("status") == "REJECTED_UNSUPPORTED_DOCUMENT":
            st.error("🚨 STATUS: REJECTED_UNSUPPORTED_DOCUMENT — Credential rejected as non-identity/unauthorized document.")
            return

        dec = result.get("final_decision", {})
        status = dec.get("status", "CLEARED")
        score = dec.get("risk_score", 0)

        st.divider()

        # Decision Banner
        if status == "CLEARED":
            st.success(f"🟢 **STATUS: CLEARED** — Threat Score: **{score}/100** (Low Risk)")
        elif status == "SECONDARY_REVIEW":
            st.warning(f"🟡 **STATUS: SECONDARY_REVIEW** — Threat Score: **{score}/100** (Secondary Inspection Mandated)")
        else:
            st.error(f"🔴 **STATUS: DENIED_FRAUD** — Threat Score: **{score}/100** (Severe Forensic / Biometric Threat)")

        # 4 Architectural Modules Display
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown("### 📄 Module 1: Classification & VIZ")
            cls = result.get("document_classification", {})
            st.write(f"**Type:** `{cls.get('type')}`")
            st.write(f"**Standard:** `{cls.get('standard')}`")
            st.write(f"**Confidence:** `{cls.get('confidence', 0):.2f}`")
            ident = result.get("extracted_identity", {})
            st.write(f"**Holder:** {ident.get('surname', '')}, {ident.get('given_names', '')}")
            st.write(f"**Doc #:** `{ident.get('document_number', '')}`")
            st.write(f"**DOB:** `{ident.get('date_of_birth', '')}`")
            st.write(f"**Expiry:** `{ident.get('expiry_date', '')}`")

        with m2:
            st.markdown("### 🧮 Module 2: ICAO 9303 & Parity")
            mrz = result.get("mrz_validation", {})
            st.write(f"**MRZ Detected:** `{mrz.get('mrz_detected')}`")
            st.write(f"**Doc Number Chk:** `{mrz.get('check_digit_doc_number')}`")
            st.write(f"**DOB Chk:** `{mrz.get('check_digit_dob')}`")
            st.write(f"**Expiry Chk:** `{mrz.get('check_digit_expiry')}`")
            st.write(f"**Composite Chk:** `{mrz.get('composite_checksum')}`")
            st.write(f"**VIZ-MRZ Parity:** `{mrz.get('viz_mrz_cross_match_score', 0):.2f}`")

        with m3:
            st.markdown("### 🔍 Module 3: Forensics")
            forensic = result.get("forensic_analysis", {})
            st.write(f"**ELA Anomaly Score:** `{forensic.get('ela_tamper_score', 0):.2f}`")
            st.write(f"**Photo Splice:** `{'YES' if forensic.get('photo_splice_detected') else 'NO'}`")
            st.write(f"**Typography Anomaly:** `{'YES' if forensic.get('typography_anomaly_detected') else 'NO'}`")
            st.write(f"**Flagged Regions:** `{len(forensic.get('flagged_regions', []))}`")

        with m4:
            st.markdown("### 👤 Module 4: Biometrics")
            bio = result.get("biometric_verification", {})
            st.write(f"**Face Match:** `{'CONFIRMED' if bio.get('face_match') else 'MISMATCH'}`")
            st.write(f"**Similarity Score:** `{bio.get('similarity_score', 0):.2f}`")
            st.write(f"**PAD Liveness:** `{'VERIFIED' if bio.get('liveness_confirmed') else 'SUSPECT'}`")

        st.divider()
        st.subheader("💡 Explainable Threat Reasons")
        for r in dec.get("reasons", []):
            st.markdown(f"- {r}")

        st.subheader("📦 Strict Output JSON Payload")
        st.json(result)


if __name__ == "__main__":
    if "streamlit" in sys.argv[0] or "streamlit" in sys.modules:
        run_streamlit_app()
    else:
        parser = argparse.ArgumentParser(description="AG-IDFSE Border Security Screening Engine")
        parser.add_argument("--doc", type=str, help="Path to document image")
        parser.add_argument("--live", type=str, help="Path to live presenter portrait")
        parser.add_argument("--mrz", type=str, help="Raw MRZ string")
        parser.add_argument("--hint", type=str, help="Document taxonomy hint")
        args = parser.parse_args()

        if args.doc or args.mrz:
            run_cli_scan(args.doc, args.live, args.mrz, args.hint)
        else:
            try:
                import streamlit
                run_streamlit_app()
            except ImportError:
                parser.print_help()
