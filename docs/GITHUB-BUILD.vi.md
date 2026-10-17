# Build Windows bằng GitHub Actions

Mục tiêu: tạo và kiểm tra `.exe` trên runner **windows-latest** của GitHub, dùng mô hình thật hiện có. Người dùng không cần cài Python/PyInstaller trên máy cá nhân cho bước build này.

## Phạm vi đã ghi vào GitHub theo sự đồng ý của người dùng

- Kho: `thanhthuy92746g-lgtm/kiem-tra-chinh-ta`.
- Nhánh: `build/windows-exe`; đã tạo commit đầu tiên của kho trên nhánh này, không ghi đè nhánh có sẵn. Remote HEAD hiện trỏ vào nhánh này.
- Mã nguồn, kiểm thử, hướng dẫn, PDF HD05 làm căn cứ, lockfile, thông báo giấy phép và workflow `.github/workflows/check.yml`.
- Gói `resources/trained-model.zip` khoảng **18,1 MiB**: SQLite đã kiểm chứng, từ vựng, báo cáo đánh giá, nguồn mô hình và ghi công. SHA-256 gói hiện tại: `eb73a9a7daa39cc695690d42c394293781123713469a00f535d7e79820fdd304`. Gói dùng whitelist trắng, không chép whitelist cá nhân.
- Không đưa raw corpus, `.venv`, cache, tệp Word đầu vào của người dùng hoặc tệp xuất cá nhân vào kho. Các Word mẫu được tạo từ câu minh hoạ trong mã để kiểm thử.

Người dùng đã đồng ý đưa mã/mô hình lên kho và chạy build Windows. Đã commit/push, theo dõi và sửa thiết lập CI. Lượt chạy [39047586753](https://github.com/thanhthuy92746g-lgtm/kiem-tra-chinh-ta/actions/runs/39047586753) tại commit `87ad671141925d64fad86d08ff39dcbc070deb27` thành công: bộ 222 pytest trên hai hệ và job đóng gói Windows đều đạt. Bản cập nhật đã sửa phạm vi số/ngày chung đoạn; bốn ca kiểm tra mới chạy bằng executable cho hai hồ sơ, không thay mô hình ngôn ngữ. Đã bổ sung thư viện EGL cho Linux và UTF-8 cho các lệnh Python trên Windows; không bỏ qua kiểm thử.

## Bản Windows đã tạo

- Artifact **VietSpell-Windows-x64-trained**, ID `12106607575`, khoảng **70,8 MB**; gồm ZIP bộ ONEDIR đã kiểm chứng bằng 36 kiểm tra phát hành. Digest SHA-256 của **artifact GitHub**: `9f372b7d8ad21e8ba6d2bb445c315294414d96bf9b31236b5c3e451edf9770c7` (không phải hash riêng của tệp exe hoặc ZIP bên trong).
- Artifact **VietSpell-Windows-build-reports**, ID `12106720675`, khoảng **560 KB**, giữ báo cáo/Word mẫu và các bản xuất dùng kiểm chứng.
- Vào trang run ở trên, đăng nhập GitHub rồi tải tại **Artifacts**. Endpoint tải không cho phiên ẩn danh trong cloud; binary chưa được tải về máy Linux này. Kết quả chạy Windows được xác minh qua trạng thái thành công của job, quy trình fail-on-error và sự tồn tại của hai artifact.
- Giải nén toàn bộ ZIP tải về và ZIP bộ chương trình bên trong, mở `VietSpell/VietSpell.exe`. Không cần Python. Cần thử trực tiếp GUI và xem tài liệu trong Microsoft Word để hoàn tất kiểm chứng trực quan.

## Các bước tự động sau khi push

1. Cài Python 3.11 và các gói đúng lockfile/hash; chạy pytest trên Linux và Windows.
2. Nếu kiểm thử đạt, runner Windows khôi phục mô hình từ ZIP vào `data/` trống. Kiểm tra hash từng tệp, hash SQLite đã cố định, quick_check, vocabulary và báo cáo hồi quy. Không bootstrap mô hình mẫu.
3. Build ONEDIR bằng PyInstaller, kiểm tra bằng chính `VietSpell.exe` và `vietspell-cli.exe`: ca lỗi/sạch, HD05 đúng/sai, bốn kiểu xuất của hai hồ sơ, bản gốc không đổi và worker GUI offscreen.
4. Chỉ khi đạt kiểm tra và thư mục dưới 250 MiB mới tạo `VietSpell-Windows-x64-trained.zip`; lưu tại artifact **VietSpell-Windows-x64-trained**, giữ 14 ngày. Báo cáo chẩn đoán được giữ riêng nếu có.

Workflow chỉ có quyền `contents: read`; không tạo GitHub Release hoặc ghi ngược vào kho. Người dùng tải artifact ở tab **Actions** sau khi job thành công. Bản tải về cần giải nén toàn bộ, mở GUI trên Windows thật và xem các tệp xuất trong Microsoft Word trước khi coi là hoàn tất kiểm chứng trực quan. Lượt thành công trước đó là `39010557364`; artifact của lượt đó chưa có bản sửa số/ngày chung đoạn.

## Chuẩn bị/kiểm tra gói mô hình tại máy phát triển

```bash
.venv/bin/python tools/ci_model.py prepare
.venv/bin/python tools/ci_model.py restore --data build/ci-model-verified
VIETSPELL_DATA="$PWD/build/ci-model-verified" .venv/bin/python tools/check_release.py --out build/ci-model-release-check
```

Chọn thư mục đích mới; restore từ chối ghi đè nơi đã có dữ liệu. Bản nguồn tải về có `data/` nhưng không chép lặp ZIP CI để tránh tăng kích thước; prepare tạo lại ZIP từ mô hình đã kèm. Không dùng --allow-demo để vượt lỗi build mô hình thật. SHA-256 ZIP có thể thay đổi khi đóng gói lại do timestamp; hash SQLite cố định vẫn được kiểm chứng độc lập.
