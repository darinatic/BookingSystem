<script setup lang="ts">
import type { Doctor } from '../types'

defineProps<{ doctors: Doctor[]; selectedId: string | null }>()
defineEmits<{ select: [id: string] }>()
</script>

<template>
  <div class="panel">
    <div class="panel__head"><p class="panel__title">Doctors</p></div>
    <div class="panel__body">
      <button
        v-for="d in doctors"
        :key="d.id"
        class="doctor"
        :class="{ 'doctor--active': d.id === selectedId }"
        @click="$emit('select', d.id)"
      >
        <span class="doctor__name">{{ d.name }}</span>
        <span class="doctor__specialty">{{ d.specialty }}</span>
      </button>
    </div>
  </div>
</template>
