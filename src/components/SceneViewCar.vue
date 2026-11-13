<template>
  <div class="cockpit">
    <canvas ref="canvasRef" class="scene-canvas"></canvas>

    <header class="hud-top">
      <div class="hud-top__brand">
        <span class="dot"></span>
        <h1>汽车制造车间 · 四大工艺流程 3D 复现</h1>
      </div>
      <div class="hud-top__hint">{{ mode === 'free' ? '鼠标转向 · W/S 前后 · A/D 左右 · Shift 冲刺 · ESC 退出' : '左键拖拽旋转 · 滚轮缩放 · 按 F 自由漫游' }}</div>
    </header>

    <aside class="flow-panel">
      <div class="flow-panel__title">生产流程 <span>PRODUCTION FLOW</span></div>
      <div
        v-for="(z, i) in ZONES"
        :key="z.key"
        class="flow-step"
        :class="{ active: activeZones.includes(z.key) }"
        :style="{ '--zc': z.color }"
      >
        <div class="flow-step__no">{{ i + 1 }}</div>
        <div class="flow-step__body">
          <div class="flow-step__name">{{ z.name }} <em>{{ z.en }}</em></div>
          <div class="flow-step__desc">{{ z.desc }}</div>
          <div v-if="z.key === 'asm'" class="flow-step__subs">
            <span v-for="s in ASM_SUBS" :key="s" :class="{ on: asmSteps.includes(s) }">{{ s }}</span>
          </div>
        </div>
      </div>
      <div class="flow-panel__foot">料架散件 → 骨架 → 白车身 → 涂装 → 底盘合装 → 内饰 → 车门 → 灯具 → 整车下线</div>
    </aside>

    <footer class="hud-bottom">
      <span>引擎：Three.js {{ threeVersion }}</span>
      <span>模式：{{ mode === 'orbit' ? '环绕漫游（按 F 自由漫游）' : '自由漫游 · WASD 移动 · 鼠标转向 · ESC 退出' }}</span>
      <span>页面：?scene=car（独立模型集 models-car）</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { PointerLockControls } from 'three/examples/jsm/controls/PointerLockControls.js'
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer.js'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'
import { ModelLoader } from '../three/ExplodeController.js'

const canvasRef = ref(null)
const threeVersion = THREE.REVISION
const mode = ref('orbit')
const activeZones = ref('')
const asmSteps = ref([])

// —— 四大工艺（依据 Leuze/Toyota 总装资料：车门分装→内饰→底盘合装 Marriage→车轮/车窗/座椅/大灯→油液→终检）——
const ZONES = [
  { key: 'stamp', name: '冲压车间', en: 'STAMPING', x: -20, color: '#4aa8ff',
    desc: '钢卷经开料落料，由大型压力机冲压成地板、机盖、车门、顶盖等覆盖件，料架送往焊装' },
  { key: 'weld', name: '焊装车间', en: 'WELDING', x: -6, color: '#ffc04a',
    desc: '机器人点焊车身骨架，地板、侧围、顶盖与四门逐步闭合，拼成完整白车身（BIW）' },
  { key: 'paint', name: '涂装车间', en: 'PAINTING', x: 7, color: '#3dff88',
    desc: '白车身经前处理、电泳底漆、面漆喷涂与烘干，出喷漆房即成成品漆面' },
  { key: 'asm', name: '总装车间', en: 'ASSEMBLY', x: 20, color: '#dfe9ff',
    desc: '底盘合装 → 内饰 → 车门/玻璃 → 灯具/终检，加注油液后整车下线' },
]
const zoneOf = (x) => (x < -13 ? 'stamp' : x < 1 ? 'weld' : x < 13 ? 'paint' : 'asm')

// 总装四工位（与 shell 里 4 座龙门/工具臂一一对应）
const ASM_SUBS = ['底盘合装', '内饰安装', '车门 · 玻璃', '灯具 · 终检']
const ASM_X = [15.5, 18.5, 21.5, 24.5]

