# PDF Assist

PDF Assist is a desktop PDF editor MVP built with PySide6 and PyMuPDF. It provides an Acrobat-style foundation for opening PDFs, viewing pages, navigating, zooming, rotating, applying simple annotations, and saving edited files.

## MVP Features

- Open PDF files and render pages in a central viewer
- Page navigation: next, previous, jump to page number, and thumbnail sidebar navigation
- Thumbnail sidebar with page previews, page numbers, click-to-navigate, and drag-and-drop page reordering
- Page operations:
  - Rotate current page clockwise / anticlockwise
  - Delete current page (with confirmation)
  - Insert pages from another PDF at current position or append to end
  - Move current page up or down by one position
  - Duplicate current page (inserted directly after the source page)
  - Extract current page to a separate one-page PDF
- Basic tools:
  - Select / view mode
  - Select Annotation mode (click to select an annotation on the current page, drag selected annotation to move)
  - Add text box mode (click to place text) with text font-size and text-colour controls
  - Highlight mode (drag rectangle) with highlight colour control
  - Freehand drawing mode (drag to draw) with pen colour and pen width controls
- Delete Selected Annotation action (with confirmation) for currently selected annotation
- Arrow-key nudging for selected annotations (2 PDF points per arrow key, 10 PDF points with Shift+Arrow)
- Undo/redo for page operations and annotation edits (Rotate, Delete, Insert, Move Up/Down, Duplicate, Add Text, Highlight, Freehand)
- Save As for writing edited PDFs to a new path
- Text-layer search across all pages with Find/Previous/Next navigation, result count, and non-destructive on-page overlays (active match is emphasized)
- Unsaved-change warning before opening a different PDF, closing a document, or exiting
- Password-protected PDFs can be opened by entering the correct password in a masked prompt
- User-friendly message-box error handling for common failures

## Installation

1. Ensure Python 3.10+ is installed.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Known Limitations

- This is an MVP and focuses on foundational editing workflows.
- Complex layout-aware editing of existing content is not implemented.
- Full direct editing of existing PDF text like Adobe Acrobat is complex and will be added gradually. This first version supports viewing, page operations, text insertion, highlighting, and drawing.
- Annotation placement is tied to current render scale and page rotation behavior from PyMuPDF.
- Annotation selection currently uses annotation bounds hit-testing; some tightly overlapping annotation types may require precise clicking.
- Annotation resizing is not implemented yet.
- Style controls apply to newly created annotations/content only; editing style of existing annotations is not implemented yet.
- Some third-party annotation types may not support movement safely.
- Save As is intentionally safer: saving to the exact currently-open file path is restricted for now.
- Same-path overwrite may remain limited until incremental-save handling is implemented safely.
- Search is text-layer only. Scanned/image-only PDFs typically return no matches because OCR is not implemented.
- PDF Assist does not bypass or crack PDF passwords, does not store entered passwords, and respects PDF security/permission restrictions exposed by PyMuPDF.
- Undo/redo is an in-memory snapshot MVP; very large PDFs may consume more memory.
- Undo/redo does not apply to navigation/zoom changes or extracted-page exports.

## Roadmap Ideas

- Annotation selection/move/resize controls
- Operation-specific (non-snapshot) undo/redo stack
- More advanced thumbnail organization controls beyond drag-and-drop reordering
- Better text style controls (font family, color, alignment)
- Export options and optimization presets
