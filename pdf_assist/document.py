from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import fitz


class PDFDocumentError(Exception):
    pass


@dataclass
class RenderResult:
    image: bytes
    width: int
    height: int


class PDFDocument:
    def __init__(self) -> None:
        self.doc: fitz.Document | None = None
        self.path: str | None = None

    @property
    def is_open(self) -> bool:
        return self.doc is not None

    @property
    def page_count(self) -> int:
        return self.doc.page_count if self.doc else 0

    def open(self, path: str) -> None:
        try:
            doc = fitz.open(path)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to open PDF: {exc}") from exc
        if doc.needs_pass:
            doc.close()
            raise PDFDocumentError("This PDF is encrypted or password protected.")
        self.close()
        self.doc = doc
        self.path = path

    def close(self) -> None:
        if self.doc:
            self.doc.close()
        self.doc = None
        self.path = None

    def save_as(self, path: str) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            self.doc.save(path)
        except Exception:
            try:
                self.doc.save(path, incremental=False, garbage=4, deflate=True)
            except Exception as exc:  # noqa: BLE001
                raise PDFDocumentError(f"Failed to save PDF: {exc}") from exc

    def render_page(self, page_index: int, zoom: float = 1.0, rotation: int = 0) -> RenderResult:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return RenderResult(image=pix.tobytes("ppm"), width=pix.width, height=pix.height)

    def rotate_page(self, page_index: int, degrees: int) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        page.set_rotation((page.rotation + degrees) % 360)

    def delete_page(self, page_index: int) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        if self.doc.page_count <= 1:
            raise PDFDocumentError("Cannot delete the only page in the document.")
        self.doc.delete_page(page_index)

    def insert_pdf(self, source_path: str, at_index: int | None = None) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            src = fitz.open(source_path)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to open source PDF: {exc}") from exc
        if src.needs_pass:
            src.close()
            raise PDFDocumentError("Source PDF is encrypted or password protected.")
        try:
            start_at = self.doc.page_count if at_index is None else at_index
            self.doc.insert_pdf(src, start_at=start_at)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to insert pages: {exc}") from exc
        finally:
            src.close()

    def add_text(self, page_index: int, x: float, y: float, text: str, font_size: float = 14) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        page.insert_text((x, y), text, fontsize=font_size, color=(0, 0, 0))

    def add_highlight_rect(self, page_index: int, rect: fitz.Rect) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        annot = page.add_rect_annot(rect)
        annot.set_colors(stroke=(1, 1, 0), fill=(1, 1, 0))
        annot.set_opacity(0.35)
        annot.update()

    def add_freehand(self, page_index: int, points: Iterable[tuple[float, float]]) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        pts = list(points)
        if len(pts) < 2:
            return
        page = self.doc.load_page(page_index)
        annot = page.add_ink_annot([pts])
        annot.set_colors(stroke=(1, 0, 0))
        annot.set_border(width=2)
        annot.update()
