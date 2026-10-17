# Chuẩn bị bản thử nghiệm Windows

Mã nguồn và mô hình đã vượt kiểm thử trên Linux; cần chạy bước này trên **Windows 10/11 x64** để tạo `.exe`. Chưa có binary Windows trong gói mã nguồn.

1. Cài **Python 3.11 x64** từ python.org, gồm Python Launcher (`py`).
2. Giải nén toàn bộ `VietSpell-source-trained-HD05.zip` vào thư mục làm việc, giữ nguyên `data/`.
3. Mở `tools/BUILD-WINDOWS.cmd`. Lần đầu cần Internet để cài thư viện đã khoá phiên bản/hash. Chương trình kiểm tra mô hình thật và không huấn luyện/tải lại ngữ liệu.
4. Khi báo thành công, mở `dist/VietSpell/VietSpell.exe`. Thư mục sản phẩm gồm cả `_internal/`, `data/`, `samples/`, `HUONG-DAN.md`, giấy phép và `BUILD-REPORT.json`. Không chỉ chép riêng tệp `.exe`.
5. Chạy thử trực tiếp: mở tệp `.docx`, chọn cả hai hồ sơ lần lượt, soát, duyệt gợi ý, xuất tệp. Mở các bản RED/TRACK/PLAIN/HIGHLIGHT trong `samples/` bằng Microsoft Word để kiểm tra cách hiển thị, revision và chữ đỏ/tô sáng. Thử thêm tài liệu thực đã bỏ thông tin riêng tư trước khi phát hành rộng.

Script chỉ tạo `dist/VietSpell-Windows-x64-trained.zip` sau khi build, kiểm tra tự động và kiểm tra kích thước thư mục dưới 250 MiB đều đạt. Báo cáo tự động không xác nhận việc mở GUI trên màn hình hay hiển thị trong Word; hai bước đó cần thực hiện trực tiếp. Script chưa được chạy trên Windows trong phiên cloud này.

Có thể dùng máy Windows của GitHub Actions thay cho cài công cụ trên máy cá nhân. Quy trình và phạm vi ghi vào kho được ghi tại [GITHUB-BUILD.vi.md](GITHUB-BUILD.vi.md). Cần đưa mã nguồn và gói mô hình CI vào kho trước khi job này chạy; hiện mới chuẩn bị cục bộ, chưa đẩy lên GitHub.

Nếu lỗi, giữ nguyên phần thông báo lỗi để chẩn đoán. Không tắt kiểm tra hash/TLS, không thêm `--allow-demo` để vượt lỗi mô hình thật. Không cần cung cấp GitHub token cho quy trình build cục bộ này.
