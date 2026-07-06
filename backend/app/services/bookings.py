from postgrest import APIError
from supabase import Client

from ..db import get_client
from ..errors import NotFoundError, SlotUnavailableError
from ..state_machine import validate_transition

UNIQUE_VIOLATION = "23505"


def create_booking(slot_id: str, patient_id: str, client: Client | None = None) -> dict:
    client = client or get_client()

    if not client.table("slots").select("id").eq("id", slot_id).execute().data:
        raise NotFoundError("slot not found")
    if not client.table("patients").select("id").eq("id", patient_id).execute().data:
        raise NotFoundError("patient not found")

    # The partial unique index is the real guard: if another request already holds an
    # active booking for this slot, the INSERT raises 23505 and we surface a conflict.
    try:
        res = (
            client.table("bookings")
            .insert({"slot_id": slot_id, "patient_id": patient_id, "status": "confirmed"})
            .execute()
        )
    except APIError as exc:
        if exc.code == UNIQUE_VIOLATION:
            raise SlotUnavailableError("slot already booked") from exc
        raise
    return res.data[0]


def list_patient_bookings(patient_id: str) -> list[dict]:
    return (
        get_client()
        .table("bookings")
        .select("*, slots(start_time, end_time, doctors(name, specialty))")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )


def cancel_booking(booking_id: str) -> dict:
    return _transition(booking_id, "cancelled")


def complete_booking(booking_id: str) -> dict:
    return _transition(booking_id, "completed")


def _transition(booking_id: str, target: str) -> dict:
    client = get_client()
    rows = client.table("bookings").select("*").eq("id", booking_id).execute().data
    if not rows:
        raise NotFoundError("booking not found")
    current = rows[0]["status"]
    validate_transition(current, target)

    # Compare-and-swap on the current status makes the transition atomic: if a
    # concurrent request changed the status first, no row matches and we conflict.
    # updated_at is maintained by a DB trigger (moddatetime).
    res = (
        client.table("bookings")
        .update({"status": target})
        .eq("id", booking_id)
        .eq("status", current)
        .execute()
    )
    if not res.data:
        raise SlotUnavailableError("booking was modified concurrently")
    return res.data[0]
