"""
Emoji analysis: frequency, context, signature, evolution over time.
"""

import re
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatself.parsers.txt_parser import Chat

try:
    import emoji as emoji_lib
    HAS_EMOJI_LIB = True
except ImportError:
    HAS_EMOJI_LIB = False

# Broad Unicode emoji regex (covers most common ranges)
EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002600-\U000026FF"  # misc symbols
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess, etc.
    "\U0001FA70-\U0001FAFF"  # food, etc.
    "\U00002300-\U000023FF"  # technical
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0001F000-\U0001F02F"  # mahjong
    "\U00003030-\U00003040"  # misc CJK
    "]+",
    flags=re.UNICODE,
)


def extract_emojis(text: str) -> list[str]:
    """Extract individual emojis from text."""
    if HAS_EMOJI_LIB:
        return [e["emoji"] for e in emoji_lib.emoji_list(text)]
    # Fallback: regex-based extraction
    raw = EMOJI_RE.findall(text)
    result = []
    for chunk in raw:
        result.extend(chunk)
    return result


def emoji_name(e: str) -> str:
    """Get human-readable name for an emoji."""
    if HAS_EMOJI_LIB:
        return emoji_lib.demojize(e).strip(":")
    return e


class EmojiAnalyzer:
    def __init__(self, chat: "Chat", my_name: str):
        self.chat = chat
        self.my_name = my_name
        self.my_msgs    = [m for m in chat.messages if m.sender == my_name and m.text]
        self.their_msgs = [m for m in chat.messages if m.sender != my_name and m.text]

    def frequency(self, sender: str = "me", top_n: int = 20) -> list[dict]:
        msgs = self.my_msgs if sender == "me" else self.their_msgs
        counter: Counter = Counter()
        for m in msgs:
            counter.update(extract_emojis(m.text))
        return [
            {"emoji": e, "name": emoji_name(e), "count": c}
            for e, c in counter.most_common(top_n)
        ]

    def usage_rate(self) -> dict:
        """What % of messages contain at least one emoji."""
        def rate(msgs):
            if not msgs: return 0.0
            with_emoji = sum(1 for m in msgs if extract_emojis(m.text))
            return round(with_emoji / len(msgs) * 100, 1)
        return {
            "me": rate(self.my_msgs),
            "them": rate(self.their_msgs),
        }

    def evolution_by_year(self, top_emojis: int = 5) -> list[dict]:
        """Top emojis you used each year."""
        by_year: dict[str, Counter] = defaultdict(Counter)
        for m in self.my_msgs:
            year = m.timestamp.strftime("%Y")
            by_year[year].update(extract_emojis(m.text))
        result = []
        for year in sorted(by_year):
            top = [e for e, _ in by_year[year].most_common(top_emojis)]
            result.append({"year": year, "top": top, "total": sum(by_year[year].values())})
        return result

    def context(self, target_emoji: str, window: int = 1) -> list[dict]:
        """
        What messages come BEFORE and AFTER using a specific emoji.
        Returns samples of context around emoji usage.
        """
        samples = []
        msgs = self.chat.messages
        for i, m in enumerate(msgs):
            if m.sender == self.my_name and m.text and target_emoji in m.text:
                before = msgs[i - window].text if i >= window else None
                after  = msgs[i + window].text if i + window < len(msgs) else None
                samples.append({
                    "message": m.text,
                    "before": before,
                    "after": after,
                    "timestamp": m.timestamp.isoformat(),
                })
                if len(samples) >= 10:
                    break
        return samples

    def summary(self) -> dict:
        return {
            "my_top_emojis": self.frequency("me", 20),
            "their_top_emojis": self.frequency("them", 20),
            "usage_rate": self.usage_rate(),
            "evolution": self.evolution_by_year(),
        }
