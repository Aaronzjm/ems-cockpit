import fs from 'node:fs'
import path from 'node:path'

const dir = 'D:/1zjm/agent/ems-cockpit/public/models'

function readGlbJson(file) {
  const buf = fs.readFileSync(file)
  const magic = buf.readUInt32LE(0)
  if (magic !== 0x46546c67) throw new Error('not glb: ' + file)
  const jsonLen = buf.readUInt32LE(12)
  const jsonType = buf.readUInt32LE(16)
  if (jsonType !== 0x4e4f534a) throw new Error('first chunk not JSON')
  return JSON.parse(buf.subarray(20, 20 + jsonLen).toString('utf8'))
}

for (const f of ['charging_pile.glb', 'photovoltaic_canopy.glb', 'storage_container.glb', 'transformer_substation.glb', 'ground_facility.glb']) {
  const p = path.join(dir, f)
  const g = readGlbJson(p)
  console.log('\n=== ' + f + ' ===')
  ;(g.materials || []).forEach((m, i) => {
    const pbr = m.pbrMetallicRoughness || {}
    const bc = (pbr.baseColorFactor || [1, 1, 1, 1]).map(v => +v.toFixed(3))
    const ef = (m.emissiveFactor || [0, 0, 0]).map(v => +v.toFixed(3))
    const es = m.extensions?.KHR_materials_emissive_strength?.emissiveStrength
    console.log(
      `  [${i}] ${m.name || '(unnamed)'} base=[${bc}] metal=${pbr.metallicFactor ?? 1} rough=${pbr.roughnessFactor ?? 1} emissive=[${ef}]${es ? ' strength=' + es : ''}`
    )
  })
  // which meshes use which material
  const meshes = g.meshes || []
  console.log('  meshes: ' + meshes.length)
}
