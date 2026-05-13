# Codex Notes

- **Latest reference label:** PDF Assist Prompt 6
- **Current change summary:** Added MVP annotation selection/deletion workflow: new Select Annotation tool mode, selected-annotation overlay, and Delete Selected Annotation action with explicit confirmation. Selection is page-scoped and cleared on navigation/open-close/structural changes/undo-redo. Added safe document helpers to find, inspect, and delete only one selected annotation by xref with clear errors.
- **Known limitations / follow-up:** Annotation hit-testing currently relies on annotation rectangles and may require precision for overlapping/tight annotations. Moving/resizing annotations is still not implemented. Snapshot history memory trade-offs still apply for large PDFs.
- **Reminder:** Future PRs should include their reference label in PR title or PR notes.
