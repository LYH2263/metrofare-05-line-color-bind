<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, patchJSON } from '../api'
import { lineStore } from '../store'

const d = ref(null)
const editing = ref(null)   // 正在改色的线路编码
const draftColor = ref('')
const error = ref('')

const groups = computed(() => {
  if (!d.value) return []
  // 一条线路一个分组；换乘站会出现在它归属的每个分组里
  return lineStore.lines.map((line) => ({
    ...line,
    stations: d.value.stations.filter((s) => s.line_codes.includes(line.code)),
  }))
})

async function reload() {
  await lineStore.load()
  d.value = await getJSON('/api/dashboard')
}
onMounted(reload)

function startEdit(line) {
  editing.value = line.code
  draftColor.value = line.color
  error.value = ''
}

async function saveColor() {
  error.value = ''
  try {
    await patchJSON(`/api/lines/${editing.value}`, { color: draftColor.value })
    editing.value = null
    await reload()
  } catch (e) {
    error.value = `改色被拒：${e.message}`
  }
}
</script>

<template>
  <div class="page">
    <h1>线网概览</h1>
    <div v-if="d" class="panel">
      <p>站点 {{ d.station_count }} · 区间 {{ d.edge_count }}</p>
      <p>正常 {{ d.clean_stations }} · 种子 {{ d.dirty_stations }}</p>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-for="g in groups" :key="g.code" class="panel line-group" :style="{ borderLeftColor: g.color }">
      <div class="line-head">
        <span class="band-swatch" :style="{ background: g.color }"></span>
        <strong>{{ g.name }}</strong>
        <span class="muted">{{ g.code }} · {{ g.color }}</span>
        <button class="mini" @click="startEdit(g)">改色带</button>
        <span v-if="editing === g.code" class="color-edit">
          <input v-model="draftColor" maxlength="7" placeholder="#RRGGBB" />
          <button class="mini" @click="saveColor">保存</button>
          <button class="mini ghost" @click="editing = null">取消</button>
        </span>
      </div>
      <div class="station-chips">
        <router-link
          v-for="s in g.stations"
          :key="g.code + s.code"
          class="chip"
          :to="`/stations/${s.code}`"
          :style="{ borderColor: g.color, color: g.color }"
        >
          <span class="chip-dot" :style="{ background: g.color }"></span>{{ s.name }}
          <span class="muted">{{ s.code }}</span>
        </router-link>
      </div>
    </div>
  </div>
</template>
