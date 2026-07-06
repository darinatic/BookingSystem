<script setup lang="ts">
import type { Patient } from '../types'

defineProps<{ patients: Patient[]; modelValue: string }>()
defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<template>
  <div class="switcher">
    <label for="patient">Booking as</label>
    <select
      id="patient"
      :value="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-for="p in patients" :key="p.id" :value="p.id">{{ p.name }}</option>
    </select>
  </div>
</template>
