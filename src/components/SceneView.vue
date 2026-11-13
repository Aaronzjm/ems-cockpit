<template>
  <div class="cockpit">
    <canvas ref="canvasRef" class="scene-canvas"></canvas>

    <!-- 顶部标题栏 -->
    <header class="hud-top">
      <div class="hud-top__brand">
        <span class="dot"></span>
        <h1 v-if="viewMode === 'overview'">光储充一体化 EMS 驾驶舱</h1>
        <h1 v-else>{{ viewedName }}</h1>
      </div>
      <div class="hud-top__hint">
        <span v-if="viewMode === 'device'">点击设备查看分解结构 · 右上角返回总览</span>
        <span v-else-if="hoveredName">当前选中：<b>{{ hoveredName }}</b></span>
        <span v-else>左键拖拽旋转 · 滚轮缩放 · 点击设备查看</span>
      </div>
      <!-- 单设备模式右上角返回按钮 -->
      <button v-if="viewMode === 'device'" class="btn-back" @click="exitDeviceView">
        ← 返回总览
      </button>
    </header>

    <!-- 单设备模式：左侧展开/复原控制栏 -->
    <aside v-if="viewMode === 'device'" class="hud-panel hud-left">
      <h2>{{ viewedName }}</h2>
      <p class="dev-sub">点击下方按钮查看设备分解结构</p>
      <div class="panel-actions">
        <button @click="toggleViewedDevice">
          {{ viewedExploded ? '复原设备' : '展开设备' }}
        </button>
      </div>
    </aside>

    <!-- 左侧：设备清单 -->
    <aside v-if="viewMode === 'overview'" class="hud-panel hud-left">
      <h2>设备清单</h2>
      <ul>
        <li
          v-for="d in deviceList"
          :key="d.key"
          :class="{ active: selectedKey === d.key }"
          @click="onDeviceClick(d.key)"
        >
          <i class="swatch" :style="{ background: d.color }"></i>
          <span class="name">{{ d.name }}</span>
          <em v-if="d.key !== 'controlroom'" class="state" :class="{ on: explodedMap[d.key] }">
            {{ explodedMap[d.key] ? '分解中' : '正常' }}
          </em>
          <em v-else class="state enter">查看</em>
        </li>
      </ul>
      <div class="panel-actions">
        <button v-if="selectedKey && selectedKey !== 'controlroom'" @click="toggleSelected">
          {{ explodedMap[selectedKey] ? '复原该设备' : '分解该设备' }}
        </button>
        <button class="ghost" @click="restoreAll">全部复原</button>
      </div>
    </aside>

    <!-- 右侧：实时数据看板 -->
    <aside class="hud-panel hud-right">
      <h2>运行总览</h2>
      <div class="metrics">
        <div class="metric">
          <label>光伏实时功率</label>
          <strong>{{ metrics.pvPower }}<small>kW</small></strong>
          <div class="bar"><i :style="{ width: pvRatio + '%' }"></i></div>
        </div>
        <div class="metric">
          <label>储能荷电状态 SOC</label>
          <strong>{{ metrics.soc }}<small>%</small></strong>
          <div class="bar"><i :style="{ width: metrics.soc + '%' }"></i></div>
        </div>
        <div class="metric">
          <label>充电桩输出</label>
          <strong>{{ metrics.charging }}<small>kW</small></strong>
          <div class="bar"><i :style="{ width: chargeRatio + '%' }"></i></div>
        </div>
        <div class="metric">
          <label>变压器负载率</label>
          <strong>{{ metrics.load }}<small>%</small></strong>
          <div class="bar warn"><i :style="{ width: metrics.load + '%' }"></i></div>
        </div>
      </div>
      <div class="alerts">
        <h3>告警记录</h3>
        <p v-for="a in alerts" :key="a.t" :class="a.level">
          <time>{{ a.t }}</time>{{ a.text }}
        </p>
      </div>
    </aside>

    <!-- 底部状态条 -->
    <footer class="hud-bottom">
      <span>引擎：Three.js {{ threeVersion }}</span>
      <span>模式：{{ mode === 'orbit' ? '环绕漫游' : '自由漫游' }}（按 F 切换）</span>
      <span>设备：{{ deviceList.length }} 台</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import gsap from 'gsap'
import { ExplodeController, ModelLoader } from '../three/ExplodeController.js'

const canvasRef = ref(null)
const threeVersion = THREE.REVISION
const mode = ref('orbit')
const selectedKey = ref(null)
const hoveredName = ref('')
const explodedMap = reactive({})
const viewMode = ref('overview') // 'overview' | 'device'
const viewedKey = ref(null)
const viewedName = ref('')
const viewedExploded = ref(false)
let overviewCameraPos = null
let overviewTargetPos = null
let groundRoot = null
// 镜头飞行中：禁用交互，避免拖拽与补间互抢导致画面抳动
let flying = false
// 场景陈设（车辆 / 充电线 / 信息亭）：进出单设备模式时统一显隐
const furnitureRoots = []

