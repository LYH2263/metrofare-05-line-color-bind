<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
const err = ref('')
onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
const run = async () => {
  err.value = ''
  try {
    out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: true })
  } catch (e) {
    out.value = null
    err.value = '试算失败：' + e.message
  }
}
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <button @click="run">试算</button>
    </div>
    <div v-if="err" class="err">{{ err }}</div>
    <div v-if="out" class="panel">
      <p v-if="out.reachable">站数 {{ out.hops }} · 票价 <span class="hero-num">¥{{ out.fare }}</span></p>
      <p v-if="out.reachable">
        途经线路：
        <template v-for="(seg, i) in out.line_sequence" :key="i">
          <span v-if="i && out.line_sequence[i-1].code !== seg.code" class="muted"> ⇄ </span>
          <span class="line-chip" :style="{ '--line-color': seg.color }">
            {{ seg.name ?? '未指定' }} <code>{{ seg.code ?? '—' }}</code>
          </span>
        </template>
      </p>
      <p v-if="out.reachable" class="muted">换线 {{ out.transfers }} 次（相邻区间线路不同计一次）</p>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
