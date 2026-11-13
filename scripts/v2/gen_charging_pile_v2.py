# -*- coding: utf-8 -*-
"""v2 白色快充桩 charging_pile_v2.glb（参考图：细白桩身 + 顶部绿光帽）

屏幕/枪座朝向本地 +y（= 世界 -Z，对着车头方向）。
发光只有顶部绿光帽 + 底部细描边（thin 截面，过审计）。
"""
import pathlib, os

SRC = pathlib.Path(r"D:\1zjm\agent\ems-cockpit\scripts\gen_all_models_v4.py")
src = SRC.read_text(encoding="utf-8")
cut = src.rindex("\nbuild_ground()")
g = {"__name__": "v4lib"}
exec(compile(src[:cut], str(SRC), "exec"), g)
g["OUT"] = r"D:\1zjm\agent\ems-cockpit\public\models-v2"
os.makedirs(g["OUT"], exist_ok=True)

reset = g["reset"]; palette = g["palette"]; M = g["M"]; root = g["root"]
box = g["box"]; export = g["export"]


def build():
    reset()
    P = palette()
    P['white'] = M("PileWhite", (0.62, 0.66, 0.70, 1.0), 0.40, 0.20)
    rt = root("PileV2_Root")

    # 底座 + 细描边
    box("part_base", (0.0, 0.0, 0.05), (0.42, 0.32, 0.10), P['dark'], rt)
    box("part_base_outline_x0", (0.0, -0.16, 0.11), (0.42, 0.04, 0.02), P['gg'], rt)
    box("part_base_outline_x1", (0.0, 0.16, 0.11), (0.42, 0.04, 0.02), P['gg'], rt)
    box("part_base_outline_z0", (-0.21, 0.0, 0.11), (0.04, 0.32, 0.02), P['gg'], rt)
    box("part_base_outline_z1", (0.21, 0.0, 0.11), (0.04, 0.32, 0.02), P['gg'], rt)

    # 白色桩身 + 顶帽 + 绿光帽
    box("part_column", (0.0, 0.0, 0.85), (0.26, 0.18, 1.55), P['white'], rt)
    box("part_cap", (0.0, 0.0, 1.68), (0.30, 0.22, 0.10), P['white'], rt)
    box("part_cap_glow", (0.0, 0.0, 1.75), (0.26, 0.20, 0.04), P['gg'], rt)

    # 屏幕（朝 +y = 世界 -Z = 车侧）
    box("part_screen", (0.0, 0.10, 1.15), (0.18, 0.02, 0.35), P['scr'], rt)

    # 两侧枪座 + 枪 + 垂线
    for i, sx in enumerate([-1, 1]):
        box("part_holster_%d" % i, (sx * 0.17, -0.06, 1.00), (0.08, 0.10, 0.30), P['dark'], rt)
        box("part_gun_%d" % i, (sx * 0.17, -0.10, 1.15), (0.06, 0.08, 0.22), P['body'], rt)
        box("part_cable_%d" % i, (sx * 0.17, -0.12, 0.65), (0.03, 0.03, 0.55), P['dark'], rt)

    export("charging_pile_v2.glb")


build()
print("DONE charging_pile_v2")
