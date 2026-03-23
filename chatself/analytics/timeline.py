"""
Timeline analysis: personal evolution year by year across all chats.
"""

from collections import Counter, defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatself.parsers.txt_parser import Chat

from chatself.analytics.vocabulary import tokenize, ALL_STOPWORDS


class TimelineAnalyzer:
    """
    Analyzes evolution across ALL chats together, year by year.
    Pass a list of Chat objects and your name.
    """

    def __init__(self, chats: "list[Chat]", my_name: str):
        self.chats = chats
        self.my_name = my_name

    def _my_messages_by_year(self) -> dict[str, list]:
        by_year: dict[str, list] = defaultdict(list)
        for chat in self.chats:
            for m in chat.messages:
                if m.sender == self.my_name and m.text and not m.is_media:
                    year = m.timestamp.strftime("%Y")
                    by_year[year].append(m)
        return by_year

    def year_by_year(self) -> list[dict]:
        by_year = self._my_messages_by_year()
        result = []
        for year in sorted(by_year):
            msgs = by_year[year]
            texts = [m.text for m in msgs]
            words = []
            for t in texts:
                words.extend(w for w in tokenize(t) if w not in ALL_STOPWORDS and len(w) > 3)
            top_words = [w for w, _ in Counter(words).most_common(10)]
            hours = Counter(m.timestamp.hour for m in msgs)
            peak_hour = max(hours, key=hours.get) if hours else None
            night_msgs = sum(1 for m in msgs if m.timestamp.hour >= 23 or m.timestamp.hour < 5)
            result.append({
                "year": year,
                "messages_sent": len(msgs),
                "avg_length": round(sum(len(t) for t in texts) / len(texts), 1) if texts else 0,
                "vocabulary_size": len(set(words)),
                "top_words": top_words,
                "peak_hour": peak_hour,
                "nocturnality_pct": round(night_msgs / len(msgs) * 100, 1) if msgs else 0,
            })
        return result

    def most_active_days(self, top_n: int = 10) -> list[dict]:
        day_counter: Counter = Counter()
        day_chat: dict[str, str] = {}
        for chat in self.chats:
            for m in chat.messages:
                day = m.timestamp.strftime("%Y-%m-%d")
                day_counter[day] += 1
                if day not in day_chat or day_counter[day] > day_counter.get(day_chat[day], 0):
                    day_chat[day] = chat.name
        return [
            {"date": day, "messages": count, "top_chat": day_chat.get(day, "?")}
            for day, count in day_counter.most_common(top_n)
        ]

    def new_contacts_per_year(self) -> dict[str, int]:
        """How many new chats started each year."""
        by_year: Counter = Counter()
        for chat in self.chats:
            if chat.messages:
                year = chat.messages[0].timestamp.strftime("%Y")
                by_year[year] += 1
        return dict(sorted(by_year.items()))

    def summary(self) -> dict:
        return {
            "year_by_year": self.year_by_year(),
            "most_active_days": self.most_active_days(),
            "new_contacts_per_year": self.new_contacts_per_year(),
        }
