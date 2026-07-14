# app/services/semantic_router.py

# replacing this whole this with a hybrid wud be better for the next ver anyways this is just v1 

from enum import Enum

class Mode(str, Enum):
    QA = "qa"
    FLASHCARDS = "flashcards"
    POP_QUIZ = "pop_quiz"
    SHORT_NOTES = "short_notes"

KEYWORD_MAP = {
    Mode.FLASHCARDS: ["flashcard", "flash card"],
    Mode.POP_QUIZ: ["quiz", "test me", "pop quiz"],
    Mode.SHORT_NOTES: ["short notes", "summarize", "summary", "notes on"],
}

def classify(user_message: str) -> Mode:
    text = user_message.lower()
    for mode, keywords in KEYWORD_MAP.items():
        if any(k in text for k in keywords):
            return mode
    return Mode.QA