<template>
  <div class="dashboard">
    <!-- 顶部 -->
    <div class="header">
      <div class="header-left">
        <div class="logo">🖥️</div>
        <span class="time">{{ currentTime }}</span>
      </div>
      <h1 class="title">分布式服务器监控控制大屏</h1>
      <div class="header-right">
        <button @click="showAddServer = true" class="btn-header">➕ 添加主机</button>
        <button @click="showAllCommands = true" class="btn-header">📋 命令库</button>
        <span class="status-dot" :class="{ online: wsConnected }"></span>
        <span class="status-text">{{ wsConnected ? '已连接' : '断开' }}</span>
        <span class="version">v1.0 Docker</span>
      </div>
    </div>

    <!-- 主体 -->
    <div class="main-content">
      <!-- 监控中心 -->
      <div class="panel local-panel">
        <div class="panel-header">
          <span class="dot online"></span>
          <span>监控中心</span>
          <span class="badge">本机</span>
        </div>
        <div class="gauges-row">
          <GaugeCircle label="CPU" :value="local.cpu" color="#00d4ff" />
          <GaugeCircle label="内存" :value="local.memory" color="#f6dd0e" />
          <GaugeCircle label="磁盘" :value="local.disk" color="#e65d5d" />
        </div>
        <div class="info-row">
          <div class="info-item">
            <span class="info-label">系统负载</span>
            <span class="info-value">{{ local.load }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">网络 ↑</span>
            <span class="info-value">{{ formatNet(local.net_sent) }} MB/s</span>
          </div>
          <div class="info-item">
            <span class="info-label">网络 ↓</span>
            <span class="info-value">{{ formatNet(local.net_recv) }} MB/s</span>
          </div>
        </div>
        <div class="chart-container">
          <div ref="chartRef" class="chart"></div>
        </div>
      </div>

      <!-- 被控主机 -->
      <div v-for="sid in serverIds" :key="sid" class="panel server-panel">
        <div class="panel-header">
          <span class="dot" :class="{ online: serversStats[sid]?.online, offline: !serversStats[sid]?.online }"></span>
          <span>{{ serverList[sid]?.name || sid }}</span>
          <span class="badge">{{ serverList[sid]?.host?.split('.').pop() }}</span>
          <button @click="removeServer(sid)" class="btn-remove" title="移除">✕</button>
        </div>
        <div class="gauges-row small">
          <GaugeCircle label="CPU" :value="serversStats[sid]?.cpu || 0" color="#00d4ff" size="small" />
          <GaugeCircle label="内存" :value="serversStats[sid]?.memory || 0" color="#f6dd0e" size="small" />
          <GaugeCircle label="磁盘" :value="serversStats[sid]?.disk || 0" color="#e65d5d" size="small" />
        </div>
        <div class="info-row">
          <div class="info-item">
            <span class="info-label">负载</span>
            <span class="info-value">{{ serversStats[sid]?.load || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">运行时间</span>
            <span class="info-value small-text">{{ serversStats[sid]?.uptime || 'N/A' }}</span>
          </div>
        </div>
        <!-- 命令区 -->
        <div class="cmd-section">
          <div class="cmd-input-row">
            <input :value="cmds[sid] || ''" @input="updateCmd(sid, $event.target.value)"
              @focus="onFocus(sid)" @keyup.enter="runCmd(sid)"
              @keydown.down.prevent="moveDown(sid)" @keydown.up.prevent="moveUp(sid)"
              placeholder="输入命令..." class="cmd-input" />
            <button @click="runCmd(sid)" class="btn-exec">▶</button>
          </div>
          <div v-show="showSuggest[sid]" class="suggest-box">
            <div class="suggest-title">可用命令 (↑↓选择 回车执行)：</div>
            <div v-for="(item, idx) in getFiltered(sid)" :key="item.cmd"
              :class="['suggest-item', { active: suggestIdx[sid] === idx }]"
              @mousedown.prevent="selectCmd(sid, item.cmd)"
              @mouseenter="suggestIdx[sid] = idx">
              <code>{{ item.cmd }}</code>
              <span>{{ item.desc }}</span>
            </div>
          </div>
          <div v-if="results[sid]" class="result-box">
            <div class="result-header">
              <span>执行结果</span>
              <button @click="results[sid] = ''" class="btn-close-sm">✕</button>
            </div>
            <pre>{{ results[sid] }}</pre>
          </div>
          <div v-if="loading[sid]" class="loading-text">⚡ 执行中...</div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="serverIds.length === 0" class="panel empty-panel">
        <div class="empty-content">
          <div class="empty-icon">🖥️</div>
          <p>还没有被控主机</p>
          <p class="empty-sub">点击右上角"添加主机"开始监控</p>
          <button @click="showAddServer = true" class="btn-empty">➕ 添加第一台主机</button>
        </div>
      </div>
    </div>

    <!-- 添加主机弹窗 -->
    <div v-if="showAddServer" class="modal-overlay" @click.self="showAddServer = false">
      <div class="modal">
        <div class="modal-header">
          <h2>➕ 添加被控主机</h2>
          <button @click="showAddServer = false" class="btn-close">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>IP 地址 *</label>
            <input v-model="newServer.ip" placeholder="192.168.1.100" class="form-input" />
          </div>
          <div class="form-group">
            <label>SSH 用户名</label>
            <input v-model="newServer.username" placeholder="root" class="form-input" />
          </div>
          <div class="form-group">
            <label>SSH 密码 *</label>
            <input v-model="newServer.password" type="password" placeholder="输入密码" class="form-input" />
          </div>
          <div class="form-group">
            <label>SSH 端口</label>
            <input v-model.number="newServer.port" type="number" placeholder="22" class="form-input" />
          </div>
          <div class="form-group">
            <label>显示名称</label>
            <input v-model="newServer.name" placeholder="可选" class="form-input" />
          </div>
          <div v-if="addError" class="msg error">{{ addError }}</div>
          <div v-if="addSuccess" class="msg success">{{ addSuccess }}</div>
          <button @click="addServer" class="btn-submit" :disabled="adding">
            {{ adding ? '添加中...' : '✅ 确认添加' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 命令库弹窗 -->
    <div v-if="showAllCommands" class="modal-overlay" @click.self="showAllCommands = false">
      <div class="modal wide">
        <div class="modal-header">
          <h2>📋 命令库 ({{ totalCommands }}条)</h2>
          <button @click="showAllCommands = false" class="btn-close">✕</button>
        </div>
        <div class="modal-body cmd-lib">
          <div v-for="(cmds, cat) in commandList" :key="cat" class="cmd-category">
            <h3>{{ cat }}</h3>
            <div v-for="(desc, cmd) in cmds" :key="cmd" class="cmd-lib-item">
              <code>{{ cmd }}</code>
              <span>{{ desc }}</span>
              <div class="cmd-lib-actions">
                <button v-for="sid in serverIds" :key="sid"
                  @click="quickRun(sid, cmd)" class="btn-mini"
                  :style="{ background: getColor(sid) }">
                  {{ getLabel(sid) }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import GaugeCircle from './GaugeCircle.vue'

const local = reactive({ cpu: 0, memory: 0, disk: 0, load: 0, net_sent: 0, net_recv: 0 })
const serversStats = reactive({})
const wsConnected = ref(false)
const currentTime = ref('')
const showAddServer = ref(false)
const showAllCommands = ref(false)

const cmds = reactive({})
const results = ref({})
const loading = ref({})
const showSuggest = reactive({})
const suggestIdx = reactive({})

const allCommands = ref([])
const commandList = ref({})
const serverList = ref({})

const newServer = reactive({ ip: '', username: 'root', password: '', port: 22, name: '' })
const adding = ref(false)
const addError = ref('')
const addSuccess = ref('')

const colors = ['#4fd2f1', '#f6dd0e', '#e65d5d', '#7b68ee', '#5cb85c', '#f0ad4e']
const colorMap = {}
let colorIdx = 0

let ws = null

const serverIds = computed(() => Object.keys(serverList.value))
const totalCommands = computed(() => {
  let count = 0
  Object.values(commandList.value).forEach(cmds => { count += Object.keys(cmds).length })
  return count
})

const getColor = (sid) => {
  if (!colorMap[sid]) { colorMap[sid] = colors[colorIdx++ % colors.length] }
  return colorMap[sid]
}
const getLabel = (sid) => serverList.value[sid]?.host?.split('.').pop() || sid

const updateTime = () => {
  currentTime.value = new Date().toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const formatNet = (bytes) => ((bytes || 0) / 1024 / 1024).toFixed(1)

const initWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${protocol}://${window.location.hostname}:8000/ws`)
  ws.onopen = () => { wsConnected.value = true }
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      Object.assign(local, data.local || {})
      if (data.servers) {
        Object.keys(data.servers).forEach(k => {
          serversStats[k] = data.servers[k]
          if (showSuggest[k] === undefined) showSuggest[k] = false
          if (suggestIdx[k] === undefined) suggestIdx[k] = -1
        })
      }
    } catch (err) {}
  }
  ws.onclose = () => { wsConnected.value = false; setTimeout(initWebSocket, 3000) }
}

const fetchCommands = async () => {
  try {
    const res = await axios.get('/api/commands')
    commandList.value = res.data
    const flat = []
    Object.entries(res.data).forEach(([cat, cmds]) => {
      Object.entries(cmds).forEach(([cmd, desc]) => flat.push({ cmd, desc, cat }))
    })
    allCommands.value = flat
  } catch (e) {}
}

const fetchServers = async () => {
  try {
    const res = await axios.get('/api/servers')
    serverList.value = res.data
  } catch (e) {}
}

const addServer = async () => {
  if (!newServer.ip || !newServer.password) { addError.value = '请填写IP和密码'; return }
  adding.value = true; addError.value = ''; addSuccess.value = ''
  try {
    const res = await axios.post('/api/servers/add', {
      ip: newServer.ip, password: newServer.password,
      username: newServer.username || 'root', port: newServer.port || 22,
      name: newServer.name || undefined
    })
    if (res.data.success) {
      addSuccess.value = res.data.message
      newServer.ip = ''; newServer.password = ''; newServer.name = ''
      await fetchServers()
      setTimeout(() => { showAddServer.value = false; addSuccess.value = '' }, 800)
    } else { addError.value = res.data.error || '添加失败' }
  } catch (e) { addError.value = '请求失败: ' + e.message }
  adding.value = false
}

const removeServer = async (sid) => {
  if (!confirm(`确定移除 ${sid}？`)) return
  try {
    await axios.post('/api/servers/remove', { server_id: sid })
    delete cmds[sid]; delete results.value[sid]; delete colorMap[sid]
    await fetchServers()
  } catch (e) { alert('移除失败: ' + e.message) }
}

const sendCommand = async (sid, cmd) => {
  if (!cmd?.trim()) return
  loading.value[sid] = true
  try {
    const res = await axios.post('/api/control', { server_id: sid, command: cmd.trim() })
    if (res.data.error) results.value[sid] = '❌ ' + res.data.error
    else {
      const out = res.data.stdout || ''; const err = res.data.stderr || ''
      results.value[sid] = out + (err ? '\n---\n' + err : '')
      if (!out && !err) results.value[sid] = '(无输出)'
    }
  } catch (e) { results.value[sid] = '❌ ' + e.message }
  loading.value[sid] = false
  cmds[sid] = ''
}

const updateCmd = (sid, val) => { cmds[sid] = val }
const onFocus = (sid) => { showSuggest[sid] = true; suggestIdx[sid] = -1 }
const getFiltered = (sid) => {
  const q = (cmds[sid] || '').toLowerCase().trim()
  return q ? allCommands.value.filter(c => c.cmd.toLowerCase().includes(q) || c.desc.includes(q)) : allCommands.value
}
const moveDown = (sid) => {
  const list = getFiltered(sid)
  if (suggestIdx[sid] < list.length - 1) suggestIdx[sid]++
}
const moveUp = (sid) => { if (suggestIdx[sid] > 0) suggestIdx[sid]-- }
const selectCmd = (sid, cmd) => { cmds[sid] = cmd; showSuggest[sid] = false; sendCommand(sid, cmd) }
const runCmd = (sid) => { showSuggest[sid] = false; if (cmds[sid]?.trim()) sendCommand(sid, cmds[sid]) }
const quickRun = (sid, cmd) => { showAllCommands.value = false; sendCommand(sid, cmd) }

// 图表
const chartRef = ref(null)
let chart = null
let chartData = new Array(40).fill(0)
const initChart = () => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 40, right: 10, top: 10, bottom: 20 },
    xAxis: { type: 'category', data: chartData.map((_, i) => i + 1), axisLine: { lineStyle: { color: '#1a3a6a' } }, axisLabel: { fontSize: 9, color: '#6b9bd6' } },
    yAxis: { type: 'value', min: 0, max: 100, axisLine: { lineStyle: { color: '#1a3a6a' } }, splitLine: { lineStyle: { color: '#0d1f3a' } }, axisLabel: { fontSize: 9, color: '#6b9bd6' } },
    series: [{
      data: chartData, type: 'line', smooth: true, showSymbol: false,
      lineStyle: { color: '#00d4ff', width: 2 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(0,212,255,0.3)' }, { offset: 1, color: 'rgba(0,212,255,0.02)' }
      ])}
    }]
  })
}
const updateChart = (val) => {
  if (!chart) return
  chartData.push(val || 0)
  if (chartData.length > 40) chartData.shift()
  chart.setOption({ xAxis: { data: chartData.map((_, i) => i + 1) }, series: [{ data: chartData }] })
}

