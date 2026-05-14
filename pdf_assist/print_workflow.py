from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
)

from .print_file_utils import (
    default_output_path,
    filter_supported_files,
    get_supported_files_from_client_folder,
    get_supported_files_from_folder,
)
from .print_pdf_builder import build_print_preview_pdf


class PreviewWorker(QThread):
    progress = Signal(int, int, str)
    finished_ok = Signal(str, list, list)
    failed = Signal(str)

    def __init__(self, files: list[Path], preview_path: Path) -> None:
        super().__init__()
        self.files = files
        self.preview_path = preview_path

    def run(self) -> None:
        try:
            processed, warnings = build_print_preview_pdf(self.files, self.preview_path, self.progress.emit)
            self.finished_ok.emit(str(self.preview_path), [str(p) for p in processed], warnings)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class PrintAssistBuilderDialog(QDialog):
    def __init__(self, parent=None, open_pdf_callback=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Print Assist Builder")
        self.resize(900, 550)
        self.open_pdf_callback = open_pdf_callback
        self.files: list[Path] = []
        self.preview_pdf_path: Path | None = None
        self.temp_dir_ctx = None
        self.preview_opened_in_pdf_assist = False
        self.worker: PreviewWorker | None = None
        self.output_path = default_output_path()
        self._build_ui()
        self._refresh_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.file_list)

        self.file_count_label = QLabel("Selected files: 0")
        self.output_label = QLabel(f"Output: {self.output_path}")
        self.status_label = QLabel("Ready")
        layout.addWidget(self.file_count_label)
        layout.addWidget(self.output_label)

        grid = QGridLayout()
        buttons = [
            ("Add Files", self.add_files),
            ("Add Folder", self.add_folder),
            ("Add Client Folder", self.add_client_folder),
            ("Remove Selected", self.remove_selected),
            ("Move Up", self.move_up),
            ("Move Down", self.move_down),
            ("Clear", self.clear_all),
            ("Choose Output", self.choose_output),
            ("Create Preview PDF", self.create_preview),
            ("Save Final PDF", self.save_final_pdf),
            ("Print Preview PDF", self.print_preview_pdf),
            ("Open Preview in PDF Assist", self.open_preview_in_pdf_assist),
            ("Open Preview Externally", self.open_preview_externally),
            ("Open Output Folder", self.open_output_folder),
            ("Close", self.close),
        ]
        self.action_buttons: list[QPushButton] = []
        for idx, (text, handler) in enumerate(buttons):
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            grid.addWidget(btn, idx // 3, idx % 3)
            self.action_buttons.append(btn)

        layout.addLayout(grid)
        bottom = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        bottom.addWidget(self.progress)
        bottom.addWidget(self.status_label)
        layout.addLayout(bottom)

    def _refresh_ui(self) -> None:
        self.file_count_label.setText(f"Selected files: {len(self.files)}")
        self.output_label.setText(f"Output: {self.output_path}")

    def _append_files(self, candidates: list[Path]) -> None:
        existing = {p.resolve() for p in self.files}
        for path in candidates:
            resolved = path.resolve()
            if resolved not in existing:
                self.files.append(path)
                item = QListWidgetItem(str(path))
                self.file_list.addItem(item)
                existing.add(resolved)
        self._refresh_ui()

    def add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Files")
        if not paths:
            return
        supported, unsupported = filter_supported_files([Path(p) for p in paths])
        self._append_files(supported)
        if unsupported:
            QMessageBox.warning(self, "Unsupported Files", f"Skipped unsupported files: {len(unsupported)}")

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Add Folder")
        if not folder:
            return
        supported, unsupported = get_supported_files_from_folder(folder)
        self._append_files(supported)
        if unsupported:
            QMessageBox.warning(self, "Unsupported Files", f"Skipped unsupported files: {len(unsupported)}")

    def add_client_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Add Client Folder")
        if not folder:
            return
        supported, unsupported = get_supported_files_from_client_folder(folder)
        self._append_files(supported)
        if unsupported:
            QMessageBox.warning(self, "Unsupported Files", f"Skipped unsupported files: {len(unsupported)}")

    def remove_selected(self) -> None:
        rows = sorted({self.file_list.row(item) for item in self.file_list.selectedItems()}, reverse=True)
        for row in rows:
            self.file_list.takeItem(row)
            self.files.pop(row)
        self._refresh_ui()

    def move_up(self) -> None:
        row = self.file_list.currentRow()
        if row > 0:
            self.files[row - 1], self.files[row] = self.files[row], self.files[row - 1]
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row - 1, item)
            self.file_list.setCurrentRow(row - 1)

    def move_down(self) -> None:
        row = self.file_list.currentRow()
        if 0 <= row < self.file_list.count() - 1:
            self.files[row + 1], self.files[row] = self.files[row], self.files[row + 1]
            item = self.file_list.takeItem(row)
            self.file_list.insertItem(row + 1, item)
            self.file_list.setCurrentRow(row + 1)

    def clear_all(self) -> None:
        self.files.clear()
        self.file_list.clear()
        self._refresh_ui()

    def choose_output(self) -> None:
        chosen, _ = QFileDialog.getSaveFileName(self, "Choose Output", str(self.output_path), "PDF Files (*.pdf)")
        if chosen:
            self.output_path = Path(chosen)
            self._refresh_ui()

    def _set_busy(self, busy: bool) -> None:
        for btn in self.action_buttons:
            if btn.text() != "Close":
                btn.setEnabled(not busy)
        if busy:
            self.status_label.setText("Generating preview...")

    def create_preview(self) -> None:
        if not self.files:
            QMessageBox.information(self, "No Files", "Add at least one supported file.")
            return
        if self.temp_dir_ctx is None:
            self.temp_dir_ctx = tempfile.TemporaryDirectory(prefix="pdf_assist_preview_")
        self.preview_pdf_path = Path(self.temp_dir_ctx.name) / "preview.pdf"
        self.preview_opened_in_pdf_assist = False
        self._set_busy(True)
        self.progress.setValue(0)
        self.worker = PreviewWorker(self.files, self.preview_pdf_path)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_preview_ok)
        self.worker.failed.connect(self._on_preview_failed)
        self.worker.start()

    def _on_progress(self, current: int, total: int, message: str) -> None:
        pct = int((current / max(1, total)) * 100)
        self.progress.setValue(pct)
        self.status_label.setText(message)

    def _on_preview_ok(self, preview_path: str, processed: list[str], warnings: list[str]) -> None:
        self._set_busy(False)
        self.progress.setValue(100)
        self.status_label.setText(f"Preview ready. Processed {len(processed)} files.")
        if warnings:
            QMessageBox.warning(self, "Preview Warnings", "\n".join(warnings))
        QMessageBox.information(self, "Preview Created", f"Preview PDF created:\n{preview_path}")

    def _on_preview_failed(self, message: str) -> None:
        self._set_busy(False)
        self.progress.setValue(0)
        self.status_label.setText("Preview failed.")
        QMessageBox.critical(self, "Preview Error", message)

    def save_final_pdf(self) -> None:
        if not self.preview_pdf_path or not self.preview_pdf_path.exists():
            QMessageBox.information(self, "No Preview", "Create Preview PDF before saving final output.")
            return
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.preview_pdf_path, self.output_path)
            self.status_label.setText("Final PDF saved from preview.")
            QMessageBox.information(self, "Saved", f"Saved final PDF to:\n{self.output_path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save Error", str(exc))

    def print_preview_pdf(self) -> None:
        if not self.preview_pdf_path or not self.preview_pdf_path.exists():
            QMessageBox.information(self, "No Preview", "Create Preview PDF before printing.")
            return
        if os.name == "nt":
            try:
                os.startfile(str(self.preview_pdf_path), "print")  # type: ignore[attr-defined]
                self.status_label.setText("Sent preview PDF to default print handling.")
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Print Error", f"Unable to print preview PDF: {exc}")
        else:
            QMessageBox.information(
                self,
                "Printing Not Supported",
                "Print Preview PDF uses Windows/default PDF print handling and is only supported on Windows.",
            )

    def open_preview_in_pdf_assist(self) -> None:
        if not self.preview_pdf_path or not self.preview_pdf_path.exists():
            QMessageBox.information(self, "No Preview", "Create Preview PDF before opening it.")
            return
        if self.open_pdf_callback is None:
            QMessageBox.information(self, "Unavailable", "Open Preview in PDF Assist is not available.")
            return
        ok = self.open_pdf_callback(self.preview_pdf_path)
        if ok:
            self.preview_opened_in_pdf_assist = True
            self.status_label.setText("Opened preview in PDF Assist.")

    def open_preview_externally(self) -> None:
        if not self.preview_pdf_path or not self.preview_pdf_path.exists():
            QMessageBox.information(self, "No Preview", "Create Preview PDF before opening it.")
            return
        try:
            if os.name == "nt":
                os.startfile(str(self.preview_pdf_path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.preview_pdf_path)])
            else:
                subprocess.Popen(["xdg-open", str(self.preview_pdf_path)])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Open Error", str(exc))

    def open_output_folder(self) -> None:
        folder = self.output_path.parent
        try:
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Open Folder Error", str(exc))

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.worker and self.worker.isRunning():
            self.worker.wait(2000)
        if self.preview_opened_in_pdf_assist:
            event.accept()
            return
        if self.temp_dir_ctx is not None:
            self.temp_dir_ctx.cleanup()
            self.temp_dir_ctx = None
        event.accept()
