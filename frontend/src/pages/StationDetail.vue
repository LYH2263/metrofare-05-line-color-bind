<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, putJSON } from '../api'

const route = useRoute()
const st = ref(null)
const allLines = ref([])
const picked = ref(new Set())
const err = ref('')
const saving = ref(false)

const load = async () => {
  err.value = ''
  const code = route.params.code
  const [station, lines] = await Promise.all([
    getJSON(`/api/stations/${code}`),
    getJSON('/api/lines'),
  ])
  st.value = station
  allLines.value = lines.items
  picked.value = new Set(station.lines.map(l => l.code))
}
onMounted(load)
watch(() => route.params.code, load)

const toggle = (code) => {
  const next = new Set(picked.value)
  next.has(code) ? next.delete(code) : next.add(code)
  picked.value = next
}

const save = async () => {
  err.value = ''
  if (!picked.value.size) {
    err.value = '站点至少归属一条线路'
    return
  }
  saving.value = true
  try {
    st.value = await putJSON(`/api/stations/${st.value.code}/lines`,
      { lines: [...picked.value] })
  } catch (e) {
    err.value = '保存失败：' + e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="page" v-if="st">
    <h1>{{ st.name }}</h1>
    <p class="muted">编码 {{ st.code }}</p>

    <div class="panel">
      <h3>所属线路</h3>
      <p v-if="st.lines.length">
        <span v-for="l in st.lines" :key="l.code"
              class="line-chip" :style="{ '--line-color': l.color }">
          {{ l.name }} <code>{{ l.code }}</code>
        </span>
      </p>
      <p v-else class="err">无归属（异常状态，请立即补归属）</p>
    </div>

    <div class="panel">
      <h3>修改归属</h3>
      <p v-for="l in allLines" :key="l.code">
        <label>
          <input type="checkbox" :checked="picked.has(l.code)" @change="toggle(l.code)">
          <span class="line-chip" :style="{ '--line-color': l.color }">
            {{ l.name }} <code>{{ l.code }}</code>
          </span>
        </label>
      </p>
      <button :disabled="saving" @click="save">保存归属</button>
      <span v-if="err" class="err">{{ err }}</span>
    </div>
  </div>
</template>
