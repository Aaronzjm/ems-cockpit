# -*- coding: utf-8 -*-
"""只重建 photovoltaic_canopy.glb（v5：加大到覆盖 4 个画线车位）

复用 gen_all_models_v4.py 里的工具函数（exec 加载、砍掉末尾全量构建调用，
避免用旧配电室覆盖 v5 的 control_room.glb）。

v5 变化（对齐底座 part_slot_* 画线车位，世界 x∈[-10.45,-0.5]、z∈[+1.4,+6.4]）：
  - 顶棚 11.4m × 5.6m（原 7.4 × 4.2），SceneView 里摆到世界 (-5.6, 0, +3.5)
  - 立柱 5 列 × 2 排：列在车位分界处（世界 x = -10.85/-8.025/-5.475/-2.925/-0.35），
    排在世界 z = 1.1 / 5.9，不挡车、不压桩
  - 光伏板 3 排 × 5 列，命名沿用 part_panel_r_c / part_panel_edge_r_c（爆炸规则不变）
  - part_beam / part_beam_glow_* / part_trunk / part_base_outline_* 命名不变
"""
import pathlib

SRC = pathlib.Path(r"D:\1zjm\agent\ems-cockpit\scripts\gen_all_models_v4.py")
src = SRC.read_text(encoding="utf-8")
# 砍掉文件末尾的全量构建调用，只取工具函数
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


def build_canopy_v5():
    reset()
    P = palette()
    rt = root("Canopy_Root")

    # —— 立柱：5 列 × 2 排（列在车位分界处，避免压到车位线和车）——
    col_x = [-5.25, -2.425, 0.125, 2.675, 5.25]   # 世界 x = -5.6 + col_x
    row_y = [2.4, -2.4]                            # 世界 z = 3.5 - row_y → 1.1 / 5.9
    i = 0
    for y in row_y:
        for x in col_x:
            cyl("part_pillar_%d" % i, (x, y, 1.55), 0.16, 3.1, P['dark'], rt, verts=16)
            ring("part_pillar_ring_%d" % i, (x, y, 0.06), 0.40, 0.055, P['body'], rt)
            i += 1

    # —— 主梁顶棚 ——
    box("part_beam", (0.0, 0.0, 3.16), (11.4, 5.6, 0.14), P['body'], rt)
    for i, y in enumerate([-2.8, 2.8]):
        # 檐口线脚：正常深色（非发光）
        box("part_beam_glow_%d" % i, (0.0, y, 3.24), (11.4, 0.035, 0.035), P['dark'], rt)

    # —— 光伏板 3 排 × 5 列 ——
    for r in range(3):
        for c in range(5):
            px = (c - 2) * 2.24
            py = (r - 1) * 1.86
            box("part_panel_%d_%d" % (r, c), (px, py, 3.30), (2.12, 1.76, 0.06), P['panel'], rt)
            # 组件边框：正常深色
            box("part_panel_edge_%d_%d" % (r, c), (px, py, 3.36), (2.14, 0.05, 0.02), P['dark'], rt)

    # —— 线槽（沿中间立柱列走）——
    box("part_trunk", (0.125, 0.0, 3.02), (0.16, 4.4, 0.10), P['dark'], rt)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 11.4, 5.6, P['gg'], rt, y=0.045)

    export("photovoltaic_canopy.glb")


build_canopy_v5()
print("DONE canopy v5")
