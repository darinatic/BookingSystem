import type { Booking, Doctor, Patient, Slot } from './types'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    throw new ApiError(res.status, body?.detail ?? `Request failed (${res.status})`)
  }
  return body as T
}

export const api = {
  listDoctors: () => request<Doctor[]>('/doctors'),
  listPatients: () => request<Patient[]>('/patients'),
  listAvailableSlots: (doctorId: string) => request<Slot[]>(`/doctors/${doctorId}/slots`),
  listBookings: (patientId: string) => request<Booking[]>(`/patients/${patientId}/bookings`),
  book: (slotId: string, patientId: string) =>
    request<Booking>('/bookings', {
      method: 'POST',
      body: JSON.stringify({ slot_id: slotId, patient_id: patientId }),
    }),
  cancel: (bookingId: string) =>
    request<Booking>(`/bookings/${bookingId}/cancel`, { method: 'POST' }),
}
