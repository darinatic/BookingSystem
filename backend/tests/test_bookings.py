from datetime import datetime, timedelta, timezone

import pytest

from app.db import get_client
from app.errors import InvalidTransitionError, SlotUnavailableError
from app.services import bookings, catalog


def test_hold_blocks_slot_and_cancel_frees_it(sandbox):
    slot_id = sandbox["slot_id"]
    doctor_id = sandbox["doctor_id"]
    p1, p2 = sandbox["patient_ids"][:2]

    assert any(s["id"] == slot_id for s in catalog.list_available_slots(doctor_id))

    hold = bookings.create_booking(slot_id, p1)
    assert hold["status"] == "pending"

    # A pending hold already reserves the slot.
    assert all(s["id"] != slot_id for s in catalog.list_available_slots(doctor_id))
    with pytest.raises(SlotUnavailableError):
        bookings.create_booking(slot_id, p2)

    confirmed = bookings.confirm_booking(hold["id"])
    assert confirmed["status"] == "confirmed"

    bookings.cancel_booking(confirmed["id"])
    assert any(s["id"] == slot_id for s in catalog.list_available_slots(doctor_id))

    # Slot can be rebooked once freed.
    assert bookings.create_booking(slot_id, p2)["status"] == "pending"


def _expire(booking_id: str) -> None:
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    get_client().table("bookings").update({"expires_at": past}).eq("id", booking_id).execute()


def test_expired_hold_is_freed_on_next_read(sandbox):
    slot_id = sandbox["slot_id"]
    doctor_id = sandbox["doctor_id"]
    p1, p2 = sandbox["patient_ids"][:2]

    hold = bookings.create_booking(slot_id, p1)
    _expire(hold["id"])

    # Reading availability sweeps the expired hold, so the slot is open again
    # and another patient can take it.
    assert any(s["id"] == slot_id for s in catalog.list_available_slots(doctor_id))
    assert bookings.create_booking(slot_id, p2)["status"] == "pending"


def test_expired_hold_cannot_be_confirmed(sandbox):
    slot_id = sandbox["slot_id"]
    p1 = sandbox["patient_ids"][0]

    hold = bookings.create_booking(slot_id, p1)
    _expire(hold["id"])

    with pytest.raises(SlotUnavailableError):
        bookings.confirm_booking(hold["id"])


def test_completed_booking_cannot_be_cancelled(sandbox):
    slot_id = sandbox["slot_id"]
    p1 = sandbox["patient_ids"][0]

    hold = bookings.create_booking(slot_id, p1)
    bookings.confirm_booking(hold["id"])
    bookings.complete_booking(hold["id"])

    with pytest.raises(InvalidTransitionError):
        bookings.cancel_booking(hold["id"])
