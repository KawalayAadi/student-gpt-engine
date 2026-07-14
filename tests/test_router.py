# tests/test_router.py
from app.services.semantic_router import classify, Mode


def test_flashcards():
    assert classify("make me flashcards on photosynthesis") == Mode.FLASHCARDS


def test_pop_quiz():
    assert classify("quiz me on the French Revolution") == Mode.POP_QUIZ


def test_short_notes():
    assert classify("short notes on mitosis") == Mode.SHORT_NOTES


def test_short_notes_via_summarize_keyword():
    assert classify("can you summarize the chapter on cells") == Mode.SHORT_NOTES


def test_default_qa():
    assert classify("what is the derivative of x^2") == Mode.QA


def test_case_insensitive():
    assert classify("FLASHCARD me on the Treaty of Versailles") == Mode.FLASHCARDS


def test_empty_string_defaults_to_qa():
    assert classify("") == Mode.QA