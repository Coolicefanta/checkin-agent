import random
from datetime import datetime, timedelta

ROUTES = [
    {"route_id": "route_001", "name": "抚远→黑瞎子岛", "departure": "抚远", "arrival": "黑瞎子岛",
     "duration_min": 30, "cabin_classes": ["economy"]},
    {"route_id": "route_002", "name": "抚远→俄罗斯哈巴罗夫斯克", "departure": "抚远", "arrival": "哈巴罗夫斯克",
     "duration_min": 120, "cabin_classes": ["economy", "business"]},
    {"route_id": "route_003", "name": "哈尔滨→抚远", "departure": "哈尔滨", "arrival": "抚远",
     "duration_min": 180, "cabin_classes": ["economy", "business"]},
]

_VOYAGES = None

def _build_voyages():
    base_date = datetime(2026, 7, 1, 6, 0)
    voyages = []
    v_id = 1
    for route in ROUTES:
        slots = {"route_001": [(7,0),(9,0),(11,0),(14,0),(17,0)],
                 "route_002": [(8,0),(13,0),(16,0)]}.get(route["route_id"], [(6,30),(9,30),(14,0)])
        for h, m in slots:
            dt = base_date.replace(hour=h, minute=m)
            voyages.append({
                "voyage_id": f"voyage_{v_id:03d}", "route_id": route["route_id"],
                "route_name": route["name"], "departure_port": route["departure"],
                "arrival_port": route["arrival"],
                "departure_time": dt.isoformat(),
                "arrival_time": (dt + timedelta(minutes=route["duration_min"])).isoformat(),
                "cabin_classes": route["cabin_classes"], "duration_min": route["duration_min"],
            })
            v_id += 1
    return voyages

def _seat_props(row, col):
    return {"is_window": col in ("A","F"), "is_aisle": col in ("B","E"),
            "is_front": row <= 3, "is_rear": row >= 8,
            "near_toilet": row in (5,6), "near_entrance": row == 1}

_SEATS_CACHE = {}
def _build_seats(voyage_id, cabin_class):
    seats = []
    for row in range(1, 11):
        for col in ("A","B","C","D","E","F"):
            seats.append({"seat_id": f"{voyage_id}-{row}{col}", "voyage_id": voyage_id,
                          "cabin_class": cabin_class, "row": row, "column": col,
                          **_seat_props(row, col), "status": "available",
                          "price_multiplier": 1.0 if cabin_class == "economy" else 1.5})
    return seats

_VOYAGES = None; _ORDERS_CACHE = {}; _WEATHER_CACHE = {}

def get_routes():
    return ROUTES

def get_voyages(route_id=None):
    global _VOYAGES
    if _VOYAGES is None: _VOYAGES = _build_voyages()
    return [v for v in _VOYAGES if v["route_id"] == route_id] if route_id else _VOYAGES

def get_seats(voyage_id, cabin_class="economy"):
    key = f"{voyage_id}:{cabin_class}"
    if key not in _SEATS_CACHE:
        _SEATS_CACHE[key] = _build_seats(voyage_id, cabin_class)
    return _SEATS_CACHE[key]

def get_weather(voyage_id):
    if voyage_id not in _WEATHER_CACHE:
        c = ["sunny","cloudy","rainy","windy"]
        _WEATHER_CACHE[voyage_id] = {"voyage_id": voyage_id,
            "weather": random.choices(c, weights=[0.4,0.3,0.2,0.1], k=1)[0],
            "temperature": round(random.uniform(5, 32), 1), "wind_level": random.randint(1, 5)}
    return _WEATHER_CACHE[voyage_id]

def get_order(order_id):
    if order_id not in _ORDERS_CACHE:
        voyages = get_voyages()
        v = voyages[abs(hash(order_id)) % len(voyages)]
        _ORDERS_CACHE[order_id] = {"order_id": order_id,
            "user_id": f"user_{abs(hash(order_id+'_u')) % 5 + 1:03d}",
            "voyage": v, "status": "pending", "seat_number": None}
    return _ORDERS_CACHE[order_id]

def get_user_preferences(user_id):
    profiles = {
        "user_001": [{"key":"window","value":0.9,"source":"stated"}, {"key":"front","value":0.7,"source":"stated"}],
        "user_002": [{"key":"aisle","value":0.8,"source":"stated"}, {"key":"near_entrance","value":0.6,"source":"stated"}],
        "user_003": [{"key":"rear","value":0.5,"source":"extracted"}, {"key":"away_from_toilet","value":0.7,"source":"extracted"}],
        "user_004": [],
        "user_005": [{"key":"window","value":1.0,"source":"stated"}, {"key":"aisle","value":-0.5,"source":"extracted"}, {"key":"front","value":0.9,"source":"stated"}],
    }
    return profiles.get(user_id, [])
