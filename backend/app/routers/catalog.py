from fastapi import APIRouter

from ..services import bookings, catalog

router = APIRouter()


@router.get("/doctors")
def get_doctors():
    return catalog.list_doctors()


@router.get("/doctors/{doctor_id}/slots")
def get_available_slots(doctor_id: str):
    return catalog.list_available_slots(doctor_id)


@router.get("/patients")
def get_patients():
    return catalog.list_patients()


@router.get("/patients/{patient_id}/bookings")
def get_patient_bookings(patient_id: str):
    return bookings.list_patient_bookings(patient_id)
