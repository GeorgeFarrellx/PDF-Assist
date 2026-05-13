from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HistoryEntry:
    pdf_bytes: bytes
    page_index: int
    action_label: str = ""


class PDFHistory:
    def __init__(self, max_depth: int = 20) -> None:
        self.max_depth = max(1, max_depth)
        self._undo: list[HistoryEntry] = []
        self._redo: list[HistoryEntry] = []

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def push_undo(self, entry: HistoryEntry) -> None:
        self._undo.append(entry)
        if len(self._undo) > self.max_depth:
            self._undo = self._undo[-self.max_depth :]

    def pop_undo(self) -> HistoryEntry | None:
        if not self._undo:
            return None
        return self._undo.pop()

    def push_redo(self, entry: HistoryEntry) -> None:
        self._redo.append(entry)
        if len(self._redo) > self.max_depth:
            self._redo = self._redo[-self.max_depth :]

    def pop_redo(self) -> HistoryEntry | None:
        if not self._redo:
            return None
        return self._redo.pop()

    def clear_redo(self) -> None:
        self._redo.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)
