<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'
const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })
const run = async () => { out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist: true }) }
</script>
<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option></select>
      <button @click="run">试算</button>
    </div>
    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <p>站数 {{ out.hops }} · 换线 <strong>{{ out.transfers }}</strong> 次 · 票价 <span class="hero-num">¥{{ out.fare }}</span></p>
        <p class="muted">起讫编码 {{ out.start }} → {{ out.end }}</p>
        <div class="seq">
          <template v-for="(e, i) in out.path_edges" :key="i">
            <span class="seg" :style="{ borderColor: e.line_color }">
              <span class="band-swatch" :style="{ background: e.line_color }"></span>
              {{ e.a }} → {{ e.b }}
              <span class="muted">{{ e.line_code }}</span>
            </span>
            <span v-if="i > 0 && out.path_edges[i - 1].line_code !== e.line_code" class="transfer-mark">换线</span>
          </template>
        </div>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
