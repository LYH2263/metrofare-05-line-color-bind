<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, putJSON } from '../api'

const d = ref(null)
const draft = ref({})
const saving = ref({})
const err = ref({})

const load = async () => {
  d.value = await getJSON('/api/dashboard')
  for (const l of d.value.lines) draft.value[l.code] = l.color
}
onMounted(load)

const saveColor = async (line) => {
  err.value[line.code] = ''
  const color = draft.value[line.code] || ''
  if (!/^#[0-9a-fA-F]{6}$/.test(color)) {
    err.value[line.code] = '色值需为 #RRGGBB（如 #e85d04）'
    return
  }
  saving.value[line.code] = true
  try {
    const updated = await putJSON(`/api/lines/${line.code}/color`, { color })
    line.color = updated.color
    draft.value[line.code] = updated.color
  } catch (e) {
    err.value[line.code] = '改色失败：' + e.message
  } finally {
    saving.value[line.code] = false
  }
}
</script>

<template>
  <div class="page"><h1>线网概览</h1>
    <div v-if="d" class="panel">
      <p>站点 {{ d.station_count }} · 区间 {{ d.edge_count }}</p>
      <p>正常 {{ d.clean_stations }} · 种子 {{ d.dirty_stations }}</p>
    </div>

    <div v-for="l in (d?.lines ?? [])" :key="l.code" class="panel">
      <div class="line-group" :style="{ '--line-color': l.color }">
        <h3>
          <span>{{ l.name }}</span>
          <span class="line-chip" :style="{ '--line-color': l.color }"><code>{{ l.code }}</code></span>
        </h3>
        <p v-if="!l.stations.length" class="muted">该线路暂无归属站点</p>
        <p v-else>
          <router-link v-for="s in l.stations" :key="s.code"
                       class="line-chip" :style="{ '--line-color': l.color }"
                       :to="`/stations/${s.code}`">
            {{ s.name }} <code>{{ s.code }}</code>
          </router-link>
        </p>
        <p>
          <label class="muted">色带
            <input v-model="draft[l.code]" placeholder="#RRGGBB" maxlength="7">
          </label>
          <button :disabled="saving[l.code]" @click="saveColor(l)">改色带</button>
          <span v-if="err[l.code]" class="err">{{ err[l.code] }}</span>
        </p>
      </div>
    </div>
  </div>
</template>
