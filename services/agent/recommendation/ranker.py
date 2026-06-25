from shared.schemas.seat import Seat

ScoredSeat = tuple[Seat, float]


def rank_seats(scored_seats: list[ScoredSeat]) -> list[ScoredSeat]:
    return sorted(scored_seats, key=lambda x: x[1], reverse=True)


def deduplicate(seats: list[ScoredSeat]) -> list[ScoredSeat]:
    seen: set[str] = set()
    result: list[ScoredSeat] = []
    for seat, score in seats:
        if seat.seat_id not in seen:
            seen.add(seat.seat_id)
            result.append((seat, score))
    return result


def top_n(seats: list[ScoredSeat], n: int = 3) -> list[ScoredSeat]:
    return seats[:n]
