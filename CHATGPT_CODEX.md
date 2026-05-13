# Codex Notes

- **Latest reference label:** PDF Assist Prompt 7
- **Current change summary:** Added MVP selected-annotation movement: drag-to-move preview overlay in Select Annotation mode, commit move on release using PDF-coordinate deltas, and arrow/Shift+arrow nudging for selected annotations. Added safe document move helper with page/xref validation and type-aware movement logic that raises clear errors when movement is unsafe.
- **Known limitations / follow-up:** Annotation hit-testing still relies on annotation rectangles and can be harder with overlaps. Annotation resizing is still not implemented. Some third-party annotation types may not support safe movement updates. Snapshot history memory trade-offs still apply for large PDFs.
- **Reminder:** Future PRs should include their reference label in PR title or PR notes.
