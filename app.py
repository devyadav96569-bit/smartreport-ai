import re
from io import BytesIO
from datetime import datetime

import pandas as pd
import streamlit as st

# Optional PDF extraction. The app still works with pasted text if this dependency
# is unavailable or the PDF is scanned/image-only.
try:
    import pdfplumber
except Exception:
    pdfplumber = None

st.set_page_config(page_title="SmartReport AI", page_icon="🩺", layout="wide")

# Demo reference intervals only. Actual intervals vary by lab, method, age, sex,
# pregnancy status, and other clinical factors. Always prefer the report's own range.
REFERENCE_RANGES = {
    "hemoglobin": {"unit": "g/dL", "low": 12.0, "high": 17.5, "label": "Hemoglobin"},
    "wbc": {"unit": "10^3/µL", "low": 4.0, "high": 11.0, "label": "White blood cells (WBC)"},
    "platelets": {"unit": "10^3/µL", "low": 150.0, "high": 450.0, "label": "Platelets"},
    "glucose": {"unit": "mg/dL", "low": 70.0, "high": 99.0, "label": "Fasting glucose"},
    "creatinine": {"unit": "mg/dL", "low": 0.6, "high": 1.3, "label": "Creatinine"},
    "total_cholesterol": {"unit": "mg/dL", "low": 0.0, "high": 200.0, "label": "Total cholesterol"},
    "hdl": {"unit": "mg/dL", "low": 40.0, "high": 999.0, "label": "HDL cholesterol"},
    "ldl": {"unit": "mg/dL", "low": 0.0, "high": 100.0, "label": "LDL cholesterol"},
    "triglycerides": {"unit": "mg/dL", "low": 0.0, "high": 149.0, "label": "Triglycerides"},
    "tsh": {"unit": "mIU/L", "low": 0.4, "high": 4.0, "label": "TSH"},
}

# Match common forms such as "Hemoglobin: 13.4 g/dL" or "WBC 12.1".
PATTERNS = {
    "hemoglobin": r"(?:hemoglobin|haemoglobin|hgb|hb)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "wbc": r"(?:white blood cells?|wbc|total leukocyte count|tlc)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "platelets": r"(?:platelets?|platelet count)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "glucose": r"(?:fasting blood sugar|fasting glucose|blood glucose|glucose|fbs)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "creatinine": r"(?:serum creatinine|creatinine)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "total_cholesterol": r"(?:total cholesterol|cholesterol total)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "hdl": r"(?:hdl(?: cholesterol)?)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "ldl": r"(?:ldl(?: cholesterol)?)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "triglycerides": r"(?:triglycerides?|tg)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
    "tsh": r"(?:tsh|thyroid stimulating hormone)\s*[:=\-]?\s*(\d+(?:\.\d+)?)",
}

def extract_pdf_text(uploaded_file):
    if pdfplumber is None:
        return "", "PDF extraction package is unavailable. Paste the report text below instead."
    try:
        with pdfplumber.open(BytesIO(uploaded_file.getvalue())) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages).strip()
        if not text:
            return "", "No selectable text found. This may be a scanned PDF; paste its text manually."
        return text, ""
    except Exception as exc:
        return "", f"Could not read this PDF ({exc}). Paste the report text manually."

def analyze_report(report_text, custom_ranges):
    found = []
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, report_text, flags=re.IGNORECASE)
        if not match:
            continue
        value = float(match.group(1))
        ref = custom_ranges.get(key, REFERENCE_RANGES[key])
        if value < ref["low"]:
            status = "Below range"
        elif value > ref["high"]:
            status = "Above range"
        else:
            status = "Within range"
        found.append({
            "Test": ref["label"],
            "Value": value,
            "Unit": ref["unit"],
            "Reference interval (demo)": f'{ref["low"]:g}–{ref["high"]:g} {ref["unit"]}',
            "Flag": status,
            "_key": key,
        })
    return found

st.title("🩺 SmartReport AI")
st.caption("Hackathon prototype • Medical report value extraction and reference-range flagging")

st.warning(
    "Educational prototype only — not a diagnostic tool. It can miss values or misread formatting. "
    "Do not use it for treatment decisions. Confirm every value and reference interval against the original "
    "laboratory report and consult a qualified clinician."
)

