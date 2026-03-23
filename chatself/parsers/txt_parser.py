"""
Parser for WhatsApp .txt exports.

WhatsApp exports chats as .txt files with two common formats:

Android:
  [27/03/2024, 14:35:22] Alice: Hello!
  [27/03/2024, 14:35:45] Bob: Hey there

iOS:
  [27/3/24, 14:35:22] Alice: Hello!
  [27/3/24, 14:35:45] Bob: Hey there

Multi-line messages are indented or have no timestamp prefix.
Media messages appear as '<Media omitted>' or 'image omitted', etc.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator


TIMESTAMP_PATTERNS = [
    # Android: [27/03/2024, 14:35:22]
    re.compile(r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}(?::\d{2})?)\]\s"),
    # iOS: [27/3/24, 14:35:22]  (same but shorter year)
    re.compile(r"^\[(\d{1,2}/\d{1,2}/\d{2}),\s(\d{1,2}:\d{2}(?::\d{2})?)\]\s"),
    # Without brackets: 27/03/2024, 14:35 -
    re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2}(?::\d{2})?)\s-\s"),
]

MEDIA_PATTERNS = re.compile(
    r"^(<Media omitted>|image omitted|video omitted|audio omitted|"
    r"document omitted|sticker omitted|GIF omitted|Contact card omitted|"
    r"This message was deleted|You deleted this message)",
    re.IGNORECASE,
)

DATE_FORMATS = [
    "%d/%m/%Y",
    "%d/%m/%y",
    "%m/%d/%Y",
    "%m/%d/%y",
]


@dataclass
class Message:
    timestamp: datetime
    sender: str
    text: str
    is_media: bool = False
    media_type: str | None = None
    is_deleted: bool = False

    @property
    def is_from(self, name: str) -> bool:
        return self.sender.lower() == name.lower()


@dataclass
class Chat:
    name: str
    participants: list[str] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def date_range(self) -> tuple[datetime, datetime] | None:
        if not self.messages:
            return None
        return self.messages[0].timestamp, self.messages[-1].timestamp

    def messages_by(self, sender: str) -> list[Message]:
        return [m for m in self.messages if m.sender == sender]


class TxtParser:
    """Parse one or more WhatsApp .txt export files into Chat objects."""

    def parse_file(self, path: str | Path) -> Chat:
        path = Path(path)
        chat_name = path.stem
        raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        messages = list(self._parse_lines(raw_lines))
        participants = sorted({m.sender for m in messages})
        return Chat(name=chat_name, participants=participants, messages=messages)

    def parse_directory(self, directory: str | Path) -> list[Chat]:
        directory = Path(directory)
        chats = []
        for txt_file in sorted(directory.glob("*.txt")):
            try:
                chats.append(self.parse_file(txt_file))
            except Exception as e:
                print(f"Warning: could not parse {txt_file.name}: {e}")
        return chats

    def _parse_lines(self, lines: list[str]) -> Iterator[Message]:
        current_ts: datetime | None = None
        current_sender: str | None = None
        current_text_parts: list[str] = []

        for line in lines:
            parsed = self._try_parse_header(line)
            if parsed:
                if current_ts and current_sender:
                    yield self._build_message(current_ts, current_sender, current_text_parts)
                current_ts, current_sender, first_text = parsed
                current_text_parts = [first_text]
            elif current_ts:
                # Continuation of a multi-line message
                current_text_parts.append(line)

        if current_ts and current_sender:
            yield self._build_message(current_ts, current_sender, current_text_parts)

    def _try_parse_header(self, line: str) -> tuple[datetime, str, str] | None:
        for pattern in TIMESTAMP_PATTERNS:
            match = pattern.match(line)
            if match:
                date_str, time_str = match.group(1), match.group(2)
                ts = self._parse_datetime(date_str, time_str)
                if ts is None:
                    continue
                rest = line[match.end():]
                # rest is "Sender: message text" or just system message
                if ": " in rest:
                    sender, text = rest.split(": ", 1)
                else:
                    sender, text = "System", rest
                return ts, sender.strip(), text.strip()
        return None

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime | None:
        for fmt in DATE_FORMATS:
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", f"{fmt} %H:%M:%S")
                return dt
            except ValueError:
                pass
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", f"{fmt} %H:%M")
                return dt
            except ValueError:
                pass
        return None

    def _build_message(self, ts: datetime, sender: str, text_parts: list[str]) -> Message:
        text = "\n".join(text_parts).strip()
        is_media = bool(MEDIA_PATTERNS.match(text))
        is_deleted = "deleted this message" in text.lower()
        media_type = None
        if is_media:
            for mtype in ["image", "video", "audio", "sticker", "document", "GIF", "contact"]:
                if mtype.lower() in text.lower():
                    media_type = mtype.lower()
                    break
        return Message(
            timestamp=ts,
            sender=sender,
            text=text if not is_media else "",
            is_media=is_media,
            media_type=media_type,
            is_deleted=is_deleted,
        )
