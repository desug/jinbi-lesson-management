from __future__ import annotations


CLASS_TYPE_VIP = "VIP"
CLASS_TYPE_SMALL = "小班"
CLASS_TYPE_SMALL_VIP = "小班+一对一"
CLASS_TYPE_ONE_TO_TWO = "一对二"

CLASS_TYPES = [
    CLASS_TYPE_VIP,
    CLASS_TYPE_SMALL,
    CLASS_TYPE_SMALL_VIP,
    CLASS_TYPE_ONE_TO_TWO,
]

CLASS_TYPE_LABELS = {
    CLASS_TYPE_VIP: "VIP 学员",
    CLASS_TYPE_SMALL: "小班学员",
    CLASS_TYPE_SMALL_VIP: "小班+一对一",
    CLASS_TYPE_ONE_TO_TWO: "一对二",
}

_ALIASES = {
    "vip": CLASS_TYPE_VIP,
    "vip班型": CLASS_TYPE_VIP,
    "VIP班型": CLASS_TYPE_VIP,
    "一对一": CLASS_TYPE_VIP,
    "1对1": CLASS_TYPE_VIP,
    "一对1": CLASS_TYPE_VIP,
    "1对一": CLASS_TYPE_VIP,
    "小班": CLASS_TYPE_SMALL,
    "small": CLASS_TYPE_SMALL,
    "小班+一对一": CLASS_TYPE_SMALL_VIP,
    "小班+vip": CLASS_TYPE_SMALL_VIP,
    "小班+VIP": CLASS_TYPE_SMALL_VIP,
    "小班一对一": CLASS_TYPE_SMALL_VIP,
    "小班vip": CLASS_TYPE_SMALL_VIP,
    "一对二": CLASS_TYPE_ONE_TO_TWO,
    "1对2": CLASS_TYPE_ONE_TO_TWO,
    "一对2": CLASS_TYPE_ONE_TO_TWO,
    "1对二": CLASS_TYPE_ONE_TO_TWO,
}

_DB_ALIASES = {
    CLASS_TYPE_VIP: [CLASS_TYPE_VIP, "vip", "VIP班型", "一对一"],
    CLASS_TYPE_SMALL: [CLASS_TYPE_SMALL, "small"],
    CLASS_TYPE_SMALL_VIP: [CLASS_TYPE_SMALL_VIP, "小班＋一对一", "小班+VIP", "小班+vip"],
    CLASS_TYPE_ONE_TO_TWO: [CLASS_TYPE_ONE_TO_TWO],
}


def _compact(value: str | None) -> str:
    return (value or "").strip().replace(" ", "").replace("＋", "+")


def normalize_class_type(value: str | None, default: str = "") -> str:
    text = _compact(value)
    if not text:
        return default

    if text in CLASS_TYPES:
        return text

    lowered = text.lower()
    if lowered in _ALIASES:
        return _ALIASES[lowered]
    if text in _ALIASES:
        return _ALIASES[text]

    return default


def detect_class_type_in_text(value: str | None) -> str:
    text = _compact(value)
    lowered = text.lower()
    if not text:
        return ""

    if "小班+一对一" in text or "小班+vip" in lowered or "小班一对一" in text or "小班vip" in lowered:
        return CLASS_TYPE_SMALL_VIP
    if "一对二" in text or "1对2" in text or "一对2" in text or "1对二" in text:
        return CLASS_TYPE_ONE_TO_TWO
    if "一对一" in text or "1对1" in text or "一对1" in text or "1对一" in text or "vip" in lowered:
        return CLASS_TYPE_VIP
    if "小班" in text or "small" in lowered:
        return CLASS_TYPE_SMALL

    return ""


def normalize_class_type_filter(value: str | None) -> str:
    text = _compact(value)
    if not text:
        return "all"
    if text.lower() in {"all", "全部", "全部学员"}:
        return "all"

    return normalize_class_type(text) or detect_class_type_in_text(text)


def class_type_db_values(class_type: str) -> list[str]:
    normalized = normalize_class_type(class_type)
    if not normalized:
        return []
    return _DB_ALIASES.get(normalized, [normalized])


def class_type_label(class_type: str | None) -> str:
    normalized = normalize_class_type(class_type) or detect_class_type_in_text(class_type)
    return CLASS_TYPE_LABELS.get(normalized, (class_type or "").strip() or "未设置班型")
