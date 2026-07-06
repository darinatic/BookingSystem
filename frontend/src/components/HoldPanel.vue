<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import type { Slot } from '../types'
import { formatDay, formatTime } from '../format'

const props = defineProps<{ slot: Slot; doctorName: string; expiresAt: string }>()
defineEmits<{ confirm: []; release: [] }>()

const now = ref(Date.now())
const timer = window.setInterval(() => (now.value = Date.now()), 1000)
onUnmounted(() => clearInterval(timer))

const secondsLeft = computed(() =>
  Math.max(0, Math.round((new Date(props.expiresAt).getTime() - now.value) / 1000)),
)
const countdown = computed(() => {
  const m = Math.floor(secondsLeft.value / 60)
  const s = secondsLeft.value % 60
  return `${m}:${s.toString().padStart(2, '0')}`
})
const expired = computed(() => secondsLeft.value === 0)
</script>

<template>
  <div class="hold">
    <div>
      <div class="hold__title">Slot held, confirm to book</div>
      <div class="hold__meta">
        {{ doctorName }} · {{ formatDay(slot.start_time) }} · {{ formatTime(slot.start_time) }}
      </div>
      <div class="hold__count">
        {{ expired ? 'Hold expired, please pick another slot' : `Confirm within ${countdown}` }}
      </div>
    </div>
    <div class="hold__actions">
      <button class="btn btn--ghost" @click="$emit('release')">Release</button>
      <button class="btn btn--primary" :disabled="expired" @click="$emit('confirm')">
        Confirm booking
      </button>
    </div>
  </div>
</template>
