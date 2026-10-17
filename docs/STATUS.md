# Kết quả kiểm chứng hiện tại

## Mô hình đã cài

Mô hình thật từ Wikipedia tiếng Việt (dump 01/10/2026, 80.000 bài) và OPUS/OpenSubtitles v2018; không trộn câu mẫu tự soạn. Đã xác minh MD5 chính thức của Wikimedia; TLS giữ nguyên. OPUS đọc gzip hoàn tất, chưa có checksum độc lập của nhà phát hành trong quy trình.

- 8.169.345 câu huấn luyện; 78.064.093 lượt âm tiết hợp lệ, giữ 78.060.212 lượt sau lọc unigram hiếm.
- 7.880 unigram, 816.675 bigram, 1.666.758 trigram; SQLite 51,6 MiB; quality=corpus.
- SHA-256: `52847125dd6f51d79fe956b19ea3150ee1abb3a634201198c8afcb7e47e121d8`.
- Đã sao lưu mô hình mẫu vào data/backups/ trước khi thay, giữ whitelist người dùng. Bootstrap không ghi đè mô hình thật.

## Kiểm chứng đạt trên Linux

- Python 3.12.14, PySide6 6.8.3, python-docx 1.2.0. Đã cài từ lockfile có hash ở virtualenv sạch; pip check không có phụ thuộc hỏng.
- **190 bài pytest đạt**: ngôn ngữ, Unicode/run, thứ tự bảng, thể thức, kế thừa style/theme, worker/cancel Qt, chia dữ liệu, cài mô hình an toàn và 14 ca HD05 mới.
- **17 kiểm tra sản phẩm đạt trên mô hình thật**: ba lỗi quyết định, câu mất dấu, giữ Tôi/đang, không sửa cống Đôi, viết hoa Nhất, minh tế/sử lý và các ca sạch.
- GUI offscreen chạy vòng lặp Qt và worker thật với Word mẫu: bảng 16 phát hiện, đủ an→ăn, .→?, di→đi. Có kiểm tra vị trí UTF-16 sau emoji.
- Xuất/đọc lại RED, TRACK, PLAIN, HIGHLIGHT bằng mô hình thật; nội dung sửa đúng và HIGHLIGHT giữ nguyên chữ. Kiểm thử bảo vệ bản gốc, định dạng không liên quan và revision XML.
- Lõi soát được kiểm tra khi socket bị chặn; ứng dụng không truy cập mạng khi chạy.
- **32 kiểm tra phát hành đạt trên mã nguồn và 32 kiểm tra đạt trên binary PyInstaller Linux**: model doctor, các ca lỗi/sạch, HD05 đúng/sai, xuất/đọc lại bốn chế độ của hai hồ sơ, giữ nguyên bản gốc, GUI worker cả hai hồ sơ. Báo cáo ở data/release-check/ và data/release-frozen-linux/. Binary đã thử trong đường dẫn có khoảng trắng và chữ Việt.
- Mẫu HD05 đúng (kế hoạch và công văn) không có phát hiện với mô hình thật; mẫu cố ý sai phát hiện các lỗi số văn bản, cỡ/nghiêng trích yếu, ngày tháng, lùi đầu dòng, chức vụ và nơi nhận. Đây là ca hồi quy tự dựng, không thay thế bộ lỗi văn bản thực tế.

## Đo phát triển

300 câu wiki và 300 câu OPUS giữ ngoài tập train; loại câu trùng khỏi cả hai nguồn. Đã dùng chúng chẩn đoán bộ soát, nên đây **chưa phải kiểm định mù hoặc bộ lỗi hành chính tự nhiên gán nhãn**.

| Mức Cân bằng | Câu gốc có phát hiện | Token gốc bị đánh dấu | Phương ngữ: phát hiện | Thiếu một ký tự: phát hiện | Bỏ dấu: phát hiện |
| --- | --- | --- | --- | --- | --- |
| Wiki | 59/300 (19,7%) | 1,28% | 93,0% | 77,7% | 86,3% |
| OPUS | 14/300 (4,7%) | 0,60% | 94,4% | 88,7% | 92,7% |

“Có phát hiện” bao gồm âm tiết lạ/từ ngoại lai và có thể có lỗi thật trong nguồn, không đồng nghĩa chắc chắn báo nhầm. “Phát hiện” lỗi nhân tạo gồm cảnh báo không có gợi ý, không đồng nghĩa sửa đúng. Top 1/top 5, mức Chặt, mẫu số và hash ở data/MODEL-CARD.md và các JSON đánh giá. Mức Chặt giảm nhiễu nhưng bỏ sót nhiều lỗi gõ. Không tuyên bố tái lập số đo tham chiếu.

## Pháp lý và phần còn lại

NĐ30: đã đọc PDF gốc từ cổng Chính phủ, OCR tra cứu và xem ảnh trang cho các điểm cần sửa; xem docs/LEGAL-REVIEW.md. Đã bảo vệ khoản/điểm viết thường trong viện dẫn, phân biệt trích yếu công văn 12–13 đứng với loại có tên 13–14 đậm, chấp nhận HÒA/HOÀ và giữ căn cứ biên tập riêng.

