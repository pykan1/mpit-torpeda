<template>
  <div v-if="thinking" class="animate-fade-in">
    <button
      @click="expanded = !expanded"
      class="w-full flex items-center gap-2 text-sm font-medium text-yellow-700 mb-2 hover:text-yellow-800 transition-colors"
    >
      <IconBrain class="w-4 h-4 flex-shrink-0" />
      <span>Размышления ИИ</span>
      <span class="ml-auto">
        <IconChevronUp v-if="expanded" class="w-4 h-4" />
        <IconChevronDown v-else class="w-4 h-4" />
      </span>
    </button>

    <div v-if="expanded" class="thinking-panel animate-fade-in">
      <div class="flex items-center gap-2 mb-3 pb-2 border-b border-yellow-200">
        <div class="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></div>
        <span class="text-yellow-600 font-semibold text-xs uppercase tracking-wide">Chain of Thought</span>
      </div>
      <div class="text-gray-700 leading-relaxed">{{ thinking }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import IconBrain from './icons/IconBrain.vue'
import IconChevronUp from './icons/IconChevronUp.vue'
import IconChevronDown from './icons/IconChevronDown.vue'

defineProps({ thinking: { type: String, default: '' } })
const expanded = ref(true)
</script>
