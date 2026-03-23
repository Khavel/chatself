"""
Parser for decrypted WhatsApp SQLite database (msgstore.db).

This is the advanced path for users who have decrypted their E2E backup.
Produces the same Chat/Message objects as TxtParser for a unified API.
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from chatself.parsers.txt_parser import Chat, Message


KIND_MAP = {
    0: "text",
    1: "image",
    2: "audio",
    3: "video",
    4: "contact",
    5: "location",
    7: "url",
    9: "document",
    13: "gif",
    15: "deleted",
    16: "sticker",
}


class DbParser:
    """Parse a decrypted msgstore.db into a list of Chat objects."""

    def __init__(self, db_path: str | Path, contacts_path: str | Path | None = None):
        self.db_path = Path(db_path)
        self.contacts: dict[str, str] = {}
        if contacts_path:
            self._load_contacts(Path(contacts_path))

    def _load_contacts(self, path: Path) -> None:
        import json
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = json.load(f)
        for c in raw:
            jid = c.get("jid", "")
            name = c.get("name", "")
            if jid and name:
                self.contacts[jid] = name

    def _jid_to_name(self, jid: str) -> str:
        return self.contacts.get(jid, jid.split("@")[0] if jid else "Unknown")

    def parse(self) -> list[Chat]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        chats = self._load_chats(conn)
        conn.close()
        return chats

    def _load_chats(self, conn: sqlite3.Connection) -> list[Chat]:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT j.raw_string AS jid, j.display_name AS display_name
            FROM jid j
            WHERE j.raw_string IS NOT NULL
            ORDER BY j.raw_string
        """)
        jid_rows = cursor.fetchall()

        chats = []
        for row in jid_rows:
            jid = row["jid"]
            display = row["display_name"] or self._jid_to_name(jid)
            messages = self._load_messages(conn, jid)
            if not messages:
                continue
            participants = sorted({m.sender for m in messages})
            chats.append(Chat(name=display, participants=participants, messages=messages))

        return chats

    def _load_messages(self, conn: sqlite3.Connection, jid: str) -> list[Message]:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT
                    m.timestamp,
                    m.from_me,
                    m.data AS text,
                    m.message_type,
                    j.raw_string AS sender_jid
                FROM message m
                JOIN jid j ON j.raw_string = ?
                WHERE m.key_remote_jid = ?
                ORDER BY m.timestamp ASC
            """, (jid, jid))
        except sqlite3.OperationalError:
            return []

        messages = []
        for row in cursor.fetchall():
            ts = datetime.fromtimestamp(row["timestamp"] / 1000)
            from_me = bool(row["from_me"])
            sender = "Me" if from_me else self._jid_to_name(jid)
            kind = KIND_MAP.get(row["message_type"], "unknown")
            is_media = kind not in ("text", "url", "deleted", "unknown")
            messages.append(Message(
                timestamp=ts,
                sender=sender,
                text=row["text"] or "",
                is_media=is_media,
                media_type=kind if is_media else None,
                is_deleted=(kind == "deleted"),
            ))

        return messages
