# -*- coding: utf-8 -*-
"""v2 信息柱 info_totem.glb（参考图左缘的瘦高信息终端）

屏幕朝本地 -y（= 世界 +Z，对着主相机方向）。
发光：顶部薄绿光盖 + 小 logo 条（thin 截面）。
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
box = g["box"]; export = g["export"]


def build():
    reset()
    P = palette()
    rt = root("TotemV2_Root")

    box("part_base", (0.0, 0.0, 0.05), (0.50, 0.36, 0.10), P['dark'], rt)
    box("part_body", (0.0, 0.0, 1.10), (0.44, 0.30, 2.00), P['body'], rt)
    box("part_screen", (0.0, -0.16, 1.20), (0.34, 0.02, 1.30), P['scr'], rt)
    box("part_logo", (0.0, -0.16, 0.45), (0.30, 0.02, 0.12), P['gg'], rt)
    box("part_cap_glow", (0.0, 0.0, 2.14), (0.46, 0.32, 0.04), P['gg'], rt)

    export("info_totem.glb")


build()
print("DONE info_totem v2")