Đã nhận và đối chiếu **PDF 36 trang Hướng dẫn 05-HD/VPTW ngày 27/5/2026** do người dùng gửi; lưu tại docs/legal/HD05-VPTW-2026.pdf. Đã sửa các thông số kế thừa sai từ NĐ30 và cách nhận diện thành phần Đảng, gỡ cảnh báo “chưa đối chiếu bản gốc”. Không còn cần truy cập cổng bị chặn để hoàn tất đối chiếu tập quy tắc này. Xem docs/LEGAL-REVIEW.md cho căn cứ từng quy tắc và giới hạn về dàn trang, A5, lề hai mặt, tab, số trang, chữ ký/con dấu.

Đã build và kiểm chứng ONEDIR trên **Linux và Windows**. Lượt chạy GitHub [39010557364](https://github.com/thanhthuy92746g-lgtm/kiem-tra-chinh-ta/actions/runs/39010557364) thành công tại commit `39d31ecdd2f6bcce912f394147c103ae4724f95f`: pytest hai hệ qua, job đóng gói Windows qua đủ kiểm tra bằng executable và đạt giới hạn thư mục 250 MiB. Artifact bộ Windows khoảng 70,7 MB, artifact báo cáo khoảng 417 KB. Chưa xem GUI trên màn hình hoặc mở tệp xuất bằng Microsoft Word. Xem docs/GITHUB-BUILD.vi.md và docs/WINDOWS-RESULTS.json.

`tools/BUILD-WINDOWS.cmd` chuẩn bị một lượt cài, pytest, build và kiểm tra trên Windows x64 có Python 3.11 x64. Packager dùng chính hai executable để soát/xuất/kiểm tra GUI, đặt báo cáo vào BUILD-REPORT.json và chỉ tạo ZIP khi đạt kiểm tra cùng giới hạn 250 MiB. Từ chối mô hình mẫu trừ khi truyền rõ --allow-demo.

Workflow GitHub Actions đã chạy kiểm thử Linux/Windows rồi build **mô hình thật** trên Windows. `tools/ci_model.py` tạo gói riêng 18,1 MiB ở resources/trained-model.zip, gồm SQLite, từ vựng, báo cáo và ghi công; whitelist cá nhân được thay bằng tệp trắng. Đã thử đóng gói/khôi phục mô hình cục bộ, xác minh checksum và chạy lại đủ **32 kiểm tra phát hành trên mô hình vừa khôi phục**. Đã kiểm tra từ chối ghi đè thư mục có dữ liệu, checksum hỏng và thành phần ZIP ngoài danh sách; không đưa raw corpus/tài liệu người dùng vào gói CI. Người dùng đã đồng ý ghi GitHub, nhánh đã được đẩy và bộ exe đã được tạo trên runner Windows. Máy cloud hiện tại vẫn Linux, không chạy trực tiếp binary Windows tại đây.

Chỉ soát thân và bảng; chưa soát đầu/chân trang, footnote/endnote/textbox. Field/đối tượng/Track Changes sẵn có có giới hạn sửa tự động. Bộ sinh 25.481 dạng/từ vựng 7.880 ít hơn tham chiếu; có thể báo từ hiếm/ngoại lai và bỏ sót lỗi giống tên riêng. Cần bộ gán nhãn mới để đánh giá tổng quát.

## Cấu hình và bàn giao

Người dùng đã Lưu/Publish cấu hình; Python, mô hình quality=corpus và 190 kiểm thử đều còn hoạt động sau thao tác xuất bản. Chưa xác minh bằng một tác vụ cloud hoàn toàn mới. Hướng dẫn khởi động được cập nhật theo quy trình CI dùng mô hình thật và bản Windows đã tạo; không cần Publish môi trường để tải artifact. `tools/setup_cloud.sh` đã được chạy lại thành công, giữ nguyên hash mô hình; khi checkout sạch thiếu SQLite, script khôi phục ZIP mô hình đã kiểm chứng trước khi dùng mô hình mẫu.

Mã đã commit/push lên **build/windows-exe**, remote HEAD trỏ vào nhánh này. Mô hình thật dành cho CI đã có trong kho. Các gói nguồn cũ (source-demo, source-trained, source-trained-HD05) là các lần bàn giao trước, không phải bộ exe Windows. Bộ Windows tải từ GitHub Actions sau khi đăng nhập; endpoint tải artifact từ phiên cloud ẩn danh trả HTTP 404 nên binary chưa được đưa về máy Linux này.

Gói **VietSpell-source-trained-HD05-GitHub.zip** chứa quy trình build GitHub và tools/ci_model.py trước khi CI chạy; GitHub là nơi giữ mã mới nhất. Gói nguồn có mô hình ở data/; ZIP mô hình dành riêng cho GitHub không được chép lặp vào gói nguồn. Phạm vi đã ghi lên GitHub và hướng dẫn tải bộ Windows ở docs/GITHUB-BUILD.vi.md.
