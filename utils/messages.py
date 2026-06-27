import json
import os

_lang_cache: dict = {}


def load_lang(lang_code: str) -> dict:
    if lang_code not in _lang_cache:
        path = os.path.join(
            os.path.dirname(__file__), "..", "languages", f"{lang_code}.json"
        )
        with open(path, encoding="utf-8") as f:
            _lang_cache[lang_code] = json.load(f)
    return _lang_cache[lang_code]


def get(key: str, lang: str = "vi", **kwargs) -> str:
    strings = load_lang(lang)
    text = strings.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def format_price(amount: int) -> str:
    return f"{amount:,.0f} VND".replace(",", ".")


def build_summary(data: dict, lang: str, route_label: str, car_label: str) -> str:
    is_scheduled = data.get("booking_type") == "scheduled"
    template_key = "summary_template_scheduled" if is_scheduled else "summary_template_now"

    kwargs = dict(
        route=route_label,
        car=car_label,
        price=format_price(data["price"]),
        name=data["name"],
        flight=data["flight"],
        arrival=data["arrival_time"],
        passengers=data["passengers"],
        contact_method=data.get("contact_method", "—"),
    )
    if is_scheduled:
        kwargs["booking_date"] = data.get("booking_date", "—")

    return get(template_key, lang=lang, **kwargs)
