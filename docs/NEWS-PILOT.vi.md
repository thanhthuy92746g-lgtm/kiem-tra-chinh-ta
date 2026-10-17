# Thử ngữ liệu công khai phục vụ văn bản Công an nhân dân

Mục tiêu là kiểm tra liệu ngữ liệu báo chí đã biên tập có giúp giảm gợi ý sai trong văn bản trang trọng. Đây là thử nghiệm dữ liệu, không thay ứng dụng hoặc mô hình đang dùng. Không có mã RSS/thu thập nào chạy trong ứng dụng ngoại tuyến.

## Điều chỉnh theo mục đích sử dụng trong Công an nhân dân

Theo yêu cầu người dùng, nguồn ưu tiên chuyển sang Bộ Công an, Báo Công an nhân dân, Công an tỉnh Ninh Bình và một số Công an tỉnh khác. Cấu hình có thể đọc bằng máy ở `resources/police-pilot.json`.

| Nguồn dự kiến | Hạn mức bài toàn văn được nhận | Tỷ lệ ngân sách 60 bài | Vai trò |
| --- | ---: | ---: | --- |
| Cổng Bộ Công an — bocongan.gov.vn | 18 | 30% | Ngôn ngữ cơ quan, hướng dẫn thủ tục, phổ biến quy định |
| Báo Công an nhân dân — cand.com.vn | 18 | 30% | Văn phong biên tập và cách dùng thuật ngữ trong ngữ cảnh |
| Công an tỉnh Ninh Bình — congan.ninhbinh.gov.vn | 15 | 25% | Nhu cầu địa phương, tên cơ quan và địa danh |
| Ba Công an tỉnh khác, chưa chọn miền | 9, tối đa 3/tỉnh | 15% | Đối chiếu khả năng áp dụng ngoài Ninh Bình |

Đây là **hạn mức lấy mẫu ban đầu trước loại trùng/chia tập**, không phải tỷ lệ phối trộn với 78 triệu lượt âm tiết của mô hình hiện tại, cũng không phải trọng số tối ưu đã đo được. Không đủ nguồn nào thì ghi thiếu, không bù bằng các nguồn khác. Công cụ đã áp dụng trần 18/18/15 trên cả nhiều feed cùng miền; 9 bài tỉnh khác được giữ dự phòng, hiện chưa có miền đăng ký nên chưa thể thu. Sau lọc phải báo cả số bài, số câu và lượt âm tiết theo nguồn; số bài bằng nhau không đảm bảo lượng văn bản bằng nhau. Đợt 60 bài trước hết kiểm chứng quy trình và lỗi báo nhầm điển hình, chưa đủ để hứa cải thiện mô hình lớn. Không nhân bản bài để đạt tỷ lệ.

Ưu tiên nội dung công khai có văn phong gần tài liệu sử dụng: thông báo, chỉ đạo/triển khai công tác, cải cách hành chính, hướng dẫn cư trú/căn cước, giao thông, phòng cháy chữa cháy, phổ biến pháp luật và công tác xây dựng lực lượng. Giới hạn tin tường thuật vụ việc, lời thoại trích dẫn và bài lặp; bỏ quảng cáo/giải trí không liên quan. Rà câu sạch thay vì mặc nhiên coi mọi bài chính thống không có lỗi. Bài đăng lại giữa Bộ, báo và địa phương phải cùng một nhóm khi chia dữ liệu.

Ba miền trên là đích cần kiểm tra, **chưa xác minh trực tiếp danh tính website, liên kết chính thức, RSS, điều kiện sử dụng hoặc HTML trong phiên này** vì đều bị proxy CONNECT 403 khi đọc robots.txt. Kết quả lưu tại `data/news-pilot/police-source-probe-1.json`. Khi truy cập được, đối chiếu liên kết từ cổng Bộ/tỉnh và thông tin cơ quan chủ quản trước khi nhận bài. Chọn ba tỉnh bổ sung từ liên kết chính thức, không tự tạo miền theo tên tỉnh và không mở wildcard. Nếu nguồn không có RSS, có thể bổ sung bộ đọc trang chuyên mục công khai sau khi kiểm tra robots/HTML; hiện công cụ chưa thực hiện cách này.