let t1, t2
onMounted(() => {
  updateTime(); t1 = setInterval(updateTime, 1000)
  initWebSocket(); fetchCommands(); fetchServers()
  nextTick(() => { initChart(); t2 = setInterval(() => updateChart(local.cpu), 2000) })
})
onBeforeUnmount(() => {
  ws?.close(); clearInterval(t1); clearInterval(t2); chart?.dispose()
})
</script>

<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; }
</style>

<style scoped>
.dashboard { width: 100vw; height: 100vh; background: linear-gradient(135deg, #060d1a 0%, #0a1a3a 50%, #0d1f4a 100%); color: #e0e8f0; display: flex; flex-direction: column; padding: 8px 12px; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 2px solid #1a3a6a; margin-bottom: 8px; flex-shrink: 0; }
.logo { font-size: 24px; margin-right: 10px; }
.time { color: #6b9bd6; font-size: 13px; }
.title { font-size: 22px; background: linear-gradient(90deg, #00d4ff, #7b68ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.header-right { display: flex; align-items: center; gap: 12px; }
.btn-header { background: rgba(79,210,241,0.1); border: 1px solid #4fd2f1; color: #4fd2f1; padding: 5px 12px; border-radius: 5px; cursor: pointer; font-size: 12px; }
.btn-header:hover { background: rgba(79,210,241,0.25); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #e65d5d; }
.status-dot.online { background: #4fd2f1; box-shadow: 0 0 6px #4fd2f1; }
.status-text { font-size: 12px; color: #6b9bd6; }
.version { font-size: 10px; color: #3a5a8a; background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 10px; }

.main-content { display: flex; gap: 10px; flex: 1; min-height: 0; overflow-x: auto; }
.panel { background: rgba(10,25,55,0.8); border: 1px solid #1a3a6a; border-radius: 10px; padding: 12px; min-width: 280px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
.local-panel { max-width: 340px; }
.panel-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 14px; color: #4fd2f1; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #e65d5d; }
.dot.online { background: #4fd2f1; box-shadow: 0 0 6px #4fd2f1; }
.dot.offline { background: #e65d5d; }
.badge { font-size: 10px; background: rgba(79,210,241,0.15); color: #4fd2f1; padding: 1px 8px; border-radius: 10px; margin-left: auto; }
.btn-remove { background: rgba(230,93,93,0.2); border: 1px solid #e65d5d; color: #e65d5d; width: 22px; height: 22px; border-radius: 50%; cursor: pointer; font-size: 11px; margin-left: 4px; }

.gauges-row { display: flex; justify-content: space-around; margin-bottom: 10px; }
.gauges-row.small { gap: 6px; }
.info-row { display: flex; justify-content: space-around; margin-bottom: 10px; }
.info-item { text-align: center; }
.info-label { font-size: 10px; color: #6b9bd6; display: block; }
.info-value { font-size: 16px; font-weight: bold; }
.small-text { font-size: 11px !important; }

.chart-container { flex: 1; min-height: 150px; }
.chart { width: 100%; height: 100%; }

.cmd-section { margin-top: auto; padding-top: 8px; border-top: 1px solid #1a3a6a; }
.cmd-input-row { display: flex; gap: 4px; }
.cmd-input { flex: 1; background: rgba(0,0,0,0.4); border: 1px solid #2a5a8a; color: #e0e8f0; padding: 6px 10px; border-radius: 5px; font-size: 12px; outline: none; }
.cmd-input:focus { border-color: #4fd2f1; }
.cmd-input::placeholder { color: #3a5a8a; font-size: 10px; }
.btn-exec { background: #4fd2f1; border: none; color: #0a1a2f; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-weight: bold; }

.suggest-box { background: #0d1f4a; border: 1px solid #2a5a8a; border-radius: 5px; max-height: 200px; overflow-y: auto; margin-top: 3px; }
.suggest-title { font-size: 10px; color: #4fd2f1; padding: 4px 8px; border-bottom: 1px solid #1a2a4a; }
.suggest-item { display: flex; align-items: center; gap: 6px; padding: 5px 8px; cursor: pointer; border-bottom: 1px solid #1a2a4a; font-size: 11px; }
.suggest-item.active { background: rgba(79,210,241,0.15); }
.suggest-item:hover { background: rgba(79,210,241,0.1); }
.suggest-item code { color: #adff2f; font-size: 10px; background: rgba(0,0,0,0.3); padding: 2px 5px; border-radius: 3px; }
.suggest-item span { color: #6b9bd6; font-size: 10px; }

.result-box { margin-top: 6px; background: #0a0f1a; border: 1px solid #1a3a6a; border-radius: 4px; max-height: 180px; overflow: auto; }
.result-header { display: flex; justify-content: space-between; padding: 4px 8px; background: #111a2a; font-size: 10px; color: #6b9bd6; }
.btn-close-sm { background: none; border: none; color: #e65d5d; cursor: pointer; }
.result-box pre { padding: 6px 8px; font-size: 10px; color: #adff2f; white-space: pre-wrap; word-break: break-all; margin: 0; }
.loading-text { text-align: center; color: #f6dd0e; font-size: 11px; padding: 6px; }

.empty-panel { display: flex; align-items: center; justify-content: center; }
.empty-content { text-align: center; color: #6b9bd6; }
.empty-icon { font-size: 50px; margin-bottom: 12px; }
.empty-content p { margin: 6px 0; font-size: 14px; }
.empty-sub { font-size: 12px !important; color: #3a5a8a; }
.btn-empty { margin-top: 15px; background: rgba(79,210,241,0.2); border: 1px solid #4fd2f1; color: #4fd2f1; padding: 8px 20px; border-radius: 6px; cursor: pointer; }

.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal { background: #0d1f4a; border: 2px solid #2a5a8a; border-radius: 12px; width: 450px; max-height: 75vh; display: flex; flex-direction: column; }
.modal.wide { width: 700px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #1a3a6a; }
.modal-header h2 { font-size: 16px; color: #4fd2f1; margin: 0; }
.btn-close { background: none; border: none; color: #e65d5d; font-size: 18px; cursor: pointer; }
.modal-body { padding: 14px 16px; overflow-y: auto; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 12px; color: #6b9bd6; margin-bottom: 4px; }
.form-input { width: 100%; background: rgba(0,0,0,0.3); border: 1px solid #2a5a8a; color: #e0e8f0; padding: 8px 10px; border-radius: 5px; font-size: 13px; outline: none; }
.form-input:focus { border-color: #4fd2f1; }
.btn-submit { width: 100%; background: #4fd2f1; border: none; color: #0a1a2f; padding: 10px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: bold; margin-top: 6px; }
.btn-submit:disabled { opacity: 0.5; }
.msg { font-size: 12px; margin-bottom: 8px; }
.msg.error { color: #e65d5d; }
.msg.success { color: #4fd2f1; }

.cmd-lib { max-height: 60vh; }
.cmd-category { margin-bottom: 14px; }
.cmd-category h3 { font-size: 13px; color: #f6dd0e; margin-bottom: 6px; }
.cmd-lib-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; border-bottom: 1px solid #1a2a4a; font-size: 11px; }
.cmd-lib-item code { color: #adff2f; font-size: 10px; background: rgba(0,0,0,0.3); padding: 2px 5px; border-radius: 3px; }
.cmd-lib-item span { flex: 1; color: #6b9bd6; font-size: 10px; }
.cmd-lib-actions { display: flex; gap: 3px; }
.btn-mini { border: none; color: #fff; padding: 2px 8px; border-radius: 3px; cursor: pointer; font-size: 10px; font-weight: bold; }

.panel::-webkit-scrollbar, .suggest-box::-webkit-scrollbar, .result-box::-webkit-scrollbar, .modal-body::-webkit-scrollbar { width: 3px; }
.panel::-webkit-scrollbar-thumb, .suggest-box::-webkit-scrollbar-thumb, .result-box::-webkit-scrollbar-thumb, .modal-body::-webkit-scrollbar-thumb { background: #2a4a7a; border-radius: 2px; }
.main-content::-webkit-scrollbar { height: 4px; }
.main-content::-webkit-scrollbar-thumb { background: #2a4a7a; border-radius: 2px; }
</style>
