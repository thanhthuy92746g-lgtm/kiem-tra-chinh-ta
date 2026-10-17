# VietSpell

Ứng dụng **Python 3.11+ / PySide6** soát chính tả, ngữ cảnh và thể thức tiếng Việt trong tệp Word `.docx`. Tài liệu được xử lý tại máy, không gọi API, không tải mô hình và không gửi dữ liệu qua mạng khi chạy.

Đây là bản triển khai mới từ đặc tả được cung cấp, không phải mã nguồn hoặc mô hình của bản tham chiếu. Môi trường cloud và gói `source-trained` có mô hình **Wikipedia + OPUS/OpenSubtitles**: 8.169.345 câu, khoảng 78,1 triệu lượt âm tiết, từ vựng 7.880 mục, SQLite 51,6 MiB. Không đưa các câu mẫu tự soạn vào mô hình này. Xem `data/MODEL-CARD.md` để đọc phép đo thực tế và giới hạn chất lượng; gợi ý ngôn ngữ vẫn cần người dùng duyệt.

`data/` không được theo dõi trong Git. Với checkout chưa có dữ liệu, `bootstrap_data.py` tạo **mô hình mẫu nhỏ** từ các câu tự soạn lặp 1.000 lần, chỉ để thử chức năng. Script giữ nguyên mô hình đã có; không dùng `--force` nếu muốn giữ mô hình thật. Mô hình mẫu không báo âm tiết lạ hàng loạt và hạn chế tìm gần đúng vì từ vựng quá nhỏ; không dùng nó để kết luận chất lượng soát văn bản thực tế.

## Tải bản Windows đã đóng gói

