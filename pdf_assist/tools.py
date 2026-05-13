from enum import Enum


class ToolMode(str, Enum):
    VIEW = "view"
    ADD_TEXT = "add_text"
    HIGHLIGHT = "highlight"
    FREEHAND = "freehand"
