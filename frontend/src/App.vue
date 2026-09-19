<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from './api'
const lines = ref([])
onMounted(async () => { try { lines.value = (await getJSON('/api/lines')).items } catch { /* 离线展示 */ } })
</script>
<template>
  <div class="metro-shell">
    <header class="line-bar">
      <span v-for="l in lines" :key="l.code"
            class="line-chip" :style="{ '--line-color': l.color }">
        {{ l.name }} <code>{{ l.code }}</code>
      </span>
      <span class="brand">Metrofare</span>
    </header>
    <nav class="tab-nav">
      <router-link to="/">线网</router-link>
      <router-link to="/stations">站点</router-link>
      <router-link to="/planner">票价试算</router-link>
      <router-link to="/fares">规则</router-link>
      <router-link to="/network">邻接</router-link>
      <router-link to="/history">记录</router-link>
      <router-link to="/settings">设置</router-link>
    </nav>
    <router-view />
  </div>
</template>
