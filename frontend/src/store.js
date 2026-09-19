import { reactive } from 'vue'
import { getJSON } from './api'

// 全站共享的线路色带口径：改色后刷新这里，顶栏/线网页/详情看到的就是同一值
export const lineStore = reactive({
  lines: [],
  async load() {
    this.lines = (await getJSON('/api/lines')).items
  },
  byCode(code) {
    return this.lines.find((l) => l.code === code)
  },
})