**Đã xác nhận người dùng xuất bản cấu hình mới**: backend trả revision=null, phiên bản `a0400ba7-9431-485f-9d06-e5d91584a49b~cecfgver_6ad354d41a6c8192bb90a66542869e64`, có đủ ba miền chính và giữ các miền/preset cũ. Không cần Lưu/Xuất bản lại cùng nội dung. Kiểm tra sau xuất bản: ba miền Công an vẫn CONNECT 403; GitHub và vanban.chinhphu.vn HTTP 200 trên cùng máy. Lỗi còn ở đường truy cập các nguồn mới của phiên cloud hiện tại, chưa xác định là đồng bộ hay chính sách khác của nền tảng. Không suy luận rằng website không có RSS/không cho thu thập, và không xin token hoặc đổi proxy để vượt chặn. Bước chẩn đoán tiếp theo là phiên cloud mới dùng môi trường đã xuất bản; nếu vẫn lỗi, gửi báo cáo kết nối cho hỗ trợ nền tảng.

Tập đánh giá cần bao gồm câu của Ninh Bình, nguồn trung ương và một tỉnh được giữ hoàn toàn ngoài train/dev. `prepare --holdout-host MIEN_DA_DANG_KY` giữ toàn bộ nhóm bài/bản đăng lại của nguồn đó trong test, ngoài 20% nhóm test và 20% dev từ các nhóm còn lại. Ưu tiên giữ xuất xứ nguồn holdout khi câu bị đăng lại; manifest báo lượng câu/âm tiết sau lọc theo từng miền/tập. Chỉ thêm miền tỉnh đã xác minh vào `other_provinces.hosts` và mạng trước khi dùng. Kiểm tra phân bố thực tế sau chia, bổ sung nhóm độc lập nếu tập Ninh Bình quá ít; không chuyển bài sau khi đã xem kết quả test.

Thuật ngữ/tên cơ quan/cấp bậc/chữ viết tắt cần danh mục có căn cứ riêng để kiểm tra gợi ý sai; không biến mọi tên người hoặc từ lạ trong báo thành whitelist. Giữ ngày bài viết và tên đơn vị theo thời điểm, tránh coi tên lịch sử là lỗi chỉ vì tổ chức đã đổi. Quy tắc thể thức vẫn dựa trên NĐ30 và HD05 đã đối chiếu; bài báo không thay thế các căn cứ này. Chưa có quy tắc riêng nào của ngành được bổ sung chỉ từ nội dung tin.

Sau khi có câu đã rà, so mô hình hiện tại với ứng viên bổ sung dữ liệu trong thư mục riêng, trước hết không lặp/ngầm tăng trọng số ngữ liệu mới. Dùng dev quyết định có cần thu thêm hoặc thử tỷ lệ khác; giữ test tới cuối. Chưa có dữ liệu nên chưa thể tính tỷ lệ train tối ưu, tỷ lệ báo nhầm hoặc mức tăng chất lượng trong ngành.

## Trạng thái nguồn

Lượt trước đã thử robots.txt của **baochinhphu.vn**, **nhandan.vn**, **baotintuc.vn**, đều bị proxy CONNECT 403. Giữ lịch sử và các miền mạng cũ, nhưng ba nguồn này không nằm trong hạn mức thử chuyên ngành hiện tại. **Chưa tải bài báo hoặc train bằng tin báo từ bất kỳ nguồn nào**. Không suy luận rằng RSS có toàn văn hoặc nội dung được phép tái phân phối. Cấu hình ba miền Công an đã xuất bản nhưng truy cập từ máy đang chạy vẫn bị chặn; chỉ thử lại khi có trạng thái mạng mới hoặc trên phiên mới.

## Công cụ đã chuẩn bị

