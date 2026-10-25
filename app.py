import re
from io import BytesIO
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

st.set_page_config(
    page_title="SmartReport AI",
    page_icon="🩺",
    layout="wide"
)

RANGES = {
    "Hemoglobin": ("g/dL", 12, 17.5),
    "WBC": ("10^3/µL", 4, 11),
    "Platelets": ("10^3/µL", 150, 450),
    "Fasting glucose": ("mg/dL", 70, 99),
    "Creatinine": ("mg/dL", 0.6, 1.3),
    "Total cholesterol": ("mg/dL", 0, 200),
    "HDL": ("mg/dL", 40, 999),
    "LDL": ("mg/dL", 0, 100),
    "Triglycerides": ("mg/dL", 0, 149),
    "TSH": ("mIU/L", 0.4, 4),
}

SAMPLE = """Fictional sample report
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

st.markdown("""
<style>
.stApp {
 background: radial-gradient(ellipse at top left,#192544,#090e19 65%);
}
.block-container {max-width:1400px;padding-top:2rem}
[data-testid="stSidebar"] {background:#101829}
.hero {
 padding:30px;border-radius:22px;
 background:linear-gradient(120deg,#182744,#17152f);
 border:1px solid #354567;margin-bottom:20px;
}
.hero h1 {font-size:42px;margin-bottom:8px}
.hero p {color:#b8c6dc}
.metric {
 background:#131e30;border:1px solid #34425b;
 padding:18px;border-radius:16px;min-height:110px;
}
.metric-label {color:#aab9d0;font-size:14px}
.metric-value {font-size:32px;font-weight:800}
.feature {
 background:#131e30;border:1px solid #34425b;
 padding:16px;border-radius:14px;min-height:100px;
}
div.stButton>button[kind="primary"] {
 background:linear-gradient(90deg,#625cf6,#a05cf6);
 border:0;border-radius:12px;min-height:48px;
 font-weight:700;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <p>HEALTHCARE · MEDTECH · HACKATHON PROJECT</p>
  <h1>🩺 SmartReport <span style="color:#b9a5ff">AI</span></h1>
  <p>Understand your lab reports more clearly.
  Extract selected values, compare reference intervals and
  review results in one dashboard.</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "Educational prototype only — not a diagnostic tool. "
    "Verify every extracted value and reference interval against "
    "the original laboratory report. Never use this app to make "
    "treatment decisions."
)

with st.sidebar:
    st.header("⚙️ Demo settings")
    st.caption("Default ranges are illustrative.")
    ranges = {}

    with st.expander("Edit reference ranges"):
        for name, (unit, default_low, default_high) in RANGES.items():
            st.markdown(f"**{name} ({unit})**")
            a, b = st.columns(2)
            low = a.number_input(
                "Low", value=float(default_low), key=name+"_low"
            )
            high = b.number_input(
                "High", value=float(default_high), key=name+"_high"
            )
            ranges[name] = (
                (low, high) if low <= high
                else (default_low, default_high)
            )

    st.divider()
    st.caption("🔒 Use fictional data for public demos.")

left, right = st.columns([1.5, 1], gap="large")

with left:
    st.subheader("① Upload or paste report")
    uploaded = st.file_uploader("Upload text-based PDF", type=["pdf"])
    text = st.text_area("Report text", value=SAMPLE, height=260)

    if uploaded is not None:
        if pdfplumber is None:
            st.info("PDF reader unavailable. Paste report text instead.")
        else:
            try:
                with pdfplumber.open(BytesIO(uploaded.getvalue())) as pdf:
                    extracted = "\n".join(
                        p.extract_text() or "" for p in pdf.pages
                    ).strip()
                if extracted:
                    text = st.text_area(
                        "Extracted PDF text — verify carefully",
                        value=extracted, height=180
                    )
                else:
                    st.info("No selectable text found. Paste report text.")
            except Exception:
                st.error("Could not read PDF. Paste report text instead.")

    analyze = st.button(
        "✨ Analyze report", type="primary", use_container_width=True
    )

with right:
    st.subheader("What SmartReport does")
    st.markdown("""
    <div class="feature">📄 <b>Extract values</b><br>
    <small>Find supported test results.</small></div><br>
    <div class="feature">🎯 <b>Compare intervals</b><br>
    <small>Use configurable demo ranges.</small></div><br>
    <div class="feature">🔎 <b>Highlight results</b><br>
    <small>Show values outside intervals.</small></div><br>
    <div class="feature">📥 <b>Export results</b><br>
    <small>Download a CSV report.</small></div>
    """, unsafe_allow_html=True)

def analyze_report(report):
    rows = []

    patterns = {
        "Hemoglobin": r"(?:hemoglobin|haemoglobin|hgb|hb)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "WBC": r"(?:white blood cells?|wbc|total leukocyte count|tlc)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "Platelets": r"(?:platelets?|platelet count)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "Fasting glucose": r"(?:fasting blood sugar|fasting glucose|blood glucose|glucose|fbs)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "Creatinine": r"(?:serum creatinine|creatinine)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "Total cholesterol": r"(?:total cholesterol|cholesterol total)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "HDL": r"\bhdl(?: cholesterol)?\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "LDL": r"\bldl(?: cholesterol)?\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "Triglycerides": r"(?:triglycerides?|tg)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
        "TSH": r"(?:tsh|thyroid stimulating hormone)\s*[:=-]?\s*(\d+(?:\.\d+)?)",
    }

    for name, pattern in patterns.items():
        match = re.search(pattern, report, re.I)
        if not match:
            continue

        value = float(match.group(1))
        unit, default_low, default_high = RANGES[name]
        low, high = ranges.get(name, (default_low, default_high))

        if value < low:
            flag = "Below range"
        elif value > high:
            flag = "Above range"
        else:
            flag = "Within range"

        rows.append({
            "Test": name,
            "Value": value,
            "Unit": unit,
            "Reference interval": f"{low:g}–{high:g} {unit}",
            "Flag": flag,
        })

    return rows

if analyze:
    if not text.strip():
        st.error("Please paste a report first.")
    else:
        st.session_state["results"] = analyze_report(text)
        st.session_state["time"] = datetime.now().strftime("%d %b %Y, %H:%M")

if "results" in st.session_state:
    rows = st.session_state["results"]
    st.divider()
    st.subheader("② Analysis results")

    total = len(rows)
    outside = sum(r["Flag"] != "Within range" for r in rows)
    normal = total - outside
    above = sum(r["Flag"] == "Above range" for r in rows)
    below = sum(r["Flag"] == "Below range" for r in rows)

    c1, c2, c3, c4 = st.columns(4)
    metrics = [
        ("Detected values", total, "#b9a5ff"),
        ("Within interval", normal, "#55dfac"),
        ("Above interval", above, "#ff8596"),
        ("Below interval", below, "#ffd078"),
    ]

    for col, (label, value, color) in zip(
        [c1, c2, c3, c4], metrics
    ):
        with col:
            st.markdown(
                f'<div class="metric"><div class="metric-label">'
                f'{label}</div><div class="metric-value" '
                f'style="color:{color}">{value}</div></div>',
                unsafe_allow_html=True
            )

    if not rows:
        st.info("No supported test values detected.")
    else:
        if outside:
            st.info(
                f"{outside} value(s) are outside demo intervals. "
                "These flags are not diagnoses."
            )
        else:
            st.success(
                "No detected values were outside demo intervals. "
                "This does not rule out health problems."
            )

        df = pd.DataFrame(rows)
        overview, details, charts, notes = st.tabs([
            "Overview", "Detailed results", "Visual charts", "Review notes"
        ])

        with overview:
            a, b = st.columns([1, 1.4])
            with a:
                st.markdown("#### Result distribution")
                distribution = pd.DataFrame({
                    "Status": ["Within range", "Above range", "Below range"],
                    "Count": [normal, above, below],
                })
                st.bar_chart(distribution.set_index("Status"))

            with b:
                st.markdown("#### Values to verify")
                flagged = [r for r in rows if r["Flag"] != "Within range"]
                if flagged:
                    for row in flagged:
                        st.markdown(
                            f"**{row['Test']}** — {row['Value']:g} "
                            f"{row['Unit']}  \n"
                            f"Status: **{row['Flag']}** · "
                            f"Demo interval: {row['Reference interval']}"
                        )
                        st.divider()
                else:
                    st.write("No out-of-interval flags detected.")

        with details:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇ Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="smartreport_results.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with charts:
            st.caption("Tests use different units; compare each result only in context.")
            st.bar_chart(df.set_index("Test")[["Value"]])

        with notes:
            st.markdown("""
            - Verify every number and unit against the original report.
            - Prefer the laboratory's own reference interval.
            - Interpretation depends on health history and other factors.
            - Ask a qualified clinician to review concerning results.
            """)
            st.warning(
                "An out-of-range result does not by itself establish a "
                "disease or emergency."
            )
            st.caption(
                "Analysis time: " + st.session_state.get("time", "")
            )

st.divider()
st.caption(
    "SmartReport AI · Hackathon prototype · Rule-based extraction · "
    "Not for diagnosis or treatment decisions."
)
