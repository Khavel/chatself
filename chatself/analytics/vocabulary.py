"""
Vocabulary analysis: verbal tics, n-grams, language evolution.
"""

import re
from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatself.parsers.txt_parser import Chat

STOPWORDS_ES = {
    "de", "la", "el", "en", "y", "a", "que", "los", "las", "un", "una", "es",
    "por", "con", "no", "lo", "se", "me", "te", "si", "ya", "mi", "tu", "su",
    "le", "más", "para", "como", "pero", "sobre", "al", "del", "son", "era",
    "fue", "hay", "he", "ha", "han", "yo", "tú", "él", "ella", "nosotros",
    "esto", "esta", "ese", "esa", "muy", "bien", "pues", "ah", "eh", "ok",
    "que", "sí", "no", "ni", "o", "u", "e", "i",
}

STOPWORDS_EN = {
    "i", "me", "my", "the", "a", "an", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "is", "was", "are", "be", "have", "it", "he",
    "she", "we", "you", "they", "do", "did", "not", "that", "this", "as",
    "from", "by", "so", "if", "when", "all", "had", "has",
}

ALL_STOPWORDS = STOPWORDS_ES | STOPWORDS_EN


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def ngrams(tokens: list[str], n: int) -> list[tuple]:
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


class VocabularyAnalyzer:
    def __init__(self, chat: "Chat", my_name: str):
        self.my_texts = [
            m.text for m in chat.messages
            if m.sender == my_name and m.text and not m.is_media
        ]

    def word_frequency(self, top_n: int = 30, exclude_stopwords: bool = True) -> list[tuple[str, int]]:
        counter: Counter = Counter()
        for text in self.my_texts:
            tokens = tokenize(text)
            if exclude_stopwords:
                tokens = [t for t in tokens if t not in ALL_STOPWORDS and len(t) > 2]
            counter.update(tokens)
        return counter.most_common(top_n)

    def verbal_tics(self, top_n: int = 20) -> list[tuple[str, int]]:
        """Short repeated phrases that are signature expressions."""
        counter: Counter = Counter()
        for text in self.my_texts:
            # Exact short phrases (1-3 words)
            text_lower = text.lower().strip()
            if len(text_lower) <= 30:
                counter[text_lower] += 1
            # Also bigrams and trigrams
            tokens = tokenize(text)
            counter.update(" ".join(g) for g in ngrams(tokens, 2))
            counter.update(" ".join(g) for g in ngrams(tokens, 3))
        return counter.most_common(top_n)

    def bigrams(self, top_n: int = 20) -> list[tuple[str, int]]:
        counter: Counter = Counter()
        for text in self.my_texts:
            tokens = [t for t in tokenize(text) if t not in ALL_STOPWORDS]
            counter.update(" ".join(g) for g in ngrams(tokens, 2))
        return counter.most_common(top_n)

    def trigrams(self, top_n: int = 20) -> list[tuple[str, int]]:
        counter: Counter = Counter()
        for text in self.my_texts:
            tokens = [t for t in tokenize(text) if t not in ALL_STOPWORDS]
            counter.update(" ".join(g) for g in ngrams(tokens, 3))
        return counter.most_common(top_n)

    def avg_message_length(self) -> float:
        if not self.my_texts:
            return 0.0
        return round(sum(len(t) for t in self.my_texts) / len(self.my_texts), 1)

    def vocabulary_size(self) -> int:
        words = set()
        for text in self.my_texts:
            words.update(tokenize(text))
        return len(words)

    def summary(self) -> dict:
        return {
            "total_sent": len(self.my_texts),
            "avg_length": self.avg_message_length(),
            "vocabulary_size": self.vocabulary_size(),
            "top_words": self.word_frequency(20),
            "verbal_tics": self.verbal_tics(15),
            "top_bigrams": self.bigrams(10),
            "top_trigrams": self.trigrams(10),
        }
