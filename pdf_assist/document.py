from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import fitz
from .search import SearchResult


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

    def open(self, path: str, password: str | None = None) -> None:
        try:
            doc = fitz.open(path)
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to open PDF: {exc}") from exc

        try:
            if doc.needs_pass:
                if password is None:
                    raise PDFDocumentError("PASSWORD_REQUIRED")
                if not doc.authenticate(password):
                    raise PDFDocumentError("Incorrect password. Please try again.")
                if doc.needs_pass:
                    raise PDFDocumentError("Failed to authenticate PDF with the provided password.")

            self.close()
            self.doc = doc
            self.path = path
            self._dirty = False
        except Exception:
            doc.close()
            raise

    def close(self) -> None:
        if self.doc:
            self.doc.close()
        self.doc = None
        self.path = None
        self._dirty = False

    def to_bytes(self) -> bytes:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            return self.doc.tobytes()
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to snapshot PDF: {exc}") from exc

    def restore_from_bytes(self, data: bytes) -> None:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            restored = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to restore PDF snapshot: {exc}") from exc
        if restored.needs_pass:
            restored.close()
            raise PDFDocumentError("Restored PDF snapshot is encrypted or password protected.")
        self.doc.close()
        self.doc = restored
        self._dirty = True

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

    def search_text(self, query: str) -> list[SearchResult]:
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        term = query.strip()
        if not term:
            return []
        results: list[SearchResult] = []
        try:
            for page_index in range(self.doc.page_count):
                page = self.doc.load_page(page_index)
                for rect in page.search_for(term):
                    results.append(
                        SearchResult(
                            page_index=page_index,
                            rect=(rect.x0, rect.y0, rect.x1, rect.y1),
                        )
                    )
            return results
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to search PDF text: {exc}") from exc

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

    def find_annotation_at_point(self, page_index: int, x: float, y: float) -> int | None:
        self._validate_page_index(page_index)
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            page = self.doc.load_page(page_index)
            point = fitz.Point(x, y)
            for annot in page.annots() or []:
                if annot.rect.contains(point):
                    return annot.xref
            return None
        except PDFDocumentError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to find annotation: {exc}") from exc

    def get_annotation_rect(self, page_index: int, annotation_id: int) -> fitz.Rect:
        self._validate_page_index(page_index)
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            page = self.doc.load_page(page_index)
            for annot in page.annots() or []:
                if annot.xref == annotation_id:
                    return fitz.Rect(annot.rect)
            raise PDFDocumentError("Selected annotation no longer exists on this page.")
        except PDFDocumentError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to read annotation bounds: {exc}") from exc

    def move_annotation(self, page_index: int, annotation_id: int, dx: float, dy: float) -> fitz.Rect:
        self._validate_page_index(page_index)
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            page = self.doc.load_page(page_index)
            for annot in page.annots() or []:
                if annot.xref != annotation_id:
                    continue
                rect = annot.rect
                new_rect = fitz.Rect(rect.x0 + dx, rect.y0 + dy, rect.x1 + dx, rect.y1 + dy)
                if annot.type[0] == fitz.PDF_ANNOT_INK:
                    vertices = list(annot.vertices or [])
                    if not vertices:
                        raise PDFDocumentError("Cannot move this ink annotation safely.")
                    moved_vertices = [
                        [fitz.Point(point.x + dx, point.y + dy) for point in stroke]
                        for stroke in vertices
                    ]
                    annot.set_vertices(moved_vertices)
                elif annot.type[0] in (
                    fitz.PDF_ANNOT_HIGHLIGHT,
                    fitz.PDF_ANNOT_UNDERLINE,
                    fitz.PDF_ANNOT_STRIKE_OUT,
                    fitz.PDF_ANNOT_SQUIGGLY,
                ):
                    quads = list(annot.vertices or [])
                    if not quads:
                        raise PDFDocumentError("Cannot move this text-markup annotation safely.")
                    moved_quads = [fitz.Point(point.x + dx, point.y + dy) for point in quads]
                    annot.set_vertices(moved_quads)
                else:
                    annot.set_rect(new_rect)
                annot.update()
                self._dirty = True
                return annot.rect
            raise PDFDocumentError("Selected annotation was not found on this page.")
        except PDFDocumentError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to move annotation: {exc}") from exc

    def delete_annotation(self, page_index: int, annotation_id: int) -> None:
        self._validate_page_index(page_index)
        if not self.doc:
            raise PDFDocumentError("No document loaded.")
        try:
            page = self.doc.load_page(page_index)
            deleted = False
            for annot in page.annots() or []:
                if annot.xref == annotation_id:
                    page.delete_annot(annot)
                    deleted = True
                    break
            if not deleted:
                raise PDFDocumentError("Selected annotation no longer exists on this page.")
            self._dirty = True
        except PDFDocumentError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PDFDocumentError(f"Failed to delete selected annotation: {exc}") from exc
