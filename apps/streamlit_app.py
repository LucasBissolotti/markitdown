from __future__ import annotations
import io
import zipfile
import subprocess
import sys
import importlib
from pathlib import Path
from typing import Dict, List

try:
    import streamlit as st
    HAS_STREAMLIT = True
except Exception:
    HAS_STREAMLIT = False

from markitdown import MarkItDown
try:
    # Preferred public export
    from markitdown import FileConversionException, MissingDependencyException
except Exception:
    # Fallback to internal module path if package doesn't re-export
    try:
        from markitdown._exceptions import FileConversionException, MissingDependencyException
    except Exception:
        # If imports fail, define a local fallback base exception
        class FileConversionException(Exception):
            pass
        class MissingDependencyException(Exception):
            pass


def convert_paths(paths: list[str]) -> Dict[str, str]:
    """Convert local file paths to Markdown text. Returns mapping path->markdown or error message."""
    converter = MarkItDown()
    out: Dict[str, str] = {}
    for p in paths:
        try:
            result = converter.convert(p)
            text = getattr(result, "text_content", None)
            out[p] = text if text is not None else str(result)
        except FileConversionException as e:
            out[p] = f"ERROR: {e}"
        except Exception as e:
            out[p] = f"ERROR: {e}"
    return out


def install_markitdown_extras(extras: List[str]) -> tuple[bool, str]:
    """Install optional markitdown extras into the running environment.

    Returns (success, output).
    """
    if not extras:
        return False, "No extras selected"
    pkg = f"markitdown[{','.join(extras)}]"
    try:
        # Use the same Python executable running the app
        cmd = [sys.executable, "-m", "pip", "install", pkg]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        out = proc.stdout + "\n" + proc.stderr
        if proc.returncode == 0:
            # attempt to reload markitdown package so new deps are picked up
            try:
                import markitdown as _m
                importlib.reload(_m)
            except Exception:
                pass
            return True, out
        return False, out
    except Exception as e:
        return False, str(e)


def make_zip_from_dict(contents: Dict[str, str]) -> bytes:
    """Create an in-memory ZIP from a dict name->text and return bytes."""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, text in contents.items():
            safe_name = Path(name).name
            md_name = f"{Path(safe_name).stem}.md"
            zf.writestr(md_name, text)
    bio.seek(0)
    return bio.read()


def streamlit_app() -> None:
    if not HAS_STREAMLIT:
        raise RuntimeError("Streamlit is not installed in this environment. Install it with `pip install streamlit`.")

    st.set_page_config(page_title="MarkItDown - Batch Converter", layout="wide")
    st.title("MarkItDown — Batch converter")

    # initialize session state for results so download is always available in sidebar
    if 'converted_results' not in st.session_state:
        st.session_state['converted_results'] = None
    if 'zip_bytes' not in st.session_state:
        st.session_state['zip_bytes'] = None

    uploaded = st.file_uploader("Upload files (or select a folder via path below)", accept_multiple_files=True)
    st.write("Or provide a folder path (server-side):")
    folder = st.text_input("Folder path (optional)")

    recurse = st.checkbox("Recurse into subfolders", value=True)

    convert_button = st.button("Convert uploaded / folder files")

    # Inline summary (removed sidebar)
    def render_inline_summary():
        if st.session_state.get('converted_results'):
            results_sb = st.session_state['converted_results']
            total = len(results_sb)
            success = sum(1 for v in results_sb.values() if not str(v).startswith('ERROR:'))
            st.markdown(f"**Files converted:** {success}/{total}")
            with st.expander("Converted files (click to expand)", expanded=False):
                for p, txt in results_sb.items():
                    label = Path(p).name
                    if str(txt).startswith('ERROR:'):
                        st.write(f"❌ {label}")
                    else:
                        st.write(f"✅ {label}")
            # summary only — download button is shown below as the main action
        else:
            st.write("No conversions yet")

    # note: render summary and download AFTER any conversion so updated session_state is shown immediately

    if convert_button:
        paths: list[str] = []
        temp_dir = Path(".") / "converted_streamlit_tmp"
        temp_dir.mkdir(exist_ok=True)

        if uploaded:
            for f in uploaded:
                dst = temp_dir / f.name
                with open(dst, "wb") as fh:
                    fh.write(f.getbuffer())
                paths.append(str(dst))

        if folder:
            p = Path(folder)
            if p.exists() and p.is_dir():
                # include all files by default
                it = p.rglob("*") if recurse else p.iterdir()
                for fp in it:
                    if fp.is_file():
                        paths.append(str(fp))
            else:
                st.error("Folder path does not exist or is not a directory")

        if not paths:
            st.warning("No files to convert")
            return

        status = st.empty()
        results: Dict[str, str] = {}
        total = len(paths)
        for i, p in enumerate(paths, start=1):
            status.info(f"Converting {i}/{total}: {p}")
            try:
                res = convert_paths([p])
                results.update(res)
            except Exception as e:
                results[p] = f"ERROR: {e}"

        status.success("Conversion finished")

        # store results in session state so UI can render tabs and sidebar download
        st.session_state['converted_results'] = results
        zip_bytes = make_zip_from_dict(results)
        st.session_state['zip_bytes'] = zip_bytes

    # Render converted results as tabs (persistent across reruns)
    results_to_show = st.session_state.get('converted_results')
    if results_to_show:
        # create tabs for each file
        file_names = [Path(p).name for p in results_to_show.keys()]
        tabs = st.tabs(file_names)
        for tab, (p, text) in zip(tabs, results_to_show.items()):
            with tab:
                st.subheader(Path(p).name)
                # Use an expander so the user can minimize/maximize the markdown view
                with st.expander("View Markdown", expanded=False):
                    if str(text).startswith('ERROR:'):
                        st.error(text)
                    else:
                        st.markdown(text)

        # After rendering tabs, show inline summary and prominent download button
        render_inline_summary()
        # Ensure ZIP exists
        if not st.session_state.get('zip_bytes') and st.session_state.get('converted_results'):
            try:
                st.session_state['zip_bytes'] = make_zip_from_dict(st.session_state['converted_results'])
            except Exception as e:
                st.error(f"Could not create ZIP: {e}")

        if st.session_state.get('zip_bytes'):
            st.download_button("Download all .md as ZIP", data=st.session_state['zip_bytes'], file_name="markitdown_converted.zip", mime="application/zip", key="download_main")
        else:
            st.info("No converted files yet — convert files to enable ZIP download")


if __name__ == "__main__" and HAS_STREAMLIT:
    streamlit_app()
