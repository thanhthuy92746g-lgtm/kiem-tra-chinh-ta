# VietSpell — hướng dẫn sử dụng bản Windows

Giải nén **toàn bộ** thư mục VietSpell, rồi mở `VietSpell.exe`. Giữ `_internal/` và `data/` cùng thư mục với chương trình. Không cần cài Python hoặc Microsoft Word để soát và xuất `.docx`; Microsoft Word giúp xem kết quả và sửa định dạng.

1. Mở tệp Word `.docx` và chọn hồ sơ **Văn bản nhà nước — NĐ30** hoặc **Văn bản Đảng — HD05** (05-HD/VPTW ngày 27/5/2026).
2. Giữ mức **Cân bằng**, bấm **Soát lỗi** hoặc F5. Nếu nhiều cảnh báo không phù hợp ngữ cảnh, thử mức Chặt.
3. Bấm từng phát hiện để xem nguyên nhân, căn cứ và gợi ý. Chỉ chọn những sửa đổi phù hợp; có thể tự nhập gợi ý. Tên riêng, thuật ngữ và từ hiếm cần người đọc quyết định.
4. Xuất sang tệp mới: **RED** sửa bằng chữ đỏ; **TRACK** dùng theo dõi thay đổi; **PLAIN** sửa trực tiếp; **HIGHLIGHT** giữ nguyên chữ và tô sáng chỗ cần xem.
5. Mở bản xuất trong Word để kiểm tra nội dung và định dạng trước khi sử dụng. Bản gốc được giữ nguyên. Các cảnh báo lề, cỡ chữ, đậm/nghiêng và thành phần thể thức cần sửa trực tiếp trong Word.

Ứng dụng xử lý tại máy, không gửi tài liệu qua mạng. Mô hình huấn luyện từ Wikipedia và OPUS; đây là bản thử nghiệm, không bảo đảm mọi gợi ý đều đúng. Báo cáo JSON có thể chứa trích đoạn tài liệu.

Chỉ soát phần thân và bảng. Đầu/chân trang, chú thích, hộp văn bản, vị trí thực tế sau dàn trang, con dấu và chữ ký số cần kiểm tra trong Word. Văn bản có field hoặc Track Changes cũ có thể cần xử lý trước khi sửa tự động. Không mở trực tiếp `.doc`, `.docm` hoặc tệp có mật khẩu.

`samples/` gồm bản nhà nước, bản Đảng, công văn Đảng đúng/sai và các bản xuất để kiểm tra. `BUILD-REPORT.json` ghi kiểm tra tự động của bộ chương trình; không thay thế việc xem trực tiếp GUI và Word trên máy Windows.
