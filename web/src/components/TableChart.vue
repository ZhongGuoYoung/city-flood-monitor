<!-- src/components/TableChart.vue -->
<!-- eslint-disable vue/multi-word-component-names -->
<template>
  <svg aria-hidden="true" style="position:absolute;width:0;height:0;overflow:hidden">
    <!-- 工具栏图标（行列转换 / 图表转换 / 编辑表格 / 导出表格） -->
    <symbol id="icon-行列转换"
                viewBox="0 0 1024 1024">
            <path d="M233.344 344.832H121.92a55.744 55.744 0 0 0-55.744 55.68v501.568a55.744 55.744 0 0 0 55.744 55.744h111.424a55.744 55.744 0 0 0 55.744-55.744V400.512a55.744 55.744 0 0 0-55.744-55.68z m0 585.152v-27.84H121.92V400.512h111.424v501.568zM902.08 66.176H400.512a55.744 55.744 0 0 0-55.744 55.744v111.424a55.744 55.744 0 0 0 55.744 55.744h501.568a55.744 55.744 0 0 0 55.744-55.744V121.92a55.744 55.744 0 0 0-55.744-55.744z m0 195.072v-27.904H400.512V121.92h501.568v111.424zM177.6 66.176a111.424 111.424 0 1 0 111.488 111.424 111.424 111.424 0 0 0-111.488-111.424z m0 167.168a55.744 55.744 0 1 1 55.744-55.744 55.744 55.744 0 0 1-55.744 55.744z m682.688 117.056l-166.912 96.384a27.84 27.84 0 0 0 0 48.512l52.352 30.08a698.24 698.24 0 0 1-219.584 222.912l-32.896-55.744a28.992 28.992 0 0 0-48.512 0L348.16 859.776a27.84 27.84 0 0 0 23.936 41.792h195.648a27.84 27.84 0 0 0 23.936-41.792l-35.648-62.4a753.984 753.984 0 0 0 240.192-244.8l66.88 38.4a27.84 27.84 0 0 0 39.04-23.424v-192.64a27.84 27.84 0 0 0-41.792-23.936z m-439.68 495.936l48.768-83.584 48.512 83.584z m425.728-327.104l-83.584-48.512 83.584-47.936z"
                  p-id="6585"></path>
        </symbol>
        <symbol id="icon-图表转换"
                viewBox="0 0 1024 1024">
            <path d="M648 624h288a24 24 0 0 1 0 48h-288a24 24 0 0 1 0-48z m0 96h288a24 24 0 0 1 0 48h-288a24 24 0 0 1 0-48z m0 96h288a24 24 0 0 1 0 48h-288a24 24 0 0 1 0-48z m0 96h288a24 24 0 0 1 0 48h-288a24 24 0 0 1 0-48z m-96-288a24 24 0 1 1 0 48 24 24 0 0 1 0-48z m0 96a24 24 0 1 1 0 48 24 24 0 0 1 0-48z m0 96a24 24 0 1 1 0 48 24 24 0 0 1 0-48z m0 96a24 24 0 1 1 0 48 24 24 0 0 1 0-48zM64 128a64 64 0 0 1 64-64h320a64 64 0 0 1 64 64v320a64 64 0 0 1-64 64H128a64 64 0 0 1-64-64V128z m48 304a32 32 0 0 0 32 32h288a32 32 0 0 0 32-32V144a32 32 0 0 0-32-32H144a32 32 0 0 0-32 32v288z m48-16c35.424-97.44 72.96-127.872 112.592-91.328 39.632 36.528 70.72 31.568 93.216-14.896 22.48-29.04 38.96-29.04 49.44 0 1.008 17.936 1.008 53.344 0 106.224H160z m224-192a32 32 0 1 1 0-64 32 32 0 0 1 0 64zM198.08 688.768c48.752 105.504 149.12 182.256 268.64 197.888a22.4 22.4 0 0 1-5.824 44.432c-135.856-17.776-249.76-105.376-304.464-225.664l-48.48 19.392a16 16 0 0 1-21.584-18.24l29.888-137.92a16 16 0 0 1 25.376-9.312l108.032 82.752a16 16 0 0 1-3.792 27.552l-47.792 19.12z m640.048-306.224c-48.736-105.504-149.12-182.256-268.624-197.888a22.4 22.4 0 1 1 5.824-44.432c135.84 17.776 249.76 105.376 304.448 225.664l48.48-19.392a16 16 0 0 1 21.584 18.24l-29.888 137.92a16 16 0 0 1-25.36 9.312l-108.048-82.752a16 16 0 0 1 3.792-27.552l47.792-19.12z"
                  p-id="8571"></path>
        </symbol>
        <symbol id="icon-编辑表格"
                viewBox="0 0 1024 1024">
            <path d="M896 288.256v62.464h2.56c22.016 0 43.008 5.632 61.44 16.896V288.256H896z m-211.456 164.352v-163.84h-64v163.84H404.48v-163.84H340.48v163.84H129.024v-163.84H65.024v388.096h-1.024v64h1.024v219.136h279.04L404.48 840.192v-99.84h49.664l30.208-60.928 17.408 17.408 20.48-20.48H404.48v-159.744h216.064v62.464L729.088 471.04l18.432-18.432h-62.976z m-344.064 442.88H129.024v-155.136h210.944c0.512 0 0.512 155.136 0.512 155.136z m0-219.136H129.024v-159.744h210.944c0.512 0 0.512 159.744 0.512 159.744z m558.08-35.84l-2.56 2.56v33.28h-33.28L798.72 740.352h97.28v155.136h-211.456v-8.704l-145.408 72.704h420.352v-379.904l-60.928 60.928z"
                  p-id="5084"></path>
            <path d="M684.544 879.104v-25.088l-12.288 12.288 12.288 12.8z"
                  p-id="5085"></path>
            <path d="M896 288.256v62.464h2.048c22.528 0 43.52 6.144 61.952 17.408V288.256H896z m-766.976 0H65.024v608.256h-1.024v62.976h280.064l31.744-62.976H129.024V288.256z m769.024 352.256l-2.048 2.048v253.952h-230.912l-125.952 62.976h420.864V578.56l-61.952 61.952z"
                  p-id="5086"></path>
            <path d="M937.472 431.104c-22.016-22.016-57.344-22.016-79.36 0l-39.424 39.424 38.912 38.912 0.512 0.512 0.512 0.512 38.912 38.912 39.424-39.424c22.528-21.504 22.528-56.832 0.512-78.848z m-396.288 316.928l237.568-237.568 79.36 79.36-237.568 237.568-79.36-79.36z m-118.784 198.144l158.208-79.36L501.76 787.456l-79.36 158.72zM65.024 64.512h894.976v224.256H65.024V64.512z"
                  p-id="5087"></path>
        </symbol>
        <symbol id="icon-导出表格"
                viewBox="0 0 1024 1024">
            <path d="M896 640v192h128l-192 192-192-192h128v-192h128z m0-384v320h-256v320H0V256h896zM256 576H64v256h192V576z m320 0H320v256h256V576z m0-256H320v192h256V320zM256 320H64v192h192V320z m576 0h-192v192h192V320z m192-256v320h-64V128H256V64h768z"
                  p-id="12046"></path>
            <path d="M0 192v64h896V192z"
                  p-id="12047"></path>

        </symbol>
  </svg>

  <el-container class="view-container" v-bind="attrs">
    <el-header class="view-header">
      <div class="right" ref="toolbarBoxDom">
        <template v-for="(v, k) in toolbar" :key="k">
          <el-tooltip
            v-if="['行列转换','编辑表格','导出表格'].includes(k) ? v.show && !toolbar['图表转换'].mode : v.show"
            :content="k" placement="top" show-after="800" hide-after="0"
            :enterable="false" :append-to="toolbarBoxDom || 'body'"
          >
            <svg @click="handleToolbar(k)"><use :xlink:href="'#icon-' + k"/></svg>
          </el-tooltip>
        </template>
      </div>
    </el-header>

    <el-main class="view-main">
      <!-- 图表模式 -->
      <div v-if="toolbar['图表转换'].mode" class="my-chart" ref="tableToChartDom"></div>

      <!-- 表格模式：行列转换开关 -->
      <template v-else>
        <!-- 行列转换后的表格 -->
        <el-table
          v-if="toolbar['行列转换'].mode"
          class="my-table"
          :data="transformTableData"
          header-row-class-name="table-header-row"
          header-cell-class-name="table-header-cell"
          row-class-name="table-row"
          cell-class-name="table-cell"
          :row-key="row => row?.prop || row?.label || JSON.stringify(row)"
          @sort-change="transformTableSortChange"
        >
          <el-table-column
            v-for="(item, idx) in transformTableColumn"
            :key="item.prop || idx"
            :prop="item.prop"
            :label="item.label"
            :align="item.align || 'center'"
            :width="item.width"
            :fixed="item.fixed"
            :sortable="item.sortable"
          >
            <!-- 不解构 slot props，避免 undefined 报错 -->
            <template #default="scope">
              <template v-if="idx === 0">
                {{ scope?.row?.label }}
              </template>
              <template v-else>
                <template v-if="toolbar['编辑表格'].mode">
                  <el-input v-if="scope && scope.row && model[idx - 1]" v-model="model[idx - 1][scope.row.prop]" />
                  <template v-else>--</template>
                </template>
                <template v-else>
                  {{
                    scope && scope.row && model[idx - 1]
                      ? (Object.hasOwn(scope.row, 'format')
                          ? scope.row.format(model[idx - 1][scope.row.prop])
                          : model[idx - 1][scope.row.prop])
                      : ''
                  }}
                </template>
              </template>
            </template>
          </el-table-column>
        </el-table>

        <!-- 普通表格（未行列转换） -->
        <el-table
          v-else
          class="my-table"
          :data="model"
          header-row-class-name="table-header-row"
          header-cell-class-name="table-header-cell"
          row-class-name="table-row"
          cell-class-name="table-cell"
          :row-key="row => row?.[props.column?.[0]?.prop] ?? JSON.stringify(row)"
          @selection-change="selectionChange"
        >
          <el-table-column
            v-for="(item, idx) in props.column"
            :key="item.prop || item.type || idx"
            :type="item.type"
            :prop="item.prop"
            :align="item.align || 'center'"
            :width="item.width"
            :fixed="item.fixed"
            :sortable="item.sortable"
          >
            <template #header>
              {{ item.label }} <span v-if="item.unit" style="font-size:12px;">({{ item.unit }})</span>
            </template>
            <template #default="scope">
              <template v-if="item.type !== 'selection'">
                <template v-if="toolbar['编辑表格'].mode">
                  <template v-if="idx === 0">
                    {{ Object.hasOwn(item,'format') ? item.format(scope?.row?.[item.prop]) : (scope?.row?.[item.prop] ?? '') }}
                  </template>
                  <template v-else>
                    <el-input v-if="scope && scope.row" v-model="scope.row[item.prop]" />
                    <template v-else>--</template>
                  </template>
                </template>
                <template v-else>
                  {{ Object.hasOwn(item,'format') ? item.format(scope?.row?.[item.prop]) : (scope?.row?.[item.prop] ?? '') }}
                </template>
              </template>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted, useAttrs } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, GridComponent, DataZoomComponent, MarkPointComponent, MarkLineComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent, MarkPointComponent, MarkLineComponent, VisualMapComponent, CanvasRenderer])

