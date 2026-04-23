<template>
  <div class="flex items-start gap-3 p-4 rounded-xl border" :class="containerClass">
    <component :is="iconComponent" class="w-5 h-5 mt-0.5 flex-shrink-0" :class="iconClass" />
    <div class="flex-1">
      <div class="flex items-center gap-2 mb-1">
        <span class="font-semibold text-sm" :class="labelClass">Guardrail: {{ label }}</span>
        <span class="text-xs px-2 py-0.5 rounded-full font-mono" :class="badgeClass">{{ guardrail.severity }}</span>
      </div>
      <ul v-if="guardrail.violations?.length" class="space-y-0.5">
        <li v-for="v in guardrail.violations" :key="v" class="text-xs text-red-600 flex items-center gap-1.5">
          <IconBan class="w-3 h-3 flex-shrink-0" /> {{ v }}
        </li>
      </ul>
      <ul v-if="guardrail.warnings?.length" class="space-y-0.5 mt-1">
        <li v-for="w in guardrail.warnings" :key="w" class="text-xs text-yellow-600 flex items-center gap-1.5">
          <IconWarning class="w-3 h-3 flex-shrink-0" /> {{ w }}
        </li>
      </ul>
      <p v-if="!guardrail.violations?.length && !guardrail.warnings?.length" class="text-xs text-drivee-600">
        SQL проверен — вредоносных команд не обнаружено
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import IconCheck from './icons/IconCheck.vue'
import IconX from './icons/IconX.vue'
import IconWarning from './icons/IconWarning.vue'
import IconBan from './icons/IconBan.vue'
import IconShield from './icons/IconShield.vue'

const props = defineProps({ guardrail: { type: Object, required: true } })

const iconComponent = computed(() => {
  if (props.guardrail.severity === 'blocked') return IconX
  if (props.guardrail.severity === 'warning') return IconWarning
  return IconCheck
})

const iconClass = computed(() => {
  if (props.guardrail.severity === 'blocked') return 'text-red-600'
  if (props.guardrail.severity === 'warning') return 'text-yellow-600'
  return 'text-drivee-600'
})

const label = computed(() => {
  if (props.guardrail.severity === 'blocked') return 'ЗАБЛОКИРОВАНО'
  if (props.guardrail.severity === 'warning') return 'ПРЕДУПРЕЖДЕНИЕ'
  return 'БЕЗОПАСНО'
})

const containerClass = computed(() => {
  if (props.guardrail.severity === 'blocked') return 'bg-red-50 border-red-200'
  if (props.guardrail.severity === 'warning') return 'bg-yellow-50 border-yellow-200'
  return 'bg-drivee-50 border-drivee-200'
})

const labelClass = computed(() => {
  if (props.guardrail.severity === 'blocked') return 'text-red-700'
  if (props.guardrail.severity === 'warning') return 'text-yellow-700'
  return 'text-drivee-700'
})

const badgeClass = computed(() => {
  if (props.guardrail.severity === 'blocked') return 'bg-red-100 text-red-600'
  if (props.guardrail.severity === 'warning') return 'bg-yellow-100 text-yellow-600'
  return 'bg-drivee-100 text-drivee-600'
})
</script>