// —— 产线时间轴：匀速行走 + 工位停留，循环播放（4 台车身错相 1/4 周期）——
const LINE_SPEED = 2.6
const STOPS = [
  { x: -25, d: 1.0 },
  { x: -24, d: 3.0 }, { x: -20, d: 3.0 }, { x: -16, d: 3.0 },   // 冲压 3 台压力机
  { x: -10, d: 4.0 }, { x: -6, d: 4.0 }, { x: -2, d: 4.0 },     // 焊装 3 工位（骨架→侧围→全闭合）
  { x: 7, d: 6.0 },                                              // 涂装喷漆房
  { x: 15.5, d: 3.5 }, { x: 18.5, d: 3.5 }, { x: 21.5, d: 3.5 }, { x: 24.5, d: 3.5 }, // 总装 4 工位
  { x: 27, d: 0.5 },                                             // 下线 → 换成品车驶出
]
const segs = []
let LOOP = 0
{
  let t = 0
  let px = STOPS[0].x
  for (let i = 0; i < STOPS.length; i++) {
    const s = STOPS[i]
    if (i > 0) {
      const tr = Math.abs(s.x - px) / LINE_SPEED
      segs.push({ t0: t, t1: t + tr, x0: px, x1: s.x })
      t += tr
    }
    if (s.d > 0) { segs.push({ t0: t, t1: t + s.d, x0: s.x, x1: s.x }); t += s.d }
    px = s.x
  }
  LOOP = t
}
function xAt(tt) {
  for (const s of segs) {
    if (tt < s.t1) return s.x0 + ((s.x1 - s.x0) * (tt - s.t0)) / (s.t1 - s.t0)
  }
  return STOPS[STOPS.length - 1].x
}

const PRESS_X = [-24, -20, -16]
const STATION_X = [-10, -6, -2]
const PAINTS = [0xc22a1e, 0x2456c8, 0xd99a10, 0xd8dee6]
const BODIES_N = 4
const BED_Y = 0.5
const BOOTH_X = 7

let renderer, labelRenderer, composer, scene, camera, controls, freeControls
let clock, loader
let animId = 0
const keys = { w: false, a: false, s: false, d: false, shift: false }
let velocity = new THREE.Vector3()

const presses = []
const robots = []
const tools = []
const bodies = []
const boothMats = []
let boothGlow = null
let lastUiPush = 0
let pops = []
const _v = new THREE.Vector3()
const SPARK_GEO = new THREE.SphereGeometry(0.07, 8, 6)
const SPARK_COLOR = new THREE.Color(2.2, 1.5, 0.8) // >1 只有火花过 bloom 阈值

function easeOutBack(t) {
  const c1 = 1.70158
  const c3 = c1 + 1
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
}

// 零件组渐进显示：首次可见时 0.01→1 回弹 pop-in
function showGroup(nodes, on, el, b) {
  if (!on) return
  for (const n of nodes) {
    if (!n.visible) {
      n.visible = true
      n.scale.setScalar(0.01)
      pops.push({ o: n, t0: el, b })
    }
  }
}

function init() {
  const canvas = canvasRef.value
  const w = window.innerWidth
  const h = window.innerHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x04060a)
  scene.fog = new THREE.Fog(0x04060a, 130, 300)

  camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 600)
  camera.position.set(-38, 24, 42)

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0

  labelRenderer = new CSS2DRenderer()
  labelRenderer.setSize(w, h)
  labelRenderer.domElement.className = 'label-layer'
  canvas.parentElement.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.06
  controls.maxPolarAngle = Math.PI / 2.15
  controls.minDistance = 8
  controls.maxDistance = 180
  controls.target.set(0, 2, 0)

  freeControls = new PointerLockControls(camera, renderer.domElement)

  // 光照沿用 v2 标定（暗调科技风，不闷黑）
  scene.add(new THREE.AmbientLight(0xaaccee, 1.5))
  const keyLight = new THREE.DirectionalLight(0xeef4ff, 1.8)
  keyLight.position.set(18, 30, 16)
  scene.add(keyLight)
  const fillLight = new THREE.DirectionalLight(0x6fa8ff, 1.15)
  fillLight.position.set(-20, 14, -14)
  scene.add(fillLight)
  const rimLight = new THREE.DirectionalLight(0x30ff9a, 0.5)
  rimLight.position.set(0, 8, 22)
  scene.add(rimLight)
  scene.add(new THREE.HemisphereLight(0x3a5b85, 0x0e1220, 0.95))

  // 后期：bloom 阈值 1.05，只有灯带/火花/灯珠过线（纪律同 v2）
  composer = new EffectComposer(renderer)
  composer.addPass(new RenderPass(scene, camera))
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(w, h), 0.3, 0.45, 1.05))
  composer.addPass(new OutputPass())

  loader = new ModelLoader()
  clock = new THREE.Clock()

  bindEvents()
  loadScene()
  animate()
}

