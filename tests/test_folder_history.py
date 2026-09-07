import os
import os.path as osp
import tempfile
import unittest
import json
import time

from ballontranslator.utils.folder_history import (
    FolderHistoryItem,
    FolderHistoryManager,
    count_folder_images,
)


class TestFolderHistoryManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = osp.join(self.temp_dir.name, 'test_history.json')
        self.manager = FolderHistoryManager(file_path=self.history_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_get_items(self):
        folder_a = osp.join(self.temp_dir.name, 'manga_a')
        folder_b = osp.join(self.temp_dir.name, 'manga_b')
        os.makedirs(folder_a, exist_ok=True)
        os.makedirs(folder_b, exist_ok=True)

        self.manager.add_or_update(folder_a, starred=False)
        self.manager.add_or_update(folder_b, starred=True)

        items = self.manager.get_items()
        self.assertEqual(len(items), 2)
        # Starred item must be prioritized at index 0
        self.assertTrue(items[0].starred)
        self.assertEqual(items[0].name, 'manga_b')
        self.assertFalse(items[1].starred)
        self.assertEqual(items[1].name, 'manga_a')

    def test_toggle_star(self):
        folder_a = osp.join(self.temp_dir.name, 'manga_a')
        os.makedirs(folder_a, exist_ok=True)
        self.manager.add_or_update(folder_a, starred=False)

        # Toggle to True
        new_state = self.manager.toggle_star(folder_a)
        self.assertTrue(new_state)
        items = self.manager.get_items()
        self.assertTrue(items[0].starred)

        # Toggle to False
        new_state = self.manager.toggle_star(folder_a)
        self.assertFalse(new_state)
        items = self.manager.get_items()
        self.assertFalse(items[0].starred)

    def test_clear_history_preserves_starred_items(self):
        """CRITICAL: Starred folders must NEVER be cleared by clear_history."""
        f1 = osp.join(self.temp_dir.name, 'f1')
        f2 = osp.join(self.temp_dir.name, 'f2')
        f3 = osp.join(self.temp_dir.name, 'f3')
        os.makedirs(f1, exist_ok=True)
        os.makedirs(f2, exist_ok=True)
        os.makedirs(f3, exist_ok=True)

        self.manager.add_or_update(f1, starred=True)
        self.manager.add_or_update(f2, starred=False)
        self.manager.add_or_update(f3, starred=True)

        self.assertEqual(len(self.manager.get_items()), 3)

        # Clear history
        removed = self.manager.clear_history()
        self.assertEqual(removed, 1)

        remaining = self.manager.get_items()
        self.assertEqual(len(remaining), 2)
        remaining_names = {item.name for item in remaining}
        self.assertEqual(remaining_names, {'f1', 'f3'})
        self.assertTrue(all(item.starred for item in remaining))

    def test_persistence_and_reloading(self):
        f1 = osp.join(self.temp_dir.name, 'manga1')
        os.makedirs(f1, exist_ok=True)
        self.manager.add_or_update(f1, starred=True)

        # Create new manager instance pointing to the same file
        new_manager = FolderHistoryManager(file_path=self.history_file)
        items = new_manager.get_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, 'manga1')
        self.assertTrue(items[0].starred)

    def test_set_and_toggle_star_persistence(self):
        f1 = osp.join(self.temp_dir.name, 'manga_star_test')
        os.makedirs(f1, exist_ok=True)
        self.manager.add_or_update(f1, starred=False)

        # Explicitly set star
        self.manager.set_star(f1, True)
        self.assertTrue(self.manager.get_items()[0].starred)

        # Reload from disk
        reloaded = FolderHistoryManager(file_path=self.history_file)
        self.assertTrue(reloaded.get_items()[0].starred)

        # Toggle star to False
        self.manager.toggle_star(f1)
        self.assertFalse(self.manager.get_items()[0].starred)

        # Reload from disk
        reloaded2 = FolderHistoryManager(file_path=self.history_file)
        self.assertFalse(reloaded2.get_items()[0].starred)

    def test_search_and_filter_starred(self):
        f1 = osp.join(self.temp_dir.name, 'Naruto_01')
        f2 = osp.join(self.temp_dir.name, 'OnePiece_01')
        f3 = osp.join(self.temp_dir.name, 'Naruto_02')
        os.makedirs(f1, exist_ok=True)
        os.makedirs(f2, exist_ok=True)
        os.makedirs(f3, exist_ok=True)

        self.manager.add_or_update(f1, starred=True)
        self.manager.add_or_update(f2, starred=False)
        self.manager.add_or_update(f3, starred=False)

        # Filter starred only
        starred_items = self.manager.get_items(filter_starred=True)
        self.assertEqual(len(starred_items), 1)
        self.assertEqual(starred_items[0].name, 'Naruto_01')

        # Query search
        search_items = self.manager.get_items(query='Naruto')
        self.assertEqual(len(search_items), 2)
        search_names = {item.name for item in search_items}
        self.assertEqual(search_names, {'Naruto_01', 'Naruto_02'})


if __name__ == '__main__':
    unittest.main()
