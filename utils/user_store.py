import json
import os

_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")


def _load() -> dict:
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(_FILE), exist_ok=True)
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def register_user(chat_id: int, lang: str = "vi") -> None:
    data = _load()
    key = str(chat_id)
    if key not in data:
        data[key] = {"lang": lang}
        _save(data)
    elif data[key].get("lang") != lang:
        data[key]["lang"] = lang
        _save(data)


def get_all_users() -> dict:
    return _load()


def get_user_count() -> int:
    return len(_load())
