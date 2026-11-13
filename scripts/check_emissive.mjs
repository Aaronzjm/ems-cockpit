// 校验：每个 GLB 里，哪些网格带自发光（emissive 非零）
// 目的：确认储能柜等"整机发光"已消除，只剩描边/光缝发光
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const dir = 'public/models'
const files = ['storage_container.glb', 'transformer_substation.glb', 'charging_pile.glb',
  'photovoltaic_canopy.glb', 'control_room.glb', 'ground_facility.glb', 'kiosk.glb', 'vehicle.glb']

function parseGLB(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength)
  let off = 12
  let json = null
  while (off < buf.byteLength) {
    const len = dv.getUint32(off, true)
    const type = dv.getUint32(off + 4, true)
    if (type === 0x4e4f534a) json = JSON.parse(buf.slice(off + 8, off + 8 + len).toString('utf8'))
    off += 8 + len
  }
  return json
}

for (const f of files) {
  const g = parseGLB(readFileSync(join(dir, f)))
  const mats = (g.materials || []).map((m, i) => {
    const ef = m.emissiveFactor || [0, 0, 0]
    const st = m.extensions?.KHR_materials_emissive_strength?.emissiveStrength ?? 1
    return { i, name: m.name || ('mat' + i), ef, st, lit: Math.max(...ef) > 0.001 }
  })
  const litIdx = new Set(mats.filter(m => m.lit).map(m => m.i))
  const litNames = mats.filter(m => m.lit).map(m => `${m.name}(x${m.st} ef[${m.ef.map(v => v.toFixed(2))}])`)

  // 统计每个 mesh 用到的材质
  const meshMat = (g.meshes || []).map(m => m.primitives[0].material)
  const litMeshes = meshMat.filter(mi => litIdx.has(mi)).length

  console.log(`\n=== ${f} ===`)
  console.log(`  meshes=${meshMat.length} 发光网格=${litMeshes} 材质=${mats.length}`)
  console.log(`  发光材质: ${litNames.join(', ') || '(无)'}`)

  // 找"大块"发光网格：真正的块状发光 = 三个轴都不小
  // 细长描边只有两个轴大、截面很薄（min 轴 <= 0.10），不算块
  const nodeByMesh = {}
  ;(g.nodes || []).forEach(n => { if (n.mesh !== undefined) (nodeByMesh[n.mesh] ??= []).push(n) })
  const big = []
  ;(g.meshes || []).forEach((m, mi) => {
    if (!litIdx.has(m.primitives[0].material)) return
    const scales = (nodeByMesh[mi] || []).map(n => n.scale || [1, 1, 1])
    for (const s of scales) {
      const minAxis = Math.min(...s)
      const maxAxis = Math.max(...s)
      if (minAxis > 0.5 && maxAxis > 1.2) big.push(`${m.name || 'mesh' + mi} scale[${s.map(v => v.toFixed(2))}]`)
    }
  })
  if (big.length) console.log(`  ⚠️ 块状发光网格: ${big.join('; ')}`)
  else console.log(`  ✅ 无块状发光（只有薄截面描边，截面 <= 0.10）`)
}