const metrics = reactive({ pvPower: 286.4, soc: 76, charging: 118.5, load: 63 })
const alerts = ref([
  { t: '10:38', text: '储能舱 #2 电池簇温度偏高', level: 'warn' },
  { t: '10:31', text: '3 号充电桩完成一次订单结算', level: 'info' },
  { t: '10:22', text: '光伏阵列输出恢复正常', level: 'ok' },
])

const deviceList = [
  { key: 'canopy', name: '光伏区', color: '#3b7dff' },
  { key: 'charging', name: '智能快充桩', color: '#22e0d6' },
  { key: 'storage', name: '储能电池舱', color: '#00f26a' },
  { key: 'transformer', name: '配电变压器', color: '#ffc22e' },
  { key: 'controlroom', name: '配电室', color: '#59d7ff' },
]

const pvRatio = computed(() => Math.min(100, (metrics.pvPower / 400) * 100))
const chargeRatio = computed(() => Math.min(100, (metrics.charging / 240) * 100))

// ---- three.js 状态 ----
let renderer, labelRenderer, composer, scene, camera, controls, freeControls
let clock, explode, loader, raycaster, pointer
let animId = 0
const deviceRoots = {}
const keys = { w: false, a: false, s: false, d: false }
let velocity = new THREE.Vector3()
let ambientLight, keyLight, fillLight, rimLight, hemiLight

const NAMES = {
  canopy: '光伏区',
  storage: '储能电池舱',
  charging: '智能快充桩',
  transformer: '配电变压器',
  controlroom: '配电室',
  vehicle: '新能源汽车',
  kiosk: '园区信息亭',
  ground: '园区底座',
}

function init() {
  const canvas = canvasRef.value
  const w = window.innerWidth
  const h = window.innerHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x04060a)
  scene.fog = new THREE.Fog(0x04060a, 60, 135)

  camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 600)
  camera.position.set(22, 18, 25)

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 0.9

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(w, h)
  labelRenderer.domElement.className = 'label-layer'
  canvas.parentElement.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.06
  controls.maxPolarAngle = Math.PI / 2.15
  controls.minDistance = 8
  controls.maxDistance = 110
  controls.target.set(0, 2.0, 0)

  freeControls = new PointerLockControls(camera, renderer.domElement)

  // 光照：补到足够清楚，暗部不闷黑，整体仍保持科技暗调
  ambientLight = new THREE.AmbientLight(0xaaccee, 1.5)
  scene.add(ambientLight)
  keyLight = new THREE.DirectionalLight(0xeef4ff, 1.8)
  keyLight.position.set(18, 30, 16)
  scene.add(keyLight)
  fillLight = new THREE.DirectionalLight(0x6fa8ff, 1.15)
  fillLight.position.set(-20, 14, -14)
  scene.add(fillLight)
  rimLight = new THREE.DirectionalLight(0x30ff9a, 0.5)
  rimLight.position.set(0, 8, 22)
  scene.add(rimLight)
  hemiLight = new THREE.HemisphereLight(0x3a5b85, 0x0e1220, 0.95)
  scene.add(hemiLight)

  renderer.toneMappingExposure = 1.0

  // 后期：霓虹辉光。必须走 OutputPass 做色调映射 + sRGB 输出，
  // 否则线性 HDR 值直接上屏，金属表面会整片炸成纯白。
  composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))
  const bloom = new UnrealBloomPass(
    new THREE.Vector2(w, h),
    0.3,   // strength：克制，避免描边烧成白块
    0.45,  // radius
    1.05,  // threshold：只有真正高亮的描边越过阈值
  )
  composer.addPass(bloom)
  composer.addPass(new OutputPass())

  explode = new ExplodeController()
  loader = new ModelLoader()
  raycaster = new THREE.Raycaster()
  pointer = new THREE.Vector2()
  clock = new THREE.Clock()

  bindEvents()
  loadScene()
  animate()
}

