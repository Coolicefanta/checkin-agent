from services.agent.config import settings
from services.agent.recommendation.ranker import deduplicate, rank_seats
from services.agent.recommendation.scorer import score_seat
from shared.schemas.preference import PreferenceItem
from shared.schemas.recommendation import (
    ConflictType,
    RecommendationResult,
    RecommendedSeat,
)
from shared.schemas.seat import Seat, SeatMap, SeatStatus

def _get_weights() -> dict[str, float]:
    # build once; re-read each call to pick up runtime changes in tests
    return {
        "window": settings.score.window_weight,
        "aisle": settings.score.aisle_weight,
        "front": settings.score.front_weight,
        "rear": settings.score.rear_weight,
        "away_from_toilet": settings.score.away_from_toilet_weight,
    }


def _build_reasons(seat: Seat, preferences: list[PreferenceItem]) -> list[str]:
    _label: dict[str, tuple[str | None, str]] = {
        "window": ("is_window", "靠窗"),
        "aisle": ("is_aisle", "靠过道"),
        "front": ("is_front", "靠前排"),
        "rear": ("is_rear", "靠后排"),
        "away_from_toilet": (None, "远离厕所"),
    }
    reasons: list[str] = []
    for pref in preferences:
        if pref.value <= 0 or pref.key not in _label:
            continue
        prop, label = _label[pref.key]
        if pref.key == "away_from_toilet":
            if not seat.near_toilet:
                reasons.append(label)
        elif prop and getattr(seat, prop, False):
            reasons.append(label)
    return reasons


def recommend(
    seat_map: SeatMap,
    preferences: list[PreferenceItem],
    excluded_seats: list[str] | None = None,
    cursor: int = 0,
) -> RecommendationResult:
    excluded = set(excluded_seats or [])
    weights = _get_weights()

    available = [
        s for s in seat_map.seats
        if s.status == SeatStatus.AVAILABLE and s.seat_id not in excluded
    ]

    if not available:
        return RecommendationResult(
            voyage_id=seat_map.voyage_id,
            conflict_type=ConflictType.NO_SUITABLE_SEAT,
            exhausted=True,
            cursor=cursor,
        )

    scored = [(s, score_seat(s.model_dump(), preferences, weights)) for s in available]
    ranked = deduplicate(rank_seats(scored))

    page = ranked[cursor : cursor + 3]
    next_cursor = cursor + 3
    exhausted = next_cursor >= len(ranked)

    if not page:
        return RecommendationResult(
            voyage_id=seat_map.voyage_id,
            conflict_type=ConflictType.NO_SUITABLE_SEAT,
            exhausted=True,
            cursor=cursor,
        )

    scores = [sc for _, sc in page]
    conflict_type = (
        ConflictType.MULTIPLE_CANDIDATES
        if len(scores) >= 2 and (max(scores) - min(scores)) <= 0.1
        else ConflictType.NO_CONFLICT
    )

    candidates = [
        RecommendedSeat(
            seat_id=seat.seat_id,
            row=seat.row,
            column=seat.column,
            cabin_class=seat.cabin_class.value,
            score=round(sc, 4),
            reasons=_build_reasons(seat, preferences),
            price_multiplier=seat.price_multiplier,
        )
        for seat, sc in page
    ]

    return RecommendationResult(
        voyage_id=seat_map.voyage_id,
        candidates=candidates,
        conflict_type=conflict_type,
        exhausted=exhausted,
        cursor=next_cursor,
    )
