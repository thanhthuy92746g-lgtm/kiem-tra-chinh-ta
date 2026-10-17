# Tái lập dữ liệu và kiểm tra mô hình

Mọi thao tác bên dưới chạy từ gốc dự án bằng Python trong `.venv`. Chỉ bước tải có mạng; huấn luyện, đánh giá và ứng dụng chạy ngoại tuyến. Không dùng các câu minh hoạ tự soạn trong tập huấn luyện thật hoặc để báo chất lượng của mô hình thật.

```powershell
python tools/download_corpus.py viwiki opensubtitles
python tools/prepare_corpus.py --wiki data/raw/viwiki-pages-articles.xml.bz2 --subtitles data/raw/opus-opensubtitles-vi.txt.gz --out data/prepared-v2 --max-articles 80000 --heldout 300
python tools/build_ngram.py -i data/prepared-v2/wiki-train.txt -i data/prepared-v2/opus-train.txt --out data/trained-candidate --min-unigram 4 --min-bigram 4 --min-trigram 5 --prune-every 150000
python tools/validate_model.py --data data/trained-candidate --output data/trained-candidate/model-validation.json
python tools/evaluate.py --data data/trained-candidate --input data/prepared-v2/wiki-heldout.txt --sentences 300 --output data/trained-candidate/evaluation-wiki.json
python tools/evaluate.py --data data/trained-candidate --input data/prepared-v2/opus-heldout.txt --sentences 300 --output data/trained-candidate/evaluation-opus.json
# Đóng ứng dụng, xem kết quả đánh giá trước khi thay mô hình:
python tools/promote_model.py --candidate data/trained-candidate
```

Chọn thư mục `--out` mới nếu đã có kết quả trước, không xoá/ghi đè ngữ liệu người dùng. Công cụ tải cũng bảo vệ tệp có sẵn. Wikimedia từ chối client Python mặc định trong lần thử; công cụ hiện tự khai báo User-Agent VietSpell, đọc checksum chính thức rồi dùng URL dump có phiên bản. MD5 của nhà phát hành được kiểm tra qua nguồn HTTPS; SHA-256 bổ sung dùng ghi nhận bản đã tải. Với OPUS chưa có checksum độc lập của nhà phát hành, TLS được giữ nguyên và gzip kiểm tra CRC khi đọc toàn bộ.

`prepare_corpus.py` bỏ namespace phụ, redirect, mẫu/bảng wiki và markup thường gặp. Giữ riêng các bài wiki đầu tiên đến khi đủ 300 câu (tối đa 3 câu/bài) và một phần đầu hội thoại để lấy 300 câu OPUS. Cả hai tập huấn luyện loại những chuỗi token trùng với bất kỳ câu giữ riêng nào. Đây là cách chia xác định để tái lập, **không phải khảo sát ngẫu nhiên đại diện** mọi loại văn bản tiếng Việt; bước làm sạch không phải trình render MediaWiki hoàn chỉnh.

`build_ngram.py` ghi theo lô lên SQLite, giới hạn bộ đệm SQLite 128 MiB, chỉ loại n-gram dưới ngưỡng khi hoàn tất. Nếu ngắt, mô hình cũ không bị thay; kiểm tra tệp `_ngram-staging.sqlite` trước khi khởi động lại ở thư mục mới. Giữ ít nhất 6 GB trống. Đừng chạy nhiều phiên huấn luyện cùng thư mục đầu ra.

`validate_model.py` chạy 17 kiểm tra hành vi sản phẩm trên chính file SQLite cần cài, không dùng fixture mẫu của pytest. `evaluate.py` đo phát hiện, gợi ý top 1/top 5 và số phát hiện trên câu gốc; mỗi loại lỗi nhân tạo có tối đa một lỗi/câu đủ điều kiện. Các phát hiện trên câu gốc chỉ là ước lượng báo nhầm: ngữ liệu nguồn có thể chứa lỗi/tên riêng/từ ngoại lai. Bộ đo không thay cho đánh giá lỗi tự nhiên có người gán nhãn.

Các câu giữ riêng đã được dùng để chẩn đoán quy tắc bộ soát sau lần đo đầu. Chúng vẫn không được đưa vào huấn luyện n-gram, nhưng các con số sau hiệu chỉnh là **đo phát triển**, không phải kiểm định mù cuối cùng. Báo cáo giữ hash mô hình và hash mã bộ soát để phân biệt các lần đo. Phải có tập gán nhãn mới trước khi tuyên bố độ chính xác trên văn bản hành chính thực tế.

Sau chẩn đoán, bộ soát miễn soát thêm tên nước ngoài viết hoa không khớp cấu trúc âm tiết/nhóm khôi phục dấu, đơn vị đi sau số, ký hiệu một chữ trong đoạn giải thích chữ/âm và cụm tên nối bằng gạch nối. Ứng viên tìm gần đúng đổi hai ký tự bị trừ 2 log10 điểm tiên nghiệm so với một ký tự. Các ngưỡng cấu hình mặc định của đặc tả được giữ nguyên; đã đo lại cả mức Cân bằng và Chặt. Đây là lựa chọn thận trọng, có thể bỏ sót lỗi giống tên nước ngoài hoặc lỗi hai ký tự.

`promote_model.py` kiểm tra lại hồi quy, SQLite và sự khớp của từ vựng trước khi thay mô hình. Nó sao lưu mô hình đang dùng vào `data/backups/`, dùng thay tệp nguyên tử và giữ `whitelist.txt` của người dùng. Bản sao mô hình mẫu được giữ để thử chức năng/đối chiếu; không tự khôi phục mẫu vào mô hình thật.
