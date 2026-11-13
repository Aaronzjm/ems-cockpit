<template>
  <div class="cockpit">
    <canvas ref="canvasRef" class="scene-canvas"></canvas>

    <header class="hud-top">
      <div class="hud-top__brand">
        <span class="dot"></span>
        <h1>光储充一体化园区 · 参考图复现</h1>
      </div>
      <div class="hud-top__hint">左键拖拽旋转 · 滚轮缩放 · 按 F 自由漫游</div>
    </header>

    <footer class="hud-bottom">
      <span>引擎：Three.js {{ threeVersion }}</span>
      <span>模式：{{ mode === 'orbit' ? '环绕漫游' : '自由漫游' }}（按 F 切换）</span>
      <span>页面：?scene=v2（独立模型集 models-v2）</span>
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

let renderer, labelRenderer, composer, scene, camera, controls, freeControls
let clock, loader
let animId = 0
const keys = { w: false, a: false, s: false, d: false }
let velocity = new THREE.Vector3()
// 红色告警车位脉冲素材（方形光池 + 方形光环，参考图样式）
let alertPool = null
let alertDisc = null

function init() {
  const canvas = canvasRef.value
  const w = window.innerWidth
  const h = window.innerHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x04060a)
  scene.fog = new THREE.Fog(0x04060a, 85, 170)

  // 参考图机位：前左高角 iso 视角
  camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 600)
  camera.position.set(-19, 15, 21)

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
  controls.maxDistance = 110
  controls.target.set(-1, 1, 0)

  freeControls = new PointerLockControls(camera, renderer.domElement)

  // 光照：沿用 v1 标定值（暗调科技风，不闷黑）
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

  // 后期：霓虹辉光（OutputPass 收尾，阈值 1.05 只让描边过）
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

