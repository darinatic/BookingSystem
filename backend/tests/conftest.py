import pytest

from app.db import get_client

# Tests run against the real Supabase project: the race-condition test is only
# meaningful against a real Postgres enforcing the partial unique index.


@pytest.fixture
def sandbox():
    """Isolated doctor + one slot + a pool of patients; torn down after each test."""
    client = get_client()
    doctor = client.table("doctors").insert({"name": "Dr. Test", "specialty": "QA"}).execute().data[0]
    slot = (
        client.table("slots")
        .insert(
            {
                "doctor_id": doctor["id"],
                "start_time": "2030-01-01T09:00:00+00:00",
                "end_time": "2030-01-01T10:00:00+00:00",
            }
        )
        .execute()
        .data[0]
    )
    patients = (
        client.table("patients")
        .insert([{"name": f"Test Patient {i}"} for i in range(12)])
        .execute()
        .data
    )
    patient_ids = [p["id"] for p in patients]

    yield {"doctor_id": doctor["id"], "slot_id": slot["id"], "patient_ids": patient_ids}

    client.table("bookings").delete().eq("slot_id", slot["id"]).execute()
    client.table("slots").delete().eq("id", slot["id"]).execute()
    client.table("patients").delete().in_("id", patient_ids).execute()
    client.table("doctors").delete().eq("id", doctor["id"]).execute()
