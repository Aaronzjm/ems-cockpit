const fs = require('fs');
const path = require('path');
const dir = path.join(__dirname, '../public/models');
const files = ['storage_container','charging_pile','control_room','photovoltaic_canopy','kiosk','transformer_substation','vehicle','ground_facility'];
for (const f of files) {
  const buf = fs.readFileSync(path.join(dir, f + '.glb'));
  let o = 12, json = null;
  while (o < buf.length) {
    const l = buf.readUInt32LE(o), t = buf.readUInt32LE(o+4);
    if (t === 0x4e4f534a) { json = JSON.parse(buf.slice(o+8, o+8+l).toString()); break; }
    o += 8 + l;
  }
  if (!json) { console.log(f + ': no json'); continue; }
  const meshes = json.meshes || [];
  const nodes = json.nodes || [];
  // list mesh names via node lookup
  const names = [];
  nodes.forEach(n => { if (n.mesh !== undefined) names.push(n.name || 'mesh' + n.mesh); });
  console.log('\n=== ' + f + ' (' + meshes.length + ' meshes, ' + names.length + ' named nodes) ===');
  console.log(names.filter(n => n.startsWith('part_')).slice(0, 40).join(', '));
}
