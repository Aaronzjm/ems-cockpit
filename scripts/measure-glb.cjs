// 解析 GLB 的 JSON chunk，用节点变换 + accessor 的 POSITION min/max 计算每个节点的真实包围盒
const fs = require('fs');
const path = require('path');

const MODELS = path.join(__dirname, '..', 'public', 'models');

function readGlbJson(file) {
  const buf = fs.readFileSync(file);
  let offset = 12;
  let json = null;
  while (offset + 8 <= buf.length) {
    const chunkLen = buf.readUInt32LE(offset);
    const chunkType = buf.readUInt32LE(offset + 4);
    if (chunkType === 0x4e4f534a) json = JSON.parse(buf.slice(offset + 8, offset + 8 + chunkLen).toString('utf8'));
    offset += 8 + chunkLen;
  }
  if (!json) throw new Error('no JSON chunk in ' + file);
  return json;
}

function matFromNode(n) {
  if (n.matrix) return n.matrix.slice();
  const t = n.translation || [0, 0, 0];
  const r = n.rotation || [0, 0, 0];
  const s = n.scale || [1, 1, 1];
  const [x, y, z] = r;
  const w = r[3] === undefined ? 1 : r[3];
  const x2 = x + x, y2 = y + y, z2 = z + z;
  const xx = x * x2, xy = x * y2, xz = x * z2;
  const yy = y * y2, yz = y * z2, zz = z * z2;
  const wx = w * x2, wy = w * y2, wz = w * z2;
  const m = new Array(16).fill(0);
  m[0] = (1 - (yy + zz)) * s[0]; m[1] = (xy + wz) * s[0]; m[2] = (xz - wy) * s[0];
  m[4] = (xy - wz) * s[1]; m[5] = (1 - (xx + zz)) * s[1]; m[6] = (yz + wx) * s[1];
  m[8] = (xz + wy) * s[2]; m[9] = (yz - wx) * s[2]; m[10] = (1 - (xx + yy)) * s[2];
  m[12] = t[0]; m[13] = t[1]; m[14] = t[2]; m[15] = 1;
  return m;
}
function mul(a, b) {
  const o = new Array(16);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
    o[c * 4 + r] = a[r] * b[c * 4] + a[4 + r] * b[c * 4 + 1] + a[8 + r] * b[c * 4 + 2] + a[12 + r] * b[c * 4 + 3];
  }
  return o;
}
function xf(m, p) {
  const [x, y, z] = p;
  return [
    m[0] * x + m[4] * y + m[8] * z + m[12],
    m[1] * x + m[5] * y + m[9] * z + m[13],
    m[2] * x + m[6] * y + m[10] * z + m[14],
  ];
}

function bounds(file) {
  const j = readGlbJson(file);
  const nodes = j.nodes || [];
  const isChild = new Set();
  nodes.forEach((n) => (n.children || []).forEach((c) => isChild.add(c)));
  const world = new Array(nodes.length);
  const out = [];
  const overall = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
  function walk(i, parent) {
    const m = mul(parent, matFromNode(nodes[i]));
    world[i] = m;
    const n = nodes[i];
    if (n.mesh != null) {
      const mesh = j.meshes[n.mesh];
      const box = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
      for (const prim of mesh.primitives) {
        const acc = j.accessors[prim.attributes.POSITION];
        if (!acc || !acc.min || !acc.max) continue;
        const [mn, mx] = [acc.min, acc.max];
        for (let cx = 0; cx < 2; cx++) for (let cy = 0; cy < 2; cy++) for (let cz = 0; cz < 2; cz++) {
          const p = xf(m, [cx ? mx[0] : mn[0], cy ? mx[1] : mn[1], cz ? mx[2] : mn[2]]);
          for (let k = 0; k < 3; k++) {
            box.min[k] = Math.min(box.min[k], p[k]);
            box.max[k] = Math.max(box.max[k], p[k]);
            overall.min[k] = Math.min(overall.min[k], p[k]);
            overall.max[k] = Math.max(overall.max[k], p[k]);
          }
        }
      }
      out.push({ name: n.name || `node${i}`, min: box.min, max: box.max });
    }
    (n.children || []).forEach((c) => walk(c, m));
  }
  const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  nodes.forEach((n, i) => { if (!isChild.has(i)) walk(i, identity); });
  return { nodes: out, overall };
}

const f2 = (a) => `[${a.map((v) => v.toFixed(2)).join(', ')}]`;

const target = process.argv[2] || 'photovoltaic_canopy';
const filter = process.argv[3] ? new RegExp(process.argv[3], 'i') : null;
const b = bounds(path.join(MODELS, target + '.glb'));
console.log(`== ${target} overall min=${f2(b.overall.min)} max=${f2(b.overall.max)}`);
for (const n of b.nodes) {
  if (filter && !filter.test(n.name)) continue;
  console.log(`${n.name.padEnd(32)} min=${f2(n.min)} max=${f2(n.max)}`);
}
