from shared.schemas.preference import PreferenceItem, PreferenceSource

_PREF_TO_PROP: dict[str, str] = {
    "window": "is_window",
    "aisle": "is_aisle",
    "front": "is_front",
    "rear": "is_rear",
    "away_from_toilet": "near_toilet",
}


def _cold_start_scale(
    source: PreferenceSource,
    confidence: float,
    *,
    long_term_scale: float = 0.3,
    implicit_boost: float = 1.2,
) -> float:
    """Scale confidence for cold-start scenarios: shrink STATED/EXTRACTED, boost INFERRED."""
    if source in (PreferenceSource.STATED, PreferenceSource.EXTRACTED):
        return confidence * long_term_scale
    if source == PreferenceSource.INFERRED:
        return min(1.0, confidence * implicit_boost)
    return confidence


def score_seat(
    seat: dict,
    preferences: list[PreferenceItem],
    weights: dict[str, float],
    *,
    cold_start: bool = False,
    cold_start_long_term_scale: float = 0.3,
    cold_start_implicit_boost: float = 1.2,
) -> float:
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

        confidence = pref.confidence
        if cold_start:
            confidence = _cold_start_scale(
                pref.source,
                pref.confidence,
                long_term_scale=cold_start_long_term_scale,
                implicit_boost=cold_start_implicit_boost,
            )

        raw += weight * match_val * pref.value * confidence
        total_weight += weight

    if total_weight == 0.0:
        return 0.5

    # Normalize raw ∈ [-total_weight, total_weight] → [0, 1]
    return max(0.0, min(1.0, (raw + total_weight) / (2 * total_weight)))
