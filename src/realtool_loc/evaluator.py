"""Strict and relaxed evaluation for RealTool-Loc predictions."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from statistics import mean


STRICT_EVALUATOR_VERSION = "deterministic_v3_numeric_boundary_status_marker"
RELAXED_EVALUATOR_VERSION = "deterministic_v4_relaxed_copy_or_localize_metadata"

SCRIPT_PATTERNS = {
    "zh": re.compile(r"[\u4e00-\u9fff]"),
    "ja": re.compile(r"[\u3040-\u30ff]"),
    "th": re.compile(r"[\u0e00-\u0e7f]"),
    "bo": re.compile(r"[\u0f00-\u0fff]"),
    "ug": re.compile(r"[\u0600-\u06ff]"),
    "mn-Mong": re.compile(r"[\u1800-\u18af]"),
    "kk-Arab": re.compile(r"[\u0600-\u06ff]"),
}

WRONG_SCRIPT_PATTERNS = {
    "arab": re.compile(r"[\u0600-\u06ff]"),
    "cjk": re.compile(r"[\u4e00-\u9fff]"),
    "cyrillic": re.compile(r"[\u0400-\u052f]"),
    "kana": re.compile(r"[\u3040-\u30ff]"),
    "mongolian": re.compile(r"[\u1800-\u18af]"),
    "thai": re.compile(r"[\u0e00-\u0e7f]"),
    "tibetan": re.compile(r"[\u0f00-\u0fff]"),
}

MN_MONG_BLOCKED_SCRIPTS = ["arab", "cjk", "cyrillic", "kana", "thai", "tibetan"]
KK_ARAB_BLOCKED_SCRIPTS = ["cjk", "cyrillic", "kana", "mongolian", "thai", "tibetan"]

INDONESIAN_MARKERS = [
    "adalah",
    "berikut",
    "bumi",
    "dari",
    "dengan",
    "ditinjau",
    "gempa",
    "hasil",
    "informasi",
    "kekuatan",
    "kode",
    "lisensi",
    "lokasi",
    "menurut",
    "negara",
    "pada",
    "paket",
    "pendapatan",
    "repositori",
    "terjadi",
    "telah",
    "untuk",
    "versi",
    "wilayah",
    "waktu",
    "alat",
    "menunjukkan",
    "record",
    "produk",
    "buku",
    "cuaca",
    "tanggal",
    "penerbit",
    "judul",
    "hari",
    "libur",
    "jumlah",
    "diterbitkan",
    "ditemukan",
    "maksimum",
]

UYGUR_MARKERS = [
    "نىڭ",
    "بۇ",
    "كۈنى",
    "مەھسۇلات",
    "نەتىجىسى",
    "چۈشەندۈر",
    "كىتاب",
    "تۈرى",
    "ھەققىدە",
    "تۆۋەندىكى",
    "ئۇچۇرلار",
    "تەمىنلەندى",
    "ئىشلىتىلگەن",
    "نەشرى",
    "مەنبە",
    "لىتسېنزىيە",
]
KAZAKH_MARKER_MIN_COUNT = 2
KAZAKH_MARKERS = [
    "اقىبارات",
    "اقىباراتتى",
    "اتى",
    "اتاۋى",
    "اۋا رايى",
    "ايماعى",
    "استاناسى",
    "باسپاسى",
    "بەت",
    "بەت سانى",
    "بويلىق",
    "بويىنشا",
    "جازباسى",
    "جاعدايى",
    "جاريا",
    "جاۋىن",
    "جالپى",
    "جىلى",
    "دەم الىس",
    "دەڭگەيى",
    "قۇرال",
    "كورسەتەدى",
    "كورسەتىلگەن",
    "كودى",
    "كۇشى",
    "كۇنى",
    "كەڭدىك",
    "كىرىس",
    "كىتاپ",
    "ناتيجەسى",
    "نۇسقا",
    "نۇسقاسى",
    "سانى",
    "تاۋار",
    "تالابى",
    "تارماعى",
    "تۋرالى",
    "تۋرى",
    "تۇسىندىرىڭىز",
    "تىلى",
    "ورنى",
    "ۋاقىت",
    "ەلدىڭ",
]

THAI_DIGIT_TRANS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

MONTHS = {
    "january": 1,
    "jan": 1,
    "januari": 1,
    "มกราคม": 1,
    "february": 2,
    "feb": 2,
    "februari": 2,
    "กุมภาพันธ์": 2,
    "march": 3,
    "mar": 3,
    "maret": 3,
    "มีนาคม": 3,
    "april": 4,
    "apr": 4,
    "เมษายน": 4,
    "may": 5,
    "mei": 5,
    "พฤษภาคม": 5,
    "june": 6,
    "jun": 6,
    "juni": 6,
    "มิถุนายน": 6,
    "july": 7,
    "jul": 7,
    "juli": 7,
    "กรกฎาคม": 7,
    "august": 8,
    "aug": 8,
    "agustus": 8,
    "สิงหาคม": 8,
    "september": 9,
    "sep": 9,
    "กันยายน": 9,
    "october": 10,
    "oct": 10,
    "oktober": 10,
    "ตุลาคม": 10,
    "november": 11,
    "nov": 11,
    "พฤศจิกายน": 11,
    "december": 12,
    "dec": 12,
    "desember": 12,
    "ธันวาคม": 12,
}

MONTH_PATTERN = "|".join(re.escape(month) for month in sorted(MONTHS, key=len, reverse=True))
LIST_SEPARATOR_RE = re.compile(r"\s*(?:,|，|、|;|；|\band\b|和|及|以及)\s*", re.IGNORECASE)

VALUE_ALIASES = {
    "moderate drizzle": {
        "zh": ["中度毛毛雨", "中度细雨", "中等细雨"],
    },
    "product found": {
        "zh": ["产品已找到", "已找到产品", "找到产品"],
    },
    "public": {
        "zh": ["公开", "公共"],
        "id": ["publik", "umum"],
        "th": ["สาธารณะ"],
    },
    "true": {
        "zh": ["是", "全国性节假日", "全国性的节假日"],
        "id": ["ya", "benar"],
        "th": ["ใช่"],
    },
    "public holiday": {
        "zh": ["公共假日", "公众假日", "公共节假日", "公共假期"],
        "id": ["hari libur umum", "libur publik", "hari libur publik"],
        "th": ["วันหยุดราชการ", "วันหยุดสาธารณะ"],
    },
    "journal-article": {
        "zh": ["期刊文章", "期刊论文"],
        "ja": ["ジャーナル記事", "論文誌記事"],
        "th": ["บทความวารสาร", "บทความในวารสาร"],
        "id": ["artikel jurnal", "artikel dalam jurnal"],
    },
    "reviewed": {
        "zh": ["已审查", "已审核", "已复核"],
        "ja": ["レビュー済み", "確認済み"],
        "th": ["ตรวจสอบแล้ว", "ได้รับการตรวจสอบ"],
        "id": ["ditinjau", "telah ditinjau", "sudah ditinjau"],
    },
    "high income": {
        "zh": ["高收入"],
        "ja": ["高所得"],
        "th": ["รายได้สูง"],
        "id": ["pendapatan tinggi"],
    },
}

COUNTRY_CODE_ALIASES = {
    "CN": [
        "China",
        "中国",
        "中华人民共和国",
        "中國",
        "中国の",
        "จีน",
        "Tiongkok",
        "Cina",
        "རྒྱ་ནག",
        "جۇڭگو",
        "ᠳᠤᠮᠳᠠᠳᠤ",
        "قىتاي",
    ],
    "JP": ["Japan", "日本", "日本の", "ญี่ปุ่น", "Jepang", "ཉི་ཧོང", "ياپونىيە", "ᠶᠠᠫᠣᠨ", "ياپون"],
    "ID": ["Indonesia", "印尼", "印度尼西亚", "インドネシア", "อินโดนีเซีย", "ཨིན་ཌོ་ནེ་ཤི་ཡ", "ھىندونېزىيە", "ᠢᠨᠳᠣᠨᠧᠽ", "ىندونەزىيە"],
    "US": ["United States", "United States of America", "USA", "America", "美国", "美國", "米国", "アメリカ", "สหรัฐอเมริกา", "Amerika Serikat", "ཨ་མེ་རི་ཁ", "ئامېرىكا", "ᠠᠮᠧᠷᠢᠺᠠ", "امەريكا"],
    "MN": ["Mongolia", "蒙古", "モンゴル", "มองโกเลีย", "Mongolia", "སོག་པོ", "موڭغۇلىيە", "ᠮᠣᠩᠭᠣᠯ", "موڭعوليا"],
}

CURRENCY_CODE_ALIASES = {
    "usd": [
        "USD",
        "US dollar",
        "U.S. dollar",
        "United States dollar",
        "dollar",
        "美元",
        "米ドル",
        "ดอลลาร์สหรัฐ",
        "dolar AS",
        "dolar Amerika",
        "ཨ་རིའི་སྒོར་མོ",
        "ئامېرىكا دوللىرى",
        "ᠠᠮᠧᠷᠢᠺᠠ ᠳ᠋ᠣᠯᠯᠠᠷ",
        "امەريكا دوللىرى",
    ],
}

LANGUAGE_CODE_ALIASES = {
    "en": [
        "English",
        "英语",
        "英文",
        "英語",
        "ภาษาอังกฤษ",
        "bahasa Inggris",
        "Inggris",
        "དབྱིན་སྐད",
        "ئىنگلىزچە",
        "ᠠᠩᠭᠯᠢ",
        "اعىلшын",
    ],
}

COUNTRY_CODE_PATHS = {"countryCode", "country_code", "iso2Code", "iso2_code", "alpha_two_code"}
COPY_OR_LOCALIZE_PATHS = COUNTRY_CODE_PATHS | {"currency", "language"}


def load_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def normalize_unicode(value) -> str:
    return unicodedata.normalize("NFKC", str(value)).translate(THAI_DIGIT_TRANS)


def normalize_match_text(value) -> str:
    text = re.sub(r"\s+", "", normalize_unicode(value).lower())
    text = text.replace("／", "/")
    return re.sub(r"(?<=\d)[,.](?=\d{3}(?!\d))", "", text)


def normalize_loose_text(value) -> str:
    text = normalize_match_text(value)
    return re.sub(r"[\s,，、;；:：.!?。．、\"'`“”‘’()\[\]{}<>|/\\\-]+", "", text)


def has_letter(value) -> bool:
    return any(char.isalpha() for char in normalize_unicode(value))


def normalized_year(raw_year: str) -> int:
    year = int(raw_year)
    return year - 543 if year >= 2400 else year


def iso_date(year: int, month: int, day: int) -> str | None:
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def extract_dates(value) -> set[str]:
    text = normalize_unicode(value).lower()
    dates: set[str] = set()

    for year, month, day in re.findall(r"(?<!\d)(\d{4})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})\s*(?:日)?", text):
        date = iso_date(normalized_year(year), int(month), int(day))
        if date:
            dates.add(date)

    for day, month, year in re.findall(r"(?<!\d)(\d{1,2})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{4})(?!\d)", text):
        date = iso_date(normalized_year(year), int(month), int(day))
        if date:
            dates.add(date)

    for match in re.finditer(rf"(?<!\d)(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTH_PATTERN})\.?\s+(\d{{4}})(?!\d)", text):
        date = iso_date(normalized_year(match.group(3)), MONTHS[match.group(2)], int(match.group(1)))
        if date:
            dates.add(date)

    for match in re.finditer(rf"({MONTH_PATTERN})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?[,]?\s+(\d{{4}})(?!\d)", text):
        date = iso_date(normalized_year(match.group(3)), MONTHS[match.group(1)], int(match.group(2)))
        if date:
            dates.add(date)

    return dates


def extract_datetimes(value) -> set[str]:
    text = normalize_unicode(value).lower()
    datetimes: set[str] = set()
    iso_pattern = (
        r"(?<!\d)(\d{4})[-/](\d{1,2})[-/](\d{1,2})"
        r"(?:t|\s+| เวลา | pukul )"
        r"(\d{1,2}):(\d{2})(?::(\d{2}))?"
        r"(?:\s*(?:z|utc))?"
    )
    for year, month, day, hour, minute, second in re.findall(iso_pattern, text):
        date = iso_date(normalized_year(year), int(month), int(day))
        if date:
            datetimes.add(f"{date}T{int(hour):02d}:{int(minute):02d}:{int(second or 0):02d}Z")

    times = [
        f"{int(hour):02d}:{int(minute):02d}:{int(second or 0):02d}Z"
        for hour, minute, second in re.findall(r"(?<!\d)(\d{1,2}):(\d{2})(?::(\d{2}))?(?!\d)", text)
    ]
    if times:
        for date in extract_dates(text):
            for time in times:
                datetimes.add(f"{date}T{time}")
    return datetimes


def split_list_candidate(candidate_text: str) -> list[str]:
    if extract_dates(candidate_text):
        return []
    parts = [part.strip() for part in LIST_SEPARATOR_RE.split(candidate_text) if part.strip()]
    if len(parts) < 2:
        return []
    return parts


def single_candidate_matches(answer_lower: str, answer_normalized: str, answer_loose: str, candidate) -> bool:
    candidate_text = str(candidate)
    if candidate_text == "":
        return True
    candidate_lower = candidate_text.lower()
    candidate_normalized = normalize_match_text(candidate_text)
    candidate_loose = normalize_loose_text(candidate_text)
    candidate_datetimes = extract_datetimes(candidate_text)
    if candidate_datetimes and candidate_datetimes.intersection(extract_datetimes(answer_lower)):
        return True
    candidate_dates = extract_dates(candidate_text)
    if candidate_dates and candidate_dates.intersection(extract_dates(answer_lower)):
        return True
    if re.fullmatch(r"\d+", candidate_normalized):
        answer_numeric_text = re.sub(r"(?<=\d)[,.](?=\d{3}(?!\d))", "", answer_lower)
        return bool(re.search(rf"(?<!\d){re.escape(candidate_normalized)}(?!\d)", answer_numeric_text))
    return (
        candidate_lower in answer_lower
        or candidate_normalized in answer_normalized
        or (has_letter(candidate_text) and len(candidate_loose) >= 3 and candidate_loose in answer_loose)
    )


def candidate_matches(answer_lower: str, answer_normalized: str, answer_loose: str, candidate) -> bool:
    if single_candidate_matches(answer_lower, answer_normalized, answer_loose, candidate):
        return True
    parts = split_list_candidate(str(candidate))
    return bool(parts) and all(
        single_candidate_matches(answer_lower, answer_normalized, answer_loose, part) for part in parts
    )


def contains_any(answer: str, candidates: list[str]) -> bool:
    answer_lower = normalize_unicode(answer).lower()
    answer_normalized = normalize_match_text(answer)
    answer_loose = normalize_loose_text(answer)
    return any(candidate_matches(answer_lower, answer_normalized, answer_loose, candidate) for candidate in candidates)


def contains_code_token(answer: str, code: str) -> bool:
    normalized_answer = normalize_unicode(answer)
    normalized_code = normalize_unicode(code)
    if not normalized_code:
        return True
    return bool(
        re.search(
            rf"(?<![A-Za-z0-9]){re.escape(normalized_code)}(?![A-Za-z0-9])",
            normalized_answer,
            flags=re.IGNORECASE,
        )
    )


def has_wrong_script(answer: str, blocked_scripts: list[str]) -> bool:
    return any(WRONG_SCRIPT_PATTERNS[name].search(answer) for name in blocked_scripts)


def kazakh_marker_count(answer: str) -> int:
    return sum(1 for marker in KAZAKH_MARKERS if marker in answer)


def language_diagnostics(answer: str, expected_language: str) -> dict:
    if expected_language == "en":
        latin_words = re.findall(r"\b[A-Za-z]{2,}\b", answer)
        wrong_script_present = any(pattern.search(answer) for pattern in SCRIPT_PATTERNS.values())
        marker_present = len(latin_words) >= 3
        target_script_present = bool(latin_words) and not wrong_script_present
        language_match = target_script_present and marker_present
    elif expected_language == "zh":
        target_script_present = bool(SCRIPT_PATTERNS["zh"].search(answer))
        wrong_script_present = bool(SCRIPT_PATTERNS["ja"].search(answer))
        marker_present = True
        language_match = target_script_present and not wrong_script_present
    elif expected_language == "ja":
        target_script_present = bool(SCRIPT_PATTERNS["ja"].search(answer))
        wrong_script_present = False
        marker_present = True
        language_match = target_script_present
    elif expected_language == "th":
        target_script_present = bool(SCRIPT_PATTERNS["th"].search(answer))
        wrong_script_present = False
        marker_present = True
        language_match = target_script_present
    elif expected_language == "bo":
        target_script_present = bool(SCRIPT_PATTERNS["bo"].search(answer))
        wrong_script_present = False
        marker_present = True
        language_match = target_script_present
    elif expected_language == "ug":
        target_script_present = bool(SCRIPT_PATTERNS["ug"].search(answer))
        wrong_script_present = False
        marker_present = any(marker in answer for marker in UYGUR_MARKERS)
        language_match = target_script_present and marker_present
    elif expected_language == "mn-Mong":
        target_script_present = bool(SCRIPT_PATTERNS["mn-Mong"].search(answer))
        wrong_script_present = has_wrong_script(answer, MN_MONG_BLOCKED_SCRIPTS)
        marker_present = True
        language_match = target_script_present and not wrong_script_present
    elif expected_language == "kk-Arab":
        target_script_present = bool(SCRIPT_PATTERNS["kk-Arab"].search(answer))
        wrong_script_present = has_wrong_script(answer, KK_ARAB_BLOCKED_SCRIPTS)
        marker_present = kazakh_marker_count(answer) >= KAZAKH_MARKER_MIN_COUNT
        language_match = target_script_present and marker_present and not wrong_script_present
    elif expected_language == "id":
        wrong_script_present = any(pattern.search(answer) for code, pattern in SCRIPT_PATTERNS.items() if code != "ug")
        marker_present = contains_any(answer, INDONESIAN_MARKERS)
        target_script_present = not wrong_script_present
        language_match = target_script_present and marker_present
    else:
        raise ValueError(f"Unsupported language: {expected_language}")
    return {
        "target_script_present": target_script_present,
        "wrong_script_present": wrong_script_present,
        "language_marker_present": marker_present,
        "language_match": language_match,
    }


def language_matches(answer: str, expected_language: str) -> bool:
    return language_diagnostics(answer, expected_language)["language_match"]


def normalize_prediction(record: dict) -> tuple[str, str, str]:
    sample_id = record.get("id") or record.get("sample_id")
    method = record.get("method", "unknown")
    answer = None
    for answer_key in ["answer", "response", "output"]:
        if answer_key in record:
            answer = record[answer_key]
            break
    if not sample_id or answer is None:
        raise ValueError(f"Prediction record must include id/sample_id and answer/response/output: {record}")
    return sample_id, method, answer


def value_at_path(data: dict, path: str):
    current = data
    for raw_part in path.split("."):
        part = raw_part
        while "[" in part:
            key, rest = part.split("[", 1)
            if key:
                current = current[key]
            index, tail = rest.split("]", 1)
            current = current[int(index)]
            part = tail
        if part:
            current = current[part]
    return current


def role_specs(sample: dict, role: str) -> list[dict]:
    return [spec for spec in sample.get("field_specs", []) if spec.get("required", True) and spec.get("role") == role]


def required_specs(sample: dict) -> list[dict]:
    return [spec for spec in sample.get("field_specs", []) if spec.get("required", True)]


def unique_values(values: list) -> list[str]:
    output = []
    seen = set()
    for value in values:
        text = str(value)
        if text not in seen:
            output.append(text)
            seen.add(text)
    return output


def semantic_aliases(raw, language: str, path: str) -> list[str]:
    raw_key = str(raw).lower()
    aliases = list(VALUE_ALIASES.get(raw_key, {}).get(language, []))
    if raw_key == "public" and path == "holidayTypes":
        aliases.extend(VALUE_ALIASES["public holiday"].get(language, []))
    if raw_key == "true" and path == "nationalHoliday":
        aliases.extend(VALUE_ALIASES["true"].get(language, []))
    return aliases


def copy_or_localize_aliases(spec: dict) -> list[str]:
    path = str(spec.get("path", ""))
    if path not in COPY_OR_LOCALIZE_PATHS:
        return []
    raw = str(spec.get("value", ""))
    if path in COUNTRY_CODE_PATHS:
        return COUNTRY_CODE_ALIASES.get(raw.upper(), [])
    if path == "currency":
        return CURRENCY_CODE_ALIASES.get(raw.lower(), [])
    if path == "language":
        return LANGUAGE_CODE_ALIASES.get(raw.lower(), [])
    return []


def relaxed_copy_or_localize_ok(spec: dict, answer: str) -> bool:
    raw = str(spec.get("value", ""))
    aliases = copy_or_localize_aliases(spec)
    if not aliases:
        return False
    return contains_code_token(answer, raw) or contains_any(answer, aliases)


def spec_candidates(sample: dict, spec: dict) -> list[str]:
    raw = spec.get("value")
    language = sample.get("expected_answer_language") or sample.get("user_language")
    return unique_values(
        [str(value) for value in spec.get("accepted_values", [])]
        + [raw]
        + semantic_aliases(raw, language, spec.get("path", ""))
    )


def spec_present(sample: dict, spec: dict, answer: str, *, evaluation_policy: str = "strict") -> bool:
    if evaluation_policy == "relaxed" and relaxed_copy_or_localize_ok(spec, answer):
        return True
    aliases = spec_candidates(sample, spec)
    if contains_any(answer, aliases):
        return True
    return contains_any(answer, [spec.get("value")])


def immutable_ok(spec: dict, answer: str, *, evaluation_policy: str = "strict") -> bool:
    raw = str(spec.get("value", ""))
    if raw == "" or raw in answer:
        return True
    return evaluation_policy == "relaxed" and relaxed_copy_or_localize_ok(spec, answer)


def underlocalized_status_fields(sample: dict, answer: str) -> list[str]:
    if sample["expected_answer_language"] == "en":
        return []
    answer_lower = normalize_unicode(answer).lower()
    fields = []
    for spec in sample.get("field_specs", []):
        if not spec.get("required", True) or not spec.get("requires_localization"):
            continue
        raw = str(spec.get("value", ""))
        raw_lower = raw.lower()
        if not raw_lower or not any(ch.isalpha() for ch in raw_lower):
            continue
        localized_aliases = [
            str(alias)
            for alias in spec_candidates(sample, spec)
            if str(alias).lower() != raw_lower
        ]
        if raw_lower in answer_lower and not contains_any(answer, localized_aliases):
            fields.append(spec["path"])
    return fields


def evaluate_answer(sample: dict, answer: str, method: str = "unknown", *, evaluation_policy: str = "strict") -> dict:
    if evaluation_policy not in {"strict", "relaxed"}:
        raise ValueError(f"Unsupported evaluation_policy: {evaluation_policy}")
    req_specs = required_specs(sample)
    covered = [
        spec["path"]
        for spec in req_specs
        if spec_present(sample, spec, answer, evaluation_policy=evaluation_policy)
    ]
    missing = [spec["path"] for spec in req_specs if spec["path"] not in covered]

    immutable_specs = role_specs(sample, "immutable")
    immutable_ok_fields = [
        spec["path"]
        for spec in immutable_specs
        if immutable_ok(spec, answer, evaluation_policy=evaluation_policy)
    ]
    immutable_bad = [spec["path"] for spec in immutable_specs if spec["path"] not in immutable_ok_fields]

    entity_specs = role_specs(sample, "entity")
    entity_ok_fields = [
        spec["path"]
        for spec in entity_specs
        if spec_present(sample, spec, answer, evaluation_policy=evaluation_policy)
    ]
    entity_bad = [spec["path"] for spec in entity_specs if spec["path"] not in entity_ok_fields]

    semantic_specs = role_specs(sample, "semantic") + role_specs(sample, "status")
    semantic_ok_fields = [
        spec["path"]
        for spec in semantic_specs
        if spec_present(sample, spec, answer, evaluation_policy=evaluation_policy)
    ]
    semantic_bad = [spec["path"] for spec in semantic_specs if spec["path"] not in semantic_ok_fields]

    forbidden_hits = [
        phrase
        for phrase in sample.get("forbidden_hallucinations", [])
        if phrase and phrase.lower() in answer.lower()
    ]
    underlocalized = underlocalized_status_fields(sample, answer)

    diagnostics = language_diagnostics(answer, sample["expected_answer_language"])
    language_accuracy = 1.0 if diagnostics["language_match"] else 0.0
    field_coverage = len(covered) / len(req_specs) if req_specs else 1.0
    immutable_preservation = len(immutable_ok_fields) / len(immutable_specs) if immutable_specs else 1.0
    entity_fidelity = len(entity_ok_fields) / len(entity_specs) if entity_specs else 1.0
    semantic_fidelity = len(semantic_ok_fields) / len(semantic_specs) if semantic_specs else 1.0
    localization_quality = 0.0 if underlocalized else 1.0
    hallucination_free = 0.0 if forbidden_hits else 1.0
    faithful_localization_score = mean(
        [
            language_accuracy,
            field_coverage,
            immutable_preservation,
            entity_fidelity,
            semantic_fidelity,
            localization_quality,
            hallucination_free,
        ]
    )
    core_pass = all(
        [
            language_accuracy == 1.0,
            field_coverage == 1.0,
            immutable_preservation == 1.0,
            entity_fidelity == 1.0,
            semantic_fidelity == 1.0,
            localization_quality == 1.0,
            hallucination_free == 1.0,
        ]
    )

    return {
        "id": sample["id"],
        "method": method,
        "evaluation_policy": evaluation_policy,
        "language": sample["user_language"],
        "domain": sample["domain"],
        "language_accuracy": language_accuracy,
        "target_script_present": 1.0 if diagnostics["target_script_present"] else 0.0,
        "wrong_script_free": 0.0 if diagnostics["wrong_script_present"] else 1.0,
        "language_marker_present": 1.0 if diagnostics["language_marker_present"] else 0.0,
        "field_coverage": field_coverage,
        "immutable_preservation": immutable_preservation,
        "entity_fidelity": entity_fidelity,
        "semantic_fidelity": semantic_fidelity,
        "localization_quality": localization_quality,
        "hallucination_free": hallucination_free,
        "faithful_localization_score": faithful_localization_score,
        "core_pass": core_pass,
        "missing_fields": missing,
        "immutable_corruptions": immutable_bad,
        "entity_mismatches": entity_bad,
        "semantic_mismatches": semantic_bad,
        "underlocalized_fields": underlocalized,
        "forbidden_hits": forbidden_hits,
    }


def aggregate(rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    metrics = [
        "language_accuracy",
        "target_script_present",
        "wrong_script_free",
        "language_marker_present",
        "field_coverage",
        "immutable_preservation",
        "entity_fidelity",
        "semantic_fidelity",
        "localization_quality",
        "hallucination_free",
        "faithful_localization_score",
        "core_pass",
    ]
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for group_key, group_rows in sorted(groups.items()):
        item = {key: value for key, value in zip(keys, group_key)}
        item["n"] = len(group_rows)
        for metric in metrics:
            item[metric] = mean(1.0 if row[metric] is True else 0.0 if row[metric] is False else row[metric] for row in group_rows)
        output.append(item)
    return output


def evaluate_predictions(data_path: Path, pred_path: Path, *, evaluation_policy: str = "strict") -> dict:
    samples = {sample["id"]: sample for sample in load_jsonl(data_path)}
    rows = []
    for record in load_jsonl(pred_path):
        sample_id, method, answer = normalize_prediction(record)
        if sample_id not in samples:
            raise KeyError(f"Unknown sample id in predictions: {sample_id}")
        rows.append(evaluate_answer(samples[sample_id], answer, method, evaluation_policy=evaluation_policy))
    evaluator_version = STRICT_EVALUATOR_VERSION if evaluation_policy == "strict" else RELAXED_EVALUATOR_VERSION
    return {
        "evaluator_version": evaluator_version,
        "evaluation_policy": evaluation_policy,
        "n_predictions": len(rows),
        "overall": aggregate(rows, ("method",)),
        "by_language": aggregate(rows, ("method", "language")),
        "by_domain": aggregate(rows, ("method", "domain")),
        "per_sample": rows,
    }
