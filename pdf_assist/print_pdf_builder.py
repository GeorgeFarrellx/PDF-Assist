from __future__ import annotations

import tempfile
from pathlib import Path

import fitz

from .print_office_converter import (
    EXCEL_EXTENSIONS,
    MSG_EXTENSIONS,
    WORD_EXTENSIONS,
    OfficeConversionError,
    convert_office_or_msg_to_pdf,
)

A4_PORTRAIT = fitz.paper_rect("a4")
A4_LANDSCAPE = fitz.Rect(0, 0, A4_PORTRAIT.height, A4_PORTRAIT.width)


def _target_rect(width: float, height: float) -> fitz.Rect:
    if width > height:
        return A4_LANDSCAPE
    return A4_PORTRAIT


def _fit_rect(src_w: float, src_h: float, dst: fitz.Rect, margin: float = 20.0) -> fitz.Rect:
    avail_w = max(1.0, dst.width - 2 * margin)
    avail_h = max(1.0, dst.height - 2 * margin)
    scale = min(avail_w / src_w, avail_h / src_h)
    w = src_w * scale
    h = src_h * scale
    x0 = dst.x0 + (dst.width - w) / 2
    y0 = dst.y0 + (dst.height - h) / 2
    return fitz.Rect(x0, y0, x0 + w, y0 + h)


def build_print_preview_pdf(
    files: list[Path],
    output_path: Path,
    progress_callback=None,
) -> tuple[list[Path], list[str]]:
    processed: list[Path] = []
    warnings: list[str] = []

    with tempfile.TemporaryDirectory(prefix="pdf_assist_print_") as temp_dir:
        temp_path = Path(temp_dir)
        out_doc = fitz.open()
        total = max(1, len(files))

        for index, source_path in enumerate(files, start=1):
            source = Path(source_path)
            ext = source.suffix.lower()
            if progress_callback:
                progress_callback(index - 1, total, f"Processing {source.name} ({index}/{total})")

            try:
                current_source = source
                if ext in WORD_EXTENSIONS or ext in EXCEL_EXTENSIONS or ext in MSG_EXTENSIONS:
                    converted = temp_path / f"{source.stem}_{index}.pdf"
                    current_source = convert_office_or_msg_to_pdf(source, converted)
                    ext = ".pdf"

                if ext == ".pdf":
                    with fitz.open(current_source) as src_doc:
                        for page in src_doc:
                            rect = page.rect
                            dst_page_rect = _target_rect(rect.width, rect.height)
                            out_page = out_doc.new_page(width=dst_page_rect.width, height=dst_page_rect.height)
                            target = _fit_rect(rect.width, rect.height, out_page.rect)
                            out_page.show_pdf_page(target, src_doc, page.number)
                else:
                    with fitz.open(current_source) as img_doc:
                        page = img_doc[0]
                        rect = page.rect
                        dst_page_rect = _target_rect(rect.width, rect.height)
                        out_page = out_doc.new_page(width=dst_page_rect.width, height=dst_page_rect.height)
                        target = _fit_rect(rect.width, rect.height, out_page.rect)
                        out_page.show_pdf_page(target, img_doc, 0)

                processed.append(source)
            except OfficeConversionError as exc:
                warnings.append(str(exc))
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Failed to process '{source.name}': {exc}")

        if not processed:
            out_doc.close()
            raise RuntimeError("No input files could be processed into a preview PDF.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        out_doc.save(output_path)
        out_doc.close()

    if progress_callback:
        progress_callback(total, total, "Preview PDF created.")
    return processed, warnings
