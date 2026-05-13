# Codex Notes

- **Latest reference label:** PDF Assist Prompt 5
- **Current change summary:** Added conservative snapshot-based undo/redo for destructive page operations and annotation edits. Introduced an Edit menu with Undo/Redo actions (toolbar + shortcuts), in-memory PDF history stacks, safe document byte snapshot/restore methods, and undo/redo UI enablement tied to stack availability.
- **Known limitations / follow-up:** Snapshot history keeps whole-document bytes in memory and can grow costly for very large PDFs; consider operation-specific undo commands in a future prompt. Drag-and-drop page reordering and direct editing of existing PDF text remain out of scope.
- **Reminder:** Future PRs should include their reference label in PR title or PR notes.
