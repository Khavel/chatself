"""
Relationship dynamics: balance, asymmetry, affection markers, drift.
"""

import re
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatself.parsers.txt_parser import Chat, Message

AFFECTION_PATTERNS = {
    "es": re.compile(
        r"\b(te quiero|te echo de menos|me gustas|te deseo|guapo|guapa|"
        r"eres muy|me encantas|me alegra|me mola|te necesito|te pienso|"
        r"contigo para siempre|eres todo|lo nuestro)\b",
        re.IGNORECASE,
    ),
    "en": re.compile(
        r"\b(i love you|i miss you|you're beautiful|you're cute|"
        r"i need you|thinking of you|you mean|i adore)\b",
        re.IGNORECASE,
    ),
}


class RelationshipAnalyzer:
    def __init__(self, chat: "Chat", my_name: str, lang: str = "es"):
        self.chat = chat
        self.my_name = my_name
        self.lang = lang
        self.my_msgs    = [m for m in chat.messages if m.sender == my_name]
        self.their_msgs = [m for m in chat.messages if m.sender != my_name]
        self._affection_re = AFFECTION_PATTERNS.get(lang, AFFECTION_PATTERNS["es"])

    def affection_score(self) -> dict[str, dict]:
        """
        Count and percentage of messages containing affection markers, per sender.
        """
        result = {}
        for label, msgs in [("me", self.my_msgs), ("them", self.their_msgs)]:
            text_msgs = [m for m in msgs if m.text]
            matches = [m for m in text_msgs if self._affection_re.search(m.text)]
            result[label] = {
                "count": len(matches),
                "pct": round(len(matches) / len(text_msgs) * 100, 1) if text_msgs else 0,
                "examples": [m.text[:100] for m in matches[:5]],
            }
        return result

    def drift_over_time(self) -> list[dict]:
        """
        Show how message ratio shifts month by month.
        Returns list of {month, my_pct, their_pct, balance} where balance > 0 means you send more.
        """
        by_month: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for m in self.chat.messages:
            key = m.timestamp.strftime("%Y-%m")
            if m.sender == self.my_name:
                by_month[key][0] += 1
            else:
                by_month[key][1] += 1

        result = []
        for month in sorted(by_month):
            mine, theirs = by_month[month]
            total = mine + theirs
            if total == 0:
                continue
            my_pct = round(mine / total * 100, 1)
            result.append({
                "month": month,
                "total": total,
                "mine": mine,
                "theirs": theirs,
                "my_pct": my_pct,
                "balance": round(my_pct - 50, 1),  # positive = you send more
            })
        return result

    def silence_gaps(self, min_days: int = 3) -> list[dict]:
        """Detect periods of silence (gaps > min_days between messages)."""
        gaps = []
        prev_ts = None
        for m in self.chat.messages:
            if prev_ts:
                gap_days = (m.timestamp - prev_ts).days
                if gap_days >= min_days:
                    gaps.append({
                        "from": prev_ts.strftime("%Y-%m-%d"),
                        "to": m.timestamp.strftime("%Y-%m-%d"),
                        "days": gap_days,
                        "resumed_by": m.sender,
                    })
            prev_ts = m.timestamp
        return sorted(gaps, key=lambda g: g["days"], reverse=True)

    def who_ends_conversations(self, gap_hours: int = 4) -> dict[str, int]:
        """Who sends the last message before a long gap."""
        enders: Counter = Counter()
        prev = None
        for m in self.chat.messages:
            if prev and (m.timestamp - prev.timestamp).total_seconds() > gap_hours * 3600:
                enders[prev.sender] += 1
            prev = m
        if prev:
            enders[prev.sender] += 1
        return dict(enders)

    def summary(self) -> dict:
        return {
            "affection": self.affection_score(),
            "drift": self.drift_over_time(),
            "silence_gaps": self.silence_gaps()[:10],
            "who_ends_conversations": self.who_ends_conversations(),
        }
