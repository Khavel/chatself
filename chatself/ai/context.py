"""
Build a compact, privacy-safe context string from analyzer summaries.

RAW MESSAGES NEVER LEAVE YOUR MACHINE.
Only pre-computed statistics and aggregates are passed to the LLM.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatself.analytics.patterns import PatternAnalyzer
    from chatself.analytics.vocabulary import VocabularyAnalyzer
    from chatself.analytics.relationships import RelationshipAnalyzer
    from chatself.analytics.emojis import EmojiAnalyzer


def build_context(
    chat_name: str,
    my_name: str,
    patterns: "PatternAnalyzer",
    vocab: "VocabularyAnalyzer",
    relations: "RelationshipAnalyzer",
    emojis: "EmojiAnalyzer | None" = None,
) -> str:
    """Return a structured text summary suitable for LLM system context."""
    p = patterns.summary()
    v = vocab.summary()
    r = relations.summary()

    them = _other(chat_name, my_name)
    dr = patterns.chat.date_range
    period = (
        f"{dr[0].strftime('%B %Y')} → {dr[1].strftime('%B %Y')}"
        if dr else "unknown period"
    )

    lines: list[str] = [
        "=== CHATSELF ANALYSIS CONTEXT ===",
        f"You are helping the user reflect on their WhatsApp conversation with '{them}'.",
        f"The user's name in the chat: {my_name}",
        f"Period covered: {period}",
        "",
        "--- COMMUNICATION PATTERNS ---",
        f"Total messages: {p['total_messages']}  (you: {p['my_messages']}, them: {p['their_messages']})",
        f"Message ratio (you/them): {p['message_ratio']}",
        f"Peak activity hour: {p['peak_hour']}:00",
        f"Who typically initiates conversations: {p.get('initiator', 'unknown')}",
    ]

    for sender, rt in p.get("response_times", {}).items():
        label = "you" if sender == my_name else "them"
        lines.append(f"Median response time ({label}): {rt['median_min']} min")

    lines += [
        "",
        "--- YOUR VOCABULARY ---",
        f"Messages sent: {v['total_sent']}",
        f"Average message length: {v['avg_length']} characters",
        f"Vocabulary size: {v['vocabulary_size']} unique words",
    ]

    top_words = [w for w, _ in v.get("top_words", [])[:20]]
    if top_words:
        lines.append(f"Top words you use: {', '.join(top_words)}")

    tics = [phrase for phrase, _ in v.get("verbal_tics", [])[:10]]
    if tics:
        lines.append(f"Verbal tics / recurring phrases: {', '.join(tics)}")

    bigrams = [phrase for phrase, _ in v.get("top_bigrams", [])[:10]]
    if bigrams:
        lines.append(f"Frequent two-word expressions: {', '.join(bigrams)}")

    aff = r.get("affection", {})
    me_pct  = aff.get("me",   {}).get("pct", 0)
    them_pct = aff.get("them", {}).get("pct", 0)
    lines += [
        "",
        "--- EMOTIONAL DYNAMICS ---",
        f"Affection markers in your messages: {me_pct}%",
        f"Affection markers in their messages: {them_pct}%",
    ]

    drift = r.get("drift", [])
    if drift:
        early = drift[:3]
        late  = drift[-3:]
        lines.append(
            f"Message ratio early in relationship: {[d['ratio'] for d in early]}"
        )
        lines.append(
            f"Message ratio recently: {[d['ratio'] for d in late]}"
        )

    gaps = r.get("silence_gaps", [])[:5]
    if gaps:
        lines.append(f"Notable silences (days without messages): {[g['days'] for g in gaps]}")
        lines.append(f"Longest silence: {gaps[0]['days']} days, resumed by {gaps[0]['resumed_by']}")

    if emojis:
        e = emojis.summary()
        top_emojis = [emoji for emoji, _ in e.get("top_emojis", [])[:10]]
        if top_emojis:
            lines += [
                "",
                "--- EMOJI SIGNATURE ---",
                f"Your most used emojis: {' '.join(top_emojis)}",
                f"Emoji usage rate: {e.get('usage_rate_pct', 0)}% of messages contain emoji",
            ]

    lines += [
        "",
        "--- INSTRUCTIONS FOR THE AI ---",
        "Answer questions about this conversation thoughtfully and empathetically.",
        "Focus on patterns, not individual messages.",
        "You don't have access to the actual messages — only the statistics above.",
        "When asked about feelings or dynamics, reason from the data provided.",
        "Be honest, nuanced, and avoid projecting assumptions not supported by the data.",
        "Respond in the same language the user writes in.",
    ]

    return "\n".join(lines)


def _other(chat_name: str, my_name: str) -> str:
    """Best-effort: extract the other person's name from the chat filename."""
    # WhatsApp exports are typically named "Chat with X.txt" or just "X.txt"
    name = chat_name
    for prefix in ("Chat with ", "Chat de ", "WhatsApp Chat with "):
        if name.lower().startswith(prefix.lower()):
            name = name[len(prefix):]
    if name.lower() == my_name.lower():
        return "the other person"
    return name
