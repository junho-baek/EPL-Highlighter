from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChatModel:
    source_id: str
    source_type: str
    time: datetime | str
    message: str
    author: str
    interval_start_time: datetime
    interval_end_time: datetime