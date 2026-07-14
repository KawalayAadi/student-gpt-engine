# app/templates/micro_templates.py
"""
Loads the base system_prompt.xml (role + global rules) and swaps in only the
<mode> block that matches the semantic router's output, so we don't send the
whole template (all four modes) on every request.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from functools import lru_cache

TEMPLATE_PATH = Path(__file__).parent / "system_prompt.xml"


@lru_cache(maxsize=1)
def _load_tree() -> ET.Element:
    return ET.parse(TEMPLATE_PATH).getroot()


@lru_cache(maxsize=1)
def _base_prompt() -> str:
    root = _load_tree()
    role = root.findtext("role", default="").strip()
    rules = [r.text.strip() for r in root.findall("./rules/rule") if r.text]
    rules_text = "\n".join(f"- {r}" for r in rules)
    return f"{role}\n\nRules:\n{rules_text}"


@lru_cache(maxsize=8)
def get_mode_instruction(mode: str) -> str:
    root = _load_tree()
    for mode_el in root.findall("./mode_instructions/mode"):
        if mode_el.get("name") == mode:
            return (mode_el.text or "").strip()
    # fall back to plain QA behavior if an unknown mode ever reaches here
    return "Answer the question directly, showing key steps."


def build_system_prompt(mode: str) -> str:
    """
    Returns the full system message content to send as the first message
    in the chat completion call: base role/rules + the one relevant mode block.
    """
    return f"{_base_prompt()}\n\nCurrent mode ({mode}):\n{get_mode_instruction(mode)}"