# TÍNH NĂNG 05: LƯU NHỚ KÍCH THƯỚC CỬA SỔ & TỶ LỆ ZOOM ẢNH (% SETUP)

> **Số hiệu:** 05  
> **Áp dụng cho:** `VuHPhuc/BallonsTranslator`  
> **Trạng thái:** Đã triển khai và có unit tests bảo vệ  

---

## 1. Vấn đề thực tế (Problem Statement)

1. **Bị ép Fullscreen / Maximized mọi lúc khởi động**:
   - Mặc định bản gốc của upstream luôn tự động gọi `FramelessMoveResize.maximize` trên Windows (và `showMaximized` trên macOS/Linux) mỗi khi khởi động.
   - Người dùng thường muốn làm việc với cửa sổ thu nhỏ ("đến min") để vừa dịch truyện vừa đối chiếu tài liệu hoặc xem trình duyệt. Mỗi lần bật ứng dụng lại phải bấm un-maximize và kéo lại cửa sổ từ đầu rất bất tiện.
2. **Độ rộng tối thiểu quá lớn trên màn hình độ phân giải cao**:
   - Code cũ đặt `setMinimumWidth(screen_size.width() // 2)` (màn 1080p bị chặn ở 960px, màn 2K bị chặn ở 1280px). Điều này khiến người dùng không thể thu nhỏ cửa sổ về mức nhỏ gọn thực sự.
3. **Mất tỷ lệ Zoom ảnh mỗi lần mở app**:
   - Khi xem comic / manga trên cửa sổ nhỏ, tỷ lệ 100% thường quá to hoặc không vừa tầm nhìn. Người dùng phải dùng Ctrl + Lăn chuột để zoom về % phù hợp (ví dụ 60%, 75%).
   - Tuy nhiên mỗi khi tắt app và mở lại, hoặc mở một dự án mới, tỷ lệ zoom luôn bị reset về 100%.

---

## 2. Giải pháp kỹ thuật (Technical Solution)

1. **Lưu nhớ kích thước, toạ độ và trạng thái maximized**:
   - Bổ sung cấu hình `remember_window_size`, `window_size`, `window_pos`, `window_maximized` trong `ProgramConfig` (`config.py`).
   - Mặc định `window_maximized = False`, ứng dụng khởi động ở dạng cửa sổ kích thước vừa vặn (1280x800 hoặc kích thước người dùng đã lưu) thay vì tự ý fullscreen.
   - Khi tắt ứng dụng (`closeEvent`), nếu đang maximize hoặc minimize thì lưu `normalGeometry()`, nếu đang ở cửa sổ bình thường thì lưu kích thước và toạ độ hiện tại.
   - Khi mở ứng dụng, tự động khôi phục kích thước và vị trí (có kiểm tra toạ độ nằm trong màn hình hiển thị khả dụng).
2. **Cho phép thu nhỏ cửa sổ linh hoạt**:
   - Giới hạn `setMinimumWidth(min(750, screen_size.width() // 2))` và `setMinimumHeight(450)` giúp người dùng có thể thu nhỏ cửa sổ thoải mái.
3. **Lưu nhớ tỷ lệ Zoom ảnh (% Setup)**:
   - Bổ sung cấu hình `remember_image_zoom` và `canvas_zoom` (float, mặc định 1.0) trong `ProgramConfig`.
   - Khi người dùng zoom (Ctrl + Con lăn chuột, hoặc Zoom In/Out), Canvas tự động ghi nhớ tỷ lệ `canvas_zoom`.
   - Khi chuyển trang hoặc khởi động lại ứng dụng, Canvas tự động áp dụng tỷ lệ zoom này cho ảnh mới.
   - Bổ sung phím tắt **`Ctrl+0`** để đưa tỷ lệ zoom về lại `100%` nhanh chóng.
4. **Tùy chọn cấu hình trong Config Panel**:
   - Trong mục **Application**, có 2 checkbox:
     - `Remember window size and state` (Lưu nhớ kích thước và trạng thái cửa sổ)
     - `Remember image zoom level` (Lưu nhớ tỷ lệ zoom ảnh)

---

## 3. Các file thay đổi

1. **[ballontranslator/utils/config.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/ballontranslator/utils/config.py)**:
   - Thêm các trường `remember_window_size`, `window_size`, `window_pos`, `window_maximized`, `remember_image_zoom`, `canvas_zoom` vào dataclass `ProgramConfig`.
   - Bổ sung validate an toàn trong `ProgramConfig.load()`.
2. **[ballontranslator/launch.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/ballontranslator/launch.py)**:
   - Chỉ gọi maximize nếu `config.window_maximized` là `True`.
3. **[ballontranslator/ui/mainwindow.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/ballontranslator/ui/mainwindow.py)**:
   - Điều chỉnh `setMinimumWidth` và `setMinimumHeight`.
   - Thêm hàm `restoreWindowGeometry()` và `saveWindowGeometry()`.
   - Thêm phím tắt `Ctrl+0` (`shortcutZoomReset`).
4. **[ballontranslator/ui/canvas.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/ballontranslator/ui/canvas.py)**:
   - Khởi tạo `scale_factor` từ `pcfg.canvas_zoom`.
   - Cập nhật `pcfg.canvas_zoom` khi `scale_factor` thay đổi.
   - Giữ nguyên `scale_factor` trong `updateCanvas()`.
   - Thêm phương thức `resetZoom()`.
5. **[ballontranslator/ui/configpanel.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/ballontranslator/ui/configpanel.py)**:
   - Thêm 2 checkbox cấu hình trong tab `Application`.
6. **[tests/test_window_and_zoom_persistence.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/tests/test_window_and_zoom_persistence.py)**:
   - 5 unit tests kiểm thử độ tương thích ngược, giá trị mặc định, lọc giá trị lỗi và logic reset zoom.

---

## 4. Hướng dẫn bảo toàn khi Merge Upstream

Khi kéo code mới từ `dmMaze/BallonsTranslator`:
1. **Kiểm tra `launch.py`**: Đảm bảo dòng gọi `FramelessMoveResize.maximize` có bọc điều kiện `if getattr(config, 'window_maximized', False):`.
2. **Kiểm tra `mainwindow.py`**:
   - Giữ `self.restoreWindowGeometry()` trong `__init__`.
   - Giữ `self.saveWindowGeometry()` trong `closeEvent`.
   - Giữ `shortcutZoomReset` (`Ctrl+0`) trong `setupShortcuts`.
3. **Kiểm tra `canvas.py`**:
   - Giữ đoạn đọc `pcfg.canvas_zoom` trong `__init__` và `updateCanvas`.
