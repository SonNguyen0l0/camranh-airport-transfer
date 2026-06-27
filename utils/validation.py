import re
from datetime import datetime, date


def validate_name(text: str) -> bool:
    text = text.strip()
    if len(text) < 3:
        return False
    if text.isdigit():
        return False
    if not re.search(r"[a-zA-ZÀ-ỹ]", text):
        return False
    return True


def validate_flight(text: str) -> bool:
    return bool(re.match(r"^[A-Z0-9]{2,3}[0-9]{1,4}$", text.strip().upper()))


def validate_time(text: str) -> bool:
    text = text.strip().replace(".", ":").replace("-", ":")
    return bool(re.match(r"^([01]?\d|2[0-3]):([0-5]\d)$", text))


def normalize_time(text: str) -> str:
    text = text.strip().replace(".", ":").replace("-", ":")
    parts = text.split(":")
    return f"{int(parts[0]):02d}:{parts[1]}"


def validate_date(text: str) -> tuple[bool, str]:
    text = text.strip().replace("-", "/").replace(".", "/")
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            d = datetime.strptime(text, fmt).date()
            if d < date.today():
                return False, "past"
            return True, d.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return False, "invalid"


def validate_phone(text: str) -> bool:
    digits = re.sub(r"[\s\-\(\)]", "", text.strip())
    return bool(re.match(r"^(\+?[0-9]{9,15}|0[0-9]{8,10})$", digits))


def validate_whatsapp(text: str) -> bool:
    digits = re.sub(r"[\s\-\(\)\+]", "", text.strip())
    return bool(re.match(r"^[0-9]{7,15}$", digits))


def normalize_whatsapp(text: str) -> str:
    digits = re.sub(r"[\s\-\(\)]", "", text.strip())
    if not digits.startswith("+"):
        digits = "+" + digits
    return digits


def validate_telegram(text: str) -> bool:
    t = text.strip()
    if not t.startswith("@"):
        t = "@" + t
    return bool(re.match(r"^@[a-zA-Z0-9_]{5,32}$", t))


def normalize_telegram(text: str) -> str:
    t = text.strip()
    return t if t.startswith("@") else "@" + t
