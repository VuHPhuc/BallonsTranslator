# 03 - Tự Động Đóng Cửa Sổ CMD Khi Tắt Bình Thường & Giữ CMD Khi Bị Crash/Lỗi

## 1. Mục đích tính năng
- **Khi người dùng tự tay tắt ứng dụng bình thường (Clean Exit)**:
  - Cửa sổ dòng lệnh CMD (khi chạy qua `launch_win.bat`) sẽ **tự động đóng hoàn toàn**, người dùng không phải bấm thêm phím nào (`Press any key to continue . . .`).
- **Khi ứng dụng bị lỗi hoặc crash bất thường (Crash / Error Exit)**:
  - Cửa sổ CMD **tuyệt đối không được đóng**, nó sẽ dừng lại ở lệnh `pause` để người dùng có thể đọc được chi tiết lỗi, vị trí file và Traceback nhằm phục vụ việc kiểm tra và sửa lỗi.

---

## 2. Thiết kế giải pháp kỹ thuật

### 2.1. Truyền Exit Code trong Python
Trong [ballontranslator/__main__.py](file:///e:/AI_STUFF/Ballonstranslator_win_minium/ballontranslator/__main__.py):
- Hàm `launch.main()` trả về kết quả của `app.exec()`, giá trị này bằng `0` khi ứng dụng đóng bình thường.
- Sử dụng `sys.exit()` để trả mã thoát này về cho hệ điều hành Windows:
  ```python
  import sys
  from .launch import main

  if __name__ == '__main__':
      exit_code = main()
      sys.exit(exit_code if isinstance(exit_code, int) else 0)
  ```
- Nếu xảy ra lỗi ngoại lệ (Unhandled Exception như `NameError`, `ImportError`, v.v.), Python sẽ tự động thoát với mã lỗi khác 0 (thường là `1`).

### 2.2. Điều hướng trong Batch Script (`launch_win.bat`)
Trong [launch_win.bat](file:///e:/AI_STUFF/Ballonstranslator_win_minium/launch_win.bat):
- Đoạn code khởi chạy ban đầu của upstream luôn có lệnh `pause`:
  ```batch
  :launch
  %PYTHON% -m ballontranslator  %*
  pause
  exit /b
  ```
- Được sửa thành:
  ```batch
  :launch
  %PYTHON% -m ballontranslator  %*
  if %ERRORLEVEL% equ 0 exit /b 0
  pause
  exit /b %ERRORLEVEL%
  ```
- **Cơ chế**:
  - Nếu `%ERRORLEVEL% equ 0`: ứng dụng đã đóng bình thường do tay người dùng -> gọi ngay `exit /b 0` để đóng cửa sổ CMD.
  - Nếu `%ERRORLEVEL% neq 0`: ứng dụng bị crash hoặc lỗi -> câu lệnh `if` không khớp, script tiếp tục chạy xuống lệnh `pause`, giữ cửa sổ CMD lại kèm thông báo `Press any key to continue . . .` để người dùng xem lỗi.

---

## 3. Các file và đoạn code liên quan

### 3.1. File: [ballontranslator/__main__.py](file:///e:/AI_STUFF/Ballonstranslator_win_minium/ballontranslator/__main__.py)
- Bổ sung `import sys` và truyền kết quả `exit_code` qua `sys.exit()`.

### 3.2. File: [launch_win.bat](file:///e:/AI_STUFF/Ballonstranslator_win_minium/launch_win.bat)
- Thêm điều kiện kiểm tra `%ERRORLEVEL% equ 0` trước lệnh `pause`.

---

## 4. Hướng dẫn bảo toàn chức năng khi Pull / Merge từ Upstream

Khi đồng bộ mã nguồn mới từ tác giả gốc (`dmMaze/BallonsTranslator`):

1. **Nếu `launch_win.bat` bị ghi đè**:
   - Mở file `launch_win.bat`, tìm đến nhãn `:launch`.
   - Đảm bảo ngay sau dòng `%PYTHON% -m ballontranslator  %*` có dòng:
     ```batch
     if %ERRORLEVEL% equ 0 exit /b 0
     ```

2. **Nếu `ballontranslator/__main__.py` bị ghi đè**:
   - Đảm bảo file vẫn sử dụng `sys.exit(exit_code)` thay vì chỉ gọi `main()` trần.
