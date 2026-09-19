<script setup>
import { onMounted } from 'vue'
import { lineStore } from './store'
onMounted(() => lineStore.load())
</script>

<template>
  <div class="metro-shell">
    <header class="line-bar">
      <span
        v-for="l in lineStore.lines"
        :key="l.code"
        class="line-tab"
        :style="{ borderLeftColor: l.color }"
      >{{ l.name }}</span>
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