async function loadScene() {
  const base = import.meta.env.BASE_URL

  // 先加载所有模型测量尺寸
  const models = {}
  const modelFiles = {
    ground: 'ground_facility.glb',
    canopy: 'photovoltaic_canopy.glb',
    charging: 'charging_pile.glb',
    storage: 'storage_container.glb',
    transformer: 'transformer_substation.glb',
    controlroom: 'control_room.glb',
    vehicle: 'vehicle.glb',
    kiosk: 'kiosk.glb',
  }
  for (const [key, file] of Object.entries(modelFiles)) {
    const gltf = await loader.load(`${base}models/${file}`)
    models[key] = gltf.scene
    // 打印模型尺寸方便布局
    const box = new THREE.Box3().setFromObject(gltf.scene)
    const size = box.getSize(new THREE.Vector3())
    console.log(`[Model] ${key}: size=(${size.x.toFixed(2)}, ${size.y.toFixed(2)}, ${size.z.toFixed(2)}), min=(${box.min.x.toFixed(2)}, ${box.min.y.toFixed(2)}, ${box.min.z.toFixed(2)}), max=(${box.max.x.toFixed(2)}, ${box.max.y.toFixed(2)}, ${box.max.z.toFixed(2)})`)
  }

  // 园区底座
  const ground = models.ground
  groundRoot = ground
  scene.add(ground)
  // 测量底座真实可用范围
  const groundBox = new THREE.Box3().setFromObject(ground)
  const groundSize = groundBox.getSize(new THREE.Vector3())
  console.log(`[Ground] 底座范围: X[${groundBox.min.x.toFixed(2)}, ${groundBox.max.x.toFixed(2)}] Z[${groundBox.min.z.toFixed(2)}, ${groundBox.max.z.toFixed(2)}] 尺寸: ${groundSize.x.toFixed(2)}x${groundSize.z.toFixed(2)}m`)

  /** 挂一个设备：加载 GLB → 摆位 → 注册爆炸 → 贴 CSS2D 标签 */
  const attach = (key, root, pos, gap, labelY, rotY = 0, partPredicate = null, offsetResolver = null, labelPos = null) => {
    root.position.set(...pos)
    root.rotation.y = rotY
    scene.add(root)

    const box = new THREE.Box3().setFromObject(root)
    root.userData.pickBox = box
    root.userData.height = labelY
    explode.register(key, root, gap, offsetResolver, partPredicate)
    // 自动检查是否超出底座
    const outOfBounds = box.min.x < groundBox.min.x - 0.2 || box.max.x > groundBox.max.x + 0.2 ||
                        box.min.z < groundBox.min.z - 0.2 || box.max.z > groundBox.max.z + 0.2
    if (outOfBounds) console.error(`❌ [Bounds Error] ${key} 超出底座范围!`, {x:[box.min.x.toFixed(2), box.max.x.toFixed(2)], z:[box.min.z.toFixed(2), box.max.z.toFixed(2)]})
    else console.log(`✅ [Bounds OK] ${key} 在底座内`)

    const el = document.createElement('div')
    el.className = 'dev-label'
    el.textContent = NAMES[key]
    const label = new CSS2DObject(el)
    label.position.set(...(labelPos || [0, labelY, 0]))
    root.add(label)

    root.userData.key = key
    deviceRoots[key] = root
    return root
  }

  const load = (f) => loader.load(`${base}models/${f}`)

  // —— 可交互设备（每个设备单独定制拆解规则，纯平移无旋转）——
  
  // ========== 光伏雨棚 v7（12.0×5.6m，罩 3 个间距 3.9m 的宽车位） ==========
  // 世界 (-6.2, 0, +3.5)：棚覆盖 x∈[-12.2,-0.2]、z∈[0.7,6.3]；
  // 立柱在车位分界/外侧（世界 x=-11.9/-8.15/-4.25/-0.5），两排 z=1.1/5.9；
  // 桩和车全部在棚顶下。爆炸规则不变（part 命名与 v4 一致）。
  attach('canopy', models.canopy, [-6.2, 0, 3.5], 1.0, 3.9, 0, null,
    (name) => {
      // 太阳能板组整体上抬
      if (/part_panel_/.test(name)) return { offset: new THREE.Vector3(0, 2.2, 0), order: 2 }
      // 板边随板一起
      if (/part_panel_edge_/.test(name)) return { offset: new THREE.Vector3(0, 2.2, 0), order: 2 }
      // 主梁上抬
      if (name === 'part_beam') return { offset: new THREE.Vector3(0, 1.4, 0), order: 1 }
      if (/part_beam_glow_/.test(name)) return { offset: new THREE.Vector3(0, 1.4, 0), order: 1 }
      // 线槽上抬
      if (name === 'part_trunk') return { offset: new THREE.Vector3(0, 1.0, 0), order: 1 }
      // 立柱不动；描边不动
      return null
    },
  )

  // ========== 快充桩（3台，每个画线车位尽头1台，棚下） ==========
  const SLOT_X = [-10.1, -6.2, -2.3] // 与底座 ground v6 的 part_slot_* 画线车位完全对齐（间距3.9m、宽3.0m）
  const pileGroup = new THREE.Group()
  pileGroup.userData.key = 'charging'
  for (const x of SLOT_X) {
    const c = models.charging.clone(true)
    c.position.set(x, 0, 5.95) // 车位尽头（画线在 z=6.4），线缆侧朝 -Z 对着车头
    c.userData.explodeUnit = true
    pileGroup.add(c)
  }
  attach('charging', pileGroup, [0, 0, 0], 1.0, 2.7, 0,
    // 只让最左那台桩参与展开
    (obj) => obj.userData.explodeUnit ? obj.position.x <= -9.0 : false,
    // 斜向左前滑出（避开棚立柱、左描边与底座边缘）
    () => ({ offset: new THREE.Vector3(-1.6, 0, -1.6), order: 0 }),
    // 标签挂在桩群中心（Group 原点在世界原点，默认会把标签甩到园区正中）
    [-6.2, 2.7, 5.95],
  )

  // ========== 储能电池舱（只拆最左一台柜体） ==========
  attach('storage', models.storage, [1.2, 0, -5.2], 1.0, 3.4, 0, // 左移：与配电室 z 向隙 0.58m、与变压器 x 向隙 2.29m
    // 只展开最左柜体 _0 的零件
    (obj) => {
      if (!obj.isMesh) return obj.userData.explodeUnit
      const n = obj.name
      if (n === 'part_base' || /part_base_outline/.test(n)) return false
      if (/part_switch/.test(n)) return false
      if (/part_cab_frame_0/.test(n)) return true
      if (/part_cab_glow_0/.test(n)) return true
      if (/part_cab_roof_0/.test(n)) return true
      if (/part_cab_seam_0/.test(n)) return true
      if (/part_cab_split_0/.test(n)) return true
      if (/part_cab_topline_0/.test(n)) return true
      return false
    },
    (name) => {
      // 柜门向前抽出
      if (/part_cab_glow_0/.test(name)) return { offset: new THREE.Vector3(0, 0, 1.8), order: 0 }
      // 竖缝随柜门
      if (/part_cab_seam_0/.test(name)) return { offset: new THREE.Vector3(0, 0, 1.8), order: 0 }
      if (/part_cab_topline_0/.test(name)) return { offset: new THREE.Vector3(0, 0, 1.8), order: 0 }
      // 柜门框架微抬
      if (/part_cab_frame_0/.test(name)) return { offset: new THREE.Vector3(0, 0.3, 0), order: 1 }
      // 顶盖抬高
      if (/part_cab_roof_0/.test(name)) return { offset: new THREE.Vector3(0, 1.6, 0), order: 2 }
      // 内部分隔线分层抬起（按 k 值：下层低、上层高）
      const m = name.match(/part_cab_split_0_(\d+)/)
      if (m) {
        const k = parseInt(m[1])
        return { offset: new THREE.Vector3(0, 0.5 + k * 0.5, 0.4), order: 1 + k * 0.1 }
      }
      return null
    },
  )

  // ========== 配电变压器（效果好的那个，保留并精调） ==========
  attach('transformer', models.transformer, [9.0, 0, -6.6], 1.0, 2.9, 0, null, // 右移：给左散热器爆炸滑移留落点
    (name) => {
      // 底座/描边/标牌不动
      if (name === 'part_base' || /part_base_outline/.test(name) || name === 'part_sign') return null
      // 顶盖抬起最高
      if (name === 'part_lid') return { offset: new THREE.Vector3(0, 1.8, 0), order: 3 }
      // 铜套管（bushing）上抬
      if (/part_bushing_\d/.test(name) && !/ring/.test(name)) return { offset: new THREE.Vector3(0, 1.2, 0), order: 2 }
      // 套管环随套管
      if (/part_bushing_ring_\d/.test(name)) return { offset: new THREE.Vector3(0, 1.2, 0), order: 2 }
      // 散热器向左/右滑开
      if (name === 'part_radiator_0') return { offset: new THREE.Vector3(-1.6, 0.1, 0), order: 1 }
      if (name === 'part_radiator_1') return { offset: new THREE.Vector3(1.6, 0.1, 0), order: 1 }
      // 散热片（fin）随各自散热器
      const fm = name.match(/part_fin_(\d)_(\d)/)
      if (fm) {
        const side = parseInt(fm[1])
        return { offset: new THREE.Vector3(side === 0 ? -1.6 : 1.6, 0.1, 0), order: 1 }
      }
      // 主箱体微抬
      if (name === 'part_tank') return { offset: new THREE.Vector3(0, 0.2, 0), order: 0 }
      return null
    },
  )

  // ========== 配电室（单设备查看模式专用，四面墙向外分离，真实材质） ==========
  attach('controlroom', models.controlroom, [8.8, 0, 2.2], 1.6, 3.7, -Math.PI / 2, null, // 前移：解除与电池舱的重合
    (name) => {
      // 底座/描边/地板/地面压条 → 完全不动（锚点）
      if (/part_base_outline/.test(name) || name === 'part_inner_floor' || name === 'part_floor_glow' || name === 'part_slab') return null

      // ========== 四面墙体向外拉开（glTF导出后：后墙在-Z，大门幕墙在+Z） ==========
      // 左墙 → 向左（-X）
      if (name === 'part_wall_side_0') return { offset: new THREE.Vector3(-5.0, 0.2, 0), order: 0 }
      // 右墙 → 向右（+X）
      if (name === 'part_wall_side_1') return { offset: new THREE.Vector3(5.0, 0.2, 0), order: 0 }
      // 后墙（位于 -Z）→ 向 -Z 继续推出
      if (name === 'part_wall_back') return { offset: new THREE.Vector3(0, 0.2, -5.0), order: 0 }

      // ========== 前侧幕墙骨架（大门侧，位于 +Z）→ 向 +Z 朝外抽出 ==========
      if (/part_mullion_\d/.test(name)) return { offset: new THREE.Vector3(0, 0, 5.0), order: 0 }
      if (name === 'part_lintel') return { offset: new THREE.Vector3(0, 0.2, 5.0), order: 0 }

      // ========== 屋顶四边随各自墙体走（各自外侧） ==========
      if (name === 'part_rim_back') return { offset: new THREE.Vector3(0, 2.8, -5.0), order: 1 }
      if (name === 'part_rim_front') return { offset: new THREE.Vector3(0, 2.8, 5.0), order: 1 }
      if (name === 'part_rim_side_0') return { offset: new THREE.Vector3(-5.0, 2.8, 0), order: 1 }
      if (name === 'part_rim_side_1') return { offset: new THREE.Vector3(5.0, 2.8, 0), order: 1 }
      if (name === 'part_rim_glow') return { offset: new THREE.Vector3(0, 2.7, 5.0), order: 1 }

      // ========== 大屏（贴在后墙 -Z 侧）→ 上抬 + 向前（+Z）离开墙面 ==========
      if (name === 'part_bigscreen' || name === 'part_bigscreen_frame')
        return { offset: new THREE.Vector3(0, 2.2, -2.5), order: 2 }

      // ========== 侧屏+边框随左右墙向外 ==========
      if (name === 'part_sidescreen_0' || name === 'part_sidescreen_frame_0') return { offset: new THREE.Vector3(-3.8, 0.8, -0.8), order: 2 }
      if (name === 'part_sidescreen_1' || name === 'part_sidescreen_frame_1') return { offset: new THREE.Vector3(3.8, 0.8, -0.8), order: 2 }

      // ========== 内部操作台 / 显示器 / 座椅：按排分层抬升 ==========
      // 前排（靠近幕墙）：微向前 + 微抬
      if (name === 'part_desk_0') return { offset: new THREE.Vector3(0, 0.4, -1.0), order: 3 }
      if (name === 'part_desk_top_0') return { offset: new THREE.Vector3(0, 0.5, -1.0), order: 3 }
      // 后排（靠近大屏）：向前更多 + 抬更高，和前排错开不重叠
      if (name === 'part_desk_1') return { offset: new THREE.Vector3(0, 1.0, -2.2), order: 3 }
      if (name === 'part_desk_top_1') return { offset: new THREE.Vector3(0, 1.1, -2.2), order: 3 }

      // 前排显示器（第0排，4台）：抬到桌面前上方
      const mon0 = name.match(/part_mon_0_(\d)/)
      if (mon0) return { offset: new THREE.Vector3(0, 1.6, -1.0), order: 4 }
      const base0 = name.match(/part_mon_base_0_(\d)/)
      if (base0) return { offset: new THREE.Vector3(0, 1.0, -1.0), order: 4 }

      // 后排显示器（第1排，2台）：抬得更高，保证不被前排挡住
      const mon1 = name.match(/part_mon_1_(\d)/)
      if (mon1) return { offset: new THREE.Vector3(0, 2.4, -2.2), order: 4 }
      const base1 = name.match(/part_mon_base_1_(\d)/)
      if (base1) return { offset: new THREE.Vector3(0, 1.8, -2.2), order: 4 }

      // 座椅（在后排后面）：向后退 + 微抬
      if (/part_chair_\d/.test(name) && !/back|pole|ring/.test(name))
        return { offset: new THREE.Vector3(0, 0.3, 2.8), order: 4 }
      if (/part_chair_back_\d/.test(name))
        return { offset: new THREE.Vector3(0, 0.4, 2.8), order: 4 }
      if (/part_chair_pole_\d|part_chair_base_ring_\d/.test(name))
        return { offset: new THREE.Vector3(0, 0.2, 2.8), order: 4 }

      return null
    },
  )

  // —— 场景陈设（不参与拾取，纯视觉）——
  const cableMat = new THREE.MeshBasicMaterial({ color: 0x18f0a0 })
  // 车位线不再用 JS 画：底座 ground_facility.glb 自带 part_slot_* 画线车位

  // ========== 最左两个车位停车（共2辆），最右车位留空；车头朝桩，相邻车间隙1.9m ==========
  for (const x of SLOT_X.slice(0, 2)) {
    const car = models.vehicle.clone(true)
    car.position.set(x, 0, 3.2) // 车长4.3m → z∈[1.05,5.35]，棚覆盖 z∈[0.7,6.3]
    scene.add(car)
    furnitureRoots.push(car)
    // 充电线从桩连到车头（桩前缘 z≈5.67，车头 z≈5.35）
    const line = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.02, 0.9), cableMat)
    line.position.set(x, 0.035, 5.5)
    scene.add(line)
    furnitureRoots.push(line)
  }

  const kiosk = models.kiosk.clone(true)
  kiosk.position.set(0, 0, 7.75) // 前中：避开棚右缘与配电室爆炸时大门幕墙的落点
  scene.add(kiosk)
  furnitureRoots.push(kiosk)

  // 拾取时也要能命中 Group 根（charging 是 Group）
  Object.values(deviceRoots).forEach((r) => r.traverse((o) => { o.userData.key = r.userData.key }))

  // QA 深链：?focus=<key> 直接飞到某台设备，?explode=<key> 顺便炸开
  const params = new URLSearchParams(window.location.search)
  const focusKey = params.get('focus')
  if (focusKey && deviceRoots[focusKey]) {
    focusDevice(focusKey)
  }
  const explodeKey = params.get('explode')
  if (explodeKey && deviceRoots[explodeKey]) {
    explode.toggle(explodeKey)
    syncExplodeState()
  }
}

