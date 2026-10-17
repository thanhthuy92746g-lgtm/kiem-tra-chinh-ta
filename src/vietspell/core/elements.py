from dataclasses import dataclass


@dataclass(frozen=True)
class ElementSpec:
    title: str
    sizes: tuple[int, int]
    bold: bool | None = None
    italic: bool | None = False
    uppercase: bool = False
    required: bool = False
    underline: bool | None = None


ND30_ELEMENTS = {
    "national": ElementSpec("Quốc hiệu", (12, 13), True, False, True, True),
    "motto": ElementSpec("Tiêu ngữ", (13, 14), True, required=True),
    "agency_parent": ElementSpec("Cơ quan chủ quản", (12, 13), False, uppercase=True),
    "agency": ElementSpec("Cơ quan ban hành", (12, 13), True, uppercase=True, required=True),
    "number": ElementSpec("Số, ký hiệu", (13, 13), required=True),
    "date": ElementSpec("Địa danh và ngày tháng", (13, 14), italic=True, required=True),
    "type": ElementSpec("Tên loại văn bản", (13, 14), True, uppercase=True),
    "subject": ElementSpec("Trích yếu", (13, 14), True),
    "letter_subject": ElementSpec("Trích yếu công văn", (12, 13), False),
    "body": ElementSpec("Nội dung", (13, 14), required=True),
    "authority": ElementSpec("Quyền hạn người ký", (13, 14), True, uppercase=True),
    "position": ElementSpec("Chức vụ người ký", (13, 14), True, uppercase=True),
    "signer": ElementSpec("Họ tên người ký", (13, 14), True),
    "recipients_label": ElementSpec("Nơi nhận", (12, 12), True, True, required=True),
    "recipients": ElementSpec("Danh sách nơi nhận", (11, 11)),
}
HD05_ELEMENTS = {
    "party": ElementSpec("Tiêu đề Đảng", (15, 15), True, uppercase=True, required=True),
    "agency": ElementSpec("Cơ quan ban hành", (14, 14), True, uppercase=True, required=True),
    "agency_parent": ElementSpec("Cơ quan cấp trên", (14, 14), False, uppercase=True),
    "number": ElementSpec("Số, ký hiệu", (14, 14), False, required=True),
    "date": ElementSpec("Địa danh và ngày tháng", (14, 14), False, italic=True, required=True),
    "type": ElementSpec("Tên loại văn bản", (15, 16), True, uppercase=True),
    "subject": ElementSpec("Trích yếu", (14, 15), True),
    "letter_subject": ElementSpec("Trích yếu công văn", (12, 12), False, italic=True),
    "body": ElementSpec("Nội dung", (14, 15), required=True),
    "authority": ElementSpec("Quyền hạn người ký", (14, 14), True, uppercase=True),
    "position": ElementSpec("Chức vụ người ký", (14, 14), False, uppercase=True),
    "signer": ElementSpec("Họ tên người ký", (14, 14), True),
    "greeting": ElementSpec("Kính gửi / Kính trình", (14, 14), False, italic=True),
    "addressees": ElementSpec("Người nhận ở phần Kính gửi / Kính trình", (14, 15), False),
    "recipients_label": ElementSpec("Nơi nhận", (14, 14), False, underline=True, required=True),
    "recipients": ElementSpec("Danh sách nơi nhận", (12, 12), False),
}
CANONICAL_TEXT = {"national": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "motto": "Độc lập - Tự do - Hạnh phúc", "party": "ĐẢNG CỘNG SẢN VIỆT NAM"}
