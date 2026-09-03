import os
import shutil
import tempfile
import time
import unittest
from PIL import Image
from qtpy.QtCore import QCoreApplication

from ballontranslator.ui.page_thumbnails import (
    PageThumbnailLoader,
    prioritize_pages,
    get_thumbnail_cache_dir,
    generate_single_thumbnail,
    THUMBNAIL_TARGET_SIZE,
)


class TestPageThumbnails(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.cache_dir, ignore_errors=True)

    def test_prioritize_pages(self):
        pages = ['p1.png', 'p2.png', 'p3.png', 'p4.png', 'p5.png']
        # Prioritize p3 -> p3, p2, p4, p1, p5
        ordered = prioritize_pages(pages, 'p3.png')
        self.assertEqual(ordered, ['p3.png', 'p2.png', 'p4.png', 'p1.png', 'p5.png'])

        # Non-existent priority image leaves order intact
        self.assertEqual(prioritize_pages(pages, 'nonexistent.png'), pages)

    def test_generate_single_thumbnail_rgb(self):
        img_path = os.path.join(self.temp_dir, 'large_rgb.jpg')
        cache_path = os.path.join(self.cache_dir, 'thumb_rgb.jpg')

        img = Image.new('RGB', (1200, 1800), color=(200, 100, 50))
        img.save(img_path, 'JPEG')

        success = generate_single_thumbnail(img_path, cache_path, target_size=96)
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(cache_path))

        with Image.open(cache_path) as thumb:
            self.assertLessEqual(thumb.width, 96)
            self.assertLessEqual(thumb.height, 96)
            self.assertEqual(thumb.mode, 'RGB')

    def test_generate_single_thumbnail_rgba(self):
        img_path = os.path.join(self.temp_dir, 'alpha.png')
        cache_path = os.path.join(self.cache_dir, 'thumb_alpha.png')

        img = Image.new('RGBA', (800, 600), color=(0, 128, 255, 128))
        img.save(img_path, 'PNG')

        success = generate_single_thumbnail(img_path, cache_path, target_size=96)
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(cache_path))

        with Image.open(cache_path) as thumb:
            self.assertLessEqual(thumb.width, 96)
            self.assertLessEqual(thumb.height, 96)
            self.assertEqual(thumb.mode, 'RGBA')

    def test_page_thumbnail_loader_lifecycle(self):
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication([])

        # Create mock image pages
        page_names = []
        for i in range(5):
            name = f"page_{i:02d}.jpg"
            p = os.path.join(self.temp_dir, name)
            Image.new('RGB', (200, 300), color=(i * 40, 50, 100)).save(p)
            page_names.append(name)

        loader = PageThumbnailLoader()
        received_batches = []

        def on_ready(req_id, batch):
            received_batches.append((req_id, batch))

        loader.thumbnails_ready.connect(on_ready)

        try:
            loader.load_pages(1, self.temp_dir, page_names, priority_img='page_02.jpg')

            # Process event loop until all 5 thumbnails are processed
            deadline = time.time() + 5.0
            total_items = 0
            while time.time() < deadline and total_items < len(page_names):
                app.processEvents()
                time.sleep(0.02)
                total_items = sum(len(b[1]) for b in received_batches)

            self.assertEqual(total_items, len(page_names))
            first_received = received_batches[0][1][0][0]
            self.assertEqual(first_received, 'page_02.jpg')

        finally:
            loader.request_stop()
            loader.wait(2000)

    def test_many_images_more_than_100(self):
        """Verify handling large image lists (> 100 items) smoothly."""
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication([])

        page_names = []
        for i in range(120):
            name = f"page_{i:03d}.jpg"
            p = os.path.join(self.temp_dir, name)
            Image.new('RGB', (100, 100), color=(50, 50, 50)).save(p)
            page_names.append(name)

        loader = PageThumbnailLoader()
        received_batches = []
        loader.thumbnails_ready.connect(lambda req_id, b: received_batches.append((req_id, b)))

        try:
            loader.load_pages(1, self.temp_dir, page_names)
            deadline = time.time() + 10.0
            total_items = 0
            while time.time() < deadline and total_items < len(page_names):
                app.processEvents()
                time.sleep(0.02)
                total_items = sum(len(b[1]) for b in received_batches)

            self.assertEqual(total_items, 120)
        finally:
            loader.request_stop()
            loader.wait(2000)

    def test_cancellation_on_new_request(self):
        app = QCoreApplication.instance()
        if app is None:
            app = QCoreApplication([])

        loader = PageThumbnailLoader()
        loader.cancel_current()
        self.assertFalse(loader.isRunning())


if __name__ == '__main__':
    unittest.main()