function bindEvents() {
  window.addEventListener('resize', onResize)
  renderer.domElement.addEventListener('pointerdown', onPointerDown)
  renderer.domElement.addEventListener('pointermove', onPointerMove)
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  freeControls.addEventListener('lock', () => (mode.value = 'free'))
  freeControls.addEventListener('unlock', () => (mode.value = 'orbit'))
}

function onPointerMove(e) {
  pointer.x = (e.clientX / window.innerWidth) * 2 - 1
  pointer.y = -(e.clientY / window.innerHeight) * 2 + 1
  if (mode.value !== 'orbit' || flying) return

  raycaster.setFromCamera(pointer, camera)
  const hit = pickDevice()
  if (hit) {
    hoveredName.value = NAMES[hit.object.userData.key] || ''
    renderer.domElement.style.cursor = 'pointer'
  } else {
    hoveredName.value = ''
    renderer.domElement.style.cursor = 'grab'
  }
}

function pickDevice() {
  raycaster.setFromCamera(pointer, camera)
  const hits = raycaster.intersectObjects(Object.values(deviceRoots), true)
  if (!hits.length) return null
  // 向上回溯到设备根
  let obj = hits[0].object
  while (obj && !obj.userData.key) obj = obj.parent
  return obj ? { object: obj } : null
}

