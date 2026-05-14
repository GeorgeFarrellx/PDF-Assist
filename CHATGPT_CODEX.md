# Codex Notes

- **Latest reference label:** PDF Assist Print Assist Integration Prompt 1
- **Current change summary:** Added a native PySide6 Print Assist Builder workflow inside PDF Assist, including mixed-file intake, client-folder import rules, background preview generation, exact-preview Save Final PDF copy flow, Windows/default print handling, and callback loading of preview PDFs into the existing viewer.
- **Known limitations / follow-up:** Office/Outlook conversion for DOC/DOCX/XLS*/MSG requires Windows + pywin32 + Microsoft Office/Outlook and is not available cross-platform. Direct print uses Windows/default PDF print handling only. Drag-and-drop into the Print Assist Builder was deferred in this integration.
- **Reminder:** Future PRs should include their reference label in PR title or PR notes.
