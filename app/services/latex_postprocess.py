# app/services/latex_postprocess.py
import re

LATEX_BLOCK_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
LATEX_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")

def validate_and_wrap_latex(text: str) -> dict:
    """
    Returns the text plus a flag/list so the frontend can decide how to render.
    Does not alter the model's LaTeX — just verifies delimiters are balanced
    and reports segments so the frontend renderer (e.g. KaTeX/MathJax) gets
    clean input instead of raw broken markup.
    """
    block_matches = LATEX_BLOCK_RE.findall(text)
    inline_matches = LATEX_INLINE_RE.findall(text)

    dollar_count = text.count("$")
    balanced = dollar_count % 2 == 0

    return {
        "text": text,
        "latex_blocks": block_matches,
        "latex_inline": inline_matches,
        "balanced": balanced,
    }