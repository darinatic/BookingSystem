<script setup lang="ts">
import type { Booking } from '../types'
import { formatDay, formatTime } from '../format'

defineProps<{ bookings: Booking[] }>()
defineEmits<{ cancel: [booking: Booking] }>()

const canCancel = (b: Booking) => b.status === 'confirmed' || b.status === 'pending'
</script>

<template>
  <div class="panel">
    <div class="panel__head"><p class="panel__title">My bookings</p></div>
    <div v-if="bookings.length === 0" class="empty">No bookings yet — pick a slot above.</div>
    <div v-else>
      <div v-for="b in bookings" :key="b.id" class="booking">
        <div>
          <div class="booking__when" v-if="b.slots">
            {{ formatDay(b.slots.start_time) }} · {{ formatTime(b.slots.start_time) }}
          </div>
          <div class="booking__who" v-if="b.slots?.doctors">
            {{ b.slots.doctors.name }} · {{ b.slots.doctors.specialty }}
          </div>
        </div>
        <div class="booking__right">
          <span class="badge" :class="`badge--${b.status}`">{{ b.status }}</span>
          <button v-if="canCancel(b)" class="linkbtn" @click="$emit('cancel', b)">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>