async function loadScene() {
  const base = import.meta.env.BASE_URL
  const v2 = (f) => loader.load(`${base}models-v2/${f}`)
  const v1 = (f) => loader.load(`${base}models/${f}`)

  const [ground, walls, canopy, pile, storage, totem,
    transformer, controlroom, vehicle, kiosk] = await Promise.all([
    v2('ground_park.glb'), v2('park_walls.glb'), v2('pv_canopy_v2.glb'),
    v2('charging_pile_v2.glb'), v2('storage_yard_v2.glb'), v2('info_totem.glb'),
    v1('transformer_substation.glb'), v1('control_room.glb'),
    v1('vehicle.glb'), v1('kiosk.glb'),
  ])

  const groundBox = new THREE.Box3().setFromObject(ground.scene)
  scene.add(ground.scene)
  scene.add(walls.scene)

  /** 摆一个模型 + 越界审计 */
  const place = (name, root, pos, rotY = 0) => {
    root.position.set(...pos)
    root.rotation.y = rotY
    scene.add(root)
    const box = new THREE.Box3().setFromObject(root)
    const out = box.min.x < groundBox.min.x + 0.4 || box.max.x > groundBox.max.x - 0.4 ||
      box.min.z < groundBox.min.z + 0.4 || box.max.z > groundBox.max.z - 0.4
    if (out) console.error(`❌ [Bounds] ${name} 贴近/超出底座边缘`, {
      x: [box.min.x.toFixed(2), box.max.x.toFixed(2)], z: [box.min.z.toFixed(2), box.max.z.toFixed(2)] })
    else console.log(`✅ [Bounds] ${name} 在底座内`)
    return root
  }

  // —— 光伏车棚（12.8m 长罩满 4 桩 4 车位，15:09 用户要求顶棚全覆盖；
  //    16:28 根挪到 -5.55=4 车位排中心：旧值 -4.1 是 3 车位时代残留，
  //    导致立柱落在 x=-9.8/-6.0/-2.2 穿进车里；新棚 5 立柱全在车位分界线上）——
  place('canopy', canopy.scene, [-5.55, 0, 2.2])

  // —— 4 车位：桩在车位分界处（参考图样式，两车共用），车居中停满车位 ——
  const SLOT_X = [-9.9, -7.0, -4.1, -1.2]
  const PILE_X = [-8.45, -5.55, -2.65, 0.25]
  for (const x of PILE_X) {
    const p = pile.scene.clone(true)
    place('pile', p, [x, 0, 3.5])
  }
  SLOT_X.forEach((x, i) => {
    const car = vehicle.scene.clone(true)
    place('car', car, [x, 0, 2.2])
    if (i === SLOT_X.length - 1) {
      addAlert(x, 2.2) // 最右车位 = 红色告警（光池+方环保留，徽标球按 15:09 去掉）
    }
  })

  // —— 储能院 / 变压器 / 配电室 / 信息亭 / 信息柱 ——
  place('storage', storage.scene, [5.5, 0, -5.5], Math.PI) // Blender y→世界 -z：rot π 才让敞口（Blender +y）朝相机、绿柜排在前、暗柜排在后（15:00 截图核对）
  place('transformer', transformer.scene, [10.5, 0, -4.2]) // 参考图：储能院右侧、院与右墙之间
  // 变压器右侧贴右墙的小暗柜（参考图同款，顶一条绿线）
  const auxCab = new THREE.Mesh(
    new THREE.BoxGeometry(0.9, 1.6, 1.2),
    new THREE.MeshStandardMaterial({ color: 0x14181d, roughness: 0.6, metalness: 0.3 }),
  )
  auxCab.position.set(11.8, 0.8, -6.2)
  scene.add(auxCab)
  const auxLine = new THREE.Mesh(
    new THREE.BoxGeometry(0.94, 0.03, 0.03),
    new THREE.MeshBasicMaterial({ color: new THREE.Color(0.30, 1.0, 0.50) }),
  )
  auxLine.position.set(11.8, 1.62, -6.2)
  scene.add(auxLine)
  place('controlroom', controlroom.scene, [9.2, 0, 1.8], -Math.PI / 2)
  // 参考图配电室基座为金色描边（v1 模型是绿色，仅 v2 实例覆盖）
  controlroom.scene.traverse((o) => {
    if (o.isMesh && /part_base_outline|part_floor_glow/.test(o.name)) {
      o.material = o.material.clone()
      o.material.color.set(0xffa64d)
      if (o.material.emissive) o.material.emissive.set(0xffa64d)
    }
  })
  place('kiosk', kiosk.scene, [-4.5, 0, 6.2])
  place('totem', totem.scene, [-12.2, 0, 0.0]) // 错开左列花箱

  // —— 四区标注（参考图：白字 + 斜引线 + 圆点）——
  addZoneLabel('光伏区', -5.55, 4.6, 2.2, -110, -80)
  addZoneLabel('储能区', 5.5, 3.0, -5.5, 110, -80)
  addZoneLabel('充电区', -11.6, 0.2, 6.0, -110, 80)
  addZoneLabel('配电室', 9.2, 0.3, -1.6, 110, 80)
  addGroundTraces()
}

/** 红色告警：方形光池 + 方形光环（参考图是方圈不是圆环），渲染循环里脉冲 */
function addAlert(x, z) {
  alertPool = new THREE.Group()
  alertPool.position.set(x, 0, z)
  alertDisc = new THREE.Mesh(
    new THREE.PlaneGeometry(3.6, 3.6),
    new THREE.MeshBasicMaterial({ color: 0xff2015, transparent: true, opacity: 0.22, depthWrite: false }),
  )
  alertDisc.rotation.x = -Math.PI / 2
  alertDisc.position.y = 0.045
  alertPool.add(alertDisc)
  const ringMat = new THREE.MeshBasicMaterial({ color: 0xff2a1a })
  const half = 1.8
  const bar = (w, d, px, pz) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, 0.06, d), ringMat)
    m.position.set(px, 0.07, pz)
    alertPool.add(m)
  }
  bar(3.68, 0.08, 0, -half)
  bar(3.68, 0.08, 0, half)
  bar(0.08, 3.68, -half, 0)
  bar(0.08, 3.68, half, 0)
  scene.add(alertPool)
}

