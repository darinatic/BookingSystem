<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, ApiError } from './api'
import type { Booking, Doctor, Patient, Slot } from './types'
import PatientSwitcher from './components/PatientSwitcher.vue'
import DoctorList from './components/DoctorList.vue'
import SlotPicker from './components/SlotPicker.vue'
import MyBookings from './components/MyBookings.vue'

const patients = ref<Patient[]>([])
const doctors = ref<Doctor[]>([])
const slots = ref<Slot[]>([])
const bookings = ref<Booking[]>([])

const patientId = ref('')
const doctorId = ref<string | null>(null)
const busy = ref(false)

const toast = ref<{ text: string; error: boolean } | null>(null)
let toastTimer: number | undefined

const selectedDoctor = computed(() => doctors.value.find((d) => d.id === doctorId.value) ?? null)

function notify(text: string, error = false) {
  toast.value = { text, error }
  clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => (toast.value = null), 3200)
}

async function loadSlots() {
  if (!doctorId.value) return
  slots.value = await api.listAvailableSlots(doctorId.value)
}

async function loadBookings() {
  if (!patientId.value) return
  bookings.value = await api.listBookings(patientId.value)
}

async function book(slot: Slot) {
  busy.value = true
  try {
    await api.book(slot.id, patientId.value)
    await Promise.all([loadSlots(), loadBookings()])
    notify('Slot booked.')
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      notify('That slot was just taken. Please pick another.', true)
      await loadSlots()
    } else {
      notify('Could not book that slot.', true)
    }
  } finally {
    busy.value = false
  }
}

async function cancel(booking: Booking) {
  try {
    await api.cancel(booking.id)
    await Promise.all([loadSlots(), loadBookings()])
    notify('Booking cancelled.')
  } catch {
    notify('Could not cancel that booking.', true)
  }
}

watch(doctorId, loadSlots)
watch(patientId, loadBookings)

onMounted(async () => {
  ;[patients.value, doctors.value] = await Promise.all([api.listPatients(), api.listDoctors()])
  patientId.value = patients.value[0]?.id ?? ''
  doctorId.value = doctors.value[0]?.id ?? null
})
</script>

<template>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <div class="brand__mark">+</div>
        <div>
          <div class="brand__name">GoDoc</div>
          <div class="brand__tag">Consultation booking</div>
        </div>
      </div>
      <PatientSwitcher v-model="patientId" :patients="patients" />
    </header>

    <div class="grid">
      <DoctorList :doctors="doctors" :selected-id="doctorId" @select="doctorId = $event" />
      <SlotPicker
        :slots="slots"
        :doctor-name="selectedDoctor?.name ?? null"
        :busy="busy"
        @book="book"
      />
    </div>

    <section class="section">
      <MyBookings :bookings="bookings" @cancel="cancel" />
    </section>

    <div v-if="toast" class="toast" :class="{ 'toast--error': toast.error }">
      {{ toast.text }}
    </div>
  </div>
</template>
