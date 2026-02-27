# =============================================================================
# compiler.py — Compile LaTeX → PDF and DOCX → PDF
# =============================================================================

import logging
import os
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LaTeX → PDF
# ---------------------------------------------------------------------------

def compile_latex_to_pdf(tex_path: str) -> str:
    """
    Compile a .tex file to PDF using pdflatex.
    Runs twice (standard practice for resolving references).
    Returns path to the generated PDF, or empty string on failure.

    Requirements:
      - MiKTeX or TeX Live installed on Windows
      - pdflatex available in PATH
      - resume.cls (or your custom .cls) available in the same directory or texmf tree
    """
    tex_path = Path(tex_path)
    if not tex_path.exists():
        log.error(f"LaTeX file not found: {tex_path}")
        return ""

    work_dir = tex_path.parent
    pdf_path = work_dir / (tex_path.stem + ".pdf")

    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",   # don't pause on errors
        "-output-directory", str(work_dir),
        str(tex_path)
    ]

    for run_num in (1, 2):  # compile twice
        try:
            result = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                log.warning(f"pdflatex run {run_num} warnings/errors for {tex_path.name}")
                log.debug(result.stdout[-2000:])  # last 2000 chars of log
        except subprocess.TimeoutExpired:
            log.error(f"pdflatex timed out for {tex_path}")
            return ""
        except FileNotFoundError:
            log.error(
                "pdflatex not found. Install MiKTeX (https://miktex.org/download) "
                "and ensure it's in your PATH."
            )
            return ""

    if pdf_path.exists():
        log.info(f"Resume PDF compiled: {pdf_path}")
        # Clean up auxiliary files
        for ext in [".aux", ".log", ".out"]:
            aux = work_dir / (tex_path.stem + ext)
            if aux.exists():
                aux.unlink()
        return str(pdf_path)
    else:
        log.error(f"PDF not generated. Check {work_dir / (tex_path.stem + '.log')}")
        return ""


# ---------------------------------------------------------------------------
# DOCX → PDF
# ---------------------------------------------------------------------------

def convert_docx_to_pdf(docx_path: str) -> str:
    """
    Convert a .docx file to PDF.

    Strategy (tries in order):
      1. LibreOffice (free, cross-platform — recommended)
         Install: https://www.libreoffice.org/download/download/
      2. docx2pdf Python library (requires Microsoft Word installed on Windows)
         pip install docx2pdf

    Returns path to PDF, or empty string on failure.
    """
    docx_path = Path(docx_path)
    if not docx_path.exists():
        log.error(f"DOCX file not found: {docx_path}")
        return ""

    output_dir = docx_path.parent
    pdf_path = output_dir / (docx_path.stem + ".pdf")

    # --- Strategy 1: LibreOffice ---
    libreoffice_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "soffice",  # if in PATH
        "libreoffice",
    ]

    soffice = None
    for path in libreoffice_paths:
        if shutil.which(path) or os.path.exists(path):
            soffice = path
            break

    if soffice:
        try:
            result = subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(output_dir),
                    str(docx_path)
                ],
                capture_output=True, text=True, timeout=60
            )
            if pdf_path.exists():
                log.info(f"Cover letter PDF converted (LibreOffice): {pdf_path}")
                return str(pdf_path)
        except Exception as e:
            log.warning(f"LibreOffice conversion failed: {e}")

    # --- Strategy 2: docx2pdf (requires MS Word) ---
    try:
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
        if pdf_path.exists():
            log.info(f"Cover letter PDF converted (docx2pdf/Word): {pdf_path}")
            return str(pdf_path)
    except ImportError:
        log.warning("docx2pdf not installed. Run: pip install docx2pdf")
    except Exception as e:
        log.warning(f"docx2pdf conversion failed: {e}")

    log.error(
        f"Could not convert {docx_path.name} to PDF. "
        "Install LibreOffice or Microsoft Word + docx2pdf."
    )
    return ""


# ---------------------------------------------------------------------------
# Compile all docs for a job
# ---------------------------------------------------------------------------

def compile_all(paths: dict) -> dict:
    """
    Compile resume .tex → PDF and cover letter .docx → PDF.
    Updates and returns the paths dict with 'resume_pdf' and 'cover_letter_pdf' keys.
    """
    if paths.get("resume_tex"):
        paths["resume_pdf"] = compile_latex_to_pdf(paths["resume_tex"])

    if paths.get("cover_letter_docx"):
        paths["cover_letter_pdf"] = convert_docx_to_pdf(paths["cover_letter_docx"])

    return paths
