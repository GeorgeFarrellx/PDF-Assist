from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint, QPointF, Qt, QRect
from PySide6.QtGui import QAction, QImage, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QScrollArea, QWidget

from .tools import ToolMode


class PageCanvas(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMouseTracking(True)
        self.pixmap: QPixmap | None = None
        self.tool_mode = ToolMode.VIEW
        self.drag_start: QPoint | None = None
        self.drag_current: QPoint | None = None
        self.freehand_points: list[QPoint] = []
        self.on_add_text: Callable[[QPoint], None] | None = None
        self.on_highlight: Callable[[QRect], None] | None = None
        self.on_freehand: Callable[[list[QPoint]], None] | None = None

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self.pixmap = pixmap
        self.resize(pixmap.size())
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.tool_mode == ToolMode.HIGHLIGHT and self.drag_start and self.drag_current:
            painter.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))
            painter.drawRect(QRect(self.drag_start, self.drag_current).normalized())
        if self.tool_mode == ToolMode.FREEHAND and len(self.freehand_points) > 1:
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            for i in range(1, len(self.freehand_points)):
                painter.drawLine(self.freehand_points[i - 1], self.freehand_points[i])
        super().paintEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self.pixmap:
            return
        if self.tool_mode == ToolMode.ADD_TEXT and event.button() == Qt.LeftButton:
            if self.on_add_text:
                self.on_add_text(event.position().toPoint())
            return
        if self.tool_mode in (ToolMode.HIGHLIGHT, ToolMode.FREEHAND) and event.button() == Qt.LeftButton:
            self.drag_start = event.position().toPoint()
            self.drag_current = self.drag_start
            self.freehand_points = [self.drag_start]
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self.drag_start is None:
            return
        p = event.position().toPoint()
        self.drag_current = p
        if self.tool_mode == ToolMode.FREEHAND:
            self.freehand_points.append(p)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self.drag_start is None:
            return
        if self.tool_mode == ToolMode.HIGHLIGHT and self.on_highlight:
            rect = QRect(self.drag_start, event.position().toPoint()).normalized()
            if rect.width() > 2 and rect.height() > 2:
                self.on_highlight(rect)
        if self.tool_mode == ToolMode.FREEHAND and self.on_freehand:
            self.freehand_points.append(event.position().toPoint())
            self.on_freehand(self.freehand_points)
        self.drag_start = None
        self.drag_current = None
        self.freehand_points = []
        self.update()


class PDFViewer(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.canvas = PageCanvas()
        self.setWidget(self.canvas)
        self.setWidgetResizable(False)
        self.zoom_factor = 1.0
        self.fit_mode: str | None = None
        self.page_size = (0, 0)

    def set_tool_mode(self, mode: ToolMode) -> None:
        self.canvas.tool_mode = mode

    def show_page(self, image_data: bytes, width: int, height: int) -> None:
        self.page_size = (width, height)
        image = QImage.fromData(image_data)
        pixmap = QPixmap.fromImage(image)
        self.canvas.set_pixmap(pixmap)

    def zoom_in(self) -> float:
        self.fit_mode = None
        self.zoom_factor *= 1.25
        return self.zoom_factor

    def zoom_out(self) -> float:
        self.fit_mode = None
        self.zoom_factor = max(0.2, self.zoom_factor / 1.25)
        return self.zoom_factor

    def fit_width(self) -> float:
        if self.page_size[0] <= 0:
            return self.zoom_factor
        self.fit_mode = "width"
        viewport_width = max(1, self.viewport().width() - 24)
        self.zoom_factor = viewport_width / self.page_size[0]
        return self.zoom_factor

    def fit_page(self) -> float:
        w, h = self.page_size
        if w <= 0 or h <= 0:
            return self.zoom_factor
        self.fit_mode = "page"
        vw = max(1, self.viewport().width() - 24)
        vh = max(1, self.viewport().height() - 24)
        self.zoom_factor = min(vw / w, vh / h)
        return self.zoom_factor

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.fit_mode == "width":
            self.fit_width()
        elif self.fit_mode == "page":
            self.fit_page()

    def widget_to_pdf(self, point: QPoint) -> tuple[float, float]:
        return point.x() / self.zoom_factor, point.y() / self.zoom_factor

    def rect_to_pdf(self, rect: QRect) -> tuple[float, float, float, float]:
        x1, y1 = self.widget_to_pdf(rect.topLeft())
        x2, y2 = self.widget_to_pdf(rect.bottomRight())
        return x1, y1, x2, y2
