from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatModel:
    time: datetime | str
    message: str
    author: str