from __future__ import annotations

import json
import os
import os.path as osp
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ballontranslator.utils import shared
from ballontranslator.utils.logger import logger as LOGGER

SUPPORTED_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff'}


@dataclass
class FolderHistoryItem:
    """Represents a single project folder history entry.

    >>> item = FolderHistoryItem(path='C:/manga/ch1', name='ch1', starred=True)
    >>> item.name
    'ch1'
    >>> item.starred
    True
    """

    path: str
    name: str
    starred: bool = False
    last_opened: float = 0.0
    page_count: int = 0
    cover_image: Optional[str] = None

    @property
    def exists(self) -> bool:
        return osp.isdir(self.path)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> FolderHistoryItem:
        return cls(
            path=str(data.get('path', '')),
            name=str(data.get('name', '')),
            starred=bool(data.get('starred', False)),
            last_opened=float(data.get('last_opened', 0.0)),
            page_count=int(data.get('page_count', 0)),
            cover_image=data.get('cover_image'),
        )


def get_folder_first_image(folder_path: str) -> Optional[str]:
    """Return path to the first image in the folder for thumbnail display."""
    if not osp.isdir(folder_path):
        return None
    try:
        images = []
        with os.scandir(folder_path) as it:
            for entry in it:
                if entry.is_file():
                    _, ext = osp.splitext(entry.name)
                    if ext.lower() in SUPPORTED_IMAGE_EXTS:
                        images.append(entry.path)
                        if len(images) >= 10:
                            break
        if images:
            images.sort()
            return images[0]
    except Exception:
        pass
    return None


def count_folder_images(folder_path: str) -> int:
    """Fast shallow count of image files in the directory.

    >>> count_folder_images('/non_existent_path_xyz')
    0
    """
    if not osp.isdir(folder_path):
        return 0
    try:
        count = 0
        with os.scandir(folder_path) as it:
            for entry in it:
                if entry.is_file():
                    _, ext = osp.splitext(entry.name)
                    if ext.lower() in SUPPORTED_IMAGE_EXTS:
                        count += 1
        return count
    except Exception:
        return 0


