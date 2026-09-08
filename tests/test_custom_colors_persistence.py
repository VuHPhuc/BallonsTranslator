from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication, QColorDialog

from ballontranslator.ui.color_dialog import (
    get_color_dialog_color,
    get_custom_colors,
    restore_custom_colors,
    set_custom_colors,
    sync_custom_colors_to_config,
)
from ballontranslator.utils import config as program_config
from ballontranslator.utils import shared
from ballontranslator.utils.config import ProgramConfig, load_config, pcfg, save_config
from ballontranslator.utils import updater


class CustomColorsPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_get_and_set_custom_colors(self):
        sample_colors = ['#123456', '#abcdef', '#ff0000']
        set_custom_colors(sample_colors)

        retrieved = get_custom_colors()
        self.assertEqual(len(retrieved), QColorDialog.customCount())
        self.assertEqual(retrieved[0].lower(), '#123456')
        self.assertEqual(retrieved[1].lower(), '#abcdef')
        self.assertEqual(retrieved[2].lower(), '#ff0000')

    def test_sync_custom_colors_to_config(self):
        original_colors = list(getattr(pcfg, 'custom_colors', []))
        try:
            set_custom_colors(['#aabbcc'])
            changed = sync_custom_colors_to_config(save=False)
            self.assertTrue(changed)
            self.assertIn('#aabbcc', pcfg.custom_colors[0].lower())

            # Second call without changes returns False
            self.assertFalse(sync_custom_colors_to_config(save=False))
        finally:
            pcfg.custom_colors = original_colors

    def test_restore_custom_colors_from_config(self):
        original_colors = list(getattr(pcfg, 'custom_colors', []))
        try:
            pcfg.custom_colors = ['#fedcba', '#010203']
            restore_custom_colors()
            retrieved = get_custom_colors()
            self.assertEqual(retrieved[0].lower(), '#fedcba')
            self.assertEqual(retrieved[1].lower(), '#010203')
        finally:
            pcfg.custom_colors = original_colors

    def test_custom_colors_serialized_in_config_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'config.json')
            cfg = ProgramConfig(custom_colors=['#112233', '#445566'])
            with open(config_path, 'w', encoding='utf8') as f:
                f.write(program_config.json_dump_program_config(cfg))

            loaded = ProgramConfig.load(config_path)
            self.assertEqual(loaded.custom_colors, ['#112233', '#445566'])

    def test_load_config_recovers_from_backup_when_primary_is_missing_or_corrupt(self):
        original_path = shared.CONFIG_PATH
        original_config = program_config.pcfg.copy()
        original_created_on_load = program_config.config_created_on_load

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = os.path.join(tmpdir, 'config.json')
                bak_path = config_path + '.bak'

                # Create valid backup config with custom_colors and specific language
                backup_data = {
                    'display_lang': 'en_US',
                    'custom_colors': ['#ff5500', '#00aa33'],
                }
                with open(bak_path, 'w', encoding='utf8') as f:
                    json.dump(backup_data, f)

                # Primary config is corrupt / invalid JSON
                with open(config_path, 'w', encoding='utf8') as f:
                    f.write('INVALID_JSON_CONTENT_CORRUPTED{{{')

                # load_config should automatically recover from .bak
                load_config(config_path)

                self.assertEqual(pcfg.display_lang, 'en_US')
                self.assertEqual(pcfg.custom_colors, ['#ff5500', '#00aa33'])
                # Also verify that primary config was restored from backup
                with open(config_path, 'r', encoding='utf8') as f:
                    restored = json.load(f)
                self.assertEqual(restored.get('display_lang'), 'en_US')
        finally:
            shared.CONFIG_PATH = original_path
            program_config.pcfg.merge(original_config)
            program_config.config_created_on_load = original_created_on_load

    def test_save_config_maintains_backup_file(self):
        original_path = shared.CONFIG_PATH
        original_config = program_config.pcfg.copy()
        original_created_on_load = program_config.config_created_on_load

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = os.path.join(tmpdir, 'config.json')
                bak_path = config_path + '.bak'

                load_config(config_path)
                pcfg.custom_colors = ['#123123']
                pcfg.display_lang = 'English'
                save_config()

                # Second save to trigger copy of first save into .bak
                pcfg.custom_colors = ['#999999']
                save_config()

                self.assertTrue(os.path.exists(bak_path))
                with open(bak_path, 'r', encoding='utf8') as f:
                    bak_data = json.load(f)
                self.assertEqual(bak_data.get('custom_colors'), ['#123123'])
        finally:
            shared.CONFIG_PATH = original_path
            program_config.pcfg.merge(original_config)
            program_config.config_created_on_load = original_created_on_load

    def test_updater_protects_user_config_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            cache_dir = root / '.btrans_cache'
            cache_dir.mkdir(parents=True)
            config_dir = root / 'config'
            config_dir.mkdir(parents=True)

            user_config = config_dir / 'config.json'
            user_config.write_text('{"user_setting": true}', encoding='utf8')
            user_history = config_dir / 'folder_history.json'
            user_history.write_text('{"folders": []}', encoding='utf8')

            app_updater = updater.BallonsTranslatorUpdater(
                program_path=str(root),
                cache_dir=str(cache_dir),
            )

            # Test _replace_file protects user config files
            source_file = cache_dir / 'source_config.json'
            source_file.write_text('{"overwritten": true}', encoding='utf8')

            app_updater._replace_file(source_file, user_config)
            # Content should still be the user's original setting
            self.assertEqual(user_config.read_text(encoding='utf8'), '{"user_setting": true}')

            # Test backup_source backs up config directory
            (root / 'ballontranslator').mkdir(parents=True)
            (root / 'ballontranslator' / '__init__.py').write_text('# init', encoding='utf8')
            for f in updater.SOURCE_UPDATE_FILES:
                (root / f).write_text(f'# {f}', encoding='utf8')

            backup_path = app_updater.backup_source()
            self.assertTrue((backup_path / 'config' / 'config.json').exists())
            self.assertEqual(
                (backup_path / 'config' / 'config.json').read_text(encoding='utf8'),
                '{"user_setting": true}',
            )


if __name__ == '__main__':
    unittest.main()
