export interface Doctor {
  id: string
  name: string
  specialty: string | null
}

export interface Patient {
  id: string
  name: string
  email: string | null
}

export interface Slot {
  id: string
  doctor_id: string
  start_time: string
  end_time: string
}

export type BookingStatus = 'pending' | 'confirmed' | 'cancelled' | 'completed'

export interface Booking {
  id: string
  slot_id: string
  patient_id: string
  status: BookingStatus
  expires_at: string | null
  created_at: string
  slots?: {
    start_time: string
    end_time: string
    doctors?: { name: string; specialty: string | null }
  }
}
