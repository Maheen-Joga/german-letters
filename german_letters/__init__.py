"""german-letters: formal German letters to DIN 5008, with deadlines and an English explanation."""

from .letter import Address, Letter, LetterError, check, to_text
from .templates import TEMPLATES, build

__all__ = ["Address", "Letter", "LetterError", "TEMPLATES", "build", "check", "to_text"]
__version__ = "0.1.0"
