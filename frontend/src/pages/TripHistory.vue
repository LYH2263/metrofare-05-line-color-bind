<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => {
  const rows = (await getJSON('/api/history')).items
  items.value = rows.map((h) => {
    let result = null
    try { result = JSON.parse(h.result_json) } catch { /* 旧记录可能无序列 */ }
    return { ...h, result }
  })
})
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <tr v-for="h in items" :key="h.id">
        <td>#{{ h.id }}</td>
        <td>{{ h.created_at }}</td>
        <td>
          <template v-if="h.result">
            <span class="muted">{{ h.result.start }} → {{ h.result.end }}</span>
            <span v-for="(lc, i) in h.result.line_sequence" :key="i" class="hist-seq">
              <span class="band-swatch" :style="{ background: h.result.path_edges?.[i]?.line_color }"></span>
              {{ lc }}<span v-if="i > 0 && h.result.line_sequence[i - 1] !== lc" class="transfer-mark">换</span>
            </span>
          </template>
        </td>
      </tr>
    </table>
    <p class="muted">色带为询价当刻固化，随后改色不回填此页。</p>
  </div>
</template>
