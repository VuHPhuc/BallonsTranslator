from __future__ import annotations

import datetime
import math
import os
import os.path as osp
import time
from typing import List, Optional

from qtpy.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from qtpy.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QMovie,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
    QShowEvent,
)
from qtpy.QtWidgets import (
    QAbstractButton,
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ballontranslator.ui.framelesswindow import (
    DialogCloseButton,
    OutsideClickFramelessMixin,
)
from ballontranslator.utils import shared
from ballontranslator.utils.config import pcfg
from ballontranslator.utils.folder_history import (
    FolderHistoryItem,
    FolderHistoryManager,
)


def format_relative_time(timestamp: float) -> str:
    """Return a human-friendly relative time string in Vietnamese."""
    if timestamp <= 0:
        return 'Chưa mở'
    diff = time.time() - timestamp
    if diff < 60:
        return 'Vừa xong'
    if diff < 3600:
        return f'{int(diff // 60)} phút trước'
    if diff < 86400:
        return f'{int(diff // 3600)} giờ trước'
    if diff < 86400 * 2:
        return 'Hôm qua'
    if diff < 86400 * 7:
        return f'{int(diff // 86400)} ngày trước'
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime('%d/%m/%Y %H:%M')


class AppBrandLogo(QWidget):
    """Fallback custom-rendered vector brand logo (replaces emojis)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(130, 130)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        render_hint = getattr(QPainter, 'RenderHint', QPainter).Antialiasing
        painter.setRenderHint(render_hint)

        # Background rounded rect with rich modern gradient
        bg_grad = QLinearGradient(0, 0, 130, 130)
        bg_grad.setColorAt(0.0, QColor('#3B82F6'))
        bg_grad.setColorAt(0.5, QColor('#2563EB'))
        bg_grad.setColorAt(1.0, QColor('#1D4ED8'))

        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.5))
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(QRectF(2, 2, 126, 126), 24, 24)

        # Draw stylish Manga book & translation icon inside
        book_path = QPainterPath()
        # Left page
        book_path.moveTo(32, 45)
        book_path.cubicTo(45, 38, 55, 40, 65, 46)
        book_path.lineTo(65, 85)
        book_path.cubicTo(55, 79, 45, 77, 32, 84)
        book_path.closeSubpath()

        # Right page
        book_path.moveTo(65, 46)
        book_path.cubicTo(75, 40, 85, 38, 98, 45)
        book_path.lineTo(98, 84)
        book_path.cubicTo(85, 77, 75, 79, 65, 85)
        book_path.closeSubpath()

        painter.setPen(QPen(QColor('#FFFFFF'), 3.0))
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.drawPath(book_path)

        # Draw mini speech bubble / translation sparkle on top right
        sparkle = QPainterPath()
        cx, cy = 92, 38
        r_out, r_in = 11.0, 4.5
        for i in range(8):
            ang = i * math.pi / 4.0 - math.pi / 2.0
            r = r_out if (i % 2 == 0) else r_in
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            if i == 0:
                sparkle.moveTo(x, y)
            else:
                sparkle.lineTo(x, y)
        sparkle.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor('#FDE047')))
        painter.drawPath(sparkle)


class VectorStarButton(QAbstractButton):
    """Vector-rendered star button with radiant gold gradient and scale pulse on hover."""

    toggled_star = Signal(bool)

    def __init__(self, starred: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(starred)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scale = 1.0
        self.update_tooltip()

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self.update_tooltip()
        self.update()

    def update_tooltip(self) -> None:
        if self.isChecked():
            self.setToolTip(
                self.tr('⭐ Đã gắn sao bảo vệ!\nThư mục này sẽ KHÔNG bao giờ bị xóa khi dọn dẹp lịch sử.\n(Bấm để bỏ gắn sao)')
            )
        else:
            self.setToolTip(
                self.tr('☆ Chưa gắn sao\nBấm để gắn sao ⭐ bảo vệ thư mục này khỏi bị xóa khi dọn dẹp lịch sử.')
            )

    def enterEvent(self, event: QEvent) -> None:
        self._scale = 1.18
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._scale = 1.0
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            new_val = not self.isChecked()
            self.setChecked(new_val)
            self.toggled_star.emit(new_val)
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        render_hint = getattr(QPainter, 'RenderHint', QPainter).Antialiasing
        painter.setRenderHint(render_hint)

        cx = self.width() / 2.0
        cy = self.height() / 2.0

        is_starred = self.isChecked()
        is_hovered = self.underMouse()

        outer_r = 12.0 * self._scale
        inner_r = outer_r * 0.44

        path = QPainterPath()
        points = 5
        for i in range(points * 2):
            angle = i * math.pi / points - math.pi / 2.0
            r = outer_r if (i % 2 == 0) else inner_r
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()

        if is_starred:
            # Soft radial glow around the star
            glow_grad = QRadialGradient(cx, cy, outer_r * 1.5)
            glow_grad.setColorAt(0.0, QColor(245, 158, 11, 110 if is_hovered else 65))
            glow_grad.setColorAt(1.0, QColor(245, 158, 11, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_grad))
            painter.drawEllipse(QPointF(cx, cy), outer_r * 1.45, outer_r * 1.45)

            # Luminous amber/gold gradient
            gradient = QLinearGradient(0, cy - outer_r, 0, cy + outer_r)
            gradient.setColorAt(0.0, QColor('#FDE047'))
            gradient.setColorAt(0.5, QColor('#F59E0B'))
            gradient.setColorAt(1.0, QColor('#D97706'))

            painter.setPen(QPen(QColor('#FEF08A'), 1.2))
            painter.setBrush(QBrush(gradient))
            painter.drawPath(path)
        else:
            if is_hovered:
                painter.setPen(QPen(QColor('#F59E0B'), 1.6))
                painter.setBrush(QColor(245, 158, 11, 35))
            else:
                color = QColor('#64748B') if pcfg.darkmode else QColor('#94A3B8')
                painter.setPen(QPen(color, 1.4))
                painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.drawPath(path)


class VectorDeleteButton(QAbstractButton):
    """Clean modern delete button that lights up red on hover."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(self.tr('Xóa thư mục này khỏi lịch sử'))

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        render_hint = getattr(QPainter, 'RenderHint', QPainter).Antialiasing
        painter.setRenderHint(render_hint)

        hovered = self.underMouse()
        if hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(239, 68, 68, 35))
            painter.drawRoundedRect(self.rect(), 8, 8)
            pen_color = QColor('#EF4444')
        else:
            pen_color = QColor('#6E7681') if pcfg.darkmode else QColor('#94A3B8')

        pen = QPen(pen_color, 1.6)
        pen.setCapStyle(getattr(getattr(Qt, 'PenCapStyle', Qt), 'RoundCap'))
        painter.setPen(pen)
        inset = 10.0
        end = self.width() - inset
        painter.drawLine(QPointF(inset, inset), QPointF(end, end))
        painter.drawLine(QPointF(end, inset), QPointF(inset, end))


