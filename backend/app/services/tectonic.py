"""
Tectonic-based LaTeX → PDF compiler.

Uses the `tectonic` command-line tool for fast (~130ms) compilation.
Falls back to pdflatex if Tectonic is not available.
"""

import os
import shutil
import subprocess
import tempfile


async def compile_pdf(latex_source: str) -> bytes:
    """
    Compile a LaTeX source string into PDF bytes.

    Uses Tectonic for speed (~130ms cached), falls back to pdflatex.

    Returns:
        PDF file contents as bytes
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)

        # Try Tectonic first
        tectonic_path = shutil.which("tectonic")
        if tectonic_path:
            result = subprocess.run(
                [tectonic_path, "--untrusted", tex_path],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Tectonic compilation failed:\n{result.stderr}\n{result.stdout}"
                )

            pdf_path = os.path.join(tmpdir, "resume.pdf")
        else:
            # Fallback to pdflatex
            pdflatex_path = shutil.which("pdflatex")
            if not pdflatex_path:
                raise RuntimeError(
                    "Neither tectonic nor pdflatex found. Install one to compile PDFs."
                )

            result = subprocess.run(
                [
                    pdflatex_path,
                    "-interaction=nonstopmode",
                    "-output-directory",
                    tmpdir,
                    tex_path,
                ],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"pdflatex compilation failed:\n{result.stderr}\n{result.stdout}"
                )

            pdf_path = os.path.join(tmpdir, "resume.pdf")

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(
                f"PDF not generated. Compiler output:\n{result.stdout}\n{result.stderr}"
            )

        with open(pdf_path, "rb") as f:
            return f.read()
