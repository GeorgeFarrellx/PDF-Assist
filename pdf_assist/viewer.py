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
        self.on_select_annotation: Callable[[QPoint], None] | None = None
        self.on_highlight: Callable[[QRect], None] | None = None
        self.on_freehand: Callable[[list[QPoint]], None] | None = None
        self.selected_annotation_rect: QRect | None = None
        self.search_result_rects: list[QRect] = []
        self.active_search_result_index: int | None = None
        self.on_selected_annotation_move_started: Callable[[], None] | None = None
        self.on_selected_annotation_move_finished: Callable[[int, int], None] | None = None
        self._selected_drag_active = False
        self._selected_drag_start: QPoint | None = None
        self._selected_drag_origin: QRect | None = None

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
        if self.selected_annotation_rect:
            painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
            painter.drawRect(self.selected_annotation_rect)
        for index, rect in enumerate(self.search_result_rects):
            is_active = self.active_search_result_index == index
            if is_active:
                painter.setPen(QPen(Qt.darkRed, 3, Qt.SolidLine))
                painter.fillRect(rect, Qt.yellow)
            else:
                painter.setPen(QPen(Qt.darkYellow, 1, Qt.SolidLine))
                painter.fillRect(rect, Qt.yellow)
            painter.drawRect(rect)
        super().paintEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self.pixmap:
            return
        if self.tool_mode == ToolMode.ADD_TEXT and event.button() == Qt.LeftButton:
            if self.on_add_text:
                self.on_add_text(event.position().toPoint())
            return
        if self.tool_mode == ToolMode.SELECT_ANNOTATION and event.button() == Qt.LeftButton:
            if self.on_select_annotation:
                self.on_select_annotation(event.position().toPoint())
            if self.selected_annotation_rect and self.selected_annotation_rect.contains(event.position().toPoint()):
                self._selected_drag_active = True
                self._selected_drag_start = event.position().toPoint()
                self._selected_drag_origin = QRect(self.selected_annotation_rect)
                if self.on_selected_annotation_move_started:
                    self.on_selected_annotation_move_started()
            return
        if self.tool_mode in (ToolMode.HIGHLIGHT, ToolMode.FREEHAND) and event.button() == Qt.LeftButton:
            self.drag_start = event.position().toPoint()
            self.drag_current = self.drag_start
            self.freehand_points = [self.drag_start]
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._selected_drag_active and self._selected_drag_start and self._selected_drag_origin:
            current_point = event.position().toPoint()
            delta = current_point - self._selected_drag_start
            self.selected_annotation_rect = self._selected_drag_origin.translated(delta)
            self.update()
            return
        if self.drag_start is None:
            return
        p = event.position().toPoint()
        self.drag_current = p
        if self.tool_mode == ToolMode.FREEHAND:
            self.freehand_points.append(p)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._selected_drag_active:
            if self.on_selected_annotation_move_finished and self._selected_drag_start:
                end_point = event.position().toPoint()
                delta = end_point - self._selected_drag_start
                self.on_selected_annotation_move_finished(delta.x(), delta.y())
            self._selected_drag_active = False
            self._selected_drag_start = None
            self._selected_drag_origin = None
            return
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
        self.page_size = (0.0, 0.0)
        self.on_fit_zoom_changed: Callable[[], None] | None = None

    def set_tool_mode(self, mode: ToolMode) -> None:
        self.canvas.tool_mode = mode

    def show_page(self, image_data: bytes, width: int, height: int) -> None:
        image = QImage.fromData(image_data)
        pixmap = QPixmap.fromImage(image)
        self.canvas.set_pixmap(pixmap)

    def set_selected_annotation_rect_pdf(self, rect: tuple[float, float, float, float] | None) -> None:
        if rect is None:
            self.canvas.selected_annotation_rect = None
            self.canvas.update()
            return
        x1, y1, x2, y2 = rect
        self.canvas.selected_annotation_rect = QRect(
            int(round(x1 * self.zoom_factor)),
            int(round(y1 * self.zoom_factor)),
            int(round((x2 - x1) * self.zoom_factor)),
            int(round((y2 - y1) * self.zoom_factor)),
        ).normalized()
        self.canvas.update()

    def set_page_size(self, width: float, height: float) -> None:
        self.page_size = (width, height)

    def set_search_overlays_pdf(
        self,
        rects: list[tuple[float, float, float, float]],
        active_rect_index: int | None = None,
    ) -> None:
        self.canvas.search_result_rects = [
            QRect(
                int(round(x1 * self.zoom_factor)),
                int(round(y1 * self.zoom_factor)),
                int(round((x2 - x1) * self.zoom_factor)),
                int(round((y2 - y1) * self.zoom_factor)),
            ).normalized()
            for x1, y1, x2, y2 in rects
        ]
        self.canvas.active_search_result_index = active_rect_index
        self.canvas.update()

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
        changed = False
        if self.fit_mode == "width":
            self.fit_width()
            changed = True
        elif self.fit_mode == "page":
            self.fit_page()
            changed = True
        if changed and self.on_fit_zoom_changed:
            self.on_fit_zoom_changed()

    def widget_to_pdf(self, point: QPoint) -> tuple[float, float]:
        return point.x() / self.zoom_factor, point.y() / self.zoom_factor

    def rect_to_pdf(self, rect: QRect) -> tuple[float, float, float, float]:
        x1, y1 = self.widget_to_pdf(rect.topLeft())
        x2, y2 = self.widget_to_pdf(rect.bottomRight())
        return x1, y1, x2, y2
