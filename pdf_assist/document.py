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
        self._dirty = False

    @property
    def is_open(self) -> bool:
        return self.doc is not None

    @property
    def page_count(self) -> int:
        return self.doc.page_count if self.doc else 0

    @property
    def is_dirty(self) -> bool:
        return self._dirty

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
        self._dirty = False

    def close(self) -> None:
        if self.doc:
            self.doc.close()
        self.doc = None
        self.path = None
        self._dirty = False

    def save_as(self, path: str) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        if self.path and path == self.path:
            raise PDFDocumentError(
                "Saving to the currently opened file path is not supported safely yet. "
                "Please choose a different output file path."
            )
        try:
            self.doc.save(path)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to save PDF: {exc}") from exc
        self._dirty = False

    def page_dimensions(self, page_index: int) -> tuple[float, float]:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        rect = page.rect
        return rect.width, rect.height

    def render_page(self, page_index: int, zoom: float = 1.0, rotation: int = 0) -> RenderResult:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return RenderResult(image=pix.tobytes("ppm"), width=pix.width, height=pix.height)

    def render_thumbnail(self, page_index: int, max_width: int = 140) -> RenderResult:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        if max_width <= 0:
            raise PDFDocumentError("Thumbnail width must be greater than zero.")
        try:
            page = self.doc.load_page(page_index)
            rect = page.rect
            if rect.width <= 0 or rect.height <= 0:
                raise PDFDocumentError("Page has invalid dimensions for thumbnail rendering.")
            scale = max_width / rect.width
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            return RenderResult(image=pix.tobytes("ppm"), width=pix.width, height=pix.height)
        except PDFDocumentError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to render thumbnail for page {page_index + 1}: {exc}") from exc

    def rotate_page(self, page_index: int, degrees: int) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        page.set_rotation((page.rotation + degrees) % 360)
        self._dirty = True

    def delete_page(self, page_index: int) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        if self.doc.page_count <= 1:
            raise PDFDocumentError("Cannot delete the only page in the document.")
        self.doc.delete_page(page_index)
        self._dirty = True

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
            self._dirty = True
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to insert pages: {exc}") from exc
        finally:
            src.close()


    def _validate_page_index(self, page_index: int) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        if page_index < 0 or page_index >= self.doc.page_count:
            raise PDFDocumentError(f"Page index out of range: {page_index + 1}.")

    def move_page(self, page_index: int, target_index: int) -> None:
        self._validate_page_index(page_index)
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        if target_index < 0 or target_index >= self.doc.page_count:
            raise PDFDocumentError(f"Target page index out of range: {target_index + 1}.")
        if page_index == target_index:
            return
        try:
            self.doc.move_page(page_index, target_index)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to move page: {exc}") from exc
        self._dirty = True

    def duplicate_page(self, page_index: int) -> int:
        self._validate_page_index(page_index)
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            self.doc.fullcopy_page(page_index, page_index)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to duplicate page: {exc}") from exc
        self._dirty = True
        return page_index + 1

    def extract_page(self, page_index: int, output_path: str) -> None:
        self._validate_page_index(page_index)
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        out_doc = fitz.open()
        try:
            out_doc.insert_pdf(self.doc, from_page=page_index, to_page=page_index)
            out_doc.save(output_path)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to extract current page: {exc}") from exc
        finally:
            out_doc.close()

    def add_text(self, page_index: int, x: float, y: float, text: str, font_size: float = 14) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        page.insert_text((x, y), text, fontsize=font_size, color=(0, 0, 0))
        self._dirty = True

    def add_highlight_rect(self, page_index: int, rect: fitz.Rect) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        page = self.doc.load_page(page_index)
        annot = page.add_rect_annot(rect)
        annot.set_colors(stroke=(1, 1, 0), fill=(1, 1, 0))
        annot.set_opacity(0.35)
        annot.update()
        self._dirty = True

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
        self._dirty = True
