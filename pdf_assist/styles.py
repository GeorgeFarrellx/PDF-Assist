from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextStyle:
    font_size: float = 14.0
    color: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass
class HighlightStyle:
    color: tuple[float, float, float] = (1.0, 1.0, 0.0)
    opacity: float = 0.35


@dataclass
class FreehandStyle:
    color: tuple[float, float, float] = (1.0, 0.0, 0.0)
    width: float = 2.0


@dataclass
class ToolStyles:
    text: TextStyle = field(default_factory=TextStyle)
    highlight: HighlightStyle = field(default_factory=HighlightStyle)
    freehand: FreehandStyle = field(default_factory=FreehandStyle)
