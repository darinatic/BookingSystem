<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, ApiError } from './api'
import type { Booking, Doctor, Patient, Slot } from './types'
import PatientSwitcher from './components/PatientSwitcher.vue'
import DoctorList from './components/DoctorList.vue'
import SlotPicker from './components/SlotPicker.vue'
import HoldPanel from './components/HoldPanel.vue'
import MyBookings from './components/MyBookings.vue'

const patients = ref<Patient[]>([])
const doctors = ref<Doctor[]>([])
const slots = ref<Slot[]>([])
const bookings = ref<Booking[]>([])

const patientId = ref('')
const doctorId = ref<string | null>(null)
const busy = ref(false)

// The active hold awaiting confirmation (the second step of booking).
const heldBooking = ref<Booking | null>(null)
const heldSlot = ref<Slot | null>(null)

const toast = ref<{ text: string; error: boolean } | null>(null)
let toastTimer: number | undefined

const selectedDoctor = computed(() => doctors.value.find((d) => d.id === doctorId.value) ?? null)
const heldDoctorName = computed(
  () => doctors.value.find((d) => d.id === heldSlot.value?.doctor_id)?.name ?? '',
)

function notify(text: string, error = false) {
  toast.value = { text, error }
  clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => (toast.value = null), 3200)
}

async function refresh() {
  await Promise.all([
    doctorId.value ? api.listAvailableSlots(doctorId.value).then((s) => (slots.value = s)) : null,
    patientId.value ? api.listBookings(patientId.value).then((b) => (bookings.value = b)) : null,
  ])
}

async function hold(slot: Slot) {
  busy.value = true
  try {
    heldBooking.value = await api.book(slot.id, patientId.value)
    heldSlot.value = slot
    await refresh()
    notify('Slot held. Confirm to book it.')
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      notify('That slot was just taken. Please pick another.', true)
      await refresh()
    } else {
      notify('Could not hold that slot.', true)
    }
  } finally {
    busy.value = false
  }
}

function clearHold() {
  heldBooking.value = null
  heldSlot.value = null
}

async function confirm(booking: Booking) {
  try {
    await api.confirm(booking.id)
    if (heldBooking.value?.id === booking.id) clearHold()
    await refresh()
    notify('Appointment confirmed.')
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      notify('That hold expired. Please pick the slot again.', true)
      if (heldBooking.value?.id === booking.id) clearHold()
      await refresh()
    } else {
      notify('Could not confirm that booking.', true)
    }
  }
}

async function cancel(booking: Booking) {
  try {
    await api.cancel(booking.id)
    if (heldBooking.value?.id === booking.id) clearHold()
    await refresh()
    notify('Booking cancelled.')
  } catch {
    notify('Could not cancel that booking.', true)
  }
}

watch(doctorId, () => api.listAvailableSlots(doctorId.value!).then((s) => (slots.value = s)))
watch(patientId, () => {
  clearHold()
  api.listBookings(patientId.value).then((b) => (bookings.value = b))
})

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

    <HoldPanel
      v-if="heldBooking && heldSlot"
      :slot="heldSlot"
      :doctor-name="heldDoctorName"
      :expires-at="heldBooking.expires_at!"
      @confirm="confirm(heldBooking!)"
      @release="cancel(heldBooking!)"
    />

    <div class="grid">
      <DoctorList :doctors="doctors" :selected-id="doctorId" @select="doctorId = $event" />
      <SlotPicker
        :slots="slots"
        :doctor-name="selectedDoctor?.name ?? null"
        :busy="busy"
        @book="hold"
      />
    </div>

    <section class="section">
      <MyBookings :bookings="bookings" @confirm="confirm" @cancel="cancel" />
    </section>

    <div v-if="toast" class="toast" :class="{ 'toast--error': toast.error }">
      {{ toast.text }}
    </div>
  </div>
</template>
