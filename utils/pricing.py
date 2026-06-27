import json
import os

_routes_data: dict | None = None
_config_data: dict | None = None


def _load_routes() -> dict:
    global _routes_data
    if _routes_data is None:
        path = os.path.join(os.path.dirname(__file__), "..", "routes.json")
        with open(path, encoding="utf-8") as f:
            _routes_data = json.load(f)
    return _routes_data


def _load_config() -> dict:
    global _config_data
    if _config_data is None:
        path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(path, encoding="utf-8") as f:
            _config_data = json.load(f)
    return _config_data


def get_all_routes() -> list[dict]:
    return _load_routes()["routes"]


def get_route_by_id(route_id: str) -> dict | None:
    for r in get_all_routes():
        if r["id"] == route_id:
            return r
    return None


def get_price(route_id: str, car_type: str) -> int:
    route = get_route_by_id(route_id)
    if route is None:
        return 0
    return route["prices"].get(car_type, 0)


def get_car_types() -> dict:
    return _load_config()["car_types"]


def get_car_max_passengers(car_type: str) -> int:
    cars = get_car_types()
    return cars.get(car_type, {}).get("max_passengers", 0)


def needs_deposit(price: int) -> bool:
    config = _load_config()
    return price >= config.get("deposit_threshold_vnd", 500000)


def get_deposit_amount() -> int:
    config = _load_config()
    return config.get("deposit_amount_vnd", 500000)


def get_contact() -> dict:
    return _load_config()["contact"]


def get_bank_info() -> dict:
    return _load_config()["bank"]


def get_route_label(route: dict, lang: str) -> str:
    return route.get(f"label_{lang}", route.get("label_vi", ""))


def get_car_label(car_type: str, lang: str) -> str:
    cars = get_car_types()
    car = cars.get(car_type, {})
    return car.get(f"label_{lang}", car.get("label_vi", car_type))