function onPointerDown(e) {
  if (e.button !== 0 || mode.value !== 'orbit' || flying) return
  // 单设备模式下点击不再触发爆炸，改用左侧按钮控制
  if (viewMode.value === 'device') return
  const hit = pickDevice()
  if (!hit) {
    explode.restoreAll()
    syncExplodeState()
    return
  }
  const key = hit.object.userData.key
  // 配电室点选进入单设备查看模式
  if (key === 'controlroom') {
    enterDeviceView('controlroom')
    return
  }
  selectedKey.value = key
  explode.toggle(key)
  syncExplodeState()
}

// 点击左侧列表项
function onDeviceClick(key) {
  if (key === 'controlroom') {
    enterDeviceView(key)
    return
  }
  focusDevice(key)
}

// 镜头飞行：同步补间相机位置与注视点，飞行期间锁住控制器
// 时长拉长 + 柔和缓动（sine.inOut），避免大角度回旋造成晕眩
function flyTo(destPos, destTarget, duration = 1.6) {
  flying = true
  controls.enabled = false
  const tween = { t: 0 }
  const fromPos = camera.position.clone()
  const fromTarget = controls.target.clone()
  gsap.to(tween, {
    t: 1,
    duration,
    ease: 'sine.inOut',
    onUpdate: () => {
      const k = tween.t
      camera.position.lerpVectors(fromPos, destPos, k)
      controls.target.lerpVectors(fromTarget, destTarget, k)
      camera.lookAt(controls.target)
    },
    onComplete: () => {
      camera.position.copy(destPos)
      controls.target.copy(destTarget)
      controls.update()
      flying = false
      controls.enabled = true
    },
  })
}

