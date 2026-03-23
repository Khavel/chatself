"""Tests for the WhatsApp .txt parser."""

from datetime import datetime
from textwrap import dedent

import pytest
from chatself.parsers.txt_parser import TxtParser, Chat, Message


ANDROID_SAMPLE = dedent("""\
    [27/03/2024, 14:35:22] Alice: Hello!
    [27/03/2024, 14:36:01] Bob: Hey there
    [27/03/2024, 14:36:15] Alice: How are you doing?
    This is a continuation of the previous message.
    [27/03/2024, 14:37:00] Bob: <Media omitted>
    [27/03/2024, 14:37:30] Bob: I'm good thanks
""")

IOS_SAMPLE = dedent("""\
    [27/3/24, 14:35:22] Alice: Hello!
    [27/3/24, 14:36:01] Bob: Hey there
    [27/3/24, 14:37:00] Bob: image omitted
""")


def parse_string(content: str) -> Chat:
    import tempfile, os
    parser = TxtParser()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp = f.name
    try:
        return parser.parse_file(tmp)
    finally:
        os.unlink(tmp)


def test_android_format_basic():
    chat = parse_string(ANDROID_SAMPLE)
    assert len(chat.messages) == 5
    assert "Alice" in chat.participants
    assert "Bob" in chat.participants


def test_multiline_message():
    chat = parse_string(ANDROID_SAMPLE)
    alice_msgs = [m for m in chat.messages if m.sender == "Alice"]
    long_msg = next(m for m in alice_msgs if "continuation" in m.text)
    assert "continuation" in long_msg.text


def test_media_detection():
    chat = parse_string(ANDROID_SAMPLE)
    media_msgs = [m for m in chat.messages if m.is_media]
    assert len(media_msgs) == 1


def test_ios_format():
    chat = parse_string(IOS_SAMPLE)
    assert len(chat.messages) == 3


def test_timestamp_parsing():
    chat = parse_string(ANDROID_SAMPLE)
    first = chat.messages[0]
    assert first.timestamp == datetime(2024, 3, 27, 14, 35, 22)
    assert first.sender == "Alice"
    assert first.text == "Hello!"


def test_participants():
    chat = parse_string(ANDROID_SAMPLE)
    assert set(chat.participants) == {"Alice", "Bob"}


def test_date_range():
    chat = parse_string(ANDROID_SAMPLE)
    dr = chat.date_range
    assert dr is not None
    assert dr[0] < dr[1]
