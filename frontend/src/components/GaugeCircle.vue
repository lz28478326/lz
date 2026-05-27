<template>
  <div class="gauge" :class="size">
    <svg viewBox="0 0 120 120">
      <circle cx="60" cy="60" r="50" class="bg-ring" />
      <circle cx="60" cy="60" r="50" class="color-ring"
        :stroke="color"
        :style="{ strokeDasharray: (value || 0) * 3.14 + ' 314' }" />
    </svg>
    <div class="gauge-text">
      <span class="gauge-value">{{ value || 0 }}%</span>
      <span class="gauge-label">{{ label }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: Number,
  color: { type: String, default: '#4fd2f1' },
  size: { type: String, default: 'normal' }
})
</script>

<style scoped>
.gauge { position: relative; display: flex; flex-direction: column; align-items: center; }
.gauge.normal { width: 90px; height: 90px; }
.gauge.small { width: 70px; height: 70px; }
.gauge svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.bg-ring { fill: none; stroke: #1a2a4a; stroke-width: 6; }
.color-ring { fill: none; stroke-width: 6; stroke-linecap: round; transition: stroke-dasharray 0.5s; }
.gauge-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.gauge-value { font-size: 14px; font-weight: bold; display: block; }
.gauge.small .gauge-value { font-size: 12px; }
.gauge-label { font-size: 9px; color: #6b9bd6; display: block; margin-top: 2px; }
</style>