class FolderHistoryManager:
    """Manages persistent recent folder history with star protection.

    Data is stored in `config/folder_history.json` so git pulls/updates
    never overwrite or delete user history.
    """

    _instance: Optional[FolderHistoryManager] = None

    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            self.file_path = osp.join(shared.PROGRAM_PATH, 'config', 'folder_history.json')
        else:
            self.file_path = file_path
        self.show_on_startup: bool = True
        self._items: Dict[str, FolderHistoryItem] = {}
        self.load()

    @classmethod
    def get_instance(cls) -> FolderHistoryManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _normalize_path(self, path: str) -> str:
        if not path:
            return ''
        norm = osp.normpath(osp.abspath(path))
        # Keep consistent Windows drive casing & forward slashes
        return norm.replace('\\', '/')

    def load(self) -> None:
        """Load history from JSON file safely without crashing on corrupted data."""
        self._items.clear()
        if not osp.exists(self.file_path):
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.show_on_startup = bool(data.get('show_on_startup', True))
            for entry in data.get('folders', []):
                if not isinstance(entry, dict) or not entry.get('path'):
                    continue
                norm_p = self._normalize_path(entry['path'])
                item = FolderHistoryItem.from_dict(entry)
                item.path = norm_p
                if not item.name:
                    item.name = osp.basename(norm_p)
                self._items[norm_p] = item
        except Exception as e:
            LOGGER.warning(f'Failed to load folder history from {self.file_path}: {e}')

    def save(self) -> None:
        """Atomically persist history to JSON to prevent file corruption."""
        try:
            folder_dir = osp.dirname(self.file_path)
            if not osp.exists(folder_dir):
                os.makedirs(folder_dir, exist_ok=True)

            payload = {
                'version': 1,
                'show_on_startup': self.show_on_startup,
                'folders': [item.to_dict() for item in self._items.values()],
            }

            temp_path = self.file_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.file_path)
        except Exception as e:
            LOGGER.error(f'Failed to save folder history to {self.file_path}: {e}')

    def add_or_update(
        self,
        path: str,
        starred: Optional[bool] = None,
        page_count: Optional[int] = None,
        cover_image: Optional[str] = None,
    ) -> FolderHistoryItem:
        """Record or update a folder in history, retaining star status."""
        norm_p = self._normalize_path(path)
        if not norm_p:
            return FolderHistoryItem(path='', name='')

        now = time.time()
        name = osp.basename(norm_p) or norm_p

        existing = self._items.get(norm_p)
        if existing:
            existing.last_opened = now
            existing.name = name
            if cover_image:
                existing.cover_image = cover_image
            elif not existing.cover_image or not osp.exists(existing.cover_image):
                existing.cover_image = get_folder_first_image(norm_p)

            if page_count is not None and page_count >= 0:
                existing.page_count = page_count
            elif existing.page_count <= 0:
                existing.page_count = count_folder_images(norm_p)

            if starred is not None:
                existing.starred = starred
            item = existing
        else:
            p_count = page_count if (page_count is not None and page_count >= 0) else count_folder_images(norm_p)
            c_img = cover_image if cover_image else get_folder_first_image(norm_p)
            is_starred = False if starred is None else starred
            item = FolderHistoryItem(
                path=norm_p,
                name=name,
                starred=is_starred,
                last_opened=now,
                page_count=p_count,
                cover_image=c_img,
            )
            self._items[norm_p] = item

        self.save()
        return item

    def set_star(self, path: str, starred: bool) -> bool:
        """Explicitly set starred state of an item and save. Returns new starred value."""
        norm_p = self._normalize_path(path)
        item = self._items.get(norm_p)
        if not item:
            item = self.add_or_update(path, starred=starred)
        else:
            item.starred = bool(starred)
            self.save()
        return item.starred

    def toggle_star(self, path: str) -> bool:
        """Toggle starred state of an item and save. Returns new starred value."""
        norm_p = self._normalize_path(path)
        item = self._items.get(norm_p)
        current = item.starred if item else False
        return self.set_star(path, not current)

    def remove(self, path: str) -> bool:
        """Remove a specific folder from history."""
        norm_p = self._normalize_path(path)
        if norm_p in self._items:
            del self._items[norm_p]
            self.save()
            return True
        return False

    def clear_history(self) -> int:
        """Clear all non-starred folders from history, preserving ALL starred items.

        Returns the number of deleted items.
        """
        initial_count = len(self._items)
        # Keep only starred items
        self._items = {p: item for p, item in self._items.items() if item.starred}
        removed_count = initial_count - len(self._items)
        if removed_count > 0:
            self.save()
        return removed_count

    def get_items(self, filter_starred: bool = False, query: str = '') -> List[FolderHistoryItem]:
        """Get sorted list of history items: starred first, then by last_opened descending."""
        items = list(self._items.values())
        if filter_starred:
            items = [item for item in items if item.starred]

        if query:
            q = query.strip().lower()
            items = [
                item
                for item in items
                if q in item.name.lower() or q in item.path.lower()
            ]

        # Sort: starred first (True > False), then last_opened descending
        items.sort(key=lambda x: (x.starred, x.last_opened), reverse=True)
        return items

    def set_show_on_startup(self, show: bool) -> None:
        self.show_on_startup = bool(show)
        self.save()

    def get_show_on_startup(self) -> bool:
        return self.show_on_startup

    def import_from_recent_proj_list(self, recent_list: List[str]) -> None:
        """One-time migration/sync from legacy recent_proj_list if needed."""
        if not recent_list:
            return
        modified = False
        for path in recent_list:
            norm_p = self._normalize_path(path)
            if norm_p and norm_p not in self._items and osp.isdir(norm_p):
                self._items[norm_p] = FolderHistoryItem(
                    path=norm_p,
                    name=osp.basename(norm_p) or norm_p,
                    starred=False,
                    last_opened=time.time(),
                    page_count=count_folder_images(norm_p),
                )
                modified = True
        if modified:
            self.save()
