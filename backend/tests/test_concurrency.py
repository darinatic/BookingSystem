from concurrent.futures import ThreadPoolExecutor

from supabase import create_client

from app.config import settings
from app.db import get_client
from app.errors import SlotUnavailableError
from app.services import bookings
from app.state_machine import ACTIVE_STATUSES


def test_no_double_booking_under_concurrency(sandbox):
    """N patients race for the same slot; exactly one wins, the rest get a conflict.

    Each thread uses its own client so this mirrors N independent users on N
    separate connections, not one shared connection.
    """
    slot_id = sandbox["slot_id"]
    patient_ids = sandbox["patient_ids"]
    n = len(patient_ids)

    def attempt(patient_id: str) -> str:
        client = create_client(settings.supabase_url, settings.supabase_key)
        try:
            bookings.create_booking(slot_id, patient_id, client=client)
            return "ok"
        except SlotUnavailableError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=n) as pool:
        results = list(pool.map(attempt, patient_ids))

    assert results.count("ok") == 1
    assert results.count("conflict") == n - 1

    active = (
        get_client()
        .table("bookings")
        .select("id")
        .eq("slot_id", slot_id)
        .in_("status", list(ACTIVE_STATUSES))
        .execute()
        .data
    )
    assert len(active) == 1