/**
 * 用法：
 * <TableChart
 *   v-model="rows"                // 行数据数组
 *   :column="columns"             // 列配置（见下）
 *   :toolbar="[{name:'图表转换',mode:false},{name:'行列转换',mode:false},{name:'编辑表格',mode:false},{name:'导出表格'}]"
 *   :export="{name:'导出文件', type:'csv'}"
 * />
 * 列配置示例：
 * const columns = [
 *   { label:'时间',   prop:'time',  isHeader:true, axis:'x', width:120, format:v=>v },
 *   { label:'淹没范围(%)', prop:'pct',  axis:'y', unit:'%', sortable:'custom' },
 *   { label:'风险等级',   prop:'lvl',  axis:'y', unit:'',  sortable:'custom' }
 * ]
 */

const emit = defineEmits(['update:modelValue', 'getSelectionData'])
const attrs = useAttrs()
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  title:   { type: String, default: '' },
  column:  { type: Array,  default: () => [] },   // 列定义（含 isHeader/axis/unit/format 等）
  toolbar: { type: Array,  default: () => [] },   // 工具栏按钮及初始模式
  export:  { type: Object, default: () => ({}) }, // 导出设置 {name,type:csv|xls|txt}
})
 const model = computed({
   get: () => props.modelValue,
   set: (val) => emit('update:modelValue', val)
 })
