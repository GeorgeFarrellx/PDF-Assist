from enum import Enum


class ToolMode(str, Enum):
    VIEW = "view"
    SELECT_ANNOTATION = "select_annotation"
    ADD_TEXT = "add_text"
    HIGHLIGHT = "highlight"
    FREEHAND = "freehand"