- `tools/news_pilot.py probe`: mặc định kiểm tra ba miền Công an chính; `--host` chọn một miền trong danh sách đã đăng ký. Đọc robots trước, tìm RSS/Atom được khai báo trên trang. Không tìm ra RSS thì kiểm tra mục RSS chính thức của báo; không khẳng định URL dự đoán là feed có thật.
- `collect`: lấy tối đa 60 bài từ feed đã xác minh, giới hạn 2 MiB/tài liệu, HTTPS, chỉ miền đã đăng ký, áp dụng trần từng nguồn Công an, giãn yêu cầu tối thiểu 2 giây/miền và tuân crawl-delay/robots. Trước khi thu thập phải có ghi chép đọc điều kiện sử dụng nguồn, `decision: local_pilot_only`, `basis_url` và `notes` trong JSON `--source-review`; đây là ghi nhận của người thực hiện, không phải yêu cầu người dùng xác nhận thêm một lần. Nguồn không phù hợp thì bỏ, không vượt chặn hoặc tìm đường vòng.
- RSS chỉ dùng khám phá URL/tiêu đề. Không dùng mô tả RSS làm toàn văn train. Bộ trích xuất chọn thân bài, loại điều hướng, quảng cáo, ảnh/chú thích, tin liên quan; không nhận diện được thân bài hoặc chỉ có bản xem trước thì bỏ. Các bộ chọn HTML mới chỉ thử bằng fixture, cần kiểm chứng trên mỗi báo khi truy cập được.
- Lưu URL, thời điểm lấy và hash nội dung ở `data/` bị Git bỏ qua; không đưa bài báo nguyên văn vào kho hoặc gói exe. Mọi bài mới mang nhãn `unreviewed_source` cho tới khi được rà nội dung.
- `prepare`: gom bài đăng lại/gần trùng (Jaccard shingles 5 từ >=0,8), tách nguyên nhóm bài thành train/dev/test theo seed 92746; 20% nhóm cho test, 20% cho dev. Bỏ câu chuẩn hoá trùng giữa các tập, ưu tiên giữ câu cho test. Đây là bộ lọc gần trùng đơn giản, vẫn cần xem các bản tin tổng hợp/diễn đạt lại.
- `tools/compare_models.py`: tạo lỗi nhân tạo **một lần từ mô hình tham chiếu**, đóng băng đầu vào/dataset hash và dùng cùng các ca cho tất cả mô hình. Không đổi mẫu số theo từ vựng từng mô hình. Phát hiện trên câu gốc chưa rà không được gọi là lỗi báo nhầm đã xác nhận.

Các kiểm thử công cụ bao gồm RSS/Atom, bỏ tóm tắt/điều hướng, chặn URL ngoài nguồn, bảo vệ dữ liệu, chia bài/câu không trùng, cùng một bộ lỗi giữa mô hình, hạn mức nguồn Công an qua nhiều feed và giữ riêng toàn nguồn kể cả bản đăng lại. Các câu tự soạn trong test chỉ kiểm tra công cụ, không dùng để train/đánh giá chất lượng mô hình thật. Kết quả chạy toàn bộ hiện tại ghi ở `docs/STATUS.md`. Không tạo lại exe trong thử nghiệm này.

## Đối chứng có thể làm trước khi mở mạng

Đã huấn luyện **Wikipedia riêng, bỏ hoàn toàn OPUS**, dùng đúng `data/prepared-v2/wiki-train.txt`, cùng bộ sinh và ngưỡng 4/4/5 của mô hình hiện tại. Không đổi luật/ngưỡng bộ soát.

| Thuộc tính | Mô hình hiện tại | Đối chứng Wiki riêng |
| --- | --- | --- |
| Câu train | 8.169.345 | 2.920.396 |
| Lượt âm tiết hợp lệ trước lọc mục hiếm | 78.064.093 | 45.323.822 |
| Từ vựng | 7.880 | 6.622 |
| Kiểm tra hành vi sản phẩm | 17/17 | **14/17** |
| Thay mô hình đang dùng | — | **Không** |

Đối chứng bỏ sót `an → ăn` trong “Hôm nay bạn an gì.”, `cai nay → cái này` trong câu mất dấu và `sử → xử` trong “Tôi sẽ sử lý hồ sơ.” Đây là hồi quy chức năng đã biết, không phải thống kê độ chính xác trên lỗi tự nhiên. Kết quả này chưa ủng hộ việc bỏ hoàn toàn phụ đề; không kết luận được tỷ lệ phối trộn tối ưu hoặc tác dụng của nguồn báo chí chưa có.

Trong mô hình hiện tại, Wikipedia chiếm khoảng **58,1% lượt âm tiết hợp lệ**, OPUS khoảng **41,9%** trước lọc mục hiếm. Không dùng tỷ lệ số câu để suy ra trọng số âm tiết: câu phụ đề ngắn hơn.

Các phép đo trên 300 câu wiki + 300 câu OPUS được ghi trong `data/news-pilot/comparison-*-fixed/`. Đây là tập giữ ngoài train nhưng đã dùng chẩn đoán bộ soát trước đây, **không phải kiểm định mù**. Bảng kết quả chỉ có ý nghĩa so sánh hai mô hình trên cùng ca lỗi nhân tạo. Các phát hiện trên văn bản gốc có thể là tên riêng/từ ngoại lai hoặc lỗi thực trong nguồn.

