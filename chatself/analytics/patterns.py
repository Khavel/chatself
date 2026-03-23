"""
Pattern analysis: activity hours, response times, message ratios.
"""

import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatself.parsers.txt_parser import Chat, Message


class PatternAnalyzer:
    def __init__(self, chat: "Chat", my_name: str):
        self.chat = chat
        self.my_name = my_name
        self.my_msgs   = [m for m in chat.messages if m.sender == my_name and not m.is_media]
        self.their_msgs = [m for m in chat.messages if m.sender != my_name and not m.is_media]

    def message_ratio(self) -> float:
        """How many messages you send per message they send."""
        if not self.their_msgs:
            return float("inf")
        return len(self.my_msgs) / len(self.their_msgs)

    def activity_by_hour(self) -> dict[int, int]:
        counter = Counter(m.timestamp.hour for m in self.chat.messages)
        return dict(sorted(counter.items()))

    def activity_by_weekday(self) -> dict[str, int]:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        counter = Counter(m.timestamp.weekday() for m in self.chat.messages)
        return {days[k]: v for k, v in sorted(counter.items())}

    def response_times(self) -> dict[str, dict]:
        """
        Returns median and mean response time (minutes) for each participant.
        Only considers replies within 2 hours (to avoid counting multi-day gaps).
        """
        gaps: dict[str, list[float]] = defaultdict(list)
        prev = None
        for m in self.chat.messages:
            if prev and prev.sender != m.sender:
                gap_min = (m.timestamp - prev.timestamp).total_seconds() / 60
                if 0.1 < gap_min < 120:
                    gaps[m.sender].append(gap_min)
            prev = m

        result = {}
        for sender, times in gaps.items():
            if times:
                result[sender] = {
                    "median_min": round(statistics.median(times), 1),
                    "mean_min": round(statistics.mean(times), 1),
                    "sample_size": len(times),
                }
        return result

    def who_initiates(self, gap_hours: int = 4) -> dict[str, int]:
        """Count conversation starts (messages after a gap of gap_hours) per sender."""
        initiations: Counter = Counter()
        prev_ts = None
        for m in self.chat.messages:
            if prev_ts is None or (m.timestamp - prev_ts).total_seconds() > gap_hours * 3600:
                initiations[m.sender] += 1
            prev_ts = m.timestamp
        return dict(initiations)

    def monthly_ratio(self) -> list[dict]:
        """Message ratio (you/them) per month."""
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
            result.append({
                "month": month,
                "mine": mine,
                "theirs": theirs,
                "ratio": round(mine / theirs, 2) if theirs else None,
                "total": mine + theirs,
            })
        return result

    def summary(self) -> dict:
        return {
            "total_messages": len(self.chat.messages),
            "my_messages": len(self.my_msgs),
            "their_messages": len(self.their_msgs),
            "message_ratio": round(self.message_ratio(), 2),
            "date_range": {
                "first": self.chat.messages[0].timestamp.isoformat() if self.chat.messages else None,
                "last": self.chat.messages[-1].timestamp.isoformat() if self.chat.messages else None,
            },
            "who_initiates": self.who_initiates(),
            "response_times": self.response_times(),
            "peak_hour": max(self.activity_by_hour(), key=lambda h: self.activity_by_hour()[h]) if self.chat.messages else None,
        }
