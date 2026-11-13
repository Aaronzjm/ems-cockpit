import fs from 'node:fs'
import path from 'node:path'

const dir = 'D:/1zjm/agent/ems-cockpit/public/models'

function readGlb(file) {
  const buf = fs.readFileSync(file)
  const jsonLen = buf.readUInt32LE(12)
  const json = JSON.parse(buf.subarray(20, 20 + jsonLen).toString('utf8'))
  // BIN chunk
  let off = 20 + jsonLen
  const binLen = buf.readUInt32LE(off)
  const bin = buf.subarray(off + 8, off + 8 + binLen)
  return { json, bin }
}

function accMinMax(json, idx) {
  const a = json.accessors[idx]
  return { min: a.min, max: a.max }
}

for (const f of ['transformer_substation.glb', 'storage_container.glb']) {
  const { json } = readGlb(path.join(dir, f))
  console.log('\n=== ' + f + ' ===')
  console.log('materials: ' + (json.materials || []).map(m => m.name).join(', '))
  const nodeById = (json.nodes || [])
  ;(json.meshes || []).forEach((mesh, mi) => {
    mesh.primitives.forEach((p) => {
      const matName = p.material !== undefined ? json.materials[p.material].name : '(none)'
      const posAcc = p.attributes.POSITION
      const b = accMinMax(json, posAcc)
      const size = b.min && b.max ? b.max.map((v, i) => +(v - b.min[i]).toFixed(2)) : null
      console.log(`  mesh[${mi}] "${mesh.name}" -> mat=${matName} localSize=${JSON.stringify(size)}`)
    })
  })
  // node transforms
  console.log('nodes:')
  ;(json.nodes || []).forEach((n, i) => {
    if (n.mesh !== undefined || n.name?.includes('glow') || n.name?.includes('base')) {
      console.log(`  [${i}] ${n.name} mesh=${n.mesh ?? '-'} t=${JSON.stringify(n.translation || [0,0,0])} s=${JSON.stringify(n.scale || [1,1,1])}`)
    }
  })
  // overall bbox from scene
  const scene = json.scenes[json.scene ?? 0]
  console.log('scene roots: ' + scene.nodes.map(i => json.nodes[i].name).join(', '))
}