Đã build và kiểm tra trên Windows bằng GitHub Actions: [lượt chạy thành công](https://github.com/thanhthuy92746g-lgtm/kiem-tra-chinh-ta/actions/runs/39047586753). Đăng nhập GitHub, vào **Artifacts**, tải **VietSpell-Windows-x64-trained** (khoảng 70,8 MB). Giải nén ZIP tải về và ZIP bên trong đến khi thấy thư mục `VietSpell`, rồi mở `VietSpell.exe`. Giữ nguyên toàn bộ `_internal/` và `data/`; không cần cài Python để dùng bản này.

Bộ 222 pytest đã qua trên Linux/Windows; bộ đóng gói đã vượt 36 kiểm tra bằng executable, gồm hai hồ sơ và bốn chế độ xuất Word. Vẫn cần người dùng thử GUI trên màn hình và mở kết quả trong Microsoft Word. Artifact được giữ 14 ngày; có thể chạy lại workflow khi cần bản mới.

## Chạy từ mã nguồn trên Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --require-hashes -r requirements-dev.lock
.venv\Scripts\python -m pip install --no-deps --no-build-isolation -e .
.venv\Scripts\python tools\bootstrap_data.py
.venv\Scripts\python -m vietspell doctor
.venv\Scripts\python -m vietspell gui
```

Linux tương tự, thay `.venv\Scripts\python` bằng `.venv/bin/python`. Cần các thư viện hệ thống Qt để mở cửa sổ trên Linux. Môi trường không có màn hình có thể dùng `QT_QPA_PLATFORM=offscreen` khi kiểm thử. Không cần Microsoft Word để đọc/ghi tệp.

Trong môi trường cloud checkout ở `/workspace/kiem-tra-chinh-ta`, có thể chạy `bash tools/setup_cloud.sh`. Script không thay mô hình sẵn có và không tải ngữ liệu lớn. `requirements-dev.lock` khoá phiên bản cùng hash gói cho Linux/Windows/macOS; chỉ cần mạng ở giai đoạn cài phụ thuộc và tải ngữ liệu có chủ đích.

`data/` nằm ở gốc checkout hoặc cạnh tệp `.exe`. Có thể đặt biến `VIETSPELL_DATA` hoặc dùng tham số toàn cục `--data` để chọn thư mục khác. Mọi đường dẫn làm việc đều có thể chứa khoảng trắng/chữ tiếng Việt. Công cụ khởi tạo giữ mô hình đã có, chỉ thay khi truyền `--force`.

## Quy trình sử dụng

1. Mở `.docx`, chọn hồ sơ văn bản, bấm **Soát lỗi (F5)**.
2. Xem số lỗi và cảnh báo mô hình trong dải thông báo; chọn dòng để xem nguyên nhân, căn cứ và vị trí.
3. Chọn các gợi ý muốn sửa, có thể tự sửa nội dung gợi ý. **Chấp nhận tất cả** chỉ chọn các lỗi thay chữ được; bộ lọc không thay đổi lựa chọn.
4. Xuất sang tên tệp mới: chữ đỏ (**RED**), theo dõi thay đổi (**TRACK**), sửa giữ định dạng (**PLAIN**), hoặc tô sáng mọi chỗ nghi vấn (**HIGHLIGHT**, không thay chữ). Gốc không bị ghi đè.
5. Định dạng cỡ chữ/đậm/nghiêng, lề và thành phần còn thiếu cần chỉnh trong Word. Gợi ý là hỗ trợ biên tập, người dùng quyết định theo ngữ cảnh.

Phạm vi đọc gồm phần thân và bảng lồng nhau theo thứ tự XML, kể cả hyperlink và content control. Đầu/chân trang, chú thích, hộp văn bản chưa được soát. Các chỗ chứa field/đối tượng hoặc thay đổi cũ được từ chối sửa tự động để giữ cấu trúc. Với tệp có Track Changes, phần đã xoá không được soát. Hãy chấp nhận/từ chối thay đổi cũ trước khi sửa tại các chỗ đó. Không hỗ trợ `.doc`, `.docm`, tệp mã hoá.

## CLI

```powershell
.venv\Scripts\python -m vietspell check --text "Hôm nay bạn an gì. Tôi đang di chơi."
.venv\Scripts\python -m vietspell check van-ban.docx --report bao-cao.json
.venv\Scripts\python -m vietspell fix van-ban.docx -o da-soat.docx --mode TRACK
.venv\Scripts\python -m vietspell --data D:\mo-hinh doctor
```

`check`: mã thoát 0 nếu không có phát hiện, 1 nếu có phát hiện, 2 nếu lỗi vận hành. `fix`: tự áp các gợi ý thay chữ đầu tiên, mã 0 khi xuất thành công; nên dùng GUI khi cần duyệt từng chỗ. Báo cáo JSON có vị trí ký tự NFC, loại lỗi, mức độ, nguyên nhân, căn cứ và các gợi ý. Không xuất nguyên văn tài liệu đầy đủ vào báo cáo nhưng các trích đoạn lỗi vẫn có thể chứa dữ liệu riêng tư.

## Mô hình ngữ liệu thật

Các công cụ dưới `tools/` chỉ phục vụ phát triển; tải ngữ liệu là bước có chủ đích, tách khỏi ứng dụng ngoại tuyến. Chừa ít nhất 6 GB dung lượng cho SQLite tạm. Không sử dụng PhoBERT/PyTorch/transformers.

```powershell
.venv\Scripts\python tools\download_corpus.py viwiki opensubtitles
.venv\Scripts\python tools\prepare_corpus.py --wiki data/raw/viwiki-pages-articles.xml.bz2 --subtitles data/raw/opus-opensubtitles-vi.txt.gz --out data/prepared-v2 --max-articles 80000 --heldout 300
.venv\Scripts\python tools\build_ngram.py -i data/prepared-v2/wiki-train.txt -i data/prepared-v2/opus-train.txt --out data/trained-candidate --prune-every 150000 --min-unigram 4 --min-bigram 4 --min-trigram 5
```

Các bước đánh giá và cài ứng viên an toàn xem [quy trình dữ liệu](docs/DATA-PIPELINE.md). Dùng thư mục đầu ra mới nếu dữ liệu cũ đã có.

Đang chuẩn bị thử ngữ liệu công khai phục vụ văn bản Công an nhân dân theo [kế hoạch và báo cáo pilot](docs/NEWS-PILOT.vi.md): ưu tiên Bộ Công an, Báo Công an nhân dân, Công an tỉnh Ninh Bình và một số tỉnh khác. Hạn mức nguồn lưu ở [cấu hình lấy mẫu](resources/police-pilot.json). Ba miền chính còn bị proxy chặn; chưa train bằng bài báo. Đối chứng Wikipedia riêng đã đo trên cùng bộ lỗi với bản hiện tại, trượt 3/17 ca hồi quy nên không thay mô hình trong exe. Công cụ nghiên cứu RSS/tách bài/so sánh nằm dưới tools/, không được gọi khi dùng ứng dụng.

Huấn luyện lọc từ vựng bằng âm tiết sinh theo luật, ghi unigram/bigram/trigram lên đĩa theo lô, chỉ loại mục hiếm ở bước cuối để không làm mất số đếm tích luỹ. `--prune-every` được giữ tên theo đặc tả nhưng là chu kỳ **ghi bộ đệm**, không xoá n-gram mỗi lô. Nếu huấn luyện bị ngắt, kiểm tra rồi xoá `_ngram-staging.sqlite` trước khi chạy lại; mô hình cũ chỉ được thay sau khi hoàn tất. Giải mã wiki ở mức đơn giản, chưa tương đương bộ trích xuất MediaWiki chuyên dụng.

Nguồn: `dumps.wikimedia.org` (dump Wikipedia 01/10/2026), `object.pouta.csc.fi` (OPUS/OpenSubtitles v2018). Cả hai đã được tải thành công. Wikipedia đã khớp checksum MD5 do Wikimedia công bố; SHA-256 bổ sung lưu bản đã tải. OPUS chưa có checksum độc lập từ nhà phát hành trong quy trình này, gzip kiểm tra CRC khi đọc hết. TLS luôn được xác minh. 300 câu wiki và 300 câu hội thoại được giữ riêng, loại câu trùng khỏi cả hai tập huấn luyện. Các tập này cũng được dùng chẩn đoán bộ soát nên kết quả sau sửa là đo phát triển, chưa phải kiểm định mù.

```powershell
# input phải là ngữ liệu giữ riêng, chưa dùng huấn luyện
.venv\Scripts\python tools\evaluate.py --input data/heldout.txt --sentences 300
.venv\Scripts\python tools\evaluate.py --input data/heldout.txt --sentences 300 --min-confusion 2.5 --min-fuzzy 4.0 --min-diacritic 1.0 --context-threshold -3.0
```

Không sử dụng bộ câu mẫu để báo cáo độ chính xác. Các số 291 bài, 7,8 triệu câu, 55,8 MB, 196 MB và tỉ lệ phát hiện trong đặc tả là số của **bản tham chiếu**, không thay thế kết quả của bản triển khai này. Bộ sinh âm tiết hiện sinh 25.481 dạng; chỉ các dạng quan sát đủ tần suất mới vào mô hình. Chưa tái lập đúng bộ sinh 41.632 dạng/từ vựng 8.722 mục của bản tham chiếu.

## Thể thức và căn cứ

Hồ sơ `HC-ND30` theo các mục Nghị định 30/2020/NĐ-CP mà đặc tả nêu. Mỗi phát hiện giữ căn cứ riêng; dấu cách, dấu câu, tab, dòng trống và dấu hỏi được ghi **“Chuẩn mực biên tập — không có quy định pháp quy trực tiếp”**.

Đã đối chiếu các quy tắc NĐ30 đang áp dụng với bản PDF gốc trên cổng Chính phủ và hồ sơ `DANG-HD05` với **Hướng dẫn số 05-HD/VPTW ngày 27/5/2026** (PDF 36 trang do người dùng cung cấp). Xem [ghi chép đối chiếu và phạm vi còn cần kiểm tra trong Word](docs/LEGAL-REVIEW.md). Đã sửa mẫu số văn bản Đảng, công văn 12 nghiêng, chức vụ người ký không đậm, danh sách nơi nhận 12 và căn cứ riêng từng hồ sơ. Nhận diện theo vị trí có độ tin cậy trung bình và mức cảnh báo thấp hơn; “chưa nhận diện” không đồng nghĩa chắc chắn thiếu thành phần.

Không tự viết hoa “khoản”, “điểm” trong viện dẫn: phạm vi ở cuối Mục V.7 nêu phần/chương/mục/tiểu mục/điều. Trích yếu công văn sau V/v dùng cỡ 12–13, chữ đứng; không áp nhầm quy tắc trích yếu văn bản có tên loại (13–14 đậm). Không bắt đổi “HÒA/HOÀ” giữa hai cách đặt dấu trong quốc hiệu viết hoa.

Đặc tả có mâu thuẫn ở ví dụ số `CAT-ANKT` (“không có gạch nối” nhưng chuỗi có gạch nối). Bộ nhận diện dùng mẫu tên loại văn bản/`V/v` và vị trí, không suy luận tên loại chỉ dựa trên việc có dấu `-` trong mã đơn vị.

Đã đối chiếu tài liệu phát triển bổ sung và sửa kiểm tra định dạng khi số văn bản/ngày tháng cùng một đoạn: mỗi phần có vùng ký tự riêng, tránh báo nhầm chữ đứng/nghiêng và bỏ sót chuỗi cỡ chữ. Xem [kết quả tiếp nhận và kiểm chứng](docs/REFERENCE-REVIEW.vi.md). Artifact Windows dẫn ở đầu tài liệu đã chứa bản sửa và được kiểm tra bằng executable.

## Kiểm thử và đóng gói

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.venv\Scripts\python -m pytest -q -p no:cacheprovider
.venv\Scripts\python tools\make_sample.py --out data/sample.docx
.venv\Scripts\python tools\make_party_sample.py --out data/sample-party.docx --letter
.venv\Scripts\python -m vietspell check data/sample.docx
.venv\Scripts\python tools\check_release.py
# Chỉ chạy trên Windows 10/11 x64 để tạo .exe Windows:
.venv\Scripts\python tools\package_windows.py
```

PyInstaller **ONEDIR**, gồm `VietSpell.exe`, `vietspell-cli.exe`, `_internal/`, `data/`, hướng dẫn và giấy phép. Đã tạo/kiểm tra tự động `.exe` trên runner Windows của GitHub, đạt giới hạn thư mục 250 MiB. GUI offscreen/CLI và các tệp Word xuất đã được kiểm tra tự động; vẫn cần xem GUI trực tiếp và mở các kiểu xuất trong Microsoft Word. Script không gọi onefile và không nhúng đường dẫn máy phát triển.

Với gói source-trained đầy đủ: trên Windows 10/11 x64 đã cài **Python 3.11 x64**, mở `tools/BUILD-WINDOWS.cmd`. Script cài theo lockfile, chạy pytest, build, soát bằng chính các executable, thử GUI của cả hai hồ sơ, xuất/đọc lại bốn chế độ và chỉ tạo ZIP Windows khi các kiểm tra đạt và thư mục dưới 250 MiB. Kết quả ở `dist/VietSpell/` và `dist/VietSpell-Windows-x64-trained.zip`. Cần mạng để cài phụ thuộc lần đầu; ứng dụng sau đóng gói hoạt động ngoại tuyến. Packager đã chạy thành công trên Windows CI; trình chạy `.cmd` cho máy cá nhân chưa được thử trực tiếp.

Workflow `.github/workflows/check.yml` chạy kiểm thử Linux/Windows. Khi đẩy nhánh `build/windows-exe` hoặc chạy `workflow_dispatch`, job Windows khôi phục **mô hình thật** từ `resources/trained-model.zip`, xác minh checksum/từ vựng/SQLite và build, kiểm tra hai executable trước khi lưu artifact `VietSpell-Windows-x64-trained`. Không dùng mô hình demo cho job phát hành. Gói mô hình CI được tạo bằng `python tools/ci_model.py prepare`, không kèm whitelist cá nhân, raw corpus hoặc tài liệu người dùng. Gói source-trained đã chứa `data/` nên không chép lặp ZIP mô hình CI vào ZIP nguồn; chạy lệnh prepare nếu muốn dùng CI từ gói nguồn. Xem [phạm vi đã đưa lên GitHub và kết quả](docs/GITHUB-BUILD.vi.md). Người dùng đã cho phép ghi kho và nhánh đã được đẩy; lượt chạy `39047586753` thành công.

## Kiến trúc

`core/`: chuẩn hoá, tokenizer, âm tiết, n-gram chỉ đọc, ứng viên hai mức chi phí, beam khôi phục dấu, tên riêng, thể thức. `docx_io/`: đọc theo thứ tự XML, nhận diện thành phần, kế thừa định dạng và ghi bốn chế độ. `service.py`: phiên tài liệu bất biến từ byte nguồn. `gui/`: Qt Fusion + QPalette sáng, NoticeBar sáu trạng thái, worker QThread và huỷ tác vụ. SQLite được mở trong luồng sử dụng, không chia sẻ connection giữa GUI/worker.

## Giấy phép

Mã nguồn MIT, xem `LICENSE.txt`. PySide6/Qt theo LGPLv3/GPL hoặc giấy phép thương mại tương ứng; xem `THIRD-PARTY-NOTICES.md`. Khi dùng ngữ liệu thật phải ghi công Wikipedia CC BY-SA 4.0 và OPUS/OpenSubtitles, đồng thời kiểm tra quyền phân phối từng nguồn. Dự án không cung cấp giấy phép thay cho nhà phát hành dữ liệu.