// 进入单设备查看模式
function enterDeviceView(key) {
  const root = deviceRoots[key]
  if (!root) return
  viewedKey.value = key
  viewedName.value = NAMES[key]
  // 记录当前视角，返回时恢复
  overviewCameraPos = camera.position.clone()
  overviewTargetPos = controls.target.clone()
  // 复原所有已展开的设备
  explode.restoreAll()
  syncExplodeState()
  // 隐藏其他所有物体
  if (groundRoot) groundRoot.visible = false
  Object.entries(deviceRoots).forEach(([k, obj]) => {
    if (k !== key) obj.visible = false
  })
  // 隐藏车辆、充电地标线、信息亭等陈设
  furnitureRoots.forEach((o) => { o.visible = false })
  // 关闭雾效
  scene.fog = null
  // 飞到设备居中（配电室：镜头正对大门）
  selectedKey.value = key
  const box = new THREE.Box3().setFromObject(root)
  const c = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3()).length()
  const dist = size * 1.4 + 4
  viewMode.value = 'device'
  viewedExploded.value = false
  // 单设备模式：提亮灯光 + 提高曝光，看清内部细节
  ambientLight.intensity = 2.4
  keyLight.intensity = 2.4
  fillLight.intensity = 1.6
  hemiLight.intensity = 1.3
  renderer.toneMappingExposure = 1.2
  // 飞行期间锁住控制器：避免用户拖拽与补间互抢，画面抽动会晕
  flying = true
  controls.enabled = false
  const destTarget = new THREE.Vector3(c.x, c.y + 0.3, c.z)
  const destPos = key === 'controlroom'
    // 配电室 rotY=-π/2，大门在局部 +Z → 世界 -X 方向，镜头从 -X 正对大门看
    ? new THREE.Vector3(c.x - dist * 0.78, c.y + dist * 0.34, c.z)
    : new THREE.Vector3(c.x + dist * 0.62, c.y + dist * 0.42, c.z + dist * 0.62)
  flyTo(destPos, destTarget, 1.6)
}

// 单设备模式：展开/复原当前设备
function toggleViewedDevice() {
  const key = viewedKey.value
  if (!key) return
  const nowExploded = explode.toggle(key)
  viewedExploded.value = nowExploded
  selectedKey.value = key
  syncExplodeState()
}