with st.sidebar:
    st.header("Demo settings")
    st.write("You can override the demo reference intervals below. Use the ranges printed on the patient's own report.")
    custom_ranges = {}
    with st.expander("Reference ranges", expanded=False):
        for key, ref in REFERENCE_RANGES.items():
            st.markdown(f"**{ref['label']} ({ref['unit']})**")
            c1, c2 = st.columns(2)
            low = c1.number_input("Low", value=float(ref["low"]), key=f"{key}_low")
            high = c2.number_input("High", value=float(ref["high"]), key=f"{key}_high")
            custom_ranges[key] = {"low": low, "high": high, "unit": ref["unit"], "label": ref["label"]}

st.subheader("1. Add a sample report")
uploaded = st.file_uploader("Upload a text-based PDF report (optional)", type=["pdf"])
default_text = """Sample lab report (fictional)
Hemoglobin: 13.4 g/dL
WBC: 12.1 10^3/uL
Platelets: 250 10^3/uL
Fasting glucose: 108 mg/dL
Creatinine: 0.9 mg/dL
Total cholesterol: 212 mg/dL
HDL: 48 mg/dL
LDL: 130 mg/dL
Triglycerides: 160 mg/dL
TSH: 2.1 mIU/L
"""
report_text = st.text_area("Paste report text here", value=default_text, height=220,
                           help="For best results, paste the test name and numeric result exactly as shown.")
if uploaded is not None:
    extracted, error = extract_pdf_text(uploaded)
    if extracted:
        report_text = st.text_area("Extracted PDF text (check it carefully)", value=extracted, height=220)
    elif error:
        st.info(error)

if st.button("Analyze report", type="primary", use_container_width=True):
    if not report_text.strip():
        st.error("Please upload a readable PDF or paste report text first.")
    else:
        results = analyze_report(report_text, custom_ranges)
        st.session_state["analysis_results"] = results
        st.session_state["source_text"] = report_text
        st.session_state["analysis_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")

if "analysis_results" in st.session_state:
    results = st.session_state["analysis_results"]
    st.subheader("2. Results overview")
    if not results:
        st.info("No supported test values were detected. Try pasting the report text or check the spelling/format.")
    else:
        df = pd.DataFrame([{k: v for k, v in row.items() if not k.startswith("_")} for row in results])
        total = len(results)
        abnormal = sum(row["Flag"] != "Within range" for row in results)
        c1, c2, c3 = st.columns(3)
        c1.metric("Values detected", total)
        c2.metric("Outside demo range", abnormal)
        c3.metric("Within demo range", total - abnormal)
        st.dataframe(
            df.style.apply(
                lambda col: [
                    "background-color: #ffe4e6; color: #881337" if val != "Within range" else
                    "background-color: #dcfce7; color: #166534" if col.name == "Flag" else ""
                    for val in col
                ] if col.name == "Flag" else ["" for _ in col],
                axis=0
            ),
            use_container_width=True,
            hide_index=True
        )
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download results as CSV", data=csv, file_name="smartreport_results.csv",
                           mime="text/csv", use_container_width=True)

        st.subheader("3. Review notes")
        flagged = [row for row in results if row["Flag"] != "Within range"]
        if flagged:
            st.write("The following values were outside the currently configured demo intervals:")
            for row in flagged:
                st.markdown(f"- **{row['Test']}**: {row['Value']:g} {row['Unit']} — {row['Flag']}.")
            st.info(
                "A flagged result does not by itself establish a disease or emergency. Interpretation depends on "
                "the lab's own interval, symptoms, medical history, medications, age, and other factors. "
                "Ask a clinician to review the original report, especially if multiple results are flagged."
            )
        else:
            st.success("No detected values were outside the configured demo intervals. This does not mean the report is completely normal.")
        st.caption(f"Analyzed at {st.session_state.get('analysis_time', '')}. Values are extracted by simple pattern matching; verify them manually.")

st.divider()
st.subheader("How to demo this safely")
st.markdown(
    "1. Use the built-in fictional sample.  2. Click **Analyze report**.  "
    "3. Show the flagged WBC, glucose, cholesterol and triglycerides.  "
    "4. Change a reference range in the sidebar to demonstrate that ranges are configurable.  "
    "5. Download the CSV. Never upload real patient information during a public demo."
)
st.caption("Prototype limitations: supports a small set of common lab values; does not diagnose, predict outcomes, or replace medical review.")