const toolbarBoxDom = ref()
const toolbar = ref({
  '图表转换': { show:false, mode:false },
  '行列转换': { show:false, mode:false },
  '编辑表格': { show:false, mode:false },
  '导出表格': { show:false }
})

// 同步外部 toolbar 配置
function computeToolbar(arr){
  const t1 = arr.find(v => v.name==='图表转换') || {}
  const t2 = arr.find(v => v.name==='行列转换') || {}
  const t3 = arr.find(v => v.name==='编辑表格') || {}
  const t4 = arr.find(v => v.name==='导出表格') || {}
  return {
    '图表转换': { show:Object.keys(t1).length!==0, mode:!!t1.mode },
    '行列转换': { show:Object.keys(t2).length!==0, mode:!!t2.mode },
    '编辑表格': { show:Object.keys(t3).length!==0, mode:!!t3.mode },
    '导出表格': { show:Object.keys(t4).length!==0 }
  }
}
toolbar.value = computeToolbar(props.toolbar)
watch(() => props.toolbar, v => { toolbar.value = computeToolbar(v||[]) }, { deep:true })

// —— 行列转换 —— //
const transformTableData = ref(props.column.filter(v => !v.isHeader && v.type !== 'selection'))
const transformTableColumn = computed(() => {
  const header = props.column.find(v => v.isHeader)
  return header ? [
    { label:'', prop:header.prop },
    ...model.value.map(v => ({
      label: header.format ? header.format(v[header.prop]) : v[header.prop],
      prop:  v[header.prop],
      sortable:'custom'
    }))
  ] : []
})

