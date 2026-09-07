# 06 - Folder History & Startup Screen (Màn hình lịch sử thư mục khi khởi động)

## 1. Mục Đích & Vấn Đề Giải Quyết
- **Vấn đề**: Trước đây, khi khởi động ứng dụng, app thường tự động mở ngay thư mục gần nhất mà không cho người dùng lựa chọn dự án cần làm, hoặc người dùng khó theo dõi các thư mục truyện/chapter trước đó.
- **Giải pháp**:
  - Tạo một màn hình chào / thư viện lịch sử (**Folder History & Start Screen**) hiện đại, tự động hiển thị khi mở app (có checkbox bật/tắt theo ý muốn).
  - Lưu trữ toàn bộ lịch sử thư mục dưới dạng JSON tại `config/folder_history.json`. Vì thư mục `config/` nằm trong `.gitignore`, dữ liệu lịch sử này **hoàn toàn không bao giờ bị mất hoặc bị ghi đè khi pull/merge code từ upstream**.
  - **Tính năng Ngôi sao bảo vệ ⭐**:
    - Người dùng có thể bấm biểu tượng ngôi sao để đánh dấu yêu thích/bảo vệ thư mục quan trọng.
    - Ngôi sao có hiệu ứng đồ họa phát sáng vàng (`#FFB800`), tương tác đổi màu và scale hover sống động.
    - Khi bấm nút **"Xóa toàn bộ lịch sử" (Clear History)**, hệ thống **bảo toàn 100% tất cả các thư mục có gắn sao ⭐**, chỉ dọn dẹp các thư mục không gắn sao.
  - **Phím tắt nhanh**:
    - Tại bất kỳ màn hình làm việc/dịch nào, bấm **`Ctrl+O`** hoặc **`Ctrl+H`** sẽ lập tức mở lại màn hình Lịch sử thư mục.
    - Menu Mở file trên thanh công cụ bên trái (`LeftBar`) có sẵn mục chọn *"Folder History / Start Screen... (Ctrl+O)"*.

---

## 2. Kiến Trúc & Các File Triển Khai

| File | Vai trò |
| :--- | :--- |
| `ballontranslator/utils/folder_history.py` | Quản lý logic lịch sử, đếm số trang ảnh, lấy ảnh bìa truyện, lưu JSON nguyên tử (`.tmp` -> rename), phân loại và bảo vệ thư mục có gắn sao. |
| `ballontranslator/ui/folder_launcher_dialog.py` | Cửa sổ popup Launcher / Welcome độc lập, hiện lên ngay khi khởi động trước khi mở MainWindow (giúp màn hình dịch có thời gian tải ngầm); thẻ truyện hiển thị ảnh bìa, ngôi sao phát sáng ⭐, tìm kiếm tức thời. |
| `ballontranslator/launch.py` | Hiển thị `FolderLauncherDialog` trước khi tạo/hiển thị MainWindow. Khi người dùng chọn thư mục thì MainWindow mới mở trực tiếp thư mục đó; nếu người dùng ấn nút X hoặc phím Esc để đóng popup thì ứng dụng sẽ tắt hoàn toàn (không vào màn hình dịch). |
| `ballontranslator/ui/mainwindowbars.py` | Thêm signal `show_folder_history`, gắn action vào `openMenu` của `LeftBar` với shortcut `QKeySequence.Open` (`Ctrl+O`). |
| `ballontranslator/ui/mainwindow.py` | Kết nối phím tắt `Ctrl+O` / `Ctrl+H` và nút Open để mở lại popup Launcher bất cứ lúc nào trong khi dịch. |
| `tests/test_folder_history.py` | Bộ test tự động kiểm tra lưu trữ JSON, chuyển đổi sao ⭐, và xác nhận tính năng bảo toàn thư mục có sao khi dọn dẹp lịch sử. |
| `tests/test_folder_history_page_ui.py` | Bộ test offscreen Qt kiểm tra khởi tạo FolderLauncherDialog và mở thư mục mượt mà. |

---

## 3. Cấu Trúc File Dữ Liệu `config/folder_history.json`

```json
{
  "version": 1,
  "show_on_startup": true,
  "folders": [
    {
      "path": "D:/comics/chap1",
      "name": "chap1",
      "starred": true,
      "last_opened": 1725695000.0,
      "page_count": 32
    }
  ]
}
```

---

## 4. Hướng Dẫn Sử Dụng
1. **Khởi động ứng dụng**:
   - Màn hình Lịch sử thư mục sẽ xuất hiện ở giữa màn hình.
   - Click vào bất kỳ thẻ thư mục nào để mở ngay vào giao diện làm việc.
   - Hoặc click *"📂 Mở thư mục mới..."* để chọn một thư mục khác từ máy tính.
   - Nếu bấm nút **X** (hoặc phím **Esc**) ở góc trên bên phải để đóng popup, ứng dụng sẽ tắt hoàn toàn thay vì chuyển sang màn hình dịch.
2. **Gắn sao bảo vệ ⭐**:
   - Bấm vào biểu tượng ngôi sao bên phải mỗi thẻ để gắn sao/bỏ gắn sao.
   - Thư mục có gắn sao sẽ tự động được ưu tiên đưa lên đầu danh sách.
3. **Dọn dẹp lịch sử**:
   - Bấm nút *"🗑️ Xóa lịch sử (Giữ lại ⭐)"*.
   - Hệ thống sẽ chỉ xóa những thư mục chưa gắn sao, giữ lại an toàn mọi thư mục có sao.
4. **Mở lại màn hình lịch sử bất cứ lúc nào**:
   - Bấm **`Ctrl+O`** hoặc **`Ctrl+H`** trên bàn phím khi đang ở màn hình dịch.
