# TÀI LIỆU CÁC TÍNH NĂNG TÙY BIẾN (CUSTOM FEATURES)
> **Dành cho:** Repository `VuHPhuc/BallonsTranslator`  
> **Mục đích:** Lưu giữ chi tiết kỹ thuật các chức năng đã tùy biến để khi kéo (pull/merge/rebase) code mới từ upstream (`dmMaze/BallonsTranslator`) không bị xung đột hoặc mất tính năng.

---

## 1. Tối Ưu Hiển Thị Thumbnail Danh Sách Ảnh Khi Có Nhiều Ảnh (Background Thumbnail Loader)

### Vấn đề gốc của upstream:
- Upstream đặt giới hạn cứng: `shared.PAGELIST_THUMBNAIL_MAXNUM = 100`.
- Khi thư mục có **>= 100 ảnh**, ứng dụng **tắt hoàn toàn thumbnail** (chỉ hiển thị tên file text).
- Khi có **< 100 ảnh**, ứng dụng lại đọc toàn bộ ảnh gốc kích thước lớn đồng bộ trên Main UI Thread bằng `QIcon(path)`. Nếu gặp nhiều ảnh 2K/4K/8K, UI sẽ bị treo đơ (freeze/lag) và dễ tràn bộ nhớ (Out-Of-Memory crash).

### Giải pháp đã triển khai:
- **Tải bất đồng bộ bằng background thread:** Tạo lớp `PageThumbnailLoader` (kế thừa `QThread`) trong [page_thumbnails.py](file:///e:/AI_STUFF/Ballonstranslator_win_minium/ballontranslator/ui/page_thumbnails.py).
- **Tối ưu RAM siêu nhẹ:** Dùng `PIL.Image` với `draft('RGB', (size, size))` giải mã trực tiếp ảnh thu nhỏ mà không giải nén ảnh gốc vào RAM. Kích thước thumbnail lưu đĩa chỉ khoảng ~700 bytes đến 2KB mỗi ảnh.
- **Disk Cache thông minh:** Lưu thumbnail tại `.btrans_cache/thumbnails/<dir_hash>/<file_hash>.jpg`. Các lần mở sau tải ngay lập tức từ cache trong < 0.05ms.
- **Không giật lag giao diện (No UI Jitter):** Khi nạp danh sách, tạo ngay placeholder icon kích thước chuẩn (48x48 transparent) cho mỗi `QListWidgetItem` để chiều cao dòng và căn lề chữ cố định từ đầu.
- **Ưu tiên ảnh đang chọn:** Tải thumbnail của `current_img` và các trang lân cận trước, sau đó mới tới các trang còn lại.
- **Hủy tác vụ cũ:** Khi chuyển sang thư mục/project khác, tác vụ cũ được hủy ngay lập tức, không tiêu tốn CPU/RAM vô ích.
- **Tắt app an toàn:** `closeEvent` trong `MainWindow` dừng và chờ `thumbnail_loader` hoàn tất sạch sẽ.

### Các file liên quan cần giữ khi merge upstream:
1. `ballontranslator/ui/page_thumbnails.py` *(File mới)*: Chứa toàn bộ logic worker, cache, downscale.
2. `ballontranslator/ui/mainwindow.py`:
   - Import: `from .page_thumbnails import PageThumbnailLoader`
   - Khởi tạo trong `__init__`: `self._page_list_request_id`, `self._page_list_items`
   - Khởi tạo trong `setupThread`: `self.thumbnail_loader = PageThumbnailLoader(self)` và kết nối `self.thumbnail_loader.thumbnails_ready.connect(self._on_thumbnails_ready)`
   - Cập nhật hàm `updatePageList()`: xóa bỏ giới hạn `PAGELIST_THUMBNAIL_MAXNUM`, dùng placeholder icon và gọi `self.thumbnail_loader.load_pages(...)`
   - Hàm nhận kết quả `_on_thumbnails_ready()`
   - Dọn dẹp trong `closeEvent()`: `self.thumbnail_loader.request_stop()`
3. `tests/test_page_thumbnails.py` *(File mới)*: Unit test cho thumbnail loader.

---

## 2. Nút "Reset App" Trên Thanh Tiêu Đề (Thay Thế Nút "Sponsor")

### Vấn đề gốc của upstream:
- Trên thanh tiêu đề (TitleBar) có nút "Sponsor" kèm menu mở link Patreon / Afdian của tác giả gốc.

### Giải pháp đã triển khai:
- Xóa bỏ nút Sponsor và thay thế bằng nút **Reset App** (`resetAppToolBtn`) kèm icon xoay tròn (`rotation.svg`).
- Khi click, hiển thị hộp thoại xác nhận:
  - Nếu người dùng chọn **Yes**: Gọi `self.restart_signal.emit()`.
  - Tín hiệu này kích hoạt hàm `launch.restart()`, khởi động lại toàn bộ tiến trình ứng dụng sạch sẽ, nạp lại cấu hình và giải phóng toàn bộ tài nguyên.

### Các file liên quan cần giữ khi merge upstream:
1. `ballontranslator/ui/mainwindowbars.py`:
   - Trong `TitleBar.__init__`: thay `sponsorToolBtn` bằng `self.resetAppToolBtn`, gán text `self.tr('Reset App')`, icon `themed_icon_path('rotation.svg')`, signal `self.reset_app_trigger = self.resetAppToolBtn.clicked`.
   - Trong `hlayout.addWidget(...)`: add `self.resetAppToolBtn`.
2. `ballontranslator/ui/mainwindow.py`:
   - Trong `setupShortcuts()`: `self.titleBar.reset_app_trigger.connect(self.on_reset_app)`
   - Định nghĩa hàm:
     ```python
     def on_reset_app(self) -> None:
         msg = QMessageBox(self)
         msg.setWindowTitle(self.tr('Reset App'))
         msg.setText(self.tr('Restart to reset the application? \n'))
         msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
         ret = msg.exec_()
         if ret == QMessageBox.StandardButton.Yes:
             self.restart_signal.emit()
     ```

---

## 3. Hướng Dẫn Kéo Code Mới Từ Upstream Không Bị Mất Chức Năng

Khi tác giả gốc (`dmMaze/BallonsTranslator`) cập nhật phiên bản mới và bạn muốn đồng bộ code về:

### Bước 1: Fetch và kiểm tra thay đổi
```bash
git fetch upstream
```

### Bước 2: Hợp nhất (Merge)
```bash
git merge upstream/dev
```

### Bước 3: Xử lý xung đột (Conflict) nếu có
Nếu git báo conflict ở 2 file sau, chỉ cần mở file và giữ lại các đoạn code tùy biến:
- `ballontranslator/ui/mainwindowbars.py`:
  - Giữ lại `self.resetAppToolBtn` thay vì `self.sponsorToolBtn`.
- `ballontranslator/ui/mainwindow.py`:
  - Giữ import `PageThumbnailLoader`.
  - Giữ `self.thumbnail_loader` trong `setupThread()`.
  - Giữ kết nối `reset_app_trigger` trong `setupShortcuts()`.
  - Giữ logic `updatePageList()`, `_on_thumbnails_ready()`, `on_reset_app()`, và `thumbnail_loader.request_stop()` trong `closeEvent()`.

### Bước 4: Chạy test xác minh
```bash
.\ballontrans_pylibs_win\python.exe -m unittest tests/test_page_thumbnails.py
```
Sau khi tất cả test pass, commit và push lên repository cá nhân `VuHPhuc/BallonsTranslator`.
