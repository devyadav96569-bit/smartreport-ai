# SmartReport AI — 3-hour hackathon prototype

A beginner-friendly Streamlit demo that extracts a small set of common numeric lab values from pasted text or text-based PDFs, compares them with configurable demo reference intervals, highlights out-of-range values, and exports results to CSV.

## Run locally (free)

1. Install Python 3.10 or newer from https://www.python.org/downloads/
2. Open a terminal in this folder.
3. Create and activate a virtual environment (optional but recommended):

   **Windows**
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   streamlit run app.py
   ```
6. Open the local URL printed by Streamlit (usually http://localhost:8501).

## Demo flow

- Keep the built-in fictional report.
- Click **Analyze report**.
- Show flagged values and the CSV export.
- Adjust a reference interval in the sidebar and re-run to show configurability.
- For a live demo, use fictional data only.

## Optional free deployment

You can deploy via Streamlit Community Cloud by pushing `app.py` and `requirements.txt` to a GitHub repository, then selecting that repository in Streamlit Community Cloud. Free-tier availability and limits may change. Do not put patient data, secrets, or API keys in the repository.

## Important limitations and safety

- This is an educational prototype, not a medical device or diagnostic system.
- The included reference intervals are illustrative demo values, not universal clinical ranges. Use the ranges printed on the original lab report.
- PDF extraction works only when the PDF has selectable text. Scanned PDFs need OCR, which is not included in this 3-hour version.
- Pattern matching is deliberately simple and may misread units, decimal formats, or similarly named tests. Always verify extracted values manually.
- A result outside a reference interval does not prove a disease, and a result within range does not rule out disease.
- Do not upload real patient information during a public hackathon demo.
