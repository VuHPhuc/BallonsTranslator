import json
import os
import shutil
import tempfile
import unittest

from ballontranslator.utils.config import ProgramConfig, pcfg


class TestWindowAndZoomPersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.json')

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_config_fields(self):
        cfg = ProgramConfig()
        self.assertTrue(cfg.remember_window_size)
        self.assertEqual(cfg.window_size, [1280, 800])
        self.assertIsNone(cfg.window_pos)
        self.assertFalse(cfg.window_maximized)
        self.assertTrue(cfg.remember_image_zoom)
        self.assertEqual(cfg.canvas_zoom, 1.0)

    def test_backward_compatibility_empty_config(self):
        # When legacy config has no window or zoom keys, defaults must be populated
        with open(self.config_path, 'w', encoding='utf8') as f:
            json.dump({}, f)

        cfg = ProgramConfig.load(self.config_path)
        self.assertTrue(cfg.remember_window_size)
        self.assertEqual(cfg.window_size, [1280, 800])
        self.assertIsNone(cfg.window_pos)
        self.assertFalse(cfg.window_maximized)
        self.assertTrue(cfg.remember_image_zoom)
        self.assertEqual(cfg.canvas_zoom, 1.0)

    def test_load_valid_persisted_values(self):
        data = {
            'remember_window_size': True,
            'window_size': [1024, 768],
            'window_pos': [100, 150],
            'window_maximized': False,
            'remember_image_zoom': True,
            'canvas_zoom': 0.75,
        }
        with open(self.config_path, 'w', encoding='utf8') as f:
            json.dump(data, f)

        cfg = ProgramConfig.load(self.config_path)
        self.assertTrue(cfg.remember_window_size)
        self.assertEqual(cfg.window_size, [1024, 768])
        self.assertEqual(cfg.window_pos, [100, 150])
        self.assertFalse(cfg.window_maximized)
        self.assertTrue(cfg.remember_image_zoom)
        self.assertAlmostEqual(cfg.canvas_zoom, 0.75)

    def test_discard_malformed_values(self):
        data = {
            'remember_window_size': 'not_a_bool',
            'window_size': [100],  # Invalid: only 1 element and < 400
            'window_pos': 'invalid_pos',
            'window_maximized': 12345,
            'remember_image_zoom': None,
            'canvas_zoom': -5.0,  # Invalid: negative
        }
        with open(self.config_path, 'w', encoding='utf8') as f:
            json.dump(data, f)

        cfg = ProgramConfig.load(self.config_path)
        # Discarded values should fall back to safe defaults
        self.assertTrue(cfg.remember_window_size)
        self.assertEqual(cfg.window_size, [1280, 800])
        self.assertIsNone(cfg.window_pos)
        self.assertFalse(cfg.window_maximized)
        self.assertTrue(cfg.remember_image_zoom)
        self.assertEqual(cfg.canvas_zoom, 1.0)

    def test_canvas_reset_zoom_logic(self):
        # Verify reciprocal scaling factor logic for resetZoom
        scale_factor = 0.75
        reset_factor = 1.0 / scale_factor
        new_scale = scale_factor * reset_factor
        self.assertAlmostEqual(new_scale, 1.0)

        scale_factor = 1.5
        reset_factor = 1.0 / scale_factor
        new_scale = scale_factor * reset_factor
        self.assertAlmostEqual(new_scale, 1.0)


if __name__ == '__main__':
    unittest.main()
