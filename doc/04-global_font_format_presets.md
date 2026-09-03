# 04 - Mẫu Định Dạng Phông Chữ Toàn Cục (Global Font Format Presets)

## 1. Mô tả tính năng
- Thanh công cụ **Global Font Format** nằm trong bảng định dạng văn bản (Text Panel).
- Cho phép người dùng lưu trữ, quản lý và áp dụng nhanh các mẫu định dạng phông chữ (preset styles) gồm: font family, cỡ chữ (pt), màu sắc, viền (stroke), giãn dòng, giãn chữ, căn lề và hiệu ứng chữ...
- Giúp dịch giả truyện tranh chuyển đổi nhanh phong cách thoại (nói chuyện bình thường, hét to, thì thầm, sfx hiệu ứng âm thanh, dẫn truyện, suy nghĩ nội tâm...) chỉ với 1 click.

---

## 2. Vị trí lưu trữ & Cấu trúc file

- File dữ liệu cấu hình: [config/textstyles/default.json](file:///e:/AI_STUFF/Ballonstranslator_win_minium/config/textstyles/default.json).
- Thư mục chứa: `config/textstyles/`.
- File này nằm trong danh mục bỏ qua của git (`.gitignore`), đảm bảo dữ liệu cá nhân của người dùng **không bao giờ bị ghi đè** khi chạy `git pull` hoặc `git merge` từ upstream.

---

## 3. Danh sách 14 mẫu phông chữ đã tích hợp sẵn

Toàn bộ 14 mẫu phong cách thoại tiếng Việt đã được sao chép và đồng bộ đầy đủ:

| STT | Tên Style (`_style_name`) | Phông chữ (`font_family`) | Kích thước (`size_pt`) | Mục đích sử dụng |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **NÓI CHUYỆN** | `MTO Astro City` | 14.25 pt | Thoại thông thường trong bong bóng thoại |
| **2** | **♡♥** | `LIT-Mango` | 7.5 pt | Thoại dễ thương, ngọt ngào, ngại ngùng |
| **3** | **sfx nhỏ** | `MTO augie` | 25.5 pt | Hiệu ứng âm thanh kích thước nhỏ |
| **4** | **Nói to** | `000 ObelixPro TB` | 18.75 pt | Lời thoại lớn tiếng, nhấn mạnh |
| **5** | **tức giận** | `MTO Getting Angry` | 70.5 pt | Hét to, tức giận, đe dọa |
| **6** | **dẫn truyện** | `MTO Canun` | 36.75 pt | Lời dẫn chuyện, hộp thoại trần thuật |
| **7** | **Cảm xúc** | `000 SignLanguage TB` | 11.25 pt | Biểu đạt cảm xúc nhẹ nhàng |
| **8** | **nội tâm** | `MTO COMIC 2` | 11.25 pt | Suy nghĩ thầm kín trong đầu |
| **9** | **sfx mỏng** | `SJ BOUNCY` | 9.0 pt | Âm thanh gõ nhẹ, bước chân mảnh |
| **10** | **sfx dày** | `SJ Brushzerker BB` | 27.0 pt | Âm thanh hành động, va chạm mạnh |
| **11** | **sfx nặng nề** | `VL DeathRattle BB` | 88.5 pt | Tiếng nổ lớn, sấm sét, đổ vỡ kinh hoàng |
| **12** | **đau buồn** | `SJ DownUnderEF` | 11.25 pt | Lời thoại buồn bã, u ám |
| **13** | **♡♥** | `SJ Your Highschool Crush` | 11.25 pt | Tỏ tình, lãng mạn tuổi học trò |
| **14** | **Chữ viết tay** | `Fz Fragrant` | 60.0 pt | Chữ viết tay trên thư từ, bảng hiệu, ghi chú |

---

## 4. Hướng dẫn Sao lưu & Khôi phục khi cài lại hoặc chuyển máy

1. **Sao lưu (Backup)**:
   - Copy file `config/textstyles/default.json` ra nơi an toàn.
   - Thư mục `fonts/` chứa 23 phông chữ đi kèm các mẫu trên.
2. **Khôi phục (Restore)**:
   - Dán file `default.json` vào thư mục `config/textstyles/`.
   - Đảm bảo các font chữ tương ứng đã được chép vào thư mục `fonts/`.
   - Khởi động lại ứng dụng, toàn bộ 14 nhãn mẫu sẽ xuất hiện ngay lập tức trong bảng **Global Font Format**.