function pick(obj, re) {
  const a = []
  obj.traverse((o) => { if (re.test(o.name)) a.push(o) })
  return a
}

async function loadScene() {
  const base = import.meta.env.BASE_URL
  const cm = (f) => loader.load(`${base}models-car/${f}`)
  const [plant, press, robot, booth, skidM, frameM, bodyM, partsM, vehicle] = await Promise.all([
    cm('workshop_shell.glb'), cm('press.glb'), cm('weld_robot.glb'), cm('paint_booth.glb'),
    cm('stamped_skid.glb'), cm('car_frame.glb'), cm('car_body.glb'), cm('car_parts.glb'),
    loader.load(`${base}models/vehicle.glb`),
  ])

  scene.add(plant.scene)

  // 下线跑道（厂外地坪延伸 + 两条引导灯条，成品车驶出用）
  const apron = new THREE.Mesh(
    new THREE.BoxGeometry(20, 0.2, 9),
    new THREE.MeshStandardMaterial({ color: 0x0a0e14, roughness: 0.8, metalness: 0.1 }),
  )
  apron.position.set(38.7, -0.1, 0)
  scene.add(apron)
  for (const zs of [-3.3, 3.3]) {
    const s = new THREE.Mesh(
      new THREE.BoxGeometry(20, 0.05, 0.1),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(0.55, 0.75, 1.0) }),
    )
    s.position.set(38.7, 0.03, zs)
    scene.add(s)
  }

  // —— 喷漆房（车身进洞隐藏、出洞换漆色，内灯喷涂时脉冲）——
  booth.scene.position.set(BOOTH_X, 0, 0)
  scene.add(booth.scene)
  booth.scene.traverse((o) => {
    if (o.isMesh && /^part_light_/.test(o.name)) {
      o.material = o.material.clone()
      boothMats.push(o.material)
    }
  })
  boothGlow = new THREE.PointLight(0x9dffb0, 0.35, 12, 2)
  boothGlow.position.set(BOOTH_X, 2.2, 0)
  scene.add(boothGlow)

  // —— 冲压机 ×3（ram 冲压动画 + 顶灯闪烁）——
  for (const x of PRESS_X) {
    const p = press.scene.clone(true)
    p.position.set(x, 0, -4.5)
    scene.add(p)
    const ram = p.getObjectByName('part_ram')
    const beacon = p.getObjectByName('part_beacon')
    const beaconMat = beacon.material.clone()
    beacon.material = beaconMat
    presses.push({ x, ram, ramBase: ram.position.y, beaconMat, phase: Math.random() * 6.28 })
  }

  // —— 焊接机器人 ×6（每工位 2 台，局部 +X 指向产线；关节=pivot_* 空节点）——
  for (const sx of STATION_X) {
    for (const sz of [-2.3, 2.3]) {
      const r = robot.scene.clone(true)
      r.position.set(sx, 0, sz)
      r.rotation.y = sz > 0 ? Math.PI / 2 : -Math.PI / 2
      scene.add(r)
      const spark = new THREE.Mesh(SPARK_GEO, new THREE.MeshBasicMaterial({ color: SPARK_COLOR.clone() }))
      spark.visible = false
      scene.add(spark)
      const light = new THREE.PointLight(0xffa040, 0, 6, 2)
      scene.add(light)
      robots.push({
        station: sx,
        yaw: r.getObjectByName('pivot_yaw'),
        shoulder: r.getObjectByName('pivot_shoulder'),
        elbow: r.getObjectByName('pivot_elbow'),
        wrist: r.getObjectByName('pivot_wrist'),
        tip: r.getObjectByName('part_tip'),
        spark, light,
        ph: Math.random() * 6.28,
      })
    }
  }

  // —— 总装龙门工具臂 ×4（车身到位时滑杆+工具头下降 0.45，龙门灯闪烁）——
  for (let i = 0; i < 4; i++) {
    const rod = plant.scene.getObjectByName('part_tool_' + i)
    const head = plant.scene.getObjectByName('part_toolhead_' + i)
    const strip = plant.scene.getObjectByName('part_toolstrip_' + i)
    const lamp = plant.scene.getObjectByName('part_gantry_' + i + '_lamp')
    lamp.material = lamp.material.clone()
    tools.push({
      x: ASM_X[i], label: ASM_SUBS[i],
      rod, head, strip,
      rodY: rod.position.y, headY: head.position.y, stripY: strip.position.y,
      dy: 0, lampMat: lamp.material,
    })
  }

  // —— 车身 ×4：carrier 挂 料架/骨架/涂装壳/零件组，按工位渐进组装 ——
  for (let i = 0; i < BODIES_N; i++) {
    const carrier = new THREE.Group()
    scene.add(carrier)

    const skid = skidM.scene.clone(true)
    carrier.add(skid)

    const frame = frameM.scene.clone(true)
    frame.visible = false
    carrier.add(frame)
    const fp2 = pick(frame, /^part_panel_(floor|side)/)
    const fp3 = pick(frame, /^part_panel_(roof|hood|trunk|door)/)
    for (const n of [...fp2, ...fp3]) n.visible = false

    const shell = bodyM.scene.clone(true)
    shell.visible = false
    carrier.add(shell)

    const parts = partsM.scene.clone(true)
    carrier.add(parts)
    const pg = {
      chassis: pick(parts, /^part_(axle|spring|wheel|hub|gearbox|exhaust|battery|battstrip)/),
      interior: pick(parts, /^part_(seat|dash|screen|steer)/),
      doors: pick(parts, /^part_(door_|bumper|glass)/),
      lamps: pick(parts, /^part_(lamp|grille|mirror|plate)/),
    }
    for (const grp of Object.values(pg)) for (const n of grp) n.visible = false

    // 漆色件：壳体(body/cabin/pillar) + 零件组的门/保险杠，逐台克隆材质
    const paintTargets = [
      ...pick(shell, /^part_(body|cabin|pillar)/),
      ...pick(parts, /^part_(door_|bumper)/),
    ]
    const paintMats = paintTargets.map((o) => { o.material = o.material.clone(); return o.material })
    const paintOrig = paintMats.map((mt) => ({ c: mt.color.clone(), r: mt.roughness, m: mt.metalness }))

    const c = vehicle.scene.clone(true)
    c.visible = false
    c.rotation.y = Math.PI / 2 // 成品车头朝 +x 驶出东大门（vehicle.glb 车头=本地 +Z，windshield z=+0.62 实测）
    scene.add(c)

    const offset = (i * LOOP) / BODIES_N
    bodies.push({
      carrier, skid, frame, fp2, fp3, shell, pg,
      paintMats, paintOrig,
      car: c, carActive: false, carX: 27.2,
      painted: false, offset, lastTT: offset, x: -25,
      color: PAINTS[i],
    })
  }

  // —— 区域 3D 标签（CSS2D 元素本体不做 transform 动画，避免和 renderer 抢样式）——
  for (const z of ZONES) {
    const el = document.createElement('div')
    el.className = 'zone-chip'
    el.style.setProperty('--zc', z.color)
    el.innerHTML = `<b>${z.name}</b><i>${z.en}</i>`
    const lab = new CSS2DObject(el)
    lab.position.set(z.x, 7.0, 0)
    scene.add(lab)
  }
}

