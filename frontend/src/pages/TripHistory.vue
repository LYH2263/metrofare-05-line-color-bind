<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => {
  const rows = (await getJSON('/api/history')).items
  items.value = rows.map(r => ({ ...r, result: safeParse(r.result_json) }))
})
const safeParse = (t) => { try { return JSON.parse(t) } catch { return null } }
</script>
<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <thead><tr><th>#</th><th>时间</th><th>起终（写入时编码）</th><th>票价快照</th></tr></thead>
      <tbody>
        <tr v-for="h in items" :key="h.id">
          <td>#{{ h.id }}</td>
          <td>{{ h.created_at }}</td>
          <td>
            <template v-if="h.result">
              {{ h.result.start }} → {{ h.result.end }}
              <span v-if="!h.result.reachable" class="muted">不可达</span>
            </template>
          </td>
          <td>
            <template v-if="h.result?.reachable">
              ¥{{ h.result.fare }} · 换线 {{ h.result.transfers ?? 0 }}
              <span v-for="(seg, i) in (h.result.line_sequence ?? [])" :key="i"
                    class="line-chip" :style="{ '--line-color': seg.color }">{{ seg.code }}</span>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
    <p class="muted">色带与起终点编码均为询价写入时的快照，不随后续改色回填。</p>
  </div>
</template>
