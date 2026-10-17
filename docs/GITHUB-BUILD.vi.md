# Build Windows bằng GitHub Actions — chuẩn bị để duyệt

Mục tiêu: tạo và kiểm tra `.exe` trên runner **windows-latest** của GitHub, dùng mô hình thật hiện có. Người dùng không cần cài Python/PyInstaller trên máy cá nhân cho bước build này.

## Phạm vi dự kiến ghi vào GitHub

- Kho: `thanhthuy92746g-lgtm/kiem-tra-chinh-ta`.
- Nhánh dự kiến: `build/windows-exe`; hiện kho chưa có commit/nhánh main trên remote, không ghi đè nhánh có sẵn.
- Mã nguồn, kiểm thử, hướng dẫn, PDF HD05 làm căn cứ, lockfile, thông báo giấy phép và workflow `.github/workflows/check.yml`.
- Gói `resources/trained-model.zip` khoảng **18,1 MiB**: SQLite đã kiểm chứng, từ vựng, báo cáo đánh giá, nguồn mô hình và ghi công. SHA-256 gói hiện tại: `eb73a9a7daa39cc695690d42c394293781123713469a00f535d7e79820fdd304`. Gói dùng whitelist trắng, không chép whitelist cá nhân.
- Không đưa raw corpus, `.venv`, cache, tệp Word đầu vào của người dùng hoặc tệp xuất cá nhân vào kho. Các Word mẫu được tạo từ câu minh hoạ trong mã để kiểm thử.

Nội dung đưa lên tuân theo chế độ công khai/riêng tư hiện có của kho. Hiện chỉ chuẩn bị cục bộ, **chưa commit/push và chưa chạy GitHub Actions**. Quyền ghi mã/mô hình vào GitHub cần người dùng xác nhận trước khi thực hiện.

## Các bước tự động sau khi push

1. Cài Python 3.11 và các gói đúng lockfile/hash; chạy pytest trên Linux và Windows.
2. Nếu kiểm thử đạt, runner Windows khôi phục mô hình từ ZIP vào `data/` trống. Kiểm tra hash từng tệp, hash SQLite đã cố định, quick_check, vocabulary và báo cáo hồi quy. Không bootstrap mô hình mẫu.
3. Build ONEDIR bằng PyInstaller, kiểm tra bằng chính `VietSpell.exe` và `vietspell-cli.exe`: ca lỗi/sạch, HD05 đúng/sai, bốn kiểu xuất của hai hồ sơ, bản gốc không đổi và worker GUI offscreen.
4. Chỉ khi đạt kiểm tra và thư mục dưới 250 MiB mới tạo `VietSpell-Windows-x64-trained.zip`; lưu tại artifact **VietSpell-Windows-x64-trained**, giữ 14 ngày. Báo cáo chẩn đoán được giữ riêng nếu có.

Workflow chỉ có quyền `contents: read`; không tạo GitHub Release hoặc ghi ngược vào kho. Người dùng tải artifact ở tab **Actions** sau khi job thành công. Bản tải về cần giải nén toàn bộ, mở GUI trên Windows thật và xem các tệp xuất trong Microsoft Word trước khi coi là hoàn tất kiểm chứng trực quan.

## Chuẩn bị/kiểm tra gói mô hình tại máy phát triển

```bash
.venv/bin/python tools/ci_model.py prepare
.venv/bin/python tools/ci_model.py restore --data build/ci-model-verified
VIETSPELL_DATA="$PWD/build/ci-model-verified" .venv/bin/python tools/check_release.py --out build/ci-model-release-check
```

Chọn thư mục đích mới; restore từ chối ghi đè nơi đã có dữ liệu. Bản nguồn tải về có `data/` nhưng không chép lặp ZIP CI để tránh tăng kích thước; prepare tạo lại ZIP từ mô hình đã kèm. Không dùng --allow-demo để vượt lỗi build mô hình thật. SHA-256 ZIP có thể thay đổi khi đóng gói lại do timestamp; hash SQLite cố định vẫn được kiểm chứng độc lập.
