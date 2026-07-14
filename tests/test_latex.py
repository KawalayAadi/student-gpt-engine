# tests/test_latex.py
from app.services.latex_postprocess import validate_and_wrap_latex


def test_balanced_block():
    text = "The formula is $$E=mc^2$$ which is famous."
    result = validate_and_wrap_latex(text)
    assert result["balanced"] is True
    assert result["latex_blocks"] == ["E=mc^2"]


def test_balanced_inline():
    text = "Note that $x^2$ is always positive."
    result = validate_and_wrap_latex(text)
    assert result["balanced"] is True
    assert result["latex_inline"] == ["x^2"]


def test_unbalanced_dollar_signs():
    text = "This is broken: $x^2 without a closing delimiter"
    result = validate_and_wrap_latex(text)
    assert result["balanced"] is False


def test_no_latex_present():
    text = "Plain text answer, no math here."
    result = validate_and_wrap_latex(text)
    assert result["balanced"] is True
    assert result["latex_blocks"] == []
    assert result["latex_inline"] == []


def test_multiple_inline_expressions():
    text = "We have $a$ and $b$ and $c$."
    result = validate_and_wrap_latex(text)
    assert result["balanced"] is True
    assert result["latex_inline"] == ["a", "b", "c"]


def test_block_and_inline_together():
    text = "Inline $x$ then block $$y = mx + b$$ after."
    result = validate_and_wrap_latex(text)
    assert result["balanced"] is True
    assert result["latex_blocks"] == ["y = mx + b"]
    assert result["latex_inline"] == ["x"]