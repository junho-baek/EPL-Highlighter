from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChatMessage:
    source_id: str
    source_type: str
    time: str
    message: str
    author: str
