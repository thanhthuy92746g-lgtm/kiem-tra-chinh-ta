ABBREVIATIONS = dict(pair.split(":", 1) for pair in (
    "ko:không k0:không hok:không dc:được đc:được dk:được đk:được vs:với wa:quá qá:quá "
    "trc:trước ntn:như_thế_nào mk:mình mik:mình bn:bạn ck:chồng vk:vợ ny:người_yêu "
    "iu:yêu ngta:người_ta j:gì z:vậy cf:cà_phê kq:kết_quả sp:sản_phẩm"
).split())
ABBREVIATIONS = {k: v.replace("_", " ") for k, v in ABBREVIATIONS.items()}
