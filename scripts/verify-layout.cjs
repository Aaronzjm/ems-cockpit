const fs = require('fs');
const path = require('path');
const { GLTFLoader } = require('three/examples/jsm/loaders/GLTFLoader.js');
const { Box3, Vector3, Group } = require('three');

const MODELS_DIR = path.join(__dirname, '../public/models');
const loader = new GLTFLoader();

// 布局配置（和SceneView.vue里完全一致）
const LAYOUT = {
  ground: { pos: [0,0,0], rot: 0 },
  canopy: { pos: [-6.6, 0, -2.6], rot: 0 },
  storage: { pos: [3.2, 0, -5.2], rot: 0 },
  transformer: { pos: [8.4, 0, -6.6], rot: 0 },
  controlroom: { pos: [8.8, 0, 1.2], rot: -Math.PI/2 },
};
const SLOT_X = [-9.3, -6.75, -4.2, -1.65];
const CARS = [
  { pos: [SLOT_X[0], 0, -4.1] },
  { pos: [SLOT_X[1] + 0.6, 0, -4.1] }, // 第二辆右移0.6米躲柱子
];
const CHARGING_POS = SLOT_X.map(x => ({ pos: [x,0,-1.05] }));

function loadGLB(filepath) {
  return new Promise((resolve, reject) => {
    const buf = fs.readFileSync(filepath);
    loader.parse(buf, '', resolve, reject);
  });
}

async function main() {
  console.log('🔍 开始验证布局...\n');
  const boxes = {};

  // 加载所有模型
  for (const name of ['ground_facility', 'photovoltaic_canopy', 'charging_pile', 'storage_container', 'transformer_substation', 'control_room', 'vehicle']) {
    const gltf = await loadGLB(path.join(MODELS_DIR, `${name}.glb`));
    boxes[name] = new Box3().setFromObject(gltf.scene);
    const size = boxes[name].getSize(new Vector3());
    console.log(`✅ 加载 ${name}: 尺寸 ${size.x.toFixed(2)}x${size.y.toFixed(2)}x${size.z.toFixed(2)}m`);
  }

  // 计算底座世界坐标
  const groundBox = boxes['ground_facility'].clone();
  groundBox.translate(new Vector3(...LAYOUT.ground.pos));
  console.log(`\n📏 底座范围: X[${groundBox.min.x.toFixed(2)}, ${groundBox.max.x.toFixed(2)}] Z[${groundBox.min.z.toFixed(2)}, ${groundBox.max.z.toFixed(2)}]`);

  const errors = [];
  const deviceBoxes = [];

  // 检查固定设备
  const deviceMap = {
    canopy: 'photovoltaic_canopy',
    storage: 'storage_container',
    transformer: 'transformer_substation',
    controlroom: 'control_room',
  };
  for (const [key, modelName] of Object.entries(deviceMap)) {
    const box = boxes[modelName].clone();
    const [x,y,z] = LAYOUT[key].pos;
    box.translate(new Vector3(x,y,z));
    // 配电室有旋转，旋转后的box要重新计算
    if (LAYOUT[key].rot) {
      const group = new Group();
      const obj = new Group();
      obj.add(...boxes[modelName]);
      obj.rotation.y = LAYOUT[key].rot;
      group.add(obj);
      group.position.set(x,y,z);
      box.setFromObject(group);
    }
    deviceBoxes.push({ key, box });

    // 检查越界
    if (box.min.x < groundBox.min.x - 0.1 || box.max.x > groundBox.max.x + 0.1 ||
        box.min.z < groundBox.min.z - 0.1 || box.max.z > groundBox.max.z + 0.1) {
      errors.push(`❌ ${key} 超出底座范围: X[${box.min.x.toFixed(2)},${box.max.x.toFixed(2)}] Z[${box.min.z.toFixed(2)},${box.max.z.toFixed(2)}]`);
    }
  }

  // 检查充电桩
  for (let i = 0; i < CHARGING_POS.length; i++) {
    const box = boxes['charging_pile'].clone();
    const [x,y,z] = CHARGING_POS[i].pos;
    box.translate(new Vector3(x,y,z));
    deviceBoxes.push({ key: `charging_${i}`, box });
  }

  // 检查车辆
  for (let i = 0; i < CARS.length; i++) {
    const box = boxes['vehicle'].clone();
    const [x,y,z] = CARS[i].pos;
    box.translate(new Vector3(x,y,z));
    deviceBoxes.push({ key: `car_${i}`, box });
  }

  // 检查所有设备两两重合
  for (let i = 0; i < deviceBoxes.length; i++) {
    for (let j = i+1; j < deviceBoxes.length; j++) {
      const a = deviceBoxes[i];
      const b = deviceBoxes[j];
      if (a.box.intersectsBox(b.box)) {
        errors.push(`❌ ${a.key} 和 ${b.key} 重合!`);
      }
    }
  }

  console.log('\n' + '='.repeat(50));
  if (errors.length === 0) {
    console.log('✅ 布局验证通过! 所有设备都在底座内，无重合');
    // 打印车辆位置
    console.log(`\n🚗 车辆位置:
  第一辆车: X=${CARS[0].pos[0]} (充电桩正前方，无碰撞)
  第二辆车: X=${CARS[1].pos[0].toFixed(2)} (右移0.6米，躲开雨棚柱子)
`);
  } else {
    console.log('❌ 布局有问题:');
    errors.forEach(e => console.log(e));
    process.exit(1);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
