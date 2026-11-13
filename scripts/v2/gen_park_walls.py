# -*- coding: utf-8 -*-
"""v2 周界围墙 park_walls.glb（参考图：左/后/右三面深色围墙，前侧敞开）

墙高 1.6m、厚 0.25m，顶部内侧一条细绿光带（thin，过发光审计）；
四角立柱收头。世界坐标建模，场景里摆原点。
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
box = g["box"]; cyl = g["cyl"]; export = g["export"]


def build():
    reset()
    P = palette()
    P['wtrim'] = M("WallTrim", (0.05, 0.30, 0.25, 1.0), 0.4, 0.0,
                   (0.05, 0.90, 0.75, 1.0), 0.6)
    rt = root("WallsV2_Root")

    # 三面墙（前侧 python y=-8.7 / 世界 z=+8.7 敞开）
    box("part_wall_l", (-12.7, 0.0, 0.8), (0.25, 17.4, 1.6), P['wall'], rt)
    box("part_wall_r", (12.7, 0.0, 0.8), (0.25, 17.4, 1.6), P['wall'], rt)
    box("part_wall_b", (0.0, 8.7, 0.8), (25.4, 0.25, 1.6), P['wall'], rt)

    # 顶部内侧细绿光带
    box("part_trim_l", (-12.55, 0.0, 1.63), (0.05, 17.4, 0.05), P['wtrim'], rt)
    box("part_trim_r", (12.55, 0.0, 1.63), (0.05, 17.4, 0.05), P['wtrim'], rt)
    box("part_trim_b", (0.0, 8.55, 1.63), (25.4, 0.05, 0.05), P['wtrim'], rt)

    # 墙基内侧绿光踢脚线（参考图墙根绿线）
    box("part_basetrim_l", (-12.55, 0.0, 0.06), (0.04, 17.4, 0.04), P['wtrim'], rt)
    box("part_basetrim_r", (12.55, 0.0, 0.06), (0.04, 17.4, 0.04), P['wtrim'], rt)
    box("part_basetrim_b", (0.0, 8.55, 0.06), (25.4, 0.04, 0.04), P['wtrim'], rt)

    # 后墙/右墙内面暖黄竖光缝（储能区截图背景墙同款）
    P['slitw'] = M("SlitWarm", (0.40, 0.30, 0.20, 1.0), 0.5, 0.0,
                   (1.0, 0.72, 0.30, 1.0), 0.8)
    for i, x in enumerate([-10, -6, -2, 2, 6, 10]):
        box("part_wall_slit_b_%d" % i, (x, 8.55, 1.0), (0.06, 0.03, 0.7), P['slitw'], rt)
    for i, y in enumerate([-6, -2, 2, 6]):
        box("part_wall_slit_r_%d" % i, (12.55, y, 1.0), (0.03, 0.06, 0.7), P['slitw'], rt)

    # 四角立柱收头（前侧两根作为敞口门柱）
    for i, (x, y) in enumerate([(-12.7, 8.7), (12.7, 8.7),
                                (-12.7, -8.7), (12.7, -8.7)]):
        cyl("part_post_%d" % i, (x, y, 0.9), 0.22, 1.8, P['dark'], rt)
        cyl("part_post_cap_%d" % i, (x, y, 1.82), 0.24, 0.06, P['gw'], rt)

    export("park_walls.glb")


build()
print("DONE park_walls v2")
