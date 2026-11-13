# -*- coding: utf-8 -*-
"""v2 长条光伏车棚 pv_canopy_v2.glb（参考图：一条长棚罩 4 车位，双排光伏板）

本地坐标居中，SceneViewV2 摆到世界 (-5.55, 0, 2.2)：
  - 立柱 5 列 × 2 排（列在车位分界/外侧，世界 x=-11.35/-8.45/-5.55/-2.65/0.25；
    排世界 z=0.5/3.9），柱底绿光环（参考图样式）
  - 主梁 12.8 × 4.0m，光伏板 2 排 × 11 列
  - 无底部大描边（本模型发光只有柱底环，符合参考图）
"""
import pathlib, os

SRC = pathlib.Path(r"D:\1zjm\agent\ems-cockpit\scripts\gen_all_models_v4.py")
src = SRC.read_text(encoding="utf-8")
cut = src.rindex("\nbuild_ground()")
g = {"__name__": "v4lib"}
exec(compile(src[:cut], str(SRC), "exec"), g)
g["OUT"] = r"D:\1zjm\agent\ems-cockpit\public\models-v2"
os.makedirs(g["OUT"], exist_ok=True)

reset = g["reset"]; palette = g["palette"]; root = g["root"]
box = g["box"]; cyl = g["cyl"]; ring = g["ring"]; export = g["export"]


def build():
    reset()
    P = palette()
    rt = root("CanopyV2_Root")

    col_x = [-5.8, -2.9, 0.0, 2.9, 5.8]  # 5 列落车位分界/外侧：世界 x=-11.35/-8.45/-5.55/-2.65/0.25（根在 -5.55）
    row_y = [1.7, -1.7]
    i = 0
    for y in row_y:
        for x in col_x:
            cyl("part_pillar_%d" % i, (x, y, 1.45), 0.15, 2.9, P['dark'], rt, verts=16)
            ring("part_pillar_ring_%d" % i, (x, y, 0.06), 0.38, 0.05, P['gg'], rt)
            i += 1

    box("part_beam", (0.0, 0.0, 2.95), (12.8, 4.0, 0.14), P['body'], rt)
    for i, y in enumerate([-2.0, 2.0]):
        box("part_beam_edge_%d" % i, (0.0, y, 3.03), (12.8, 0.035, 0.035), P['dark'], rt)

    for r in range(2):
        for c in range(11):
            px = (c - 5) * (12.8 / 11)
            py = (r - 0.5) * 1.9
            box("part_panel_%d_%d" % (r, c), (px, py, 3.10), (1.11, 1.80, 0.06), P['panel'], rt)
            box("part_panel_edge_%d_%d" % (r, c), (px, py, 3.16), (1.13, 0.05, 0.02), P['dark'], rt)

    box("part_trunk", (0.0, 0.0, 2.82), (0.15, 3.4, 0.10), P['dark'], rt)

    export("pv_canopy_v2.glb")


build()
print("DONE pv_canopy_v2")
