<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getJSON, putJSON } from '../api'
import { lineStore } from '../store'

const route = useRoute()
const st = ref(null)
const picked = ref([])
const editing = ref(false)
const error = ref('')

const load = async () => {
  editing.value = false
  error.value = ''
  await lineStore.load()
  st.value = await getJSON(`/api/stations/${route.params.code}`)
  picked.value = [...st.value.line_codes]
}
onMounted(load)
watch(() => route.params.code, load)

function toggle(code) {
  const i = picked.value.indexOf(code)
  if (i >= 0) picked.value.splice(i, 1)
  else picked.value.push(code)
}

async function save() {
  error.value = ''
  try {
    st.value = await putJSON(`/api/stations/${st.value.code}/lines`, { line_codes: picked.value })
    picked.value = [...st.value.line_codes]
    editing.value = false
  } catch (e) {
    error.value = `改归属被拒：${e.message}`
  }
}
</script>

<template>
  <div class="page" v-if="st">
    <h1>{{ st.name }}</h1>
    <p class="muted">编码 {{ st.code }}</p>

    <div class="panel">
      <div class="line-head">
        <strong>归属线路</strong>
        <button class="mini" @click="editing = !editing">
          {{ editing ? '取消' : '改归属' }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <ul v-if="!editing" class="membership-list">
        <li v-for="l in st.lines" :key="l.code">
          <span class="band-swatch" :style="{ background: l.color }"></span>
          {{ l.name }} <span class="muted">{{ l.code }} · {{ l.color }}</span>
        </li>
      </ul>

      <div v-else class="membership-edit">
        <label v-for="l in lineStore.lines" :key="l.code" class="check-line">
          <input type="checkbox" :checked="picked.includes(l.code)" @change="toggle(l.code)" />
          <span class="band-swatch" :style="{ background: l.color }"></span>
          {{ l.name }} <span class="muted">{{ l.code }}</span>
        </label>
        <p class="muted">至少保留一条线路；含不存在线路时整体拒绝，不会留下半截归属。</p>
        <button class="mini" @click="save">保存归属</button>
      </div>
    </div>
  </div>
</template>
