"""Conversation memory utilities."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, List


@dataclass
class Message:
    role: str
    content: str


class ShortTermMemory:
    def __init__(self, max_turns: int = 20) -> None:
        self._messages: Dict[str, Deque[Message]] = defaultdict(lambda: deque(maxlen=max_turns))

    def add(self, session_id: str, role: str, content: str) -> None:
        self._messages[session_id].append(Message(role=role, content=content))

    def get(self, session_id: str) -> List[str]:
        return [f"{msg.role}: {msg.content}" for msg in self._messages.get(session_id, [])]


class LongTermMemory:
    def __init__(self) -> None:
        self._success_patterns: Dict[str, Deque[str]] = defaultdict(lambda: deque(maxlen=50))

    def record(self, user_id: str, sql_query: str) -> None:
        self._success_patterns[user_id].append(sql_query)

    def recall(self, user_id: str) -> Iterable[str]:
        return list(self._success_patterns.get(user_id, []))


class MemoryManager:
    def __init__(self) -> None:
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    def capture_turn(self, session_id: str, role: str, message: str) -> None:
        if not session_id:
            return
        self.short_term.add(session_id, role, message)

    def recall_short_term(self, session_id: str) -> List[str]:
        if not session_id:
            return []
        return self.short_term.get(session_id)

    def record_success(self, user_id: str, sql: str) -> None:
        self.long_term.record(user_id, sql)

    def recall_long_term(self, user_id: str) -> Iterable[str]:
        return self.long_term.recall(user_id)
