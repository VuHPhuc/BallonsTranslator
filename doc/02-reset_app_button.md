# 02 - Nút Reset App Khởi Động Lại Ứng Dụng Nhanh

## 1. Mục đích tính năng
- Cho phép người dùng khởi động lại (restart/reset) toàn bộ ứng dụng nhanh chóng chỉ với 1 click ngay trên thanh tiêu đề (TitleBar).
- Giải phóng toàn bộ bộ nhớ RAM đệm, làm mới cấu hình, hoặc xử lý nhanh khi gặp sự cố mà không cần đóng mở lại thủ công.
- **Nguyên tắc an toàn (Side-by-Side)**: Thay vì xóa bỏ nút "Sponsor" gốc của tác giả upstream, nút "Reset App" được đặt ngay bên cạnh nút "Sponsor". Điều này giúp bảo toàn 100% tính năng gốc, tránh gây lỗi khi pull code upstream về.

---

## 2. Thiết kế giải pháp kỹ thuật

### 2.1. Giao diện TitleBar
- Nút `resetAppToolBtn` thuộc lớp `TitleBarToolBtn` đặt trên thanh tiêu đề.
- Sử dụng icon `rotation.svg` (mũi tên xoay tròn làm mới) từ hệ thống icon có sẵn của ứng dụng.
- Nhãn hiển thị: `Reset App`.
- Vị trí trong bố cục: Nằm ngay sau `toolsToolBtn` và `sponsorToolBtn`:
  ```python
  hlayout.addWidget(self.toolsToolBtn)
  hlayout.addWidget(self.sponsorToolBtn)
  hlayout.addWidget(self.resetAppToolBtn)
  ```

### 2.2. Luồng xử lý sự kiện
1. Người dùng nhấn nút "Reset App".
2. Ứng dụng lập tức phát tín hiệu `self.restart_signal.emit()` mà không cần hộp thoại xác nhận (reset tức thì).
3. Tín hiệu này đã được kết nối với hàm `launch.restart()` trong `launch.py`:
   - Lưu lại các thông số cấu hình và tham số dòng lệnh ban đầu.
   - Khởi động một tiến trình ứng dụng mới.
   - Đóng tiến trình hiện tại an toàn, giải phóng toàn bộ tài nguyên.

---

## 3. Các file và đoạn code liên quan

### 3.1. File: [ballontranslator/ui/mainwindowbars.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/ballontranslator/ui/mainwindowbars.py)
- **Khai báo nút**:
  ```python
  self.resetAppToolBtn = TitleBarToolBtn(self)
  self.resetAppToolBtn.setText(self.tr('Reset App'))
  self.resetAppToolBtn.setToolTip(self.tr('Restart application immediately'))
  self.resetAppToolBtn.setIcon(QIcon(themed_icon_path('rotation.svg')))
  self.resetAppToolBtn.setIconSize(QSize(16, 16))
  self.resetAppToolBtn.setToolButtonStyle(
      Qt.ToolButtonStyle.ToolButtonTextBesideIcon
  )
  self.reset_app_trigger = self.resetAppToolBtn.clicked
  ```
- **Thêm vào thanh layout**:
  ```python
  hlayout.addWidget(self.sponsorToolBtn)
  hlayout.addWidget(self.resetAppToolBtn)
  ```

### 3.2. File: [ballontranslator/ui/mainwindow.py](file:///d:/ai_stuff/Ballonstranslator_win_minium/ballontranslator/ui/mainwindow.py)
- **Kết nối trong `setupShortcuts()`**:
  ```python
  self.titleBar.reset_app_trigger.connect(self.on_reset_app)
  ```
- **Định nghĩa hàm xử lý (reset ngay lập tức)**:
  ```python
  def on_reset_app(self) -> None:
      self.restart_signal.emit()
  ```

---

## 4. Hướng dẫn bảo toàn chức năng khi Pull / Merge từ Upstream

Khi đồng bộ mã nguồn mới từ tác giả gốc (`dmMaze/BallonsTranslator`):

1. **Nếu xảy ra xung đột tại `mainwindowbars.py`**:
   - Upstream thường chỉ sửa đổi các menu `toolsMenu` hoặc `sponsor_menu`.
   - Giữ nguyên khối code tạo `self.resetAppToolBtn` và `hlayout.addWidget(self.resetAppToolBtn)` ngay cạnh `self.sponsorToolBtn`.

2. **Nếu xảy ra xung đột tại `mainwindow.py`**:
   - Đảm bảo trong `setupShortcuts()` vẫn còn dòng:
     ```python
     self.titleBar.reset_app_trigger.connect(self.on_reset_app)
     ```
   - Đảm bảo hàm `on_reset_app()` vẫn tồn tại trong lớp `MainWindow`.