// 退出单设备模式返回总览
function exitDeviceView() {
  const key = viewedKey.value
  if (key && explode.isExploded(key)) explode.toggle(key)
  viewedExploded.value = false
  syncExplodeState()
  // 恢复总览灯光亮度
  ambientLight.intensity = 1.5
  keyLight.intensity = 1.8
  fillLight.intensity = 1.15
  hemiLight.intensity = 0.95
  renderer.toneMappingExposure = 1.0
  // 恢复所有物体显示
  if (groundRoot) groundRoot.visible = true
  Object.values(deviceRoots).forEach((obj) => { obj.visible = true })
  furnitureRoots.forEach((o) => { o.visible = true })
  // 恢复雾效
  scene.fog = new THREE.Fog(0x04060a, 60, 135)
  viewMode.value = 'overview'
  viewedKey.value = null
  // 回到总览视角
  if (overviewCameraPos && overviewTargetPos) {
    flyTo(overviewCameraPos.clone(), overviewTargetPos.clone(), 1.6)
  }
}

function syncExplodeState() {
  deviceList.forEach((d) => {
    explodedMap[d.key] = explode.isExploded(d.key)
  })
}

function toggleSelected() {
  if (!selectedKey.value) return
  explode.toggle(selectedKey.value)
  syncExplodeState()
}

function restoreAll() {
  explode.restoreAll()
  syncExplodeState()
}

function focusDevice(key) {
  const root = deviceRoots[key]
  if (!root) return
  selectedKey.value = key
  const box = new THREE.Box3().setFromObject(root)
  const c = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3()).length()
  const dist = size * 1.5 + 6

  gsap.to(controls.target, { x: c.x, y: c.y, z: c.z, duration: 0.8, ease: 'power2.inOut' })
  gsap.to(camera.position, {
    x: c.x + dist * 0.62,
    y: c.y + dist * 0.5,
    z: c.z + dist * 0.62,
    duration: 0.8,
    ease: 'power2.inOut',
  })
}

// 按键判定用 e.code（物理键码）：不受中文输入法/键盘布局影响。
// 输入法中文态下 Chrome 的 e.key 会变成 "Process"(keyCode 229) 导致 WASD 丢失；e.code 始终返回 KeyW 等物理值。
const CODE_MAP = {
  KeyW: 'w', KeyA: 'a', KeyS: 's', KeyD: 'd',
  ArrowUp: 'w', ArrowLeft: 'a', ArrowDown: 's', ArrowRight: 'd',
  ShiftLeft: 'shift', ShiftRight: 'shift',
}
function onKeyDown(e) {
  if (e.code === 'KeyF' && mode.value === 'orbit') { freeControls.lock(); return }
  if (e.code === 'Escape' && mode.value === 'free') { freeControls.unlock(); return }
  const a = CODE_MAP[e.code]
  if (a) { keys[a] = true; if (e.code.startsWith('Arrow')) e.preventDefault() }
}
function onKeyUp(e) {
  const a = CODE_MAP[e.code]
  if (a) keys[a] = false
}

function onResize() {
  const w = window.innerWidth
  const h = window.innerHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
  labelRenderer.setSize(w, h)
  composer.setSize(w, h)
}

function animate() {
  animId = requestAnimationFrame(animate)
  const dt = clock.getDelta()

  if (mode.value === 'free') {
    const speed = 14
    velocity.set(
      (keys.d ? 1 : 0) - (keys.a ? 1 : 0),
      0,
      (keys.s ? 1 : 0) - (keys.w ? 1 : 0),
    )
    if (velocity.lengthSq() > 0) {
      velocity.normalize().multiplyScalar(speed * dt)
      freeControls.moveRight(velocity.x)
      freeControls.moveForward(-velocity.z)
    }
    camera.position.y = 3.2 // r186 PointerLockControls 无 getObject()
  } else if (!flying) {
    // 飞行补间中不跑 OrbitControls，避免阻尼与补间互抢造成抳动
    controls.update()
  }

  composer.render()
  labelRenderer.render(scene, camera)
}

onMounted(init)
onBeforeUnmount(() => {
  cancelAnimationFrame(animId)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  renderer?.dispose()
})
</script>

<style scoped>
.cockpit {
  position: relative;
  width: 100%;
  height: 100%;
}
.scene-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.label-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

/* ---------- HUD ---------- */
.hud-top {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: linear-gradient(180deg, rgba(4, 10, 20, 0.92), rgba(4, 10, 20, 0));
  pointer-events: none;
}
.hud-top__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.hud-top__brand h1 {
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #d9f2ff;
  text-shadow: 0 0 14px rgba(0, 220, 255, 0.5);
}
.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #00f26a;
  box-shadow: 0 0 12px #00f26a;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  50% { opacity: 0.35; }
}
.hud-top__hint {
  font-size: 12px;
  color: #7fa6c0;
  letter-spacing: 0.5px;
}
.hud-top__hint b {
  color: #22e0d6;
}
.btn-back {
  pointer-events: auto;
  padding: 8px 18px;
  background: rgba(0, 180, 255, 0.15);
  border: 1px solid rgba(0, 220, 255, 0.6);
  border-radius: 6px;
  color: #7fdfff;
  font-size: 13px;
  letter-spacing: 1px;
  cursor: pointer;
  backdrop-filter: blur(6px);
  transition: all 0.2s;
}
.btn-back:hover {
  background: rgba(0, 220, 255, 0.3);
  color: #fff;
  box-shadow: 0 0 16px rgba(0, 220, 255, 0.4);
}

