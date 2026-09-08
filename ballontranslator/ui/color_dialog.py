from __future__ import annotations

from typing import Any, List, Optional
from qtpy.QtCore import Qt
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QColorDialog, QWidget

from ballontranslator.utils.config import pcfg, save_config
from ballontranslator.utils.logger import logger as LOGGER


def get_custom_colors() -> List[str]:
    """Return the list of current custom color hex strings from QColorDialog.

    >>> from qtpy.QtWidgets import QApplication
    >>> _ = QApplication.instance() or QApplication([])
    >>> colors = get_custom_colors()
    >>> isinstance(colors, list) and len(colors) == 16
    True
    """
    colors: List[str] = []
    count = QColorDialog.customCount()
    for i in range(count):
        color = QColorDialog.customColor(i)
        if hasattr(color, 'name'):
            colors.append(color.name())
        elif isinstance(color, int):
            colors.append(QColor(color).name())
    return colors


def set_custom_colors(colors: List[str]) -> None:
    """Populate QColorDialog custom colors with the provided hex strings.

    >>> from qtpy.QtWidgets import QApplication
    >>> _ = QApplication.instance() or QApplication([])
    >>> set_custom_colors(['#ff0000', '#00ff00'])
    >>> get_custom_colors()[:2]
    ['#ff0000', '#00ff00']
    """
    if not colors:
        return
    max_count = QColorDialog.customCount()
    for i, col_str in enumerate(colors[:max_count]):
        if isinstance(col_str, str) and col_str.strip():
            color = QColor(col_str.strip())
            if color.isValid():
                QColorDialog.setCustomColor(i, color)


def restore_custom_colors() -> None:
    """Restore custom colors saved in program configuration into QColorDialog.

    >>> from qtpy.QtWidgets import QApplication
    >>> _ = QApplication.instance() or QApplication([])
    >>> restore_custom_colors()
    """
    saved_colors = getattr(pcfg, 'custom_colors', None)
    if saved_colors and isinstance(saved_colors, list):
        set_custom_colors(saved_colors)


def sync_custom_colors_to_config(save: bool = True) -> bool:
    """Sync QColorDialog custom colors back to pcfg and optionally save config.

    >>> from qtpy.QtWidgets import QApplication
    >>> _ = QApplication.instance() or QApplication([])
    >>> isinstance(sync_custom_colors_to_config(save=False), bool)
    True
    """
    current_colors = get_custom_colors()
    if not current_colors:
        return False

    saved_colors = getattr(pcfg, 'custom_colors', [])
    if current_colors != saved_colors:
        pcfg.custom_colors = current_colors
        if save:
            save_config()
        return True
    return False


def get_color_dialog_color(
    initial: Any = None,
    parent: Optional[QWidget] = None,
    title: str = "",
    options: Optional[Any] = None,
) -> QColor:
    """Show a QColorDialog to select a color, persisting custom colors on close.

    >>> from qtpy.QtWidgets import QApplication
    >>> _ = QApplication.instance() or QApplication([])
    >>> isinstance(get_custom_colors(), list)
    True
    """
    initial_color = initial if initial is not None else QColor(255, 255, 255)
    args: list[Any] = [initial_color]
    if parent is not None:
        args.append(parent)
        if title:
            args.append(title)
            if options is not None:
                args.append(options)
    elif title:
        args.extend([None, title])
        if options is not None:
            args.append(options)

    try:
        color = QColorDialog.getColor(*args)
    finally:
        sync_custom_colors_to_config(save=True)
    return color
