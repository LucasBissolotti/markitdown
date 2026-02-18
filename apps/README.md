# MarkItDown Streamlit App

Quick local Streamlit UI for batch converting files to Markdown using MarkItDown.

Requirements
- Python 3.8+
- Install dependencies:

```powershell
pip install -e packages/markitdown[all]
pip install streamlit
```

Run the app

```powershell
streamlit run apps/streamlit_app.py --server.port 8502
```

Usage
- Upload files or provide a server-side folder path.
- Click `Convert` and download the resulting ZIP.

Notes
- Some formats require extra optional dependencies; install `markitdown[all]` to cover most formats.
