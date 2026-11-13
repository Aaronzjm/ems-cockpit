import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import gsap from 'gsap'

/**
 * EMS 设备"拆解式展开"控制器
 * 支持每个设备传入自定义的零件偏移规则，精确控制每个零件的展开方向/距离/时序
 * 所有零件只做纯平移，无任何旋转
 */
export class ExplodeController {
  constructor() {
    this.devices = new Map()
  }

  /**
   * @param {string} key
   * @param {THREE.Object3D} root
   * @param {number} baseGap 基准展开幅度
   * @param {(partName: string, obj: THREE.Object3D, deviceBox: THREE.Box3) => {offset: THREE.Vector3, order?: number}|null} [offsetResolver] 
   *   自定义偏移解析器：返回 {offset, order} 指定该零件的展开偏移和时序顺序；返回 null 则该零件不移动
   * @param {(obj: THREE.Object3D) => boolean} [partPredicate] 全局过滤：只让返回 true 的零件参与
   */
  register(key, root, baseGap = 0.6, offsetResolver = null, partPredicate = null) {
    root.updateWorldMatrix(true, true)

    // 收集零件
    const collected = []
    const collect = (node) => {
      node.children.forEach((child) => {
        if (child.isMesh) collected.push(child)
        else if (child.userData.explodeUnit) collected.push(child)
        else collect(child)
      })
    }
    collect(root)
    if (collected.length === 0) collected.push(root)

    const parts = partPredicate ? collected.filter(partPredicate) : collected
    const deviceBox = new THREE.Box3().setFromObject(root)

    const records = parts.map((obj) => {
      // 强制复位旋转
      const homeQuat = obj.userData.explodeUnit
        ? obj.quaternion.clone()
        : new THREE.Quaternion()
      obj.quaternion.copy(homeQuat)

      let offset = new THREE.Vector3(0, 0, 0)
      let order = 1

      // 用自定义解析器获取偏移
      if (offsetResolver) {
        const res = offsetResolver(obj.name || '', obj, deviceBox)
        if (res) {
          offset = res.offset.clone().multiplyScalar(baseGap)
          order = res.order ?? 1
        } else {
          // 解析器返回null → 该零件不动
          offset.set(0, 0, 0)
        }
      }

      return {
        obj,
        home: obj.position.clone(),
        homeQuat,
        offset,
        order,
      }
    })

    this.devices.set(key, { root, parts: records, exploded: false, tl: null, baseGap })
  }

  isExploded(key) {
    const d = this.devices.get(key)
    return !!d && d.exploded
  }

  toggle(key, { gap, duration = 0.9 } = {}) {
    const d = this.devices.get(key)
    if (!d) return false
    const g = gap ?? d.baseGap

    if (d.tl) d.tl.kill()
    const tl = gsap.timeline()
    d.tl = tl

    if (!d.exploded) {
      const ordered = [...d.parts].sort((a, b) => a.order - b.order)
      ordered.forEach((p, i) => {
        const target = p.home.clone().add(p.offset.clone().multiplyScalar(g / d.baseGap))
        tl.to(
          p.obj.position,
          { x: target.x, y: target.y, z: target.z, duration, ease: 'power2.out' },
          i * 0.04,
        )
        p.obj.quaternion.copy(p.homeQuat)
      })
      d.exploded = true
    } else {
      const ordered = [...d.parts].sort((a, b) => b.order - a.order)
      ordered.forEach((p, i) => {
        tl.to(
          p.obj.position,
          { x: p.home.x, y: p.home.y, z: p.home.z, duration: duration * 0.75, ease: 'power3.inOut' },
          i * 0.02,
        )
        tl.to(
          p.obj.quaternion,
          { x: p.homeQuat.x, y: p.homeQuat.y, z: p.homeQuat.z, w: p.homeQuat.w, duration: duration * 0.75, ease: 'power3.inOut' },
          '<',
        )
      })
      d.exploded = false
    }
    return d.exploded
  }

  restoreAll() {
    this.devices.forEach((_d, key) => { if (this.isExploded(key)) this.toggle(key) })
  }
}

export class ModelLoader {
  constructor() {
    this.loader = new GLTFLoader()
    this.cache = new Map()
  }
  load(url) {
    if (this.cache.has(url)) return this.cache.get(url)
    const p = new Promise((resolve, reject) => {
      this.loader.load(url, (gltf) => resolve(gltf), undefined, (err) => reject(err))
    })
    this.cache.set(url, p)
    return p
  }
}
