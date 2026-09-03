from typing import Dict, List, Optional, Sequence, Tuple
import hashlib
import os
import os.path as osp
import threading
import time

from PIL import Image, ImageOps
from qtpy.QtCore import QThread, Signal, QObject

from ..utils.logger import logger as LOGGER
from ..utils import shared

THUMBNAIL_TARGET_SIZE = shared.PAGELIST_THUMBNAIL_SIZE * 2  # 96px for high-DPI sharpness


def get_thumbnail_cache_dir(directory: str) -> str:
    """Return the persistent disk cache directory for a given image folder.

    >>> issubclass(PageThumbnailLoader, QThread)
    True
    """
    cache_root = osp.join(shared.PROGRAM_PATH, '.btrans_cache', 'thumbnails')
    dir_hash = hashlib.sha256(osp.abspath(directory).encode('utf-8')).hexdigest()[:12]
    cache_dir = osp.join(cache_root, dir_hash)
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def generate_single_thumbnail(
    img_path: str,
    cache_path: str,
    target_size: int = THUMBNAIL_TARGET_SIZE,
) -> bool:
    """Generate and save a downscaled thumbnail using PIL with minimal memory.

    Returns True if generated successfully, False otherwise.
    """
    try:
        with Image.open(img_path) as img:
            img = ImageOps.exif_transpose(img)
            # Draft provides fast decoding with low memory for JPEG
            if hasattr(img, 'draft'):
                img.draft('RGB', (target_size, target_size))
            img.thumbnail((target_size, target_size), Image.Resampling.BILINEAR)

            # Preserve transparency if RGBA, otherwise RGB
            save_format = 'PNG' if img.mode in ('RGBA', 'LA', 'PA') else 'JPEG'
            if save_format == 'JPEG' and img.mode != 'RGB':
                img = img.convert('RGB')

            tmp_path = f"{cache_path}.tmp_{os.getpid()}_{threading.get_ident()}"
            if save_format == 'JPEG':
                img.save(tmp_path, 'JPEG', quality=85)
            else:
                img.save(tmp_path, 'PNG')
            os.replace(tmp_path, cache_path)
            return True
    except Exception as e:
        LOGGER.warning('Failed to generate thumbnail for %s: %s', img_path, e)
        return False


def prioritize_pages(
    pages: Sequence[str],
    priority_img: Optional[str] = None,
) -> List[str]:
    """Order pages so that the priority image and nearby pages are processed first.

    >>> prioritize_pages(['a', 'b', 'c', 'd'], 'c')
    ['c', 'b', 'd', 'a']
    """
    page_list = list(pages)
    if not page_list or priority_img not in page_list:
        return page_list

    idx = page_list.index(priority_img)
    ordered = [priority_img]
    left = idx - 1
    right = idx + 1
    n = len(page_list)

    while left >= 0 or right < n:
        if left >= 0:
            ordered.append(page_list[left])
            left -= 1
        if right < n:
            ordered.append(page_list[right])
            right += 1

    return ordered


class PageThumbnailLoader(QThread):
    """Background worker that generates and caches thumbnails without UI lag.

    >>> issubclass(PageThumbnailLoader, QThread)
    True
    """

    # Emits (request_id, [(page_name, thumbnail_cache_path), ...])
    thumbnails_ready = Signal(int, list)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._lock = threading.Lock()
        self._wake_event = threading.Event()
        self._stop_event = threading.Event()
        self._request_id: int = 0
        self._current_directory: str = ''
        self._pending_pages: List[str] = []

    def load_pages(
        self,
        request_id: int,
        directory: str,
        pages: Sequence[str],
        priority_img: Optional[str] = None,
    ) -> None:
        """Queue a new list of pages for thumbnail generation."""
        ordered = prioritize_pages(pages, priority_img)
        with self._lock:
            self._request_id = request_id
            self._current_directory = directory
            self._pending_pages = ordered

        self._wake_event.set()
        if not self.isRunning():
            self._stop_event.clear()
            self.start()

    def cancel_current(self) -> None:
        """Cancel ongoing thumbnail loading for the current request."""
        with self._lock:
            self._request_id += 1
            self._pending_pages.clear()

    def request_stop(self) -> None:
        """Signal the worker thread to exit."""
        self._stop_event.set()
        self._wake_event.set()

    def run(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                req_id = self._request_id
                directory = self._current_directory
                if not self._pending_pages:
                    self._wake_event.clear()
                    pages_to_process = []
                else:
                    pages_to_process = list(self._pending_pages)
                    self._pending_pages.clear()

            if not pages_to_process:
                self._wake_event.wait(timeout=1.0)
                continue

            try:
                cache_dir = get_thumbnail_cache_dir(directory)
            except Exception as e:
                LOGGER.error('Failed to create thumbnail cache dir: %s', e)
                continue

            batch: List[Tuple[str, str]] = []
            last_emit_time = time.monotonic()

            for page_name in pages_to_process:
                if self._stop_event.is_set():
                    break
                with self._lock:
                    if self._request_id != req_id:
                        break  # superseded by a new folder / request

                img_path = osp.join(directory, page_name)
                if not osp.isfile(img_path):
                    continue

                try:
                    stat = os.stat(img_path)
                    sig = f"{page_name}_{stat.st_mtime_ns}_{stat.st_size}"
                    thumb_name = hashlib.sha256(sig.encode('utf-8')).hexdigest()[:16] + ".jpg"
                    cache_path = osp.join(cache_dir, thumb_name)
                except Exception:
                    continue

                # Check if already cached on disk
                if not (osp.isfile(cache_path) and osp.getsize(cache_path) > 0):
                    if not generate_single_thumbnail(img_path, cache_path):
                        continue

                batch.append((page_name, cache_path))

                # Emit in batches of 16 or every 50ms for smooth UI updates
                now = time.monotonic()
                if len(batch) >= 16 or (now - last_emit_time >= 0.05 and batch):
                    self.thumbnails_ready.emit(req_id, batch)
                    batch = []
                    last_emit_time = now

            if batch:
                self.thumbnails_ready.emit(req_id, batch)
