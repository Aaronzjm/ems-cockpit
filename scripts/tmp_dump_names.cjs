const fs = require('fs')
for (const f of process.argv.slice(2)) {
  const b = fs.readFileSync(f)
  let off = 12, json = null
  while (off < b.length) {
    const len = b.readUInt32LE(off + 8)
    const type = b.toString('ascii', off + 4, off + 8)
    if (type === 'JSON') { json = JSON.parse(b.slice(off + 12, off + 12 + len).toString()); break }
    off += 12 + len
  }
  const dash = json.nodes.filter(n => /dash/.test(n.name || ''))
  const sample = json.nodes.filter(n => /brk_charge_11_a|slot_0_f|zebra_0|part_plat$/.test(n.name || ''))
    .map(n => `${n.name} y=${n.translation ? n.translation[1].toFixed(3) : '-'}`)
  console.log(f, '| dash nodes:', dash.length, '|', sample.join(', '), '| total nodes:', json.nodes.length)
}
