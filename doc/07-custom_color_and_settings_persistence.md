# TÍNH NĂNG 07: LƯU BẢNG MÀU TÙY CHỈNH (CUSTOM COLORS) & BẢO TOÀN CÀI ĐẶT KHI UPDATE

> **Số hiệu:** 07  
> **Áp dụng cho:** `VuHPhuc/BallonsTranslator`  
> **Trạng thái:** Đã triển khai và có unit tests bảo vệ  

---

## 1. Vấn đề thực tế (Problem Statement)

1. **Mất bảng màu tùy chọn (Custom colors) trong `QColorDialog`**:
   - Khi người dùng phối màu phông chữ, viền chữ, bóng đổ, gradient hoặc màu bút vẽ và nhấn nút **"Add to Custom Colors"**, Qt chỉ lưu tạm 16 ô màu này trong bộ nhớ RAM của tiến trình hiện tại.
   - Mỗi lần khởi động lại ứng dụng, bấm nút Reset App, hoặc cập nhật ứng dụng, toàn bộ 16 ô màu cá nhân hóa này đều bị xóa trắng và quay về mặc định `#ffffff`.

2. **Lỗi bị reset toàn bộ cài đặt khi cập nhật ứng dụng (Settings Reset on Update)**:
   - Khi cập nhật phiên bản mới, toàn bộ cài đặt tùy chỉnh quan trọng của người dùng (API key LLM, ngôn ngữ đích Tiếng Việt, mô hình OCR `manga_ocr`, bộ nhận diện `ctbd`, v.v.) bị reset về mặc định (`google`, `mit48px`, tiếng Trung).
   - Các nguyên nhân chính:
     - Trong cơ chế nạp cấu hình `load_config()` cũ: khi `config.json` gặp lỗi hoặc trống, ứng dụng tự động nạp cấu hình mặc định trắng và lập tức ghi đè lên file cấu hình của người dùng mà không có cơ chế tự cứu hộ từ file backup `.bak`.
     - Trong `updater.py` và script đóng gói phát hành (`build_win_minimal.ps1`): file zip cập nhật có thể chứa thư mục hoặc file cấu hình đè lên file của người dùng, hoặc updater không sao lưu `config/` trước khi áp dụng bản vá.

---

## 2. Giải pháp kỹ thuật (Technical Solution)

### 2.1. Quản lý và lưu trữ Custom Colors
1. **Trường dữ liệu trong cấu hình**:
   - Bổ sung trường `custom_colors: List[str] = field(default_factory=list)` vào `ProgramConfig` trong `ballontranslator/utils/config.py`.
   - Lưu trữ danh sách tối đa 16 chuỗi mã màu hex (ví dụ `["#ff5500", "#00aa33", ...]`) tương ứng chuẩn xác với 16 ô màu trong lưới 2 hàng x 8 cột của `QColorDialog`.
2. **Module chuyên trách `ballontranslator/ui/color_dialog.py`**:
   - `restore_custom_colors()`: Tự động nạp các mã màu đã lưu trong `pcfg.custom_colors` vào `QColorDialog.setCustomColor(i, QColor(c))` ngay khi khởi tạo ứng dụng (`MainWindow.__init__`).
   - `get_custom_colors() -> list[str]`: Trích xuất 16 mã màu hex hiện tại từ `QColorDialog`.
   - `sync_custom_colors_to_config(save=True)`: Đồng bộ bảng màu từ `QColorDialog` vào `pcfg.custom_colors` và gọi `save_config()` ngay lập tức.
   - `get_color_dialog_color(...)`: Hàm bao bọc (wrapper) thay thế an toàn cho `QColorDialog.getColor(...)`. Khi hộp thoại chọn màu đóng lại (dù bấm OK, Cancel hay Add to Custom Colors), khối `finally:` sẽ luôn đảm bảo bảng màu tùy chỉnh được lưu lại ngay tức khắc.
3. **Tích hợp toàn diện**:
   - `ColorLabel` trong `ballontranslator/ui/custom_widget/label.py` (màu chữ, màu bút vẽ, viền).
   - Các nút chọn màu hiệu ứng trong `ballontranslator/ui/text_engine/effects/cards.py` (màu viền stroke, màu bóng shadow, màu hào quang glow).
   - Hộp thoại chọn điểm màu trong `ballontranslator/ui/text_engine/effects/gradient_editor.py`.
   - Tự động đồng bộ trước khi lưu cấu hình và khi thoát app trong `MainWindow.save_config()` và `MainWindow.closeEvent()`.

