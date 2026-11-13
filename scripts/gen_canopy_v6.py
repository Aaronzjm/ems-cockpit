# -*- coding: utf-8 -*-
"""只重建 photovoltaic_canopy.glb（v6：3 车位宽棚，车与车之间留空档）

复用 gen_all_models_v4.py 工具函数（exec 加载、砍掉末尾全量构建）。

v6 变化（对齐 ground v5 的 3 个车位：中心 x=-9.3/-6.0/-2.7，间距 3.3m）：
  - 顶棚 11.0m × 5.6m，SceneView 摆到世界 (-6.0, 0, +3.5) → 覆盖 x∈[-11.5,-0.5]
  - 立柱 4 列 × 2 排：列在车位分界/外侧（世界 x=-10.9/-7.65/-4.35/-1.1），
    排在世界 z=1.1/5.9；车(含后视镜±1.0m)与立柱最小间隙 0.31m
  - 光伏板 3 排 × 5 列；part 命名沿用（爆炸规则不变）
"""
import pathlib

SRC = pathlib.Path(r"D:\1zjm\agent\ems-cockpit\scripts\gen_all_models_v4.py")
src = SRC.read_text(encoding="utf-8")
cut = src.rindex("\nbuild_ground()")
src = src[:cut]

g = {"__name__": "v4lib"}
exec(compile(src, str(SRC), "exec"), g)

reset = g["reset"]
palette = g["palette"]
root = g["root"]
box = g["box"]
cyl = g["cyl"]
ring = g["ring"]
base_outline = g["base_outline"]
export = g["export"]


def build_canopy_v6():
    reset()
    P = palette()
    rt = root("Canopy_Root")

    # —— 立柱：4 列 × 2 排（世界 x = -6.0 + col_x；世界 z = 3.5 - row_y）——
    col_x = [-4.9, -1.65, 1.65, 4.9]
    row_y = [2.4, -2.4]
    i = 0
    for y in row_y:
        for x in col_x:
            cyl("part_pillar_%d" % i, (x, y, 1.55), 0.16, 3.1, P['dark'], rt, verts=16)
            ring("part_pillar_ring_%d" % i, (x, y, 0.06), 0.40, 0.055, P['body'], rt)
            i += 1

    # —— 主梁顶棚 ——
    box("part_beam", (0.0, 0.0, 3.16), (11.0, 5.6, 0.14), P['body'], rt)
    for i, y in enumerate([-2.8, 2.8]):
        box("part_beam_glow_%d" % i, (0.0, y, 3.24), (11.0, 0.035, 0.035), P['dark'], rt)

    # —— 光伏板 3 排 × 5 列 ——
    for r in range(3):
        for c in range(5):
            px = (c - 2) * 2.2
            py = (r - 1) * 1.86
            box("part_panel_%d_%d" % (r, c), (px, py, 3.30), (2.12, 1.76, 0.06), P['panel'], rt)
            box("part_panel_edge_%d_%d" % (r, c), (px, py, 3.36), (2.14, 0.05, 0.02), P['dark'], rt)

    # —— 线槽 ——
    box("part_trunk", (0.0, 0.0, 3.02), (0.16, 4.4, 0.10), P['dark'], rt)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 11.0, 5.6, P['gg'], rt, y=0.045)

    export("photovoltaic_canopy.glb")


build_canopy_v6()
print("DONE canopy v6")
