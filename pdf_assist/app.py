from __future__ import annotations

import sys

import fitz
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
    QSplitter,
    QWidget,
)

from .document import PDFDocument, PDFDocumentError
from .thumbnails import ThumbnailSidebar
from .tools import ToolMode
from .viewer import PDFViewer


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF Assist")
        self.resize(1100, 800)

        self.doc = PDFDocument()
        self.viewer = PDFViewer()
        self.thumbnail_sidebar = ThumbnailSidebar()
        self.current_page = 0

        self.page_edit = QLineEdit("1")
        self.page_total_label = QLabel("/ 0")
        self.zoom_label = QLabel("100%")

        self._build_ui()
        self._wire_viewer_callbacks()
        self._update_ui_state()

    def _build_ui(self) -> None:
        splitter = QSplitter()
        splitter.addWidget(self.thumbnail_sidebar)
        splitter.addWidget(self.viewer)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 880])
        self.setCentralWidget(splitter)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        page_menu = menu.addMenu("Page")
        view_menu = menu.addMenu("View")
        tool_menu = menu.addMenu("Tools")

        tb = QToolBar("Main")
        self.addToolBar(tb)

        self.open_action = QAction("Open PDF", self)
        self.open_action.triggered.connect(self.open_pdf)
        self.save_action = QAction("Save As", self)
        self.save_action.triggered.connect(self.save_as)
        self.close_action = QAction("Close PDF", self)
        self.close_action.triggered.connect(self.close_pdf)
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.next_action = QAction("Next", self)
        self.next_action.triggered.connect(self.next_page)
        self.prev_action = QAction("Previous", self)
        self.prev_action.triggered.connect(self.prev_page)
        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action = QAction("Zoom Out", self)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.fit_width_action = QAction("Fit Width", self)
        self.fit_width_action.triggered.connect(self.fit_width)
        self.fit_page_action = QAction("Fit Page", self)
        self.fit_page_action.triggered.connect(self.fit_page)

        self.rotate_cw_action = QAction("Rotate Clockwise", self)
        self.rotate_cw_action.triggered.connect(lambda: self.rotate_page(90))
        self.rotate_ccw_action = QAction("Rotate Anticlockwise", self)
        self.rotate_ccw_action.triggered.connect(lambda: self.rotate_page(-90))
        self.delete_page_action = QAction("Delete Page", self)
        self.delete_page_action.triggered.connect(self.delete_page)
        self.insert_pages_action = QAction("Insert Pages", self)
        self.insert_pages_action.triggered.connect(self.insert_pages)
        self.move_page_up_action = QAction("Move Page Up", self)
        self.move_page_up_action.triggered.connect(self.move_page_up)
        self.move_page_down_action = QAction("Move Page Down", self)
        self.move_page_down_action.triggered.connect(self.move_page_down)
        self.duplicate_page_action = QAction("Duplicate Page", self)
        self.duplicate_page_action.triggered.connect(self.duplicate_page)
        self.extract_current_page_action = QAction("Extract Current Page", self)
        self.extract_current_page_action.triggered.connect(self.extract_current_page)

        self.tool_view_action = QAction("Select/View", self)
        self.tool_view_action.triggered.connect(lambda: self.set_tool(ToolMode.VIEW))
        self.tool_text_action = QAction("Add Text Box", self)
        self.tool_text_action.triggered.connect(lambda: self.set_tool(ToolMode.ADD_TEXT))
        self.tool_highlight_action = QAction("Highlight", self)
        self.tool_highlight_action.triggered.connect(lambda: self.set_tool(ToolMode.HIGHLIGHT))
        self.tool_draw_action = QAction("Freehand", self)
        self.tool_draw_action.triggered.connect(lambda: self.set_tool(ToolMode.FREEHAND))

        for a in [self.open_action, self.save_action, self.close_action, self.exit_action]:
            file_menu.addAction(a)
        for a in [self.prev_action, self.next_action, self.rotate_cw_action, self.rotate_ccw_action, self.delete_page_action, self.insert_pages_action, self.move_page_up_action, self.move_page_down_action, self.duplicate_page_action, self.extract_current_page_action]:
            page_menu.addAction(a)
        for a in [self.zoom_in_action, self.zoom_out_action, self.fit_width_action, self.fit_page_action]:
            view_menu.addAction(a)
        for a in [self.tool_view_action, self.tool_text_action, self.tool_highlight_action, self.tool_draw_action]:
            tool_menu.addAction(a)

        for a in [self.open_action, self.save_action, self.prev_action, self.next_action, self.zoom_in_action, self.zoom_out_action, self.fit_width_action, self.fit_page_action, self.rotate_cw_action, self.rotate_ccw_action, self.delete_page_action, self.insert_pages_action, self.move_page_up_action, self.move_page_down_action, self.duplicate_page_action, self.extract_current_page_action, self.tool_view_action, self.tool_text_action, self.tool_highlight_action, self.tool_draw_action]:
            tb.addAction(a)

        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        nav_layout.setContentsMargins(6, 4, 6, 4)
        nav_layout.addWidget(QLabel("Page:"))
        self.page_edit.setFixedWidth(60)
        self.page_edit.returnPressed.connect(self.goto_page)
        nav_layout.addWidget(self.page_edit)
        nav_layout.addWidget(self.page_total_label)
        nav_layout.addSpacing(20)
        nav_layout.addWidget(QLabel("Zoom:"))
        nav_layout.addWidget(self.zoom_label)
        nav_layout.addStretch()
        tb.addWidget(nav)

    def _wire_viewer_callbacks(self) -> None:
        self.viewer.canvas.on_add_text = self._on_add_text
        self.viewer.canvas.on_highlight = self._on_highlight
        self.viewer.canvas.on_freehand = self._on_freehand
        self.viewer.on_fit_zoom_changed = self._refresh_page
        self.thumbnail_sidebar.set_page_selected_callback(self._on_thumbnail_selected)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _refresh_page(self) -> None:
        if not self.doc.is_open:
            return
        try:
            page_width, page_height = self.doc.page_dimensions(self.current_page)
            self.viewer.set_page_size(page_width, page_height)
            rr = self.doc.render_page(self.current_page, zoom=self.viewer.zoom_factor)
            self.viewer.show_page(rr.image, rr.width, rr.height)
            self.page_total_label.setText(f"/ {self.doc.page_count}")
            self.page_edit.setText(str(self.current_page + 1))
            self.zoom_label.setText(f"{int(self.viewer.zoom_factor * 100)}%")
            self.statusBar().showMessage(f"Page {self.current_page + 1} of {self.doc.page_count}")
            self._update_current_thumbnail()
            self._update_ui_state()
        except PDFDocumentError as exc:
            self._show_error("Render Error", str(exc))

    def _refresh_thumbnails(self) -> None:
        if not self.doc.is_open:
            self.thumbnail_sidebar.clear()
            return
        thumbnails: list[tuple[bytes, int, int, int]] = []
        try:
            for page_index in range(self.doc.page_count):
                thumbnail = self.doc.render_thumbnail(page_index)
                thumbnails.append((thumbnail.image, thumbnail.width, thumbnail.height, page_index + 1))
            self.thumbnail_sidebar.set_thumbnails(thumbnails)
            self._update_current_thumbnail()
        except PDFDocumentError as exc:
            self._show_error("Thumbnail Error", str(exc))

    def _update_current_thumbnail(self) -> None:
        self.thumbnail_sidebar.set_current_page(self.current_page)

    def _on_thumbnail_selected(self, page_index: int) -> None:
        if not self.doc.is_open:
            return
        if page_index < 0 or page_index >= self.doc.page_count:
            return
        self.current_page = page_index
        self._refresh_page()

    def _update_ui_state(self) -> None:
        enabled = self.doc.is_open
        for a in [self.save_action, self.close_action, self.next_action, self.prev_action, self.zoom_in_action, self.zoom_out_action, self.fit_width_action, self.fit_page_action, self.rotate_cw_action, self.rotate_ccw_action, self.delete_page_action, self.insert_pages_action, self.tool_view_action, self.tool_text_action, self.tool_highlight_action, self.tool_draw_action]:
            a.setEnabled(enabled)
        self.duplicate_page_action.setEnabled(enabled)
        self.extract_current_page_action.setEnabled(enabled)
        self.move_page_up_action.setEnabled(enabled and self.current_page > 0)
        self.move_page_down_action.setEnabled(enabled and self.current_page < self.doc.page_count - 1)

    def open_pdf(self) -> None:
        if not self._confirm_discard_unsaved_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self.doc.open(path)
        except PDFDocumentError as exc:
            self._show_error("Open Error", str(exc))
            return
        self.current_page = 0
        self.viewer.zoom_factor = 1.0
        self._update_ui_state()
        self._refresh_thumbnails()
        self._refresh_page()

    def save_as(self) -> None:
        if not self.doc.is_open:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            self.doc.save_as(path)
            self.statusBar().showMessage(f"Saved to {path}")
        except PDFDocumentError as exc:
            self._show_error("Save Error", str(exc))

    def close_pdf(self) -> None:
        if not self._confirm_discard_unsaved_changes():
            return
        self.doc.close()
        self.current_page = 0
        self.viewer.canvas.pixmap = None
        self.viewer.canvas.update()
        self.thumbnail_sidebar.clear()
        self.page_total_label.setText("/ 0")
        self.page_edit.setText("1")
        self.statusBar().showMessage("Closed document")
        self._update_ui_state()

    def next_page(self) -> None:
        if self.current_page + 1 < self.doc.page_count:
            self.current_page += 1
            self._refresh_page()

    def prev_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self._refresh_page()

    def goto_page(self) -> None:
        if not self.doc.is_open:
            return
        try:
            page = int(self.page_edit.text()) - 1
        except ValueError:
            self._show_error("Invalid Page", "Please enter a valid page number.")
            return
        if page < 0 or page >= self.doc.page_count:
            self._show_error("Invalid Page", "Page number is out of range.")
            return
        self.current_page = page
        self._refresh_page()

    def zoom_in(self) -> None:
        self.viewer.zoom_in()
        self._refresh_page()

    def zoom_out(self) -> None:
        self.viewer.zoom_out()
        self._refresh_page()

    def fit_width(self) -> None:
        self.viewer.fit_width()
        self._refresh_page()

    def fit_page(self) -> None:
        self.viewer.fit_page()
        self._refresh_page()

    def _confirm_discard_unsaved_changes(self) -> bool:
        if not self.doc.is_open or not self.doc.is_dirty:
            return True
        result = QMessageBox.question(
            self,
            "Unsaved Changes",
            "This PDF has unsaved changes. Do you want to continue without saving?",
            QMessageBox.Yes | QMessageBox.No,
        )
        return result == QMessageBox.Yes

    def rotate_page(self, degrees: int) -> None:
        try:
            self.doc.rotate_page(self.current_page, degrees)
            self._refresh_thumbnails()
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Page Operation Error", str(exc))

    def delete_page(self) -> None:
        confirm = QMessageBox.question(self, "Delete Page", "Delete current page?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        try:
            self.doc.delete_page(self.current_page)
            self.current_page = min(self.current_page, self.doc.page_count - 1)
            self._refresh_thumbnails()
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Page Operation Error", str(exc))

    def insert_pages(self) -> None:
        source_path, _ = QFileDialog.getOpenFileName(self, "Insert PDF Pages", "", "PDF Files (*.pdf)")
        if not source_path:
            return
        choice = QMessageBox.question(self, "Insert Position", "Insert at current page? (No = append to end)", QMessageBox.Yes | QMessageBox.No)
        at_index = self.current_page if choice == QMessageBox.Yes else None
        try:
            self.doc.insert_pdf(source_path, at_index=at_index)
            self._refresh_thumbnails()
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Page Operation Error", str(exc))

    def move_page_up(self) -> None:
        if self.current_page <= 0:
            self.statusBar().showMessage("Current page is already the first page.")
            self._update_ui_state()
            return
        try:
            target_index = self.current_page - 1
            self.doc.move_page(self.current_page, target_index)
            self.current_page = target_index
            self._refresh_thumbnails()
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Page Operation Error", str(exc))

    def move_page_down(self) -> None:
        if self.current_page >= self.doc.page_count - 1:
            self.statusBar().showMessage("Current page is already the last page.")
            self._update_ui_state()
            return
        try:
            target_index = self.current_page + 1
            self.doc.move_page(self.current_page, target_index)
            self.current_page = target_index
            self._refresh_thumbnails()
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Page Operation Error", str(exc))

    def duplicate_page(self) -> None:
        try:
            self.current_page = self.doc.duplicate_page(self.current_page)
            self._refresh_thumbnails()
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Page Operation Error", str(exc))

    def extract_current_page(self) -> None:
        if not self.doc.is_open:
            return
        output_path, _ = QFileDialog.getSaveFileName(self, "Extract Current Page", "", "PDF Files (*.pdf)")
        if not output_path:
            return
        try:
            self.doc.extract_page(self.current_page, output_path)
            self.statusBar().showMessage(f"Extracted current page to {output_path}")
        except PDFDocumentError as exc:
            self._show_error("Extract Page Error", str(exc))

    def set_tool(self, mode: ToolMode) -> None:
        self.viewer.set_tool_mode(mode)
        self.statusBar().showMessage(f"Tool: {mode.value}")

    def _on_add_text(self, point) -> None:
        text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
        if not ok or not text.strip():
            return
        x, y = self.viewer.widget_to_pdf(point)
        try:
            self.doc.add_text(self.current_page, x, y, text.strip())
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Annotation Error", str(exc))

    def _on_highlight(self, rect) -> None:
        x1, y1, x2, y2 = self.viewer.rect_to_pdf(rect)
        try:
            self.doc.add_highlight_rect(self.current_page, fitz.Rect(x1, y1, x2, y2))
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Annotation Error", str(exc))

    def _on_freehand(self, points) -> None:
        pdf_points = [self.viewer.widget_to_pdf(p) for p in points]
        try:
            self.doc.add_freehand(self.current_page, pdf_points)
            self._refresh_page()
        except PDFDocumentError as exc:
            self._show_error("Annotation Error", str(exc))

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._confirm_discard_unsaved_changes():
            event.accept()
        else:
            event.ignore()


def run() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
