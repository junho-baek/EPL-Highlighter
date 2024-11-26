from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ChatMessage:
    source_id: str
    source_type: str
    time: str
    author: str
    message: str

    def to_dict(self):
        return {
            'source_id': self.source_id,
            'source_type': self.source_type,
            'time': self.time,
            'author': self.author,
            'message': self.message
        }
