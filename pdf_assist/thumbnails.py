from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class ReorderableThumbnailListWidget(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self._drag_source_row: int | None = None
        self.on_pages_reordered: Callable[[int, int], None] | None = None

    def startDrag(self, supportedActions) -> None:  # noqa: N802
        self._drag_source_row = self.currentRow()
        super().startDrag(supportedActions)

    def dropEvent(self, event) -> None:  # noqa: N802
        source_row = self._drag_source_row
        super().dropEvent(event)
        self._drag_source_row = None
        if source_row is None:
            return
        target_row = self.currentRow()
        if target_row < 0:
            return
        if self.on_pages_reordered:
            self.on_pages_reordered(source_row, target_row)


class ThumbnailSidebar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._on_page_selected: Callable[[int], None] | None = None
        self._on_pages_reordered: Callable[[int, int], None] | None = None

        self.list_widget = ReorderableThumbnailListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setFlow(QListWidget.TopToBottom)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setMovement(QListWidget.Snap)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setUniformItemSizes(False)
        self.list_widget.setSpacing(8)
        self.list_widget.setIconSize(QSize(120, 170))
        self.list_widget.setWordWrap(True)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.itemClicked.connect(self._handle_item_clicked)
        self.list_widget.on_pages_reordered = self._handle_pages_reordered

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.list_widget)

    def set_page_selected_callback(self, callback: Callable[[int], None] | None) -> None:
        self._on_page_selected = callback

    def set_pages_reordered_callback(self, callback: Callable[[int, int], None] | None) -> None:
        self._on_pages_reordered = callback

    def set_thumbnails(self, thumbnails: list[tuple[bytes, int, int, int]]) -> None:
        self.list_widget.clear()
        for image_data, width, height, page_number in thumbnails:
            image = QImage.fromData(image_data)
            pixmap = QPixmap.fromImage(image)
            item = QListWidgetItem(str(page_number))
            item.setIcon(QIcon(pixmap))
            item.setTextAlignment(Qt.AlignHCenter)
            item.setData(Qt.UserRole, page_number - 1)
            if width and height:
                item.setSizeHint(QSize(max(130, width + 10), max(170, height + 26)))
            self.list_widget.addItem(item)

    def set_current_page(self, page_index: int) -> None:
        if page_index < 0 or page_index >= self.list_widget.count():
            self.list_widget.clearSelection()
            return
        item = self.list_widget.item(page_index)
        self.list_widget.setCurrentItem(item)
        self.list_widget.scrollToItem(item)

    def clear(self) -> None:
        self.list_widget.clear()

    def _handle_item_clicked(self, item: QListWidgetItem) -> None:
        if not self._on_page_selected:
            return
        page_index = int(item.data(Qt.UserRole))
        self._on_page_selected(page_index)

    def _handle_pages_reordered(self, source_page_index: int, target_page_index: int) -> None:
        if not self._on_pages_reordered:
            return
        self._on_pages_reordered(source_page_index, target_page_index)