function resetBody(b) {
  b.painted = false
  b.carActive = false
  b.car.visible = false
  b.carX = 27.2
  b.carrier.visible = true
  b.skid.visible = true
  b.frame.visible = false
  b.frame.scale.setScalar(1)
  b.shell.visible = false
  b.shell.scale.setScalar(1)
  for (const n of [...b.fp2, ...b.fp3]) { n.visible = false; n.scale.setScalar(1) }
  for (const grp of Object.values(b.pg)) for (const n of grp) { n.visible = false; n.scale.setScalar(1) }
  b.paintMats.forEach((mt, i) => {
    mt.color.copy(b.paintOrig[i].c)
    mt.roughness = b.paintOrig[i].r
    mt.metalness = b.paintOrig[i].m
  })
  pops = pops.filter((p) => p.b !== b)
}

function animate() {
  animId = requestAnimationFrame(animate)
  const dt = Math.min(clock.getDelta(), 0.05)
  const el = clock.elapsedTime

  if (mode.value === 'free') {
    const speed = keys.shift ? 16 : 6 // 步行 6 m/s，按住 Shift 冲刺 16 m/s
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
    camera.position.y = 3.2 // r186 PointerLockControls 无 getObject()，直接锁定相机眼高
  } else {
    controls.update()
  }

  // —— pop-in 动画队列 ——
  for (let i = pops.length - 1; i >= 0; i--) {
    const p = pops[i]
    const t = (el - p.t0) / 0.5
    if (t >= 1) { p.o.scale.setScalar(1); pops.splice(i, 1) }
    else p.o.scale.setScalar(Math.max(0.01, easeOutBack(t)))
  }

  // —— 车身流：料架→骨架→白车身→涂装→渐进总装→成品车驶出 ——
  const zonesNow = new Set()
  const stepsNow = new Set()
  let boothBusy = false
  for (const b of bodies) {
    const tt = (el + b.offset) % LOOP
    if (tt < b.lastTT - LOOP / 2) resetBody(b) // 回卷 → 整台重置
    b.lastTT = tt
    const x = xAt(tt)
    b.x = x

    const inBooth = x > BOOTH_X - 3 && x < BOOTH_X + 3

    if (x >= 26.9 && !b.carActive) {
      // 到下线口 → 组装态隐去，换成品车驶出东大门
      b.carActive = true
      b.carrier.visible = false
      b.carX = 27.2
      b.car.position.set(b.carX, 0, 0)
      b.car.visible = true
    }

    if (!b.carActive) {
      b.carrier.position.set(x, BED_Y, 0)
      b.carrier.visible = !inBooth

      // 冲压区：料架散件
      b.skid.visible = x < -12.5
      // 焊装区：骨架渐进闭合（工位2 地板/侧围，工位3 顶盖/机盖/四门）
      const frameOn = x >= -12.5 && x < -1
      showGroup([b.frame], frameOn, el, b)
      b.frame.visible = frameOn
      if (frameOn) {
        showGroup(b.fp2, x >= -6.2, el, b)
        showGroup(b.fp3, x >= -2.2, el, b)
      }
      // 涂装壳体：焊装完成(-1)出现白车身；出喷漆房(>10)带漆色再 pop 一次
      const shellOn = x >= -1 && !inBooth
      showGroup([b.shell], shellOn, el, b)
      b.shell.visible = shellOn
      if (inBooth) boothBusy = true
      if (x > BOOTH_X + 3 && !b.painted) {
        b.painted = true
        for (const mt of b.paintMats) {
          mt.color.setHex(b.color)
          mt.roughness = 0.22
          mt.metalness = 0.6
        }
      }
      // 总装四工位：零件组按到站渐进安装
      if (x >= 14) {
        showGroup(b.pg.chassis, x >= 15.4, el, b)
        showGroup(b.pg.interior, x >= 18.4, el, b)
        showGroup(b.pg.doors, x >= 21.4, el, b)
        showGroup(b.pg.lamps, x >= 24.4, el, b)
      }
      zonesNow.add(zoneOf(x))
    } else {
      zonesNow.add('asm')
    }

    if (b.car.visible) {
      b.carX += 4.0 * dt
      b.car.position.x = b.carX
      if (b.carX > 46) b.car.visible = false
    }
  }

  // —— 冲压机：车身到位时 ram 快压，平时慢速待机 + 顶灯闪烁 ——
  for (const p of presses) {
    let working = false
    for (const b of bodies) if (!b.carActive && Math.abs(b.x - p.x) < 0.4) working = true
    p.ram.position.y = working
      ? p.ramBase - 1.7 * Math.abs(Math.sin(el * 3.2 + p.phase))
      : p.ramBase - 0.04 * (0.5 + 0.5 * Math.sin(el * 0.8 + p.phase))
    p.beaconMat.emissiveIntensity = 0.75 + 0.55 * Math.sin(el * (working ? 9 : 2.2) + p.phase)
  }

  // —— 焊接机器人：空闲慢摆；骨架到位快摆 + 枪尖火花/橙光 ——
  for (const r of robots) {
    let working = false
    for (const b of bodies) if (!b.carActive && Math.abs(b.x - r.station) < 0.4) working = true
    const sp = working ? 2.6 : 0.55
    const amp = working ? 0.5 : 0.22
    r.yaw.rotation.y = amp * Math.sin(el * sp * 0.8 + r.ph)
    r.shoulder.rotation.z = -0.55 + amp * Math.sin(el * sp + r.ph * 1.3)
    r.elbow.rotation.z = 0.9 + amp * 1.2 * Math.sin(el * sp * 1.4 + r.ph * 0.7)
    r.wrist.rotation.z = el * (working ? 6 : 1)
    if (working) {
      r.tip.getWorldPosition(_v)
      r.spark.position.copy(_v)
      r.light.position.copy(_v)
      r.spark.visible = Math.random() > 0.25
      r.spark.scale.setScalar(0.6 + Math.random() * 0.9)
      r.light.intensity = 1.5 + Math.random() * 3.5
    } else {
      r.spark.visible = false
      r.light.intensity = 0
    }
  }

  // —— 总装工具臂：车身到位下降作业，龙门灯闪烁 ——
  for (const t of tools) {
    let working = false
    for (const b of bodies) {
      if (!b.carActive && b.x >= 14 && Math.abs(b.x - t.x) < 0.55) { working = true; break }
    }
    if (working) stepsNow.add(t.label)
    const target = working ? 0.45 : 0
    t.dy += (target - t.dy) * Math.min(1, dt * 5)
    t.rod.position.y = t.rodY - t.dy
    t.head.position.y = t.headY - t.dy
    t.strip.position.y = t.stripY - t.dy
    t.lampMat.emissiveIntensity = working ? 1.5 + 0.9 * Math.sin(el * 10) : 0.85
  }

  // —— 喷漆房：喷涂中内灯带脉冲 + 绿色光晕 ——
  const bp = boothBusy ? 1.7 + 1.1 * Math.sin(el * 5) : 1.0
  for (const m of boothMats) m.emissiveIntensity = bp
  if (boothGlow) boothGlow.intensity = boothBusy ? 2.2 + 1.4 * Math.sin(el * 5) : 0.35

  // —— 工序面板高亮（4Hz 节流，避免每帧触发响应式更新）——
  if (el - lastUiPush > 0.25) {
    lastUiPush = el
    const s = [...zonesNow].join(',')
    if (s !== activeZones.value) activeZones.value = s
    const st = [...stepsNow]
    if (st.join(',') !== asmSteps.value.join(',')) asmSteps.value = st
  }

  composer.render()
  labelRenderer.render(scene, camera)
}

