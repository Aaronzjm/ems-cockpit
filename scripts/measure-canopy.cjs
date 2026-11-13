const fs = require('fs');
const path = require('path');
const { GLTFLoader } = require('three/examples/jsm/loaders/GLTFLoader.js');
const { Box3, Vector3 } = require('three');

const MODELS_DIR = path.join(__dirname, '../public/models');
const loader = new GLTFLoader();

function loadGLB(filepath) {
  return new Promise((resolve, reject) => {
    const buf = fs.readFileSync(filepath);
    loader.parse(buf, '', resolve, reject);
  });
}

async function main() {
  const canopyGltf = await loadGLB(path.join(MODELS_DIR, 'photovoltaic_canopy.glb'));
  const carGltf = await loadGLB(path.join(MODELS_DIR, 'vehicle.glb'));
  const pileGltf = await loadGLB(path.join(MODELS_DIR, 'charging_pile.glb'));
  
  // 整体雨棚尺寸
  const canopyBox = new Box3().setFromObject(canopyGltf.scene);
  const canopySize = canopyBox.getSize(new Vector3());
  const canopyCenter = canopyBox.getCenter(new Vector3());
  console.log(`📐 光伏雨棚整体尺寸: X=${canopySize.x.toFixed(2)}m Z=${canopySize.z.toFixed(2)}m Y=${canopySize.y.toFixed(2)}m`);
  console.log(`📍 雨棚覆盖范围（原点为中心）: X[${canopyBox.min.x.toFixed(2)}, ${canopyBox.max.x.toFixed(2)}] Z[${canopyBox.min.z.toFixed(2)}, ${canopyBox.max.z.toFixed(2)}]`);
  
  // 找所有立柱（柱子）的位置
  console.log(`\n🚧 雨棚立柱位置（局部坐标）:`);
  const pillars = [];
  canopyGltf.scene.traverse(obj => {
    if (obj.isMesh && /pillar|post|column|leg/i.test(obj.name)) {
      const box = new Box3().setFromObject(obj);
      const center = box.getCenter(new Vector3());
      const size = box.getSize(new Vector3());
      pillars.push({ name: obj.name, x: center.x, z: center.z, size });
      console.log(`- ${obj.name}: X=${center.x.toFixed(2)} Z=${center.z.toFixed(2)} 尺寸=${size.x.toFixed(2)}x${size.z.toFixed(2)}`);
    }
  });
  
  // 车尺寸
  const carBox = new Box3().setFromObject(carGltf.scene);
  const carSize = carBox.getSize(new Vector3());
  console.log(`\n🚗 车辆尺寸: X=${carSize.x.toFixed(2)}m Z=${carSize.z.toFixed(2)}m`);
  
  // 充电桩尺寸
  const pileBox = new Box3().setFromObject(pileGltf.scene);
  const pileSize = pileBox.getSize(new Vector3());
  console.log(`🔌 充电桩尺寸: X=${pileSize.x.toFixed(2)}m Z=${pileSize.z.toFixed(2)}m`);
  
  // 计算可放车位的位置（避开立柱）
  console.log(`\n✅ 推荐车位X坐标（间隔2.5m，避开立柱，完全在棚内）:`);
  const slotPositions = [];
  const startX = canopyBox.min.x + pileSize.x/2 + 0.5;
  for (let x = startX; x < canopyBox.max.x - pileSize.x/2 - 0.5; x += 2.5) {
    // 检查是否和立柱碰撞
    let valid = true;
    for (const p of pillars) {
      if (Math.abs(x - p.x) < 1.0) { // 留1米安全距离
        valid = false;
        break;
      }
    }
    if (valid && slotPositions.length <4) slotPositions.push(x);
  }
  console.log(slotPositions.map(x => x.toFixed(2)).join(', '));
  
  // 推荐充电桩Z位置（在棚内前端，不超出棚）
  const pileZ = canopyBox.max.z - pileSize.z/2 - 0.3;
  console.log(`\n🔌 推荐充电桩Z坐标（棚内前端）: ${pileZ.toFixed(2)}`);
  // 推荐车Z位置（在桩后方，棚内中间）
  const carZ = (canopyBox.min.z + pileZ - carSize.z/2)/2;
  console.log(`🚗 推荐车辆Z坐标（桩后棚内中间）: ${carZ.toFixed(2)}`);
  // 推荐雨棚整体放置位置（让整个停车区在底座合理位置，不越界）
  const canopyWorldX = -7.0;
  const canopyWorldZ = -8.0 + canopySize.z/2;
  console.log(`\n🌍 推荐雨棚世界坐标: X=${canopyWorldX.toFixed(2)} Z=${canopyWorldZ.toFixed(2)} (完全落在底座内)`);
  console.log(`   对应桩世界Z: ${(canopyWorldZ + pileZ).toFixed(2)}`);
  console.log(`   对应车世界Z: ${(canopyWorldZ + carZ).toFixed(2)}`);
}

main().catch(console.error);
