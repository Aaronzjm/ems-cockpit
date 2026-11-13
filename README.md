# 光储充一体化 EMS 驾驶舱

基于 **Vue 3 + Three.js** 的光储充一体化能源管理系统（EMS）3D 可视化驾驶舱，支持设备拆解式展开、自由漫游与实时数据看板。同时内置汽车制造车间「四大工艺」3D 复现场景。

## 项目亮点

- 🏭 **光储充一体化园区**：光伏区、智能快充桩、储能电池舱、配电变压器、配电室五类设备全景呈现
- 💥 **设备拆解式展开**：点击设备触发爆炸视图，每个零件按定制方向/距离/时序逐层拆解（纯平移动画）
- 🔍 **单设备透视模式**：配电室可进入独立视角，四面墙、幕墙、大屏、操作台、座椅逐层拉开查看内部
- 🚗 **汽车制造车间**：冲压 → 焊装 → 涂装 → 总装四大工艺流程 3D 复现，产线循环走位动画
- 🖥️ **科技风 HUD 界面**：设备清单、实时数据看板（功率/SOC/负载）、告警记录、霓虹辉光特效
- 🎮 **双操作模式**：环绕漫游（OrbitControls）+ 第一人称自由漫游（WASD 行走）

## 技术栈

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端框架 | Vue 3 | ^3.5 | `<script setup>` 组合式 API |
| 3D 引擎 | Three.js | ^0.186 | 场景渲染、GLB 加载、后期特效 |
| 动画 | GSAP | ^3.15 | 设备拆解补间、镜头飞行 |
| 构建工具 | Vite | ^8.3 | 开发服务器、生产构建 |
| 样式 | Sass | ^1.105 | 预处理样式 |
| 模型生成 | Blender Python | 5.2 | 用 bpy 脚本程序化生成 GLB 模型 |

### Three.js 高级特性

- `EffectComposer` + `UnrealBloomPass` 霓虹辉光后期
- `CSS2DRenderer` 设备悬浮标签
- `ACESFilmicToneMapping` 电影级色调映射
- `PointerLockControls` 第一人称漫游
- `Raycaster` 设备拾取与高亮

## 环境要求

| 项目 | 要求 |
|------|------|
| Node.js | **18 及以上**（推荐 20 / 22） |
| 包管理器 | pnpm（推荐，锁文件为 `pnpm-lock.yaml`）/ npm / yarn |
| 浏览器 | Chrome / Edge 110+（需 WebGL2 支持） |
| 显卡 | 建议独立显卡，核显可运行但帧率较低 |

> ⚠️ Vite 8 要求 Node.js 18+。若使用 npm，请先删除 `pnpm-lock.yaml` 再执行 `npm install` 以生成对应锁文件。

## 安装与运行

### 1. 克隆项目

```bash
git clone https://github.com/Aaronzjm/ems-cockpit.git
cd ems-cockpit
```

### 2. 安装依赖

```bash
# 推荐 pnpm
pnpm install

# 或 npm
npm install
```

### 3. 启动开发服务器

```bash
pnpm dev
```

启动后浏览器访问 **http://127.0.0.1:5179/**

> 开发服务器端口配置在 `vite.config.js` 中（默认 `5179`）。

### 4. 生产构建

```bash
pnpm build      # 输出到 dist/
pnpm preview    # 本地预览构建产物
```

## 场景切换

项目包含三个独立 3D 场景，通过 URL 参数 `?scene=` 切换：

| 场景 | 地址 | 说明 |
|------|------|------|
| 光储充 EMS 驾驶舱 | `/`（默认） | 主场景，设备拆解 + 数据看板 |
| 参考图复现 | `/?scene=v2` | 光储充园区参考图复现（模型集 models-v2） |
| 汽车制造车间 | `/?scene=car` | 四大工艺 3D 复现（模型集 models-car） |

## 操作指南

| 操作 | 说明 |
|------|------|
| 左键拖拽 | 旋转视角（环绕模式） |
| 滚轮 | 缩放 |
| 点击设备 | 拆解式展开 / 复原 |
| 点击「配电室」 | 进入单设备透视模式 |
| 按 `F` | 切换第一人称自由漫游 |
| `W/A/S/D` | 自由漫游移动 |
| `Shift` | 冲刺（加速） |
| `Esc` | 退出自由漫游 |

## 项目结构

```
.
├── src/
│   ├── App.vue                    # 场景路由（?scene= 参数切换）
│   ├── main.js                    # 入口
│   ├── components/
│   │   ├── SceneView.vue          # 主场景：光储充 EMS 驾驶舱
│   │   ├── SceneViewV2.vue        # 参考图复现场景
│   │   └── SceneViewCar.vue       # 汽车制造车间场景
│   └── three/
│       └── ExplodeController.js   # 设备拆解展开控制器 + 模型加载器
├── public/
│   ├── models/                    # 主场景 GLB 模型
│   ├── models-v2/                 # 参考图复现模型
│   └── models-car/                # 汽车车间模型
├── scripts/                       # Blender 建模脚本（程序化生成 GLB）
│   ├── gen_*.py                   # 主场景模型生成
│   ├── v2/                        # 参考图复现模型生成
│   └── car/                       # 汽车车间模型生成
├── index.html
├── vite.config.js
└── package.json
```

## 模型说明

所有 GLB 模型均由 **Blender Python 脚本**（`scripts/` 目录）程序化生成，非手工建模：

- 模型文件体积小（最大约 750KB），加载快
- 每个零件按命名规则（`part_*`）组织，供拆解动画精确控制
- 如需重新生成模型：在 Blender 5.2 中打开对应 `gen_*.py` 脚本运行即可

## 常见问题

| 问题 | 处理 |
|------|------|
| `pnpm` 命令不存在 | 先安装 pnpm：`npm i -g pnpm` |
| 启动报 Node 版本错误 | 升级 Node.js 到 18+ |
| 白屏/黑屏 | 确认浏览器支持 WebGL2，更新显卡驱动 |
| 帧率低 | 降低浏览器窗口分辨率，或关闭浏览器硬件加速后重试 |
| 构建产物过大警告 | 正常提示（Three.js 打包体积大），可忽略 |

## 说明

- 当前数据为**前端模拟数据**（功率、SOC、负载、告警等写死在 `SceneView.vue` 中），尚未接入真实后端。如需对接真实 EMS 数据，可替换 `metrics` 与 `alerts` 为 API 请求。
- 本项目为前端可视化演示，不含后端服务。

## 许可证

[MIT](LICENSE)
