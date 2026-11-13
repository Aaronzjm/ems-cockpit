const fs = require('fs');
const path = require('path');
const buf = fs.readFileSync(path.join(__dirname, '../public/models/control_room.glb'));
let o = 12, json = null;
while (o < buf.length) {
  const l = buf.readUInt32LE(o), t = buf.readUInt32LE(o+4);
  if (t === 0x4e4f534a) { json = JSON.parse(buf.slice(o+8, o+8+l).toString()); break; }
  o += 8 + l;
}
console.log('=== materials ===');
(json.materials||[]).forEach(m => {
  const p = m.pbrMetallicRoughness || {};
  const bc = (p.baseColorFactor||[]).map(v=>v.toFixed(3)).join(',');
  const em = (m.emissiveFactor||[]).map(v=>v.toFixed(2)).join(',');
  console.log(`  ${m.name}: base=[${bc}] rough=${p.roughnessFactor} metal=${p.metallicFactor} emissive=[${em}] ext=${JSON.stringify(m.extensions||{})}`);
});
console.log('\n=== node local translations (part_wall / part_rim / part_mullion) ===');
const nodes = json.nodes || [];
nodes.forEach(n => {
  if (/part_wall|part_rim|part_mullion|part_lintel|part_bigscreen/.test(n.name||'')) {
    console.log(`  ${n.name}: T=[${(n.translation||[0,0,0]).map(v=>v.toFixed(2)).join(', ')}]`);
  }
});
