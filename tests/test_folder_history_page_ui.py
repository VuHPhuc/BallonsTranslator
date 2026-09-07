import os
import sys
import unittest

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from qtpy.QtWidgets import QApplication, QDialog
from qtpy.QtCore import Qt, QMutex

from ballontranslator.utils.config import pcfg
from ballontranslator.utils.folder_history import FolderHistoryManager
from ballontranslator.utils import shared
from ballontranslator.utils.font_registry import FontRegistry
from ballontranslator.utils.lock import RUNTIME_LOCKS


class TestFolderLauncherDialogUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        shared.FONT_REGISTRY = FontRegistry()
        RUNTIME_LOCKS['model_loading'] = QMutex()

    def test_launcher_dialog_selection_and_shortcuts(self):
        from ballontranslator.ui.folder_launcher_dialog import FolderLauncherDialog
        dialog = FolderLauncherDialog()
        try:
            # Verify initial components
            self.assertEqual(dialog.width(), 940)
            self.assertEqual(dialog.height(), 610)
            self.assertIsNotNone(dialog.search_input)
            self.assertIsNotNone(dialog.browse_btn)
            self.assertIsNotNone(dialog.clear_btn)

            # Test selecting a folder
            test_path = 'D:/test_manga_chapter'
            dialog.on_select_folder(test_path)
            self.assertEqual(dialog.selected_folder, test_path)
            self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_drag_title_and_card_clicks(self):
        from ballontranslator.ui.folder_launcher_dialog import (
            FolderLauncherDialog,
            FolderCardItemWidget,
        )
        from ballontranslator.utils.folder_history import FolderHistoryItem
        from qtpy.QtGui import QMouseEvent
        from qtpy.QtCore import QPoint, QPointF

        dialog = FolderLauncherDialog()
        try:
            # Title bar allows drag, but buttons inside title bar do not
            self.assertTrue(dialog._can_drag_title(dialog.title_bar))
            self.assertFalse(dialog._can_drag_title(dialog.close_button))
            self.assertFalse(dialog._can_drag_title(dialog.browse_btn))
            self.assertFalse(dialog._can_drag_title(dialog.clear_btn))
            self.assertFalse(dialog._can_drag_title(dialog.search_input))

            # Test FolderCardItemWidget click
            item = FolderHistoryItem(
                path='D:/test_path',
                name='test_path',
                last_opened=100.0,
                starred=False,
                page_count=10,
                cover_image=None,
            )
            card = FolderCardItemWidget(item)
            clicked_paths = []
            card.folder_clicked.connect(clicked_paths.append)

            # Not dragged by dialog
            self.assertFalse(dialog._can_drag_title(card))

            # Simulate click on card body (not star, not delete)
            pos = QPoint(100, 30)
            press_evt = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(pos),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            card.mousePressEvent(press_evt)

            release_evt = QMouseEvent(
                QMouseEvent.Type.MouseButtonRelease,
                QPointF(pos),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            card.mouseReleaseEvent(release_evt)

            self.assertEqual(clicked_paths, ['D:/test_path'])
            card.deleteLater()
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_launcher_dialog_reject_on_close(self):
        from ballontranslator.ui.folder_launcher_dialog import FolderLauncherDialog
        dialog = FolderLauncherDialog()
        try:
            self.assertIsNone(dialog.selected_folder)
            dialog.close_button.click()
            self.assertIsNone(dialog.selected_folder)
            self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_mainwindow_has_clean_workspace(self):
        from ballontranslator.ui.mainwindow import MainWindow
        win = MainWindow(self.app, pcfg, open_dir='')
        try:
            # Main window central widget is comicTransSplitter
            self.assertEqual(win.centralStackWidget.currentWidget(), win.comicTransSplitter)
            # showFolderHistoryDialog method is present and callable
            self.assertTrue(callable(win.showFolderHistoryDialog))
        finally:
            win.close()
            win.deleteLater()

    def test_launch_exits_when_folder_dialog_rejected(self):
        from unittest import mock
        from ballontranslator import launch

        mock_dialog = mock.MagicMock()
        mock_dialog.exec_.return_value = QDialog.DialogCode.Rejected
        mock_dialog.selected_folder = None

        with mock.patch.object(launch.args, 'headless', False), \
             mock.patch.object(launch.args, 'proj_dir', ''), \
             mock.patch('ballontranslator.ui.folder_launcher_dialog.FolderLauncherDialog', return_value=mock_dialog), \
             mock.patch('ballontranslator.ui.mainwindow.MainWindow') as mock_main_win:
            # Recreate minimal mocks needed by main()
            with mock.patch('ballontranslator.launch.ensure_resource_theme_files'), \
                 mock.patch('ballontranslator.utils.core_requirements.ensure_core_requirements', return_value=False), \
                 mock.patch('ballontranslator.utils.network_mirrors.auto_fill_network_mirrors', return_value=False):
                # When dialog is rejected (e.g. user clicked X), main should return 0 and MainWindow should NOT be created
                exit_code = launch.main()
                self.assertEqual(exit_code, 0)
                mock_main_win.assert_not_called()

    def test_launch_opens_chosen_folder_when_accepted(self):
        from unittest import mock
        from ballontranslator import launch

        mock_dialog = mock.MagicMock()
        mock_dialog.exec_.return_value = QDialog.DialogCode.Accepted
        mock_dialog.selected_folder = 'D:/test_folder_manga'

        mock_instance = mock.MagicMock()
        mock_instance.restart_signal = mock.MagicMock()

        with mock.patch.object(launch.args, 'headless', False), \
             mock.patch.object(launch.args, 'proj_dir', ''), \
             mock.patch('ballontranslator.ui.folder_launcher_dialog.FolderLauncherDialog', return_value=mock_dialog), \
             mock.patch('ballontranslator.ui.mainwindow.MainWindow', return_value=mock_instance) as mock_main_win:
            with mock.patch('ballontranslator.launch.ensure_resource_theme_files'), \
                 mock.patch('ballontranslator.utils.core_requirements.ensure_core_requirements', return_value=False), \
                 mock.patch('ballontranslator.utils.network_mirrors.auto_fill_network_mirrors', return_value=False), \
                 mock.patch.object(self.app, 'exec', return_value=0):
                exit_code = launch.main()
                self.assertEqual(exit_code, 0)
                mock_main_win.assert_called_once()
                self.assertEqual(mock_main_win.call_args.kwargs.get('open_dir'), 'D:/test_folder_manga')
                mock_instance.show.assert_called_once()


if __name__ == '__main__':
    unittest.main()
