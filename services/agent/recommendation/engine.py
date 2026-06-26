from services.agent.config import settings
from services.agent.recommendation.hard_filter import filter_seats
from services.agent.recommendation.ranker import deduplicate, rank_seats
from services.agent.recommendation.reason_builder import build_reason
from services.agent.recommendation.scorer import score_seat
from shared.schemas.preference import PreferenceItem
from shared.schemas.recommendation import (
    ConflictResolution,
    ConflictType,
    RecommendationResult,
    RecommendedSeat,
)
from shared.schemas.seat import Seat, SeatMap, SeatStatus


def _get_weights() -> dict[str, float]:
    return {
        "window": settings.score.window_weight,
        "aisle": settings.score.aisle_weight,
        "front": settings.score.front_weight,
        "rear": settings.score.rear_weight,
        "away_from_toilet": settings.score.away_from_toilet_weight,
    }


def _detect_conflict(
    page: list[tuple[Seat, float]],
    all_ranked: list[tuple[Seat, float]],
    preferences: list[PreferenceItem],
    budget: float | None,
) -> tuple[ConflictType, str]:
    """Full 4-type conflict detection on the current page."""
    if not page:
        return ConflictType.NO_SUITABLE_SEAT, ""

    top_seat, top_score = page[0]
    top_reasons = build_reason(top_seat, preferences)

    # PRICE_UPGRADE: top candidate exceeds budget, but a cheaper option exists in all_ranked
    if budget is not None and top_seat.price_multiplier > budget:
        cheaper = [s for s, _ in all_ranked if s.price_multiplier <= budget]
        if cheaper:
            return ConflictType.PRICE_UPGRADE, (
                f"首选座位{top_seat.seat_id}价格倍率{top_seat.price_multiplier}超出预算{budget}，"
                f"存在{len(cheaper)}个预算内替代选择"
            )
        return ConflictType.NO_SUITABLE_SEAT, ""

    # MULTIPLE_CANDIDATES: top 2 scores differ by ≤ 0.1
    if len(page) >= 2:
        _, second_score = page[1]
        if abs(top_score - second_score) <= 0.1:
            # Check if also a PREFERENCE_TRADEOFF (different reason sets + score gap > 0.1)
            second_seat, _ = page[1]
            second_reasons = build_reason(second_seat, preferences)
            if set(top_reasons) != set(second_reasons) and abs(top_score - second_score) > 0.01:
                detail = (
                    f"座位{top_seat.seat_id}满足:{'、'.join(top_reasons) or '综合匹配'}；"
                    f"座位{second_seat.seat_id}满足:{'、'.join(second_reasons) or '综合匹配'}"
                )
                return ConflictType.PREFERENCE_TRADEOFF, detail
            return ConflictType.MULTIPLE_CANDIDATES, ""

    return ConflictType.NO_CONFLICT, ""


def recommend(
    seat_map: SeatMap,
    preferences: list[PreferenceItem],
    excluded_seats: list[str] | None = None,
    cursor: int = 0,
    *,
    budget: float | None = None,
    wheelchair: bool = False,
    motion_sickness: bool = False,
    companion_count: int = 0,
) -> RecommendationResult:
    excluded = set(excluded_seats or [])
    weights = _get_weights()

    # Stage 1: AVAILABLE + excluded
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

    # Stage 2: Hard constraint filter
    available_dicts = [s.model_dump() for s in available]
    accessibility_pref_value = max(
        (p.value for p in preferences if p.key == "accessibility"), default=0.0
    )
    filtered_dicts = filter_seats(
        available_dicts,
        wheelchair=wheelchair,
        motion_sickness=motion_sickness,
        companion_count=companion_count,
        accessibility_pref_value=accessibility_pref_value,
        total_rows=seat_map.rows,
    )

    if not filtered_dicts:
        return RecommendationResult(
            voyage_id=seat_map.voyage_id,
            conflict_type=ConflictType.NO_SUITABLE_SEAT,
            exhausted=True,
            cursor=cursor,
            conflict_detail="硬约束过滤后无可用座位",
        )

    filtered = [Seat(**d) for d in filtered_dicts]

    scored = [(s, score_seat(s.model_dump(), preferences, weights)) for s in filtered]
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

    conflict_type, conflict_detail = _detect_conflict(page, ranked, preferences, budget)

    candidates = [
        RecommendedSeat(
            seat_id=seat.seat_id,
            row=seat.row,
            column=seat.column,
            cabin_class=seat.cabin_class.value,
            score=round(sc, 4),
            reasons=build_reason(seat, preferences),
            price_multiplier=seat.price_multiplier,
        )
        for seat, sc in page
    ]

    resolution = ConflictResolution.PROCEED
    if conflict_type in (ConflictType.PRICE_UPGRADE, ConflictType.PREFERENCE_TRADEOFF, ConflictType.MULTIPLE_CANDIDATES):
        resolution = ConflictResolution.ASK_USER

    return RecommendationResult(
        voyage_id=seat_map.voyage_id,
        candidates=candidates,
        conflict_type=conflict_type,
        conflict_resolution=resolution,
        conflict_detail=conflict_detail,
        exhausted=exhausted,
        cursor=next_cursor,
    )
