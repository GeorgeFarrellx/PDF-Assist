from __future__ import annotations

from datetime import datetime
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tif",
    ".tiff",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".xlsm",
    ".xlsb",
    ".msg",
}

ATTACHMENT_FOLDER_NAMES = {"attachments", "attachment", "email attachments"}


def filter_supported_files(paths: list[str | Path]) -> tuple[list[Path], list[Path]]:
    supported: list[Path] = []
    unsupported: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            supported.append(path)
        else:
            unsupported.append(path)
    return supported, unsupported


def get_supported_files_from_folder(folder_path: str | Path) -> tuple[list[Path], list[Path]]:
    folder = Path(folder_path)
    if not folder.is_dir():
        return [], [folder]
    direct_files = [p for p in sorted(folder.iterdir()) if p.is_file()]
    return filter_supported_files(direct_files)


def get_supported_files_from_client_folder(folder_path: str | Path) -> tuple[list[Path], list[Path]]:
    folder = Path(folder_path)
    if not folder.is_dir():
        return [], [folder]

    candidates: list[Path] = [p for p in sorted(folder.iterdir()) if p.is_file()]
    for child in sorted(folder.iterdir()):
        if child.is_dir() and child.name.lower() in ATTACHMENT_FOLDER_NAMES:
            candidates.extend(p for p in sorted(child.iterdir()) if p.is_file())

    return filter_supported_files(candidates)


def default_output_path(base_dir: str | Path | None = None) -> Path:
    target_dir = Path(base_dir) if base_dir else Path.home() / "Documents"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return target_dir / f"PDF Assist Print - {timestamp}.pdf"
