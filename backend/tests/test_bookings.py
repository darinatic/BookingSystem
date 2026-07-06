import pytest

from app.errors import InvalidTransitionError, SlotUnavailableError
from app.services import bookings, catalog


def test_booking_removes_slot_from_availability_and_cancel_frees_it(sandbox):
    slot_id = sandbox["slot_id"]
    doctor_id = sandbox["doctor_id"]
    p1, p2 = sandbox["patient_ids"][:2]

    assert any(s["id"] == slot_id for s in catalog.list_available_slots(doctor_id))

    booking = bookings.create_booking(slot_id, p1)
    assert booking["status"] == "confirmed"

    assert all(s["id"] != slot_id for s in catalog.list_available_slots(doctor_id))

    with pytest.raises(SlotUnavailableError):
        bookings.create_booking(slot_id, p2)

    bookings.cancel_booking(booking["id"])
    assert any(s["id"] == slot_id for s in catalog.list_available_slots(doctor_id))

    # Slot can be rebooked once freed (partial unique index only covers active statuses).
    rebooked = bookings.create_booking(slot_id, p2)
    assert rebooked["status"] == "confirmed"


def test_completed_booking_cannot_be_cancelled(sandbox):
    slot_id = sandbox["slot_id"]
    p1 = sandbox["patient_ids"][0]

    booking = bookings.create_booking(slot_id, p1)
    bookings.complete_booking(booking["id"])

    with pytest.raises(InvalidTransitionError):
        bookings.cancel_booking(booking["id"])
