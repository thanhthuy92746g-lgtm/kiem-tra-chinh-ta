# Tiếp nhận tài liệu phát triển bổ sung

Ngày 17/10/2026, người dùng bổ sung “PROMPT TÁI TẠO ỨNG DỤNG VIETSPELL”, phiên bản tài liệu 1.0, gồm 12 phần và 21 tình huống lỗi. SHA-256 bản nhận: `f6b35abcfbb9b2248857d35788daf08eaeb68e067c6b59d650a13a5da37b3ce1`.

Tài liệu được dùng để đối chiếu hành vi và yêu cầu phát triển trên ứng dụng hiện có. Những câu khẳng định “đã hoàn thành”, số đo và thông số pháp lý trong tài liệu không tự trở thành kết quả đã kiểm chứng của checkout này. Không xây dựng lại ứng dụng từ đầu hoặc thay mô hình chỉ vì nhận thêm bản mô tả tham chiếu.

## Phần đã có và cách tiếp nhận

| Nội dung tài liệu | Hiện trạng / quyết định |
| --- | --- |
| Word `.docx`, Python/PySide6, chạy ngoại tuyến | Đã có; tiếp tục giữ việc thu ngữ liệu trong công cụ phát triển, ngoài đường chạy ứng dụng |
| N-gram SQLite chỉ đọc, nội suy cố định 0,75/0,65 | Đã có; không thay công thức hoặc thay trọng số theo số đếm |
| Khôi phục dấu, đóng băng thanh, ngưỡng theo độ dài, giữ tên riêng | Đã có; ca sản phẩm an/ăn, di/đi, cai nay, Co/Có, cống Đôi, Nhất tiếp tục được kiểm chứng với mô hình thật |
| Đọc bảng/đoạn theo thứ tự XML, bản đồ Unicode và nhiều run | Đã có; không đổi thứ tự duyệt hoặc làm phẳng mất vị trí |
| Chỗ trống chờ ký số, gạch ngang Word, tab lùi đầu dòng, kế thừa style | Đã có ca hồi quy; chấp nhận tab đầu dòng là quy ước nhận diện, vẫn cần xem vị trí dừng tab trong Word |
| Số và ngày chung một đoạn, mục 6.7 / lỗi #12 | Tìm thấy khoảng trống kiểm tra định dạng; đã sửa như mô tả dưới đây |
| Dải thông báo, độ nhạy, QThread, màu sáng, lọc lỗi | Đã có; lỗi định dạng cần sửa trong Word không có ô gợi ý thay chữ giả |
| Bốn chế độ RED/TRACK/PLAIN/HIGHLIGHT | Đã có; giữ bản gốc, trường/đối tượng và thay đổi cũ vẫn có giới hạn đã công bố |
| Hồ sơ NĐ30 và HD05 | Tiếp tục dùng các quy tắc đã đối chiếu PDF, xem [LEGAL-REVIEW.md](LEGAL-REVIEW.md) |
| Đóng gói ONEDIR, mục tiêu dưới 250 MiB | Bản Windows cập nhật đã qua kiểm tra executable (36 ca) và giới hạn 250 MiB; vẫn cần xem GUI và Word trực tiếp |

Các nhóm hồi quy ở Phần 9 được đối chiếu với `tests/test_core.py`, `test_engine.py`, `test_docx.py`, `test_format.py`, `test_gui.py`, `test_hd05.py` và công cụ kiểm tra phát hành. Không dùng tổng số bài của bản tham chiếu để kết luận đã tái lập đầy đủ bản đó.

## Sửa kiểm tra số/ngày chung một đoạn

Ví dụ đầu trang có `Số: 123/CAT-ANKT` ở bên trái và `Ninh Bình, ngày 02 tháng 10 năm 2026` ở bên phải, ngăn bằng tab. Số dùng chữ đứng, ngày dùng chữ nghiêng. Trước đây cả hai thành phần đều trỏ vào toàn bộ đoạn, khiến mỗi quy tắc đọc cả các run của phần còn lại: có thể báo số bị nghiêng và ngày không nghiêng dù từng phần đúng. Chuỗi cỡ chữ Quốc hiệu/Tiêu ngữ/Ngày cũng có thể bị bỏ qua khi cả đoạn chứa nhiều cỡ.

Đã sửa:

