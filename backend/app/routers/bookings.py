from fastapi import APIRouter

from ..schemas import BookingCreate
from ..services import bookings

router = APIRouter(prefix="/bookings")


@router.post("", status_code=201)
def create_booking(payload: BookingCreate):
    return bookings.create_booking(payload.slot_id, payload.patient_id)


@router.post("/{booking_id}/confirm")
def confirm_booking(booking_id: str):
    return bookings.confirm_booking(booking_id)


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str):
    return bookings.cancel_booking(booking_id)


@router.post("/{booking_id}/complete")
def complete_booking(booking_id: str):
    return bookings.complete_booking(booking_id)