function bindEvents() {
  window.addEventListener('resize', onResize)
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  freeControls.addEventListener('lock', () => {
    mode.value = 'free'
    // 进入漫游：相机落到厂房内、视线沿产线向东（否则从轨道机位起步会在厂房外）
    camera.position.set(-22, 3.2, 7)
    camera.lookAt(12, 2.2, 0)
  })
  freeControls.addEventListener('unlock', () => {
    mode.value = 'orbit'
    // 退出漫游：回默认俯瞰机位，避免 target 与相机错位甩视角
    camera.position.set(-38, 24, 42)
    controls.target.set(0, 2, 0)
    controls.update()
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
.cockpit { position: relative; width: 100%; height: 100%; }
.scene-canvas { position: absolute; inset: 0; width: 100%; height: 100%; }
.label-layer { position: absolute; inset: 0; pointer-events: none; }

.hud-top {
  position: absolute; top: 0; left: 0; right: 0; height: 64px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  background: linear-gradient(180deg, rgba(4, 10, 20, 0.92), rgba(4, 10, 20, 0));
  pointer-events: none;
}
.hud-top__brand { display: flex; align-items: center; gap: 10px; }
.hud-top__brand h1 {
  font-size: 19px; font-weight: 600; letter-spacing: 2px; color: #d9f2ff;
  text-shadow: 0 0 14px rgba(0, 220, 255, 0.5);
}
.dot {
  width: 9px; height: 9px; border-radius: 50%;
  background: #00f26a; box-shadow: 0 0 12px #00f26a;
  animation: pulse 2s infinite;
}
@keyframes pulse { 50% { opacity: 0.35; } }
.hud-top__hint { font-size: 12px; color: #7fa6c0; letter-spacing: 0.5px; }

.hud-bottom {
  position: absolute; bottom: 0; left: 0; right: 0; height: 40px;
  display: flex; align-items: center; justify-content: center; gap: 38px;
  font-size: 11.5px; letter-spacing: 1px; color: #5f8ba3;
  background: linear-gradient(0deg, rgba(4, 10, 20, 0.9), rgba(4, 10, 20, 0));
}

/* —— 左侧工艺流程面板 —— */
.flow-panel {
  position: absolute; left: 20px; top: 84px; width: 312px;
  padding: 14px 14px 12px;
  background: rgba(6, 12, 22, 0.82);
  border: 1px solid rgba(90, 140, 180, 0.25);
  border-radius: 10px;
  backdrop-filter: blur(6px);
  pointer-events: none;
}
.flow-panel__title {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: 13px; letter-spacing: 3px; color: #bfe3ff; margin-bottom: 10px;
}
.flow-panel__title span { font-size: 9px; letter-spacing: 1px; color: #5f8ba3; }
.flow-step {
  display: flex; gap: 10px; padding: 8px;
  border: 1px solid transparent; border-left: 3px solid var(--zc);
  border-radius: 8px; margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.02);
  transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
}
.flow-step.active {
  border-color: var(--zc);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 12px -2px var(--zc);
}
.flow-step__no {
  flex: none; width: 20px; height: 20px; margin-top: 2px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--zc); border-radius: 50%;
  color: var(--zc); font-size: 11px;
}
.flow-step__name { font-size: 13px; color: #e8f4ff; letter-spacing: 2px; }
.flow-step__name em {
  font-style: normal; font-size: 9px; color: #6d94ad;
  letter-spacing: 1px; margin-left: 6px;
}
.flow-step__desc { font-size: 11px; color: #8fb0c4; line-height: 1.55; margin-top: 3px; }
.flow-step__subs { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 5px; }
.flow-step__subs span {
  font-size: 9.5px; padding: 2px 6px; border-radius: 3px;
  border: 1px solid rgba(120, 160, 190, 0.3); color: #6d94ad; letter-spacing: 0.5px;
  transition: all 0.3s;
}
.flow-step__subs span.on {
  border-color: #dfe9ff; color: #fff;
  background: rgba(223, 233, 255, 0.15);
  box-shadow: 0 0 8px -2px #dfe9ff;
}
.flow-panel__foot {
  margin-top: 8px; padding-top: 8px;
  border-top: 1px dashed rgba(90, 140, 180, 0.25);
  font-size: 10.5px; color: #6d94ad; letter-spacing: 0.5px;
}
</style>

<style>
/* 区域 3D 标签（CSS2DObject 元素；不做 transform 动画，位移归 renderer 管） */
.zone-chip {
  display: flex; flex-direction: column; align-items: center; gap: 1px;
  padding: 4px 12px; border-radius: 4px;
  border: 1px solid var(--zc, #7fb0d0);
  background: rgba(4, 10, 20, 0.78);
  box-shadow: 0 0 10px -2px var(--zc, #7fb0d0);
  white-space: nowrap;
}
.zone-chip b {
  font-size: 13px; letter-spacing: 3px; color: #fff;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
}
.zone-chip i {
  font-style: normal; font-size: 8.5px; letter-spacing: 2px;
  color: var(--zc, #9fc4dd); opacity: 0.85;
}
</style>