- Thành phần số và ngày có phạm vi ký tự riêng; ngày giữ cả địa danh.
- Kiểm tra đậm/nghiêng/cỡ chữ và vùng cảnh báo chỉ đọc các run thuộc thành phần đó.
- Chuỗi cỡ chữ NĐ30 dùng cỡ phần ngày, không dùng cả đoạn số/ngày.
- Nhận diện số Đảng ở đầu đoạn có khoảng trắng hoặc sau tab/xuống dòng; không biến mọi chữ “Số” trong thân câu thành điểm bắt đầu số Đảng.
- Giữ địa danh khi tab nằm bên trong dòng ngày; không chỉ kiểm tra phần sau tab.

Thêm **15 ca hồi quy**: hai hồ sơ, thứ tự số/ngày, Unicode dựng sẵn/tổ hợp, đúng/sai kiểu nghiêng từng phần, chuỗi cỡ chữ và tab bên trong ngày. Đây là fixture kiểm tra chức năng, không phải ngữ liệu train hoặc bộ đo độ chính xác hành chính.

Không bổ sung quy định pháp lý mới. Bố trí thực tế sau dàn trang, căn tab, đường kẻ, thẩm quyền và chữ ký vẫn cần kiểm tra trong Word.

## Những điểm không lấy nguyên từ bản mô tả

- Các số 291 bài kiểm thử, 7.789.035 câu, từ vựng 8.722, 55,8 MB và 196 MB thuộc bản tham chiếu. Mô hình hiện tại vẫn là 8.169.345 câu, từ vựng 7.880, SQLite khoảng 51,6 MiB.
- Không dùng nhận định “báo nhầm trên văn bản hành chính bằng 0” làm cam kết sản phẩm. Chưa có bộ lỗi hành chính tự nhiên độc lập, gán nhãn đủ để kết luận đó; câu nguồn chưa rà không mặc nhiên là câu sạch.
- HD05 trong bảng tóm tắt chưa nêu đủ khác biệt: số/ngày 14 pt; chức vụ người ký 14 đứng **không đậm**; danh sách nơi nhận 12; trích yếu công văn 12 nghiêng. Giữ kết quả đối chiếu PDF ngày 27/5/2026, không chép các giá trị kế thừa từ NĐ30.
- Viện dẫn “khoản”, “điểm” không bị tự viết hoa theo NĐ30 V.7. Quy tắc trích yếu công văn tách khỏi trích yếu văn bản có tên loại.
- Ví dụ phân loại theo có/không có gạch nối sau `/` tự mâu thuẫn với `CAT-ANKT`; không thêm cách suy luận chỉ từ dấu gạch trong mã đơn vị.
- Không vá toàn cục `tempfile` hoặc nới quyền môi trường khi không có lỗi cài đặt tương ứng. Môi trường hiện tại đã chạy được phụ thuộc và bộ kiểm tra.

## Kiểm chứng và bàn giao

- **222 pytest đạt trên Linux**: 190 bài của bản exe cũ, 17 bài công cụ nghiên cứu và 15 ca mới của lần sửa này.
- Công cụ kiểm tra phát hành trên mã nguồn đạt **36/36**: mô hình thật, ca ngôn ngữ lỗi/sạch, HD05 đúng/sai, tám lượt xuất Word của hai hồ sơ, giữ nguyên bản gốc và hai worker GUI offscreen; thêm bốn kiểm tra số/ngày chung đoạn đúng và cố ý sai trên hai hồ sơ. Báo cáo tại `data/release-check-windows-update-source-final-20261017/release-report.json`. Bộ kiểm tra này cũng chạy bằng hai executable trước khi tạo artifact Windows mới.
- Mô hình/ngưỡng ngôn ngữ không đổi; không huấn luyện lại hoặc dùng các ca thử để báo tăng độ chính xác.
- Artifact Windows mới từ [lượt chạy 39047586753](https://github.com/thanhthuy92746g-lgtm/kiem-tra-chinh-ta/actions/runs/39047586753), commit `87ad671141925d64fad86d08ff39dcbc070deb27`, đã chứa bản sửa. Bộ 222 pytest Linux/Windows đạt; executable vượt 36 kiểm tra và giới hạn 250 MiB. Gói khoảng 70,8 MB, artifact `12106607575`. Lượt `39010557364` là bản cũ. Vẫn cần xem GUI trực tiếp và mở tệp xuất trong Microsoft Word; xem docs/WINDOWS-RESULTS.json.
- Nghiên cứu nguồn Công an giữ nguyên phạm vi và kết quả ở [NEWS-PILOT.vi.md](NEWS-PILOT.vi.md). Việc sửa ứng dụng ngoại tuyến không phụ thuộc vào việc mở được các nguồn báo.