class FolderCardItemWidget(QFrame):
    """A premium card representing a single comic project in the history."""

    folder_clicked = Signal(str)
    star_toggled = Signal(str, bool)
    item_deleted = Signal(str)

    def __init__(self, item: FolderHistoryItem, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.item = item
        self.setObjectName('FolderCardItemWidget')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(78)

        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(14, 10, 14, 10)
        card_layout.setSpacing(14)

        wa_transparent = getattr(getattr(Qt, 'WidgetAttribute', Qt), 'WA_TransparentForMouseEvents')

        # Left: Cover thumbnail or stylized icon
        self.cover_label = QLabel(self)
        self.cover_label.setFixedSize(56, 56)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setObjectName('FolderCoverLabel')
        self.cover_label.setAttribute(wa_transparent, True)
        self._load_cover()
        card_layout.addWidget(self.cover_label)

        # Middle: Texts
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.title_lbl = QLabel(item.name, self)
        self.title_lbl.setObjectName('CardFolderTitle')
        self.title_lbl.setAttribute(wa_transparent, True)
        f_title = self.title_lbl.font()
        f_title.setPointSize(11)
        f_title.setBold(True)
        self.title_lbl.setFont(f_title)
        title_row.addWidget(self.title_lbl)

        if not item.exists:
            self.missing_tag = QLabel(self.tr('⚠️ KHÔNG TÌM THẤY'), self)
            self.missing_tag.setObjectName('CardMissingTag')
            self.missing_tag.setAttribute(wa_transparent, True)
            title_row.addWidget(self.missing_tag)

        title_row.addStretch()
        text_layout.addLayout(title_row)

        # Path row
        self.path_lbl = QLabel(item.path, self)
        self.path_lbl.setObjectName('CardFolderPath')
        self.path_lbl.setAttribute(wa_transparent, True)
        self.path_lbl.setToolTip(item.path)
        f_path = self.path_lbl.font()
        f_path.setPointSize(9)
        self.path_lbl.setFont(f_path)
        text_layout.addWidget(self.path_lbl)

        # Meta tags row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)

        time_str = format_relative_time(item.last_opened)
        self.time_lbl = QLabel(f'🕒 {time_str}', self)
        self.time_lbl.setObjectName('CardMetaLabel')
        self.time_lbl.setAttribute(wa_transparent, True)
        meta_row.addWidget(self.time_lbl)

        if item.page_count > 0:
            self.pages_lbl = QLabel(f'📖 {item.page_count} trang', self)
            self.pages_lbl.setObjectName('CardPagesLabel')
            self.pages_lbl.setAttribute(wa_transparent, True)
            meta_row.addWidget(self.pages_lbl)

        meta_row.addStretch()
        text_layout.addLayout(meta_row)

        card_layout.addLayout(text_layout, 1)

        # Right actions: Star & Delete
        self.star_btn = VectorStarButton(starred=item.starred, parent=self)
        self.star_btn.toggled_star.connect(self._on_star_toggled)
        card_layout.addWidget(self.star_btn)

        self.del_btn = VectorDeleteButton(self)
        self.del_btn.clicked.connect(self._on_delete_clicked)
        card_layout.addWidget(self.del_btn)

        self.cover_label.setObjectName('CardCoverLabel')
        self.title_lbl.setContentsMargins(0, 1, 0, 1)
        self.path_lbl.setContentsMargins(0, 1, 0, 1)
        self.time_lbl.setContentsMargins(0, 1, 0, 1)

        self._apply_style(hover=False)

    def _load_cover(self) -> None:
        pixmap = None
        if self.item.cover_image and osp.exists(self.item.cover_image):
            try:
                raw_pm = QPixmap(self.item.cover_image)
                if not raw_pm.isNull():
                    pixmap = raw_pm.scaled(
                        56,
                        56,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
            except Exception:
                pass

        if pixmap and not pixmap.isNull():
            rounded = QPixmap(56, 56)
            rounded.fill(QColor(0, 0, 0, 0))
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 56, 56, 10, 10)
            painter.setClipPath(path)
            sx = max(0, (pixmap.width() - 56) // 2)
            sy = max(0, (pixmap.height() - 56) // 2)
            painter.drawPixmap(0, 0, pixmap, sx, sy, 56, 56)
            painter.end()
            self.cover_label.setPixmap(rounded)
        else:
            # Render a stylish vector placeholder
            placeholder = QPixmap(56, 56)
            placeholder.fill(QColor(0, 0, 0, 0))
            painter = QPainter(placeholder)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            grad = QLinearGradient(0, 0, 56, 56)
            if pcfg.darkmode:
                grad.setColorAt(0.0, QColor('#1E293B'))
                grad.setColorAt(1.0, QColor('#0F172A'))
                icon_color = QColor('#64748B')
            else:
                grad.setColorAt(0.0, QColor('#EFF6FF'))
                grad.setColorAt(1.0, QColor('#DBEAFE'))
                icon_color = QColor('#3B82F6')
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(0, 0, 56, 56, 10, 10)

            # Draw sleek stylized book glyph
            p = QPainterPath()
            p.moveTo(16, 20)
            p.lineTo(24, 20)
            p.lineTo(28, 24)
            p.lineTo(40, 24)
            p.lineTo(40, 38)
            p.lineTo(16, 38)
            p.closeSubpath()
            painter.setPen(QPen(icon_color, 1.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(p)
            painter.end()
            self.cover_label.setPixmap(placeholder)

    def _apply_style(self, hover: bool = False) -> None:
        is_dark = pcfg.darkmode

        if is_dark:
            bg = '#1F2430' if hover else '#181C24'
            border = '#388BFD' if hover else '#2D333B'
            text_title = '#FFFFFF'
            text_sub = '#8B949E'
            badge_bg = 'rgba(56, 139, 253, 0.15)'
            badge_fg = '#58A6FF'
        else:
            bg = '#F8FAFC' if hover else '#FFFFFF'
            border = '#3B82F6' if hover else '#E2E8F0'
            text_title = '#0F172A'
            text_sub = '#64748B'
            badge_bg = 'rgba(37, 99, 235, 0.1)'
            badge_fg = '#2563EB'

        border_width = '1.5px' if hover else '1px'

        self.setStyleSheet(
            f'#FolderCardItemWidget {{'
            f'  background-color: {bg};'
            f'  border: {border_width} solid {border};'
            f'  border-radius: 12px;'
            f'}}'
            f'#FolderCardItemWidget QLabel {{'
            f'  background: transparent;'
            f'  background-color: transparent;'
            f'  border: none;'
            f'}}'
            f'#CardCoverLabel {{ background: transparent; background-color: transparent; border: none; }}'
            f'#CardFolderTitle {{ color: {text_title}; background: transparent; background-color: transparent; }}'
            f'#CardFolderPath {{ color: {text_sub}; background: transparent; background-color: transparent; }}'
            f'#CardMetaLabel {{ color: {text_sub}; font-size: 11px; background: transparent; background-color: transparent; }}'
            f'#CardPagesLabel {{'
            f'  background-color: {badge_bg}; color: {badge_fg};'
            f'  border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 600;'
            f'}}'
            f'#CardMissingTag {{'
            f'  background-color: rgba(239, 68, 68, 0.14); color: #EF4444;'
            f'  border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 6px;'
            f'  padding: 1px 7px; font-size: 10px; font-weight: 700;'
            f'}}'
        )

    def enterEvent(self, event: QEvent) -> None:
        self._apply_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._apply_style(hover=False)
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.star_btn.geometry().contains(event.pos()) or self.del_btn.geometry().contains(event.pos()):
                super().mousePressEvent(event)
                return
            self._is_pressed = True
            border_color = '#2563EB' if not pcfg.darkmode else '#58A6FF'
            bg_color = 'rgba(37, 99, 235, 0.08)' if not pcfg.darkmode else 'rgba(56, 139, 253, 0.12)'
            self.setStyleSheet(
                self.styleSheet() +
                f'#FolderCardItemWidget {{ border: 1.5px solid {border_color}; background-color: {bg_color}; }}'
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and getattr(self, '_is_pressed', False):
            self._is_pressed = False
            if not self.star_btn.geometry().contains(event.pos()) and not self.del_btn.geometry().contains(event.pos()):
                if self.rect().contains(event.pos()):
                    self.folder_clicked.emit(self.item.path)
                    event.accept()
                    return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.star_btn.geometry().contains(event.pos()) and not self.del_btn.geometry().contains(event.pos()):
                self.folder_clicked.emit(self.item.path)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    def _on_star_toggled(self, starred: bool) -> None:
        self.item.starred = starred
        self._apply_style(hover=self.underMouse())
        self.star_toggled.emit(self.item.path, starred)

    def _on_delete_clicked(self) -> None:
        self.item_deleted.emit(self.item.path)


class FolderLauncherDialog(OutsideClickFramelessMixin, QDialog):
    """Split-view modern Launcher / Welcome popup window."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.manager = FolderHistoryManager.get_instance()
        self.selected_folder: Optional[str] = None
        self.filter_starred_only: bool = False
        self.search_query: str = ''
        self.fox_movie: Optional[QMovie] = None

        self.setFixedWidth(940)
        self.setFixedHeight(610)

        window_type = getattr(Qt, 'WindowType', Qt)
        widget_attribute = getattr(Qt, 'WidgetAttribute', Qt)
        self.setWindowFlags(window_type.Dialog | window_type.FramelessWindowHint)
        self.setAttribute(widget_attribute.WA_TranslucentBackground)

        # Outer root layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # Rounded surface
        self.surface = QFrame(self)
        self.surface.setObjectName('LauncherSurface')
        outer_layout.addWidget(self.surface)

        # Horizontal split layout: Left Sidebar (Branding & Animation) + Right Panel (Folder List)
        split_layout = QHBoxLayout(self.surface)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)

        # =========================================================================
        # LEFT SIDEBAR: Branding, README Spinning Fox Animation & Primary Controls
        # =========================================================================
        self.left_sidebar = QFrame(self.surface)
        self.left_sidebar.setObjectName('LauncherLeftSidebar')
        self.left_sidebar.setFixedWidth(290)
        left_layout = QVBoxLayout(self.left_sidebar)
        left_layout.setContentsMargins(24, 28, 24, 24)
        left_layout.setSpacing(14)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # 1. Animation container
        anim_box = QFrame(self.left_sidebar)
        anim_box.setObjectName('LauncherAnimBox')
        anim_box.setFixedSize(160, 160)
        anim_layout = QVBoxLayout(anim_box)
        anim_layout.setContentsMargins(0, 0, 0, 0)
        anim_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        gif_path = osp.join(shared.PROGRAM_PATH, 'resources', 'spinning_fox.gif')
        if not osp.exists(gif_path):
            gif_path = 'resources/spinning_fox.gif'

        if osp.exists(gif_path):
            self.fox_movie = QMovie(gif_path)
            if self.fox_movie.isValid():
                self.fox_movie.setScaledSize(QSize(146, 146))
                self.anim_label = QLabel(anim_box)
                self.anim_label.setMovie(self.fox_movie)
                self.anim_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                anim_layout.addWidget(self.anim_label)
                self.fox_movie.start()
            else:
                self.anim_label = AppBrandLogo(anim_box)
                anim_layout.addWidget(self.anim_label)
        else:
            self.anim_label = AppBrandLogo(anim_box)
            anim_layout.addWidget(self.anim_label)

        left_layout.addWidget(anim_box, 0, Qt.AlignmentFlag.AlignHCenter)

        # 2. App Name & Tagline
        app_title = QLabel('BalloonsTranslator', self.left_sidebar)
        app_title.setObjectName('LauncherAppTitle')
        app_title.setContentsMargins(0, 2, 0, 2)
        f_app = app_title.font()
        f_app.setPointSize(14)
        f_app.setBold(True)
        app_title.setFont(f_app)
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(app_title)

        app_subtitle = QLabel(self.tr('AI Comic Translation Suite'), self.left_sidebar)
        app_subtitle.setObjectName('LauncherAppSubtitle')
        app_subtitle.setContentsMargins(0, 1, 0, 1)
        f_sub = app_subtitle.font()
        f_sub.setPointSize(9)
        app_subtitle.setFont(f_sub)
        app_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(app_subtitle)

        tag_badge = QLabel('v2.x • Deep Learning', self.left_sidebar)
        tag_badge.setObjectName('LauncherTagBadge')
        tag_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(tag_badge, 0, Qt.AlignmentFlag.AlignHCenter)

        left_layout.addSpacing(10)

        # 3. Primary Action Buttons on Left
        self.browse_btn = QPushButton(self.tr('📂  Mở thư mục mới...'), self.left_sidebar)
        self.browse_btn.setObjectName('LauncherPrimaryBtn')
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.setFixedHeight(40)
        self.browse_btn.clicked.connect(self.on_browse_folder)
        left_layout.addWidget(self.browse_btn)

        self.clear_btn = QPushButton(self.tr('🗑️  Dọn dẹp lịch sử (Giữ ⭐)'), self.left_sidebar)
        self.clear_btn.setObjectName('LauncherClearBtn')
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_btn.setFixedHeight(36)
        self.clear_btn.setToolTip(
            self.tr('Chỉ xóa các thư mục chưa gắn sao.\nMọi thư mục có đánh dấu ⭐ sẽ được an toàn giữ lại 100%!')
        )
        self.clear_btn.clicked.connect(self.on_clear_history)
        left_layout.addWidget(self.clear_btn)

        left_layout.addStretch()

        # 4. Shortcut tip box at bottom of left sidebar
        tip_box = QFrame(self.left_sidebar)
        tip_box.setObjectName('LauncherTipBox')
        tip_box_layout = QVBoxLayout(tip_box)
        tip_box_layout.setContentsMargins(12, 10, 12, 10)
        tip_box_layout.setSpacing(4)

        tip_title = QLabel(self.tr('💡 Phím tắt nhanh:'), tip_box)
        tip_title.setObjectName('LauncherTipTitle')
        tip_title.setContentsMargins(0, 1, 0, 1)
        f_tt = tip_title.font()
        f_tt.setPointSize(9)
        f_tt.setBold(True)
        tip_title.setFont(f_tt)
        tip_box_layout.addWidget(tip_title)

        tip_desc = QLabel(self.tr('Bấm Ctrl+O ở bất kỳ đâu trong màn hình dịch để mở lại thư viện này.'), tip_box)
        tip_desc.setObjectName('LauncherTipDesc')
        tip_desc.setContentsMargins(0, 1, 0, 1)
        tip_desc.setWordWrap(True)
        f_td = tip_desc.font()
        f_td.setPointSize(8)
        tip_desc.setFont(f_td)
        tip_box_layout.addWidget(tip_desc)

        left_layout.addWidget(tip_box)
        split_layout.addWidget(self.left_sidebar)

        # =========================================================================
        # RIGHT PANEL: Folder Search, Filters & Recent Manga Chapter Cards
        # =========================================================================
        self.right_panel = QFrame(self.surface)
        self.right_panel.setObjectName('LauncherRightPanel')
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(24, 20, 24, 18)
        right_layout.setSpacing(14)

        # 1. Right Header Row (Title + Close Button)
        self.title_bar = QWidget(self.right_panel)
        self.title_bar.setObjectName('LauncherTitleBar')
        header_layout = QHBoxLayout(self.title_bar)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        header_title_box = QVBoxLayout()
        header_title_box.setSpacing(2)

        self.title_lbl = QLabel(self.tr('Thư Viện & Chapter Gần Đây'), self.title_bar)
        self.title_lbl.setObjectName('LauncherTitle')
        self.title_lbl.setContentsMargins(0, 2, 0, 2)
        t_font = self.title_lbl.font()
        t_font.setPointSize(14)
        t_font.setBold(True)
        self.title_lbl.setFont(t_font)
        header_title_box.addWidget(self.title_lbl)

        self.sub_lbl = QLabel(
            self.tr('Chọn thư mục truyện để tiếp tục dịch hoặc quản lý lịch sử'),
            self.title_bar,
        )
        self.sub_lbl.setObjectName('LauncherSubtitle')
        self.sub_lbl.setContentsMargins(0, 1, 0, 1)
        sub_font = self.sub_lbl.font()
        sub_font.setPointSize(9)
        self.sub_lbl.setFont(sub_font)
        header_title_box.addWidget(self.sub_lbl)

        header_layout.addLayout(header_title_box)
        header_layout.addStretch()

        self.close_button = DialogCloseButton(self.title_bar)
        self.close_button.clicked.connect(self.reject)
        header_layout.addWidget(self.close_button)

        right_layout.addWidget(self.title_bar)

        # 2. Search & Segmented Filter Bar Row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        self.search_input = QLineEdit(self.right_panel)
        self.search_input.setObjectName('LauncherSearchInput')
        self.search_input.setPlaceholderText(self.tr('🔍  Tìm kiếm chapter, tên truyện hoặc đường dẫn...'))
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self.on_search_changed)
        filter_row.addWidget(self.search_input, 1)

        # Segmented Filter Pill Container
        filter_pill_box = QFrame(self.right_panel)
        filter_pill_box.setObjectName('LauncherFilterPillBox')
        pill_layout = QHBoxLayout(filter_pill_box)
        pill_layout.setContentsMargins(3, 3, 3, 3)
        pill_layout.setSpacing(4)

        self.btn_all = QPushButton(self.tr('Tất cả'), filter_pill_box)
        self.btn_all.setObjectName('LauncherFilterPill')
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.setFixedHeight(32)
        self.btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_all.clicked.connect(lambda: self.set_star_filter(False))
        pill_layout.addWidget(self.btn_all)

        self.btn_starred = QPushButton(self.tr('⭐ Đã gắn sao'), filter_pill_box)
        self.btn_starred.setObjectName('LauncherFilterPill')
        self.btn_starred.setCheckable(True)
        self.btn_starred.setChecked(False)
        self.btn_starred.setFixedHeight(32)
        self.btn_starred.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_starred.clicked.connect(lambda: self.set_star_filter(True))
        pill_layout.addWidget(self.btn_starred)

        filter_row.addWidget(filter_pill_box)
        right_layout.addLayout(filter_row)

        # 3. Cards Scroll Area
        self.scroll_area = QScrollArea(self.right_panel)
        self.scroll_area.setObjectName('LauncherScrollArea')
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.viewport().setObjectName('LauncherScrollViewport')
        self.scroll_area.viewport().setStyleSheet('background: transparent;')
        self.scroll_area.setStyleSheet('background: transparent; border: none;')

        self.cards_content = QWidget()
        self.cards_content.setObjectName('LauncherCardsContent')
        self.cards_content.setStyleSheet('background: transparent;')
        self.cards_layout = QVBoxLayout(self.cards_content)
        self.cards_layout.setContentsMargins(0, 0, 6, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_content)
        right_layout.addWidget(self.scroll_area, 1)

        # 4. Right Footer Bar
        footer_row = QHBoxLayout()
        footer_row.setContentsMargins(2, 4, 2, 0)

        self.stats_lbl = QLabel('', self.right_panel)
        self.stats_lbl.setObjectName('LauncherStatsLabel')
        self.stats_lbl.setContentsMargins(0, 1, 0, 1)
        footer_row.addWidget(self.stats_lbl)

        footer_row.addStretch()

        right_layout.addLayout(footer_row)
        split_layout.addWidget(self.right_panel, 1)

        self.apply_theme_stylesheet()
        self.refresh_list()

    def apply_theme_stylesheet(self) -> None:
        is_dark = pcfg.darkmode
        if is_dark:
            surface_bg = '#141720'
            surface_border = '#2D333B'
            sidebar_bg = '#0F1218'
            sidebar_border = '#232936'
            anim_box_bg = '#FFFFFF'
            anim_box_border = 'rgba(255, 255, 255, 0.18)'
            tip_box_bg = '#161B24'
            tip_box_border = '#232936'
            text_main = '#F0F6FC'
            text_sub = '#8B949E'
            input_bg = '#1A1E26'
            input_border = '#30363D'
            pill_box_bg = '#1A1E26'
            pill_active_bg = '#2D333B'
            btn_sec_bg = '#1E232E'
            btn_sec_border = '#30363D'
            primary_bg = 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #1D4ED8)'
            primary_hover = 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3B82F6, stop:1 #2563EB)'
        else:
            surface_bg = '#FFFFFF'
            surface_border = '#E2E8F0'
            sidebar_bg = '#F8FAFC'
            sidebar_border = '#E2E8F0'
            anim_box_bg = '#FFFFFF'
            anim_box_border = '#E2E8F0'
            tip_box_bg = '#FFFFFF'
            tip_box_border = '#E2E8F0'
            text_main = '#0F172A'
            text_sub = '#64748B'
            input_bg = '#F8FAFC'
            input_border = '#E2E8F0'
            pill_box_bg = '#F1F5F9'
            pill_active_bg = '#FFFFFF'
            btn_sec_bg = '#F8FAFC'
            btn_sec_border = '#E2E8F0'
            primary_bg = 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #1D4ED8)'
            primary_hover = 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3B82F6, stop:1 #2563EB)'

        style = f"""
        #LauncherSurface {{
            background-color: {surface_bg};
            border: 1.5px solid {surface_border};
            border-radius: 16px;
        }}
        #LauncherSurface QLabel {{
            background: transparent;
            background-color: transparent;
            border: none;
            padding: 0px;
        }}
        #LauncherTitleBar {{
            background: transparent;
            background-color: transparent;
            border: none;
        }}
        #LauncherLeftSidebar {{
            background-color: {sidebar_bg};
            border-right: 1px solid {sidebar_border};
            border-top-left-radius: 16px;
            border-bottom-left-radius: 16px;
        }}
        #LauncherRightPanel {{
            background-color: {surface_bg};
            border-top-right-radius: 16px;
            border-bottom-right-radius: 16px;
        }}
        #LauncherAnimBox {{
            background-color: {anim_box_bg};
            border-radius: 20px;
            border: 1px solid {sidebar_border};
        }}
        #LauncherAnimBox QLabel {{
            background: transparent;
            background-color: transparent;
            border: none;
        }}
        #LauncherAppTitle {{
            color: {text_main};
            font-weight: 700;
            background: transparent;
            background-color: transparent;
        }}
        #LauncherAppSubtitle {{
            color: {text_sub};
            background: transparent;
            background-color: transparent;
        }}
        #LauncherTagBadge {{
            background-color: rgba(37, 99, 235, 0.12);
            color: #3B82F6;
            border-radius: 6px;
            padding: 2px 10px;
            font-size: 10px;
            font-weight: 600;
        }}
        #LauncherTipBox {{
            background-color: {tip_box_bg};
            border: 1px solid {tip_box_border};
            border-radius: 10px;
        }}
        #LauncherTipTitle {{
            color: {text_main};
            background: transparent;
            background-color: transparent;
        }}
        #LauncherTipDesc {{
            color: {text_sub};
            background: transparent;
            background-color: transparent;
        }}
        #LauncherTitle {{
            color: {text_main};
            font-weight: 700;
            background: transparent;
            background-color: transparent;
        }}
        #LauncherSubtitle {{
            color: {text_sub};
            background: transparent;
            background-color: transparent;
        }}
        #LauncherPrimaryBtn {{
            background: {primary_bg};
            color: #ffffff;
            font-weight: 600;
            font-size: 13px;
            border: none;
            border-radius: 9px;
            padding: 0 16px;
        }}
        #LauncherPrimaryBtn:hover {{
            background: {primary_hover};
        }}
        #LauncherClearBtn {{
            background-color: {btn_sec_bg};
            color: {text_main};
            border: 1px solid {btn_sec_border};
            border-radius: 9px;
            padding: 0 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        #LauncherClearBtn:hover {{
            border-color: #EF4444;
            color: #EF4444;
            background-color: rgba(239, 68, 68, 0.08);
        }}
        #LauncherSearchInput {{
            background-color: {input_bg};
            color: {text_main};
            border: 1.5px solid {input_border};
            border-radius: 10px;
            padding: 0 14px;
            font-size: 12px;
        }}
        #LauncherSearchInput:focus {{
            border-color: #3B82F6;
            background-color: {'#1C2128' if is_dark else '#FFFFFF'};
        }}
        #LauncherFilterPillBox {{
            background-color: {pill_box_bg};
            border-radius: 10px;
            border: 1px solid {btn_sec_border};
        }}
        #LauncherFilterPill {{
            background-color: transparent;
            color: {text_sub};
            border: none;
            border-radius: 7px;
            padding: 0 14px;
            font-size: 12px;
            font-weight: 500;
        }}
        #LauncherFilterPill:checked {{
            background-color: {pill_active_bg};
            color: {text_main};
            font-weight: 700;
        }}
        #LauncherFilterPill:hover:!checked {{
            color: {text_main};
        }}
        #LauncherStatsLabel {{
            color: {text_sub};
            font-size: 11px;
            background: transparent;
            background-color: transparent;
        }}
        #LauncherScrollArea, #LauncherScrollViewport, #LauncherCardsContent {{
            background: transparent;
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 6px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(148, 163, 184, 0.4);
            min-height: 24px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(148, 163, 184, 0.7);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        """
        self.setStyleSheet(style)

    def set_star_filter(self, starred_only: bool) -> None:
        self.filter_starred_only = starred_only
        self.btn_all.setChecked(not starred_only)
        self.btn_starred.setChecked(starred_only)
        self.refresh_list()

    def on_search_changed(self, text: str) -> None:
        self.search_query = text
        self.refresh_list()

    def _update_stats_and_filter_counts(self) -> None:
        total_items = len(self.manager.get_items())
        total_starred = len(self.manager.get_items(filter_starred=True))
        self.btn_all.setText(self.tr(f'Tất cả ({total_items})'))
        self.btn_starred.setText(self.tr(f'⭐ Đã gắn sao ({total_starred})'))
        self.stats_lbl.setText(
            self.tr(f'Đang lưu {total_items} thư mục  •  {total_starred} có gắn sao ⭐')
        )

    def refresh_list(self) -> None:
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        items = self.manager.get_items(
            filter_starred=self.filter_starred_only,
            query=self.search_query,
        )

        self._update_stats_and_filter_counts()

        if not items:
            empty_box = QWidget(self.cards_content)
            empty_layout = QVBoxLayout(empty_box)
            empty_layout.setContentsMargins(0, 50, 0, 50)
            empty_layout.setSpacing(12)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            empty_icon = QLabel('📚', empty_box)
            f = empty_icon.font()
            f.setPointSize(36)
            empty_icon.setFont(f)
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)

            empty_title = QLabel(
                self.tr('Chưa có thư mục nào trong danh sách') if not self.filter_starred_only else self.tr('Chưa có thư mục nào được gắn sao ⭐'),
                empty_box,
            )
            f_t = empty_title.font()
            f_t.setPointSize(12)
            f_t.setBold(True)
            empty_title.setFont(f_t)
            empty_title.setStyleSheet('color: #8B949E;' if pcfg.darkmode else 'color: #64748B;')
            empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_title)

            empty_sub = QLabel(
                self.tr('Bấm nút "Mở thư mục mới..." ở cột bên trái để bắt đầu dịch truyện!'),
                empty_box,
            )
            empty_sub.setStyleSheet('color: #6E7681;' if pcfg.darkmode else 'color: #94A3B8;')
            empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_sub)

            self.cards_layout.insertWidget(0, empty_box)
            return

        for idx, item_data in enumerate(items):
            card = FolderCardItemWidget(item_data, self.cards_content)
            card.folder_clicked.connect(self.on_select_folder)
            card.star_toggled.connect(self._on_star_toggled)
            card.item_deleted.connect(self._on_item_deleted)
            self.cards_layout.insertWidget(idx, card)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        parent = self.parentWidget()
        if parent is None:
            screen = QApplication.primaryScreen()
            if screen:
                geo = self.frameGeometry()
                geo.moveCenter(screen.geometry().center())
                self.move(geo.topLeft())
        if not getattr(self, '_fade_in_started', False):
            self._fade_in_started = True
            self.setWindowOpacity(0.0)
            self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self._fade_anim.setDuration(160)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(getattr(getattr(QEasingCurve, 'Type', QEasingCurve), 'OutCubic'))
            self._fade_anim.start()

    def _can_drag_title(self, watched: QWidget) -> bool:
        interactive = (
            getattr(self, 'close_button', None),
            getattr(self, 'browse_btn', None),
            getattr(self, 'clear_btn', None),
            getattr(self, 'search_input', None),
            getattr(self, 'btn_all', None),
            getattr(self, 'btn_starred', None),
        )
        for w in interactive:
            if w is not None and (watched is w or w.isAncestorOf(watched)):
                return False
        if hasattr(self, 'scroll_area') and (watched is self.scroll_area or self.scroll_area.isAncestorOf(watched)):
            return False
        return (
            (hasattr(self, 'title_bar') and (watched is self.title_bar or self.title_bar.isAncestorOf(watched)))
            or (hasattr(self, 'left_sidebar') and (watched is self.left_sidebar or self.left_sidebar.isAncestorOf(watched)))
        )

    def _dismiss_transient_window(self) -> None:
        self.reject()

    def _preserve_on_outside_click(self) -> bool:
        return self.parentWidget() is None

    def on_select_folder(self, folder_path: str) -> None:
        self.selected_folder = folder_path
        self.hide()
        QApplication.processEvents()
        self.accept()

    def reject(self) -> None:
        self.hide()
        QApplication.processEvents()
        super().reject()

    def _on_star_toggled(self, folder_path: str, starred: bool) -> None:
        self.manager.set_star(folder_path, starred)
        if self.filter_starred_only and not starred:
            self.refresh_list()
        else:
            self._update_stats_and_filter_counts()

    def _on_item_deleted(self, folder_path: str) -> None:
        self.manager.remove(folder_path)
        self.refresh_list()

    def on_clear_history(self) -> None:
        self.manager.clear_history()
        self.refresh_list()

    def on_browse_folder(self) -> None:
        recent_items = self.manager.get_items()
        initial_dir = recent_items[0].path if recent_items and recent_items[0].exists else None
        folder_path = QFileDialog.getExistingDirectory(
            self,
            self.tr('Chọn thư mục truyện tranh / comic'),
            initial_dir or '',
        )
        if folder_path and osp.isdir(folder_path):
            self.manager.add_or_update(folder_path)
            self.on_select_folder(folder_path)

    def closeEvent(self, event) -> None:
        if self.fox_movie:
            try:
                self.fox_movie.stop()
            except Exception:
                pass
        super().closeEvent(event)
