from ..db import get_client
from ..services.bookings import expire_holds
from ..state_machine import ACTIVE_STATUSES


def list_doctors() -> list[dict]:
    return get_client().table("doctors").select("*").order("name").execute().data


def list_patients() -> list[dict]:
    return get_client().table("patients").select("*").order("name").execute().data


def list_available_slots(doctor_id: str) -> list[dict]:
    client = get_client()
    slots = (
        client.table("slots")
        .select("*")
        .eq("doctor_id", doctor_id)
        .order("start_time")
        .execute()
        .data
    )
    if not slots:
        return []

    slot_ids = [s["id"] for s in slots]
    expire_holds(client, slot_ids)
    taken_rows = (
        client.table("bookings")
        .select("slot_id")
        .in_("slot_id", slot_ids)
        .in_("status", list(ACTIVE_STATUSES))
        .execute()
        .data
    )
    taken = {row["slot_id"] for row in taken_rows}
    return [s for s in slots if s["id"] not in taken]