.hud-panel {
  position: absolute;
  top: 84px;
  width: 250px;
  padding: 16px;
  border-radius: 10px;
  background: linear-gradient(160deg, rgba(8, 20, 34, 0.86), rgba(6, 14, 26, 0.72));
  border: 1px solid rgba(38, 148, 200, 0.28);
  box-shadow: 0 0 26px rgba(0, 120, 190, 0.16), inset 0 0 30px rgba(0, 120, 190, 0.07);
  backdrop-filter: blur(6px);
}
.hud-left { left: 22px; }
.hud-right { right: 22px; width: 274px; }

.hud-panel h2 {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 3px;
  color: #59d7ff;
  margin-bottom: 12px;
  padding-left: 9px;
  border-left: 3px solid #22e0d6;
  text-shadow: 0 0 10px rgba(0, 200, 255, 0.55);
}
.hud-panel h3 {
  font-size: 12px;
  color: #59d7ff;
  letter-spacing: 2px;
  margin: 14px 0 8px;
}

.hud-left ul { list-style: none; }
.hud-left li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 9px;
  margin-bottom: 6px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: 0.22s;
}
.hud-left li:hover {
  background: rgba(34, 224, 214, 0.09);
  border-color: rgba(34, 224, 214, 0.4);
}
.hud-left li.active {
  background: rgba(34, 224, 214, 0.16);
  border-color: rgba(34, 224, 214, 0.65);
}
.swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex: none;
}
.hud-left .name { flex: 1; color: #b9daea; }
.hud-left .state {
  font-size: 11px;
  font-style: normal;
  color: #5c85a0;
}
.hud-left .state.on {
  color: #ffb02e;
  text-shadow: 0 0 9px rgba(255, 176, 46, 0.7);
}

.panel-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.panel-actions button {
  flex: 1;
  padding: 8px 6px;
  font-size: 12px;
  color: #04121c;
  font-weight: 600;
  letter-spacing: 1px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: linear-gradient(180deg, #2ee6c8, #12b39c);
  box-shadow: 0 0 16px rgba(46, 230, 200, 0.32);
  font-family: inherit;
}
.panel-actions button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.panel-actions button.ghost {
  background: transparent;
  color: #7fc7dd;
  border: 1px solid rgba(46, 230, 200, 0.45);
  box-shadow: none;
}

.metrics .metric { margin-bottom: 12px; }
.metrics label {
  font-size: 11.5px;
  color: #7fa6c0;
  letter-spacing: 1px;
}
.metrics strong {
  display: block;
  font-size: 23px;
  font-weight: 600;
  color: #e8f8ff;
  text-shadow: 0 0 14px rgba(0, 200, 255, 0.45);
  margin: 2px 0 5px;
}
.metrics strong small {
  font-size: 11px;
  color: #6d9ab3;
  margin-left: 3px;
}
.bar {
  height: 4px;
  border-radius: 3px;
  background: rgba(40, 90, 120, 0.4);
  overflow: hidden;
}
.bar i {
  display: block;
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #12b39c, #2ee6c8);
  box-shadow: 0 0 10px rgba(46, 230, 200, 0.8);
  transition: width 0.6s ease;
}
.bar.warn i {
  background: linear-gradient(90deg, #c98a10, #ffc22e);
  box-shadow: 0 0 10px rgba(255, 194, 46, 0.8);
}

.alerts p {
  font-size: 12px;
  color: #8fb4c8;
  padding: 5px 0 5px 8px;
  border-left: 2px solid #2a5a72;
  margin-bottom: 4px;
  line-height: 1.4;
}
.alerts p.warn { border-color: #ffb02e; color: #e5c893; }
.alerts p.ok { border-color: #00f26a; }
.alerts p.info { border-color: #22e0d6; }
.alerts time {
  color: #5c85a0;
  margin-right: 6px;
  font-variant-numeric: tabular-nums;
}

.hud-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 38px;
  font-size: 11.5px;
  letter-spacing: 1px;
  color: #5f8ba3;
  background: linear-gradient(0deg, rgba(4, 10, 20, 0.9), rgba(4, 10, 20, 0));
}
</style>

<style>
/* CSS2D 标签是挂在 canvas 容器上的，不能用 scoped */
.dev-label {
  padding: 3px 9px;
  font-size: 11.5px;
  letter-spacing: 1px;
  color: #b9f4ff;
  background: rgba(6, 22, 36, 0.78);
  border: 1px solid rgba(34, 224, 214, 0.6);
  border-radius: 4px;
  white-space: nowrap;
  text-shadow: 0 0 8px rgba(0, 200, 255, 0.6);
  box-shadow: 0 0 12px rgba(0, 150, 200, 0.28);
}
.dev-label::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -7px;
  width: 1px;
  height: 7px;
  background: rgba(34, 224, 214, 0.7);
  transform: translateX(-50%);
}
</style>