// 排序：更稳的 prop-based 方式（替代 column.no）
function transformTableSortChange({ prop, order }) {
  const idx = transformTableColumn.value.findIndex(c => c.prop === prop)
  const col = model.value[idx - 1] // 第0列是标签列
  if (!col) return
  const kv = Object.entries(col).filter(([k]) => k !== transformTableColumn.value[0]?.prop)
  kv.sort((a,b) => {
    const [va, vb] = [a[1], b[1]]
    if (order === 'ascending') {
      const res = (va ?? '') - (vb ?? '')
      return [null, undefined].includes(va) ? -1 : (isNaN(res) ? String(va).localeCompare(String(vb)) : res)
    } else {
      const res = (vb ?? '') - (va ?? '')
      return [null, undefined].includes(va) ? 1 : (isNaN(res) ? String(vb).localeCompare(String(va)) : res)
    }
  })
  transformTableData.value = kv.map(([k]) => transformTableData.value.find(r => r.prop === k)).filter(Boolean)
}

// —— 图表转换 —— //
const tableToChartDom = ref()
function transformToChart(){
  const xl = props.column.find(v => ['x','X'].includes(v.axis))
  if (!xl) return
  const xAxisData = { [xl.label]: [] }
  const seriesData = {}
  const yl = props.column.filter(v => ['y','Y'].includes(v.axis))
  yl.forEach(v => seriesData[v.label] = [])

  for (const row of model.value) {
    xAxisData[xl.label].push(Object.hasOwn(xl,'format') ? xl.format(row[xl.prop]) : row[xl.prop])
    for (const y of yl) {
      seriesData[y.label].push(Object.hasOwn(y,'format') ? y.format(row[y.prop]) : row[y.prop])
    }
  }
  renderChart(xAxisData, seriesData)
}

function renderChart(xAxisData, seriesData){
  const textColor = '#fff', fontSize = 14
  const option = {
    color: ['rgb(128,255,165)', 'orange', 'green'],
    grid: { left:0, right:0, bottom:0, top:50, containLabel:true },
    tooltip: {
      trigger:'axis', axisPointer:{ type:'cross' }, textStyle:{ align:'left' },
      formatter: (params) => {
        return `<div>${params[0].name}</div>
        <div style="display:grid;grid-template-columns:repeat(3,auto);gap:5px;align-items:center;">
        ${params.map(v => {
          const target = props.column.find(f => f.label === v.seriesName) || {}
          return `${v.marker}<span>${v.seriesName}</span><span style="margin-left:1em;">${v.value ?? '--'} ${target.unit||''}</span>`
        }).join('')}
        </div>`
      }
    },
    legend: {
      top:'top', itemWidth:60, itemHeight:20,
      textStyle:{ color:textColor, fontSize }, data:Object.keys(seriesData).map(k => ({ name:k, icon:'roundRect' }))
    },
    toolbox: {
      iconStyle:{ borderColor:textColor }, itemSize:16,
      feature: {
        magicType: {
          type:['line','bar'],
          option:{
            bar:{ emphasis:{ focus:'series', itemStyle:{ shadowBlur:6, shadowColor:'rgba(0,0,0,.3)' } } }
          }
        },
        dataZoom: {}
      }
    },
    xAxis: {
      data: Object.values(xAxisData)[0],
      nameTextStyle:{ color:textColor, fontSize },
      axisLabel:{ color:textColor, fontSize },
      axisLine:{ lineStyle:{ color:'#33dba9' } },
      axisTick:{ alignWithLabel:true }
    },
    yAxis: {
      type:'value',
      nameTextStyle:{ color:textColor, fontSize },
      axisLabel:{ color:textColor, fontSize },
      axisLine:{ lineStyle:{ color:'#33dba9' } }
    },
    series: Object.entries(seriesData).map(([k, v]) => {
      const colDef = props.column.find(c => c.label === k) || {}
      const seriesColor = colDef.color
      return {
        name:k, data:v, type:'line', smooth:true, showSymbol:false, emphasis:{ focus:'series' },
        lineStyle:{ width:2, ...(seriesColor ? { color:seriesColor } : {}) },
        itemStyle: seriesColor ? { color:seriesColor } : void 0,
        markPoint: { symbol:'pin', symbolSize:45, label:{ color:'#fff', fontSize:15 }, data:[{type:'max'},{type:'min'}] }
      }
    })
  }
  nextTick(() => {
    const mychart = echarts.init(tableToChartDom.value, null, { locale:'ZH' })
    mychart.clear()
    mychart.setOption(option)
  })
}

