# TỔNG HỢP CÁC TÍNH NĂNG TÙY BIẾN (CUSTOM FEATURES)
> **Repository:** `VuHPhuc/BallonsTranslator`
> **Mục đích:** Danh mục các tính năng tùy biến độc quyền. Mỗi tính năng được tách thành một tài liệu chi tiết đánh số `01-xx` để thuận tiện theo dõi và bảo toàn khi kéo code mới từ upstream (`dmMaze/BallonsTranslator`).

---

## Danh Sách Các Tính Năng Đánh Số

| Số hiệu | Tên tính năng | Mục đích chính | File tài liệu chi tiết |
| :--- | :--- | :--- | :--- |
| **01** | **Async Thumbnail Loader** | Tải thumbnail bất đồng bộ nền, fix lỗi mất ảnh khi có >100 ảnh, chống lag và chống tràn RAM/crash. | [01-async_thumbnail_loader.md](file:///e:/AI_STUFF/Ballonstranslator_win_minium/doc/01-async_thumbnail_loader.md) |
| **02** | **Reset App Button** | Nút Reset App trên TitleBar để khởi động lại nhanh ứng dụng, đặt cạnh nút Sponsor để không ảnh hưởng tính năng gốc. | [02-reset_app_button.md](file:///e:/AI_STUFF/Ballonstranslator_win_minium/doc/02-reset_app_button.md) |
| **03** | **CMD Auto-Close / Crash-Pause** | Tự động đóng cửa sổ CMD khi tắt app bình thường; giữ lại CMD kèm lỗi/Traceback nếu app bị crash hoặc có ngoại lệ. | [03-auto_close_cmd_on_clean_exit.md](file:///e:/AI_STUFF/Ballonstranslator_win_minium/doc/03-auto_close_cmd_on_clean_exit.md) |

---

## Nguyên Tắc Khi Pull / Merge Từ Upstream (`dmMaze/BallonsTranslator`)

1. **Nguyên tắc Side-by-Side**: Khi thêm tính năng mới, ưu tiên đặt nút hoặc công cụ bên cạnh tính năng cũ thay vì ghi đè hoặc xóa bỏ hoàn toàn tính năng gốc của upstream (ví dụ: nút Reset App đặt cạnh nút Sponsor).
2. **Nguyên tắc Không can thiệp sâu vào Core nếu có thể tách module**: File worker thumbnail được tách riêng thành `ballontranslator/ui/page_thumbnails.py`, giúp giảm thiểu tối đa nguy cơ xung đột (git conflict).
3. **Các file cần kiểm tra lại sau khi `git merge upstream/dev`**:
   - `launch_win.bat`: kiểm tra lệnh `:launch` có `if %ERRORLEVEL% equ 0 exit /b 0`.
   - `ballontranslator/__main__.py`: kiểm tra `sys.exit(exit_code)`.
   - `ballontranslator/ui/mainwindowbars.py`: kiểm tra `resetAppToolBtn` cạnh `sponsorToolBtn`.
   - `ballontranslator/ui/mainwindow.py`: kiểm tra import `QPixmap`, `PageThumbnailLoader`, hàm `updatePageList` và `_on_thumbnails_ready`.
