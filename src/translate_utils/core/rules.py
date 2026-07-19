# core/rules.py
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import final

from translate_utils.core.regexes import RE_TAGS, RE_WORDS

class TranslationSpecification(ABC):
    """
    Base class for the Specification pattern.
    Allows chaining business rules using bitwise operators (&, |, ~).
    """
    @abstractmethod
    def is_satisfied_by(self, original: str, translated: str) -> bool:
        pass

    def __and__(self, other: TranslationSpecification) -> TranslationSpecification:
        return AndSpecification(self, other)

    def __or__(self, other: TranslationSpecification) -> TranslationSpecification:
        return OrSpecification(self, other)

    def __invert__(self) -> TranslationSpecification:
        return NotSpecification(self)


@final
class AndSpecification(TranslationSpecification):
    def __init__(self, left: TranslationSpecification, right: TranslationSpecification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, original: str, translated: str) -> bool:
        return self.left.is_satisfied_by(original, translated) and \
               self.right.is_satisfied_by(original, translated)


@final
class OrSpecification(TranslationSpecification):
    def __init__(self, left: TranslationSpecification, right: TranslationSpecification):
        self.left = left
        self.right = right

    def is_satisfied_by(self, original: str, translated: str) -> bool:
        return self.left.is_satisfied_by(original, translated) or \
               self.right.is_satisfied_by(original, translated)


@final
class NotSpecification(TranslationSpecification):
    def __init__(self, spec: TranslationSpecification):
        self.spec = spec

    def is_satisfied_by(self, original: str, translated: str) -> bool:
        return not self.spec.is_satisfied_by(original, translated)

# ==========================================
# Concrete Business Rules
# ==========================================

@final
class IsNotEmptySpec(TranslationSpecification):
    """Checks if the translated string is not empty or just whitespaces."""
    def is_satisfied_by(self, original: str, translated: str) -> bool:
        return bool(translated and translated.strip())


@final
class IsDifferentSpec(TranslationSpecification):
    """Checks if the translation actually differs from the original."""
    def is_satisfied_by(self, original: str, translated: str) -> bool:
        return original != translated


@final
class HasTargetAlphabetSpec(TranslationSpecification):
    """Checks if the translation contains non-ASCII characters (e.g., Cyrillic)."""
    def is_satisfied_by(self, original: str, translated: str) -> bool:
        return not translated.isascii()


@final
class IsSymbolOnlySpec(TranslationSpecification):
    """Checks if the original string consists entirely of non-alphabetical characters (e.g., punctuation, spaces, tags)."""
    def is_satisfied_by(self, original: str, translated: str) -> bool:
        clean_original = RE_TAGS.sub("", original)
        return not any(c.isalpha() for c in clean_original)


@final
class NoMixedAlphabetsSpec(TranslationSpecification):
    """
    Checks that no single word mixes Latin and non-Latin (Cyrillic) characters.
    Catches common typing typos like 'Hellт' or 'Привiт' (with English 'i').
    Ignores structural tags.
    """
    def is_satisfied_by(self, original: str, translated: str) -> bool:
        clean_translated = RE_TAGS.sub("", translated)
        
        words = RE_WORDS.findall(clean_translated)
        
        for word in words:
            has_latin = False
            has_cyrillic = False
            
            for c in word:
                if c.isalpha():
                    if c.isascii():
                        has_latin = True
                    else:
                        has_cyrillic = True
                        
                if has_latin and has_cyrillic:
                    return False
                    
        return True

# ==========================================
# Usage
# ==========================================

VALID_TRANSLATION_SPEC = IsNotEmptySpec() & (
    IsSymbolOnlySpec() | (
        IsDifferentSpec() & HasTargetAlphabetSpec() #& NoMixedAlphabetsSpec()
    )
)

def check_is_translated(original: str, translated: str) -> bool:
    """Facade function to maintain compatibility with existing codebase."""
    return VALID_TRANSLATION_SPEC.is_satisfied_by(original, translated)
