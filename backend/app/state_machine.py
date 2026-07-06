from .errors import InvalidTransitionError

# Booking lifecycle. `pending` is modeled for a future payment/hold flow but is
# never entered here (bookings are created directly as `confirmed`).
ALLOWED: dict[str, set[str]] = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"cancelled", "completed"},
    "cancelled": set(),
    "completed": set(),
}

ACTIVE_STATUSES = ("pending", "confirmed")


def validate_transition(current: str, target: str) -> None:
    if target not in ALLOWED.get(current, set()):
        raise InvalidTransitionError(f"Cannot move booking from '{current}' to '{target}'")
