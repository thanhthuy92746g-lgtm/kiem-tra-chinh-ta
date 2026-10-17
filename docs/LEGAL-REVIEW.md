# Đối chiếu hồ sơ NĐ30 và HD05 với tài liệu gốc

## Nghị định 30/2020/NĐ-CP

Nguồn: [bản PDF ký số Nghị định 30/2020/NĐ-CP trên cổng Chính phủ](https://datafiles.chinhphu.vn/cpp/files/vbpq/2020/03/30.signed.pdf), gồm 76 trang. SHA-256 tệp đã đọc: `be2514460c953141923579e4a0ddd0249c611643a59514976790dc1d90589178`.

Tệp là bản quét. Đã OCR các trang để tra cứu và xem ảnh trang gốc cho các điểm cần hiệu chỉnh; OCR không được coi là bản pháp lý thay thế. Đây là đối chiếu nội dung quy tắc với NĐ30 gốc, không phải xác nhận toàn bộ tình trạng hiệu lực/sửa đổi của pháp luật đến hiện tại.

| Quy tắc | Vị trí gốc | Trang PDF | Kết quả |
| --- | --- | --- | --- |
| A4, lề, Times New Roman Unicode, màu đen | Phụ lục I, Phần I, Mục I.1–4 | 21 | Phù hợp thông số hồ sơ HC-ND30 |
| Quốc hiệu 12–13 đậm; tiêu ngữ 13–14 đậm | Phụ lục I, Phần I, Mục II.1; bảng Mục V | 21, 32 | Phù hợp |
| Cơ quan chủ quản chữ đứng; cơ quan ban hành đậm | Phụ lục I, Phần I, Mục II.2; bảng Mục V | 22, 32 | Không áp quy tắc in đậm của người ký lên cơ quan chủ quản |
| Số/ký hiệu, khoảng để trống chờ điền | Phụ lục I, Phần I, Mục II.3 | 22–23 | Mẫu số rỗng được nhận diện; ứng dụng không coi khoảng chờ ký số là lỗi khoảng trắng |
| Ngày nhỏ hơn 10, tháng 1/2 thêm số 0 | Phụ lục I, Phần I, Mục II.4.b | 23 | Phù hợp |
| Trích yếu có tên loại 13–14 đậm | Phụ lục I, Phần I, Mục II.5; bảng Mục V | 24, 32 | Phù hợp |
| Trích yếu **công văn** sau V/v 12–13, chữ đứng | Phụ lục I, Phần I, Mục II.5; bảng Mục V | 24, 33 | Bổ sung vai trò `letter_subject`; không áp nhầm quy tắc trích yếu có tên loại |
| Nội dung 13–14, căn đều, lùi 1/1,27 cm, cách đoạn tối thiểu 6pt, dòng đơn đến 1,5 | Phụ lục I, Phần I, Mục II.6.e | 25 | Phù hợp; việc coi tab đầu dòng là tương đương là quy ước nhận diện của ứng dụng, không phải một điều khoản riêng của NĐ30 |
| TM., Q., KT., TL., TUQ. | Phụ lục I, Phần I, Mục II.7.b | 25–26 | Phù hợp |
| Nơi nhận: nhãn 12 đậm/nghiêng, danh sách 11 đứng | Phụ lục I, Phần I, Mục II.9; bảng Mục V | 28, 34 | Phù hợp |
| Chuỗi cỡ quốc hiệu + 1 = tiêu ngữ = địa danh/ngày | Chú thích 1 ở bảng Mục V | 32 | Có căn cứ cụ thể |
| Viết hoa đầu câu; tên người, địa danh, cơ quan | Phụ lục II, Mục I–IV | 37–38 | Các luật miễn soát chỉ là heuristic hỗ trợ, không phải bộ nhận diện tên riêng đầy đủ |
| Nhân dân, Nhà nước | Phụ lục II, Mục V.1 | 38 | Không báo nhầm viết hoa “Nhân dân” |
| Viện dẫn phần/chương/mục/tiểu mục/điều | Phụ lục II, Mục V.7 | 39 | Văn bản gốc không yêu cầu viết hoa “khoản/điểm” trong viện dẫn; đã có kiểm thử bảo vệ |

Phụ lục I có một số quy định khoảng cách cụ thể ở thành phần thể thức (ví dụ gạch nối của tiêu ngữ, ký hiệu văn bản). Các luật khoảng trắng/dấu câu **chung** của bộ soát vẫn được ghi là chuẩn mực biên tập, không gán NĐ30 cho toàn bộ dấu câu hay câu hỏi.

Các cách đặt dấu `hòa/hoà`, `khỏe/khoẻ`, `hủy/huỷ` đều được nhận diện trong từ vựng. Bộ soát không dùng n-gram để bắt buộc chuyển giữa hai cách đặt dấu đã được chấp nhận này.

## Hướng dẫn số 05-HD/VPTW ngày 27/5/2026

Đã đối chiếu nội dung bản PDF **HD_05_VPTW_e1550.pdf** do người dùng cung cấp, 36 trang, với các quy tắc đang triển khai. Bản đọc được lưu tại [docs/legal/HD05-VPTW-2026.pdf](legal/HD05-VPTW-2026.pdf); SHA-256: `53bb4bc543cd1f19e0f60c861364ceab9c425bc54325c04be6a3ac99108650c5`. Đã trích xuất văn bản và xem ảnh bảng Phụ lục 2 để xác định chính xác cỡ chữ/đậm/nghiêng. Đây là kiểm tra nội dung bản được cung cấp, chưa xác minh chữ ký số của PDF.

| Quy tắc | Vị trí trong hướng dẫn | Trang PDF | Kết quả trong ứng dụng |
| --- | --- | --- | --- |
| Tiêu đề Đảng 15, đứng, đậm, hoa | Phần II, I.1; Phụ lục 2, mục 1 | 2, 31 | Phù hợp |
| Cơ quan cấp trên 14 đứng, không đậm; cơ quan ban hành 14 đậm | Phần II, I.2; Phụ lục 2, mục 2 | 6, 31 | Không nhầm dấu `*` thành tên cơ quan |
| Số 05-HD/VPTW; số dưới 10 thêm 0; phân cách `-` và `/` | Phần II, I.3.2.2; Phụ lục 2, mục 3 | 9, 31 | Bổ sung nhận diện số văn bản Đảng, không dùng mẫu Số: 05/HD-VPTW của hệ nhà nước |
| Số/ký hiệu cỡ 14 đứng | Phụ lục 2, mục 3 | 31 | Sửa giá trị 13 kế thừa nhầm từ NĐ30 |
| Địa danh/ngày tháng cỡ 14 nghiêng; ngày dưới 10, tháng dưới 3 thêm 0 | Phần II, I.4.2.2; Phụ lục 2, mục 4 | 10, 31 | Dùng căn cứ HD05, không gán căn cứ NĐ30 |
| Tên loại 15–16 đậm, hoa; trích yếu 14–15 đậm | Phần II, I.5; Phụ lục 2, mục 5 | 10–11, 31 | Trích yếu là cụm từ, không tự coi chữ thường đầu trích yếu là lỗi đầu câu |
| Công văn không ghi tên loại; trích yếu dưới số/ký hiệu, cỡ 12 nghiêng | Phần II, I.5.1.1, I.5.2.3; Phụ lục 2, mục 5 | 10–11, 32 | Nhận diện “về việc…” nhiều dòng; chỉ gợi ý đổi V/v ở đầu dòng, không thay chỗ trích dẫn trong thân bài |
| Nội dung 14–15 đứng, căn đều, đầu dòng khoảng 10 mm, cách đoạn tối thiểu 6pt, Exactly 18–22pt | Phần II, I.6.2.2; Phụ lục 2, mục 6 | 12, 32 | Không dùng khoảng lùi 1–1,27 cm của hồ sơ NĐ30; tính khoảng cách Before/After giữa đoạn |
| T/M, K/T, T/L; Q. trong ví dụ quyền cấp trưởng | Phần II, I.7.1.1, I.7.1.2.c.iv | 13, 19 | Giữ Q.; TUQ. chỉ cảnh báo kiểm tra thẩm quyền, không tự suy đoán thay thế |
| Quyền hạn 14 đậm; chức vụ 14 đứng không đậm; họ tên 14 đậm | Phụ lục 2, mục 7 | 32–33 | Tách chức vụ khỏi yêu cầu in đậm của quyền hạn |
| Kính gửi/Kính trình 14 nghiêng; tên người nhận 14–15 đứng | Phần II, I.9; Phụ lục 2, mục 9 | 25, 33 | Kiểm tra riêng nhãn và tên ngay cả khi chung một đoạn, không nhầm với danh sách Nơi nhận |
| Nơi nhận 14 đứng có gạch chân; danh sách bên dưới 12 đứng | Phần II, I.9.2.1; Phụ lục 2, mục 9 | 24–25, 33 | Sửa cỡ 11 kế thừa nhầm từ NĐ30 và không bắt in đậm nhãn |
| TNR Unicode màu đen; A4; lề 20/20/30/15 mm | Phần II, IV.1–4 | 28 | Phù hợp hồ sơ trang dọc thông thường |

Các phát hiện chung về khoảng trắng, dấu câu và chữ đầu câu trong hồ sơ Đảng ghi căn cứ **biên tập**. Không áp quy tắc viết hoa viện dẫn của Phụ lục II NĐ30 như một điều khoản của HD05.

**Phạm vi đối chiếu có giới hạn:** ứng dụng kiểm tra một tập quy tắc, chưa tự kiểm chứng toàn bộ hướng dẫn. Cần xem trực tiếp đường kẻ/dấu sao/phân cách, vị trí bố trí sau dàn trang, bảng/phụ lục ngang, giấy hành chính A5, lề hai mặt, tab thực tế, số trang, nội dung chữ ký/con dấu và tính đúng thẩm quyền. Chỉ nhận diện thành phần theo văn bản/vị trí XML, không có bộ dàn trang Word; cảnh báo “chưa nhận diện” không khẳng định thành phần chắc chắn thiếu. Phần ngày, số và tên loại tham chiếu trong thân bài vẫn cần người đọc xem ngữ cảnh.

`tools/make_party_sample.py` tạo mẫu kế hoạch/công văn đúng và sai theo các con số trên. `tests/test_hd05.py` bảo vệ nhận diện, các kiểu chữ, đầu dòng, căn cứ và sự khác biệt giữa hai hồ sơ. `tools/check_release.py` chạy lại với mô hình thật, xuất bốn chế độ và kiểm tra worker GUI của cả hai hồ sơ; đây là hồi quy chức năng, không phải bộ đánh giá ngôn ngữ độc lập.
