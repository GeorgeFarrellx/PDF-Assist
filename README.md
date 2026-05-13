# PDF Assist

PDF Assist is a desktop PDF editor MVP built with PySide6 and PyMuPDF. It provides an Acrobat-style foundation for opening PDFs, viewing pages, navigating, zooming, rotating, applying simple annotations, and saving edited files.

## MVP Features

- Open PDF files and render pages in a central viewer
- Page navigation: next, previous, jump to page number, and thumbnail sidebar navigation
- Thumbnail sidebar with page previews and page numbers
- Page operations:
  - Rotate current page clockwise / anticlockwise
  - Delete current page (with confirmation)
  - Insert pages from another PDF at current position or append to end
  - Move current page up or down by one position
  - Duplicate current page (inserted directly after the source page)
  - Extract current page to a separate one-page PDF
- Basic tools:
  - Select / view mode
  - Add text box mode (click to place text)
  - Highlight mode (drag rectangle)
  - Freehand drawing mode (drag to draw)
- Undo/redo for page operations and annotation edits (Rotate, Delete, Insert, Move Up/Down, Duplicate, Add Text, Highlight, Freehand)
- Save As for writing edited PDFs to a new path
- Unsaved-change warning before opening a different PDF, closing a document, or exiting
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
- Save As is intentionally safer: saving to the exact currently-open file path is restricted for now.
- Same-path overwrite may remain limited until incremental-save handling is implemented safely.
- Undo/redo is an in-memory snapshot MVP; very large PDFs may consume more memory.
- Undo/redo does not apply to navigation/zoom changes or extracted-page exports.

## Roadmap Ideas

- Annotation selection/move/resize controls
- Operation-specific (non-snapshot) undo/redo stack
- Password prompt for encrypted PDFs
- Drag-and-drop page reordering from thumbnails (future enhancement; not implemented yet and sidebar remains navigation-only)
- Better text style controls (font family, color, alignment)
- Export options and optimization presets