function addZoneLabel(text, x, y, z, dx, dy) {
  // 引线做成 3D 线段：默认机位下按屏幕像素偏移定文字端点，
  // 旋转视角后引线仍在 3D 里正确连接（参考图同款）
  const target = new THREE.Vector3(x, y, z)
  const right = new THREE.Vector3()
  const up = new THREE.Vector3()
  const fwd = new THREE.Vector3()
  camera.matrixWorld.extractBasis(right, up, fwd)
  const dist = camera.position.distanceTo(target)
  const pxPerM = (window.innerHeight / 2) / (Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * dist)
  const textPos = target.clone()
    .addScaledVector(right, dx / pxPerM)
    .addScaledVector(up, -dy / pxPerM)
  const geo = new THREE.BufferGeometry().setFromPoints([target, textPos])
  scene.add(new THREE.Line(geo, new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.65 })))
  const dotEl = document.createElement('div')
  dotEl.className = 'zone-dot'
  const dot = new CSS2DObject(dotEl)
  dot.position.copy(target)
  scene.add(dot)
  const textEl = document.createElement('div')
  textEl.className = 'zone-text'
  textEl.textContent = text
  const label = new CSS2DObject(textEl)
  label.position.copy(textPos)
  scene.add(label)
}

/** 地面走线式实绿线 + 方形节点垫（参考图同款；亮度 <1.05 不过 bloom） */
function addGroundTraces() {
  const lineMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.30, 1.0, 0.50) })
  const padMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.45, 1.0, 0.62) })
  // 16:06 修闪烁：deck 顶 0.06（doubleSided 会从上方渲染）与贴地线顶面共面会 z-fight，
  // 走线整体抬高到 0.095（顶面 0.105）远离 deck 顶面
  const TRACE_Y = 0.095
  const seg = (x1, z1, x2, z2) => {
    const len = Math.hypot(x2 - x1, z2 - z1)
    const m = new THREE.Mesh(new THREE.BoxGeometry(len, 0.02, 0.06), lineMat)
    m.position.set((x1 + x2) / 2, TRACE_Y, (z1 + z2) / 2)
    m.rotation.y = -Math.atan2(z2 - z1, x2 - x1)
    scene.add(m)
  }
  const pad = (x, z) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.025, 0.24), padMat)
    m.position.set(x, TRACE_Y, z)
    scene.add(m)
  }
  const route = (pts, closed = false) => {
    for (let i = 0; i < pts.length - 1; i++) seg(...pts[i], ...pts[i + 1])
    if (closed) seg(...pts[pts.length - 1], ...pts[0])
    pts.forEach(([x, z]) => pad(x, z))
  }
  route([[-12.1, 7.2], [-12.1, -6.0]])                         // 左走道
  route([[-11.5, -1.6], [-2.2, -1.6], [-2.2, -6.1], [-11.5, -6.1]], true) // 后左服务带环圈（填满 14:19 反馈的空地）
  // 后右虚线走线：15:51/16:06 用户要求去掉虚线（闪烁发白），不还原
  route([[2.8, 5.0], [2.8, -2.2], [9.2, -2.2], [9.2, -1.2]])   // 充电区右侧 → 配电室前（x 让开加长车棚）
  route([[-3.1, 0.35], [1.1, 0.35], [1.1, 4.05], [-3.1, 4.05]], true) // 告警车位外圈
  route([[-4.5, 5.2], [-4.5, 4.2]])                           // 信息亭支线
}

function bindEvents() {
  window.addEventListener('resize', onResize)
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  freeControls.addEventListener('lock', () => (mode.value = 'free'))
  freeControls.addEventListener('unlock', () => (mode.value = 'orbit'))
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
  } else {
    controls.update()
  }

  // 告警脉冲
  if (alertPool) {
    const t = clock.elapsedTime
    const s = 0.5 + 0.5 * Math.sin(t * 3.2)
    alertDisc.material.opacity = 0.14 + 0.12 * s
    alertPool.scale.setScalar(1 + 0.04 * s)
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
</style>

<style>
/* CSS2D 区域标签：圆点与文字各自独立 CSS2DObject（renderer 的 transform 自带居中），
   引线是场景里的 3D 线段，见 addZoneLabel */
.zone-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: #fff; box-shadow: 0 0 6px rgba(255, 255, 255, 0.9);
}
.zone-text {
  font-size: 13px; letter-spacing: 3px; color: #fff;
  white-space: nowrap;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9);
}

</style>
