# Codex Notes

- **Latest reference label:** PDF Assist Prompt 9
- **Current change summary:** Completed Prompt 8 follow-up fixes by adding `pdf_assist/search.py` to `CHATGPT_CONTEXT.md` and clearing search state during redo.
- **Known limitations / follow-up:** Search is text-layer only (no OCR for scanned/image PDFs). Case/advanced search options (match case, whole word) are not yet implemented. Annotation hit-testing still relies on annotation rectangles and can be harder with overlaps. Snapshot history memory trade-offs still apply for large PDFs.
- **Reminder:** Future PRs should include their reference label in PR title or PR notes.