### 2.2. Cơ chế tự động cứu hộ cấu hình & chống ghi đè khi Update
1. **Tự động sao lưu và phục hồi (`config.json.bak`)**:
   - Trong `save_config()`: Mỗi khi lưu cấu hình thành công, hệ thống tự động duy trì một bản sao lưu an toàn tại `config/config.json.bak`.
   - Nếu ứng dụng đang ở trạng thái nạp cấu hình mặc định do lỗi (`config_created_on_load = True`), hệ thống **tuyệt đối không ghi đè** lên file `.bak` cũ để bảo toàn dữ liệu gốc của người dùng.
   - Trong `load_config()`: Nếu `config.json` không tồn tại, trống (0 bytes), hoặc bị hỏng cú pháp JSON do crash bất ngờ: hệ thống tự động kiểm tra và phục hồi toàn bộ cài đặt từ `config.json.bak`, đồng thời tự động khôi phục lại file `config.json` chính.
2. **Bảo vệ tuyệt đối cấu hình trong Updater (`ballontranslator/utils/updater.py`)**:
   - Trước khi cập nhật: Hàm `backup_source()` tự động sao lưu toàn bộ thư mục `config/` của người dùng sang khu vực an toàn.
   - Khi cài đặt bản cập nhật: Trong cả `_replace_directory()` và `_replace_file()`, bổ sung bộ lọc bảo vệ ngăn chặn việc xóa bỏ hoặc ghi đè bất kỳ file cấu hình nào của người dùng (`config.json`, `config.json.bak`, `folder_history.json`, v.v.).
3. **Script đóng gói phát hành (`scripts/build_win_minimal.ps1`)**:
   - Thêm danh sách loại trừ không đóng gói file cá nhân của lập trình viên (`config.json`, `*.bak`, `folder_history.json`, `logs`, `.btrans_cache`, `tmp`) vào file zip phát hành `Ballonstranslator_win_minium.zip`. Người dùng khi giải nén đè bản mới sẽ không bao giờ bị ghi đè mất file cấu hình hiện tại.

---

## 3. Danh sách các file triển khai & chỉnh sửa

| File | Nội dung thay đổi |
| :--- | :--- |
| `ballontranslator/ui/color_dialog.py` | **[MỚI]** Module quản lý bảng màu, nạp màu khi khởi động, lưu màu tức thời qua `get_color_dialog_color` và `sync_custom_colors_to_config`. |
| `ballontranslator/utils/config.py` | Thêm trường `custom_colors` vào `ProgramConfig`, kiểm tra/làm sạch dữ liệu khi nạp, cơ chế tự động phục hồi từ `config.json.bak` khi nạp lỗi và tự động duy trì sao lưu khi lưu. |
| `ballontranslator/ui/custom_widget/label.py` | Sử dụng `get_color_dialog_color` trong `ColorLabel.mousePressEvent()`. |
| `ballontranslator/ui/text_engine/effects/cards.py` | Sử dụng `get_color_dialog_color` khi chọn màu stroke, shadow, glow. |
| `ballontranslator/ui/text_engine/effects/gradient_editor.py` | Gọi `sync_custom_colors_to_config` sau khi chọn màu stop gradient. |
| `ballontranslator/ui/mainwindow.py` | Nạp màu khi mở app (`restore_custom_colors`), đồng bộ màu trước khi lưu và đóng app. |
| `ballontranslator/utils/updater.py` | Sao lưu `config/` trước khi update, chặn ghi đè/xóa các file cấu hình người dùng. |
| `scripts/build_win_minimal.ps1` | Loại trừ file cấu hình người dùng và cache runtime khỏi gói zip phát hành. |
| `tests/test_custom_colors_persistence.py` | **[MỚI]** Bộ 7 unit tests tự động kiểm tra lưu/phục hồi custom colors, phục hồi từ `.bak`, và bảo vệ cấu hình trong updater. |

---

## 4. Hướng dẫn bảo toàn khi Pull / Merge từ Upstream

Khi đồng bộ mã nguồn mới từ tác giả gốc (`dmMaze/BallonsTranslator`):
1. **Kiểm tra `ballontranslator/utils/config.py`**:
   - Đảm bảo trong `ProgramConfig` vẫn có trường `custom_colors: List[str] = field(default_factory=list)`.
   - Đảm bảo trong `load_config()` vẫn còn đoạn kiểm tra `bak_path` và tự động cứu hộ từ `config.json.bak`.
   - Đảm bảo trong `save_config()` vẫn duy trì lệnh sao lưu `shutil.copy2(..., bak_path)`.
2. **Kiểm tra `ballontranslator/ui/mainwindow.py`**:
   - Đảm bảo trong `__init__` vẫn có `restore_custom_colors()`.
3. **Kiểm tra `ballontranslator/utils/updater.py`**:
   - Đảm bảo trong `_replace_file` và `_replace_directory` có lệnh bảo vệ không xóa/ghi đè thư mục `config/`.
