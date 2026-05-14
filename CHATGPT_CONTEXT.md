# PDF Assist Project Context

- **Project name:** PDF Assist
- **Repo:** GeorgeFarrellx/PDF-Assist
- **Branch:** main
- **Purpose:** Desktop PDF viewer/editor with Acrobat-style foundations.
- **Current stack:** Python, PySide6, PyMuPDF

## Important Files (Raw GitHub Links)

- [README.md](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/README.md)
- [requirements.txt](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/requirements.txt)
- [main.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/main.py)
- [pdf_assist/__init__.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/__init__.py)
- [pdf_assist/app.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/app.py)
- [pdf_assist/search.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/search.py)
- [pdf_assist/document.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/document.py)
- [pdf_assist/viewer.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/viewer.py)
- [pdf_assist/thumbnails.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/thumbnails.py)
- [pdf_assist/tools.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/tools.py)
- [pdf_assist/styles.py](https://raw.githubusercontent.com/GeorgeFarrellx/PDF-Assist/main/pdf_assist/styles.py)

## Current Implemented Capabilities

- Launch desktop app with `python main.py`.
- Open and render PDF files.
- Navigate pages (next/previous/go to page).
- Zoom in/out and fit width/page.
- Rotate, delete, insert, move up/down, and duplicate pages.
- Add text, highlight rectangles, and freehand drawing annotations.
- Style controls for newly inserted text, highlight annotations, and freehand drawing (newly created content only).
- Select existing annotations and delete only the selected annotation with confirmation.
- Move selected annotations by dragging the selection overlay or by arrow-key nudging.
- Undo/redo for page operations and annotation edits.
- Save edited output with Save As.
- Extract current page to a separate one-page PDF without modifying the open document.
- Thumbnail sidebar for page previews, click-to-navigate page selection, and drag-and-drop page reordering.
- Text-layer PDF search across all pages with result navigation (previous/next), result count, and non-destructive search overlays on the current page.
- Password-protected PDFs can be opened with a user-entered password prompt.

## Known Limitations

- MVP scope only; direct editing of existing PDF text is not implemented.
- No OCR functionality.
- Thumbnail drag-and-drop reorder updates the document page order and uses the same undo/redo snapshot model as other page edits.
- Undo/redo uses in-memory PDF snapshots; very large PDFs may use more memory.
- PDF permissions/security restrictions are respected; PDF Assist does not bypass passwords or crack encrypted files.
- Same-path Save As overwrite is currently restricted for safety until incremental-save handling is added safely.

## Safety Rules

- Do not silently corrupt or flatten PDFs.
- Do not add OCR unless explicitly requested.
- Do not bypass PDF security/password protection.
- Prefer Save As/exported copies unless overwrite is explicitly chosen.
- Preserve PDF fidelity where possible.
- Call out any change that may affect rendering, annotations, page order, forms, metadata, bookmarks, links, signatures, save/export, or file integrity.
