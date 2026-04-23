<template>
  <svg :class="cls" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
  </svg>
</template>
<script setup>
const props = defineProps({ class: { type: String, default: 'w-4 h-4' } })
const cls = props.class
</script>