// —— 导出 —— //
function exportFile(){
  const data = toolbar.value['行列转换'].mode
    ? [ transformTableColumn.value.map(v => v.label),
        ...transformTableData.value.map(row => [row.label, ...model.value.map(m => m[row.prop])]) ]
    : [ props.column.map(c => c.label),
        ...model.value.map(r => props.column.map(c => r[c.prop])) ]

  const name = props.export.name || '导出文件'
  const type = props.export.type || 'csv'
  const mime = { txt:'text/plain', csv:'text/csv', xls:'application/vnd.ms-excel' }[type] || 'text/csv'
  let s = ''
  if (type === 'xls' || type === 'csv') {
    for (const row of data) s += row.join(',') + '\r\n'
  } else {
    for (const row of data) s += row.join('\t') + '\r\n'
  }
  const a = document.createElement('a')
  a.href = 'data:' + mime + ';charset=utf-8,\ufeff' + encodeURIComponent(s)
  a.download = name + '.' + type
  a.click()
}

// —— 工具栏点击 —— //
function handleToolbar(name){
  toolbar.value[name].mode = !toolbar.value[name].mode
  if (name === '导出表格') exportFile()
  if (name === '图表转换' && toolbar.value['图表转换'].mode) transformToChart()
  if (name === '行列转换' && toolbar.value['行列转换'].mode)
    transformTableData.value = props.column.filter(v => !v.isHeader && v.type !== 'selection')
}

onMounted(() => {
  if (toolbar.value['图表转换'].mode) transformToChart()
  if (toolbar.value['行列转换'].mode)
    transformTableData.value = props.column.filter(v => !v.isHeader && v.type !== 'selection')
})

// 监听数据变化：同步两种模式
watch(model, () => {
  if (toolbar.value['图表转换'].mode) transformToChart()
  if (toolbar.value['行列转换'].mode)
    transformTableData.value = props.column.filter(v => !v.isHeader && v.type !== 'selection')
})

// 多选回传
function selectionChange(array){ emit('getSelectionData', array) }
</script>

<style scoped lang="scss">
:deep(.my-table){
  --el-table-bg-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-border: 1px solid #c6d7de;
  --el-table-text-color: #fff;
  --el-table-header-text-color: #fff;
  --el-table-row-hover-bg-color: rgba(0,0,0,.2);

  .el-table--border .el-table__cell { border-right: none; }
  .table-header-row { height:45px; font-size:16px; }
  .table-row { min-height:56px; font-size:15px; }
  .table-cell, .table-header-cell { padding:0; }
}

.view-container{
  --color:#fff;
  width:100%; height:100%; background:#0E1A2B; color:var(--color); font-size:16px;
  display:flex; flex-direction:column;

  .view-header{
    height:40px; padding:0 20px; display:flex; justify-content:flex-end; align-items:center;
    .right{ display:flex; align-items:center; gap:10px;
      svg{ width:1.4em; height:1.4em; cursor:pointer; fill:var(--color); transition:.2s;
        &:hover{ scale:1.2; fill:orange; }
      }
    }
  }
  .view-main{ flex:1; min-height:0; display:flex; flex-direction:column; padding:8px; }
  .my-chart,.my-table{ width:100%; height:100%; }
}
</style>