| Tập và chỉ số | Hiện tại: Wiki + OPUS | Wiki riêng |
| --- | --- | --- |
| Wiki: câu gốc có phát hiện | 58/300 | 57/300 |
| Wiki: sửa đúng top 1 lỗi thiếu ký tự nhân tạo | 162/300 (54,0%) | 167/300 (55,7%) |
| Wiki: sửa đúng top 1 lỗi mất dấu nhân tạo | 247/300 (82,3%) | 245/300 (81,7%) |
| OPUS: câu gốc có phát hiện | 14/300 | 36/300 |
| OPUS: sửa đúng top 1 lỗi thiếu ký tự nhân tạo | 179/282 (63,5%) | 120/282 (42,6%) |
| OPUS: sửa đúng top 1 lỗi mất dấu nhân tạo | 263/300 (87,7%) | 225/300 (75,0%) |

Trên wiki có chỉ số tăng nhẹ và chỉ số giảm; trên hội thoại việc bỏ OPUS làm giảm rõ khả năng sửa các lỗi thử. Tập hội thoại phù hợp với miền đã bị bỏ nên không dùng nó kết luận chất lượng văn bản hành chính. Chưa có bộ hành chính tự nhiên gán nhãn mới, chưa có dữ liệu báo để so sánh, không kết luận báo chí tốt/xấu hơn Wiki. Đối chứng không được promote vì trượt ba kiểm tra sản phẩm.

Bộ so sánh mới giữ nguyên dấu câu của đầu vào thay vì nối lại bằng dấu chấm như `evaluate.py`, đồng thời đóng băng lỗi theo từ vựng baseline. Vì vậy không so trực tiếp số câu gốc có phát hiện của bảng này với các báo cáo cũ khác harness. Hai mô hình trong bảng luôn dùng cùng đầu vào/cùng lỗi: hash tập wiki `00e5cd0d06f122924423d6c551bd2daa1819da540fd619d621ae5dea5a8cbe6d`, hash tập OPUS `edcdcaa1b86b1878c3ef8576628c472fb24d1f22c7832ae62fa470ae8e4dbdd2`.

## Tiếp tục sau khi mở mạng

Từ gốc checkout, dùng `.venv/bin/python`; không cần cài gói mới:

```bash
python tools/news_pilot.py probe --out data/news-pilot/police-source-probe-2.json
# Sau khi đọc robots/điều kiện và xác minh feed, tạo source-review.json rồi:
python tools/news_pilot.py collect --feed RSS_BO_DA_XAC_MINH --feed RSS_CAND_DA_XAC_MINH --feed RSS_NINH_BINH_DA_XAC_MINH --source-review data/news-pilot/source-review.json --limit 60 --out data/news-pilot/press-collection-1
python tools/news_pilot.py prepare --articles data/news-pilot/press-collection-1/articles.jsonl --out data/news-pilot/press-split-1
```

Chọn thư mục/filename mới, không ghi đè lần trước. `source-review.json` ghi quyết định từng miền, không để `local_pilot_only` khi chưa kiểm tra nguồn. Có thể thử nguồn công khai khác phù hợp nếu báo không cho sử dụng; không thu thập diện rộng ở giai đoạn này.

Trước khi thử mô hình bổ sung, rà một tập câu thực, ghi rõ ai rà và không mặc nhiên coi báo chí không có lỗi. Dùng **dev** để chọn phương án đã định trước; giữ **test** cho lượt đánh giá cuối. So trùng câu với cả wiki/OPUS train cũ và ngữ liệu train bổ sung, ví dụ:

```bash
python tools/compare_models.py --input data/news-pilot/press-split-1/test.jsonl --baseline data --candidate DUONG_DAN_MO_HINH_THU --baseline-train data/prepared-v2/wiki-train.txt --baseline-train data/prepared-v2/opus-train.txt --baseline-train data/news-pilot/press-split-1/train.txt --out data/news-pilot/press-comparison-1
```

Chỉ giữ phương án nếu giảm gợi ý sai trên câu đã rà và vẫn bắt/sửa được lỗi; phải qua hồi quy sản phẩm và kiểm tra Word/GUI. Nếu không thấy lợi ích rõ thì giữ mô hình hiện tại. Không tự promote, đóng gói lại hoặc đưa mô hình/bài báo lên GitHub chỉ dựa trên kết quả thử nhỏ.
