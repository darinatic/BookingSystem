<script setup lang="ts">
import { computed } from 'vue'
import type { Slot } from '../types'
import { dayKey, formatDay, formatTime } from '../format'

const props = defineProps<{ slots: Slot[]; doctorName: string | null; busy: boolean }>()
defineEmits<{ book: [slot: Slot] }>()

const days = computed(() => {
  const groups = new Map<string, Slot[]>()
  for (const slot of props.slots) {
    const key = dayKey(slot.start_time)
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(slot)
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b))
})
</script>

<template>
  <div class="panel">
    <div class="panel__head">
      <p class="panel__title">
        Available slots<span v-if="doctorName"> · {{ doctorName }}</span>
      </p>
    </div>
    <div v-if="!doctorName" class="empty">Select a doctor to see open times.</div>
    <div v-else-if="slots.length === 0" class="empty">
      No open slots for this doctor right now.
    </div>
    <div v-else>
      <div v-for="[key, group] in days" :key="key" class="day">
        <div class="day__label">
          {{ formatDay(group[0].start_time) }}
          <span class="day__count">{{ group.length }} open</span>
        </div>
        <div class="chips">
          <button
            v-for="slot in group"
            :key="slot.id"
            class="chip"
            :disabled="busy"
            @click="$emit('book', slot)"
          >
            {{ formatTime(slot.start_time) }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
