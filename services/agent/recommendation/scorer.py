from shared.schemas.preference import PreferenceItem

_PREF_TO_PROP: dict[str, str] = {
    "window": "is_window",
    "aisle": "is_aisle",
    "front": "is_front",
    "rear": "is_rear",
    "away_from_toilet": "near_toilet",
}


def score_seat(seat: dict, preferences: list[PreferenceItem], weights: dict[str, float]) -> float:
    if not preferences:
        return 0.5

    raw = 0.0
    total_weight = 0.0
    for pref in preferences:
        weight = weights.get(pref.key, 0.0)
        if weight == 0.0:
            continue
        prop = _PREF_TO_PROP.get(pref.key)
        if prop is None:
            continue
        match_val = float(seat.get(prop, False))
        if pref.key == "away_from_toilet":
            match_val = 1.0 - match_val  # invert: user wants away from toilet
        raw += weight * match_val * pref.value * pref.confidence
        total_weight += weight

    if total_weight == 0.0:
        return 0.5

    # Normalize raw ∈ [-total_weight, total_weight] → [0, 1]
    return max(0.0, min(1.0, (raw + total_weight) / (2 * total_weight)))
