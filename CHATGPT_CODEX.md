# Codex Notes

- **Latest reference label:** PDF Assist Prompt 8
- **Current change summary:** Added read-only text-layer PDF search: Find/Ctrl+F UI, previous/next wrapped navigation, result counts, and non-destructive search overlays that emphasize the active match on the current page. Search state is cleared on document/page-structure changes and undo/redo to keep state safe and predictable.
- **Known limitations / follow-up:** Search is text-layer only (no OCR for scanned/image PDFs). Case/advanced search options (match case, whole word) are not yet implemented. Annotation hit-testing still relies on annotation rectangles and can be harder with overlaps. Snapshot history memory trade-offs still apply for large PDFs.
- **Reminder:** Future PRs should include their reference label in PR title or PR notes.
