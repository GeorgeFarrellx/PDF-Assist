from __future__ import annotations

import ctypes
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon


APP_USER_MODEL_ID = "PDFAssist.Desktop"
ICON_SIZES = (16, 32, 48, 64, 128, 256, 512)
ICON_DIRECTORY = Path(__file__).resolve().parent / "assets" / "icons"


@lru_cache(maxsize=1)
def application_icon() -> QIcon:
    """Build the application icon from the supplied resolution-specific artwork."""
    icon = QIcon()
    for size in ICON_SIZES:
        path = ICON_DIRECTORY / f"pdf-assist-{size}.png"
        if path.is_file():
            icon.addFile(str(path), QSize(size, size))

    if icon.isNull():
        ico_path = ICON_DIRECTORY / "pdf-assist.ico"
        if ico_path.is_file():
            icon = QIcon(str(ico_path))

    return icon


def set_windows_app_user_model_id() -> None:
    """Give Windows a stable identity for taskbar icon grouping."""
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        # Older or restricted Windows environments can safely use Qt's fallback.
        pass
