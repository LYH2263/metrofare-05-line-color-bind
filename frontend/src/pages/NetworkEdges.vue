<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/edges')).items })
</script>
<template>
  <div class="page"><h1>邻接区间</h1>
    <ul class="edge-list">
      <li v-for="(e,i) in items" :key="i" class="edge-row">
        <span class="band-swatch" :style="{ background: e.line_color }"></span>
        <span class="edge-line">{{ e.line_name }} <span class="muted">{{ e.line_code }}</span></span>
        <span class="edge-ends">{{ e.a }} — {{ e.b }}</span>
        <span class="muted">{{ e.line_color }}</span>
      </li>
    </ul>
  </div>
</template>
