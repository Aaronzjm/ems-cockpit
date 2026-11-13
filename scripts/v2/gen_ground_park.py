# -*- coding: utf-8 -*-
"""v2 场景底座 ground_park.glb（严格按参考图俯视图布局）

布局（世界坐标，平台 26×18 同 v1）：
  - 充电区 4 车位：中心 x=-9.9/-7.0/-4.1/-1.2，宽 2.6m、深 4.4m（z∈[0,4.4]），
    整圈淡自发光车位线（同 ground v7 的可见性方案：y=0.05 骑跨 deck 顶）
  - 绿色虚线导引：充电区环回路 + 通往配电室路径 + 储能区环回路
  - 区域角标：充电区(青) / 储能区(绿)
  - 斑马线前左、防撞柱前中 5 根、花箱左列 3 + 前右 2
复用 gen_all_models_v4.py 工具函数，输出到 public/models-v2/。
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
box = g["box"]; boxb = g["boxb"]; cyl = g["cyl"]
rr_prism = g["rr_prism"]; perimeter_dots = g["perimeter_dots"]
dash_poly = g["dash_poly"]; bracket = g["bracket"]; export = g["export"]


def build():
    reset()
    P = palette()
    # 车位线：绿色自发光（参考图同款绿框），亮度低于 bloom 阈值
    P['slot'] = M("SlotLineGlow", (0.10, 0.40, 0.18, 1.0), 0.50, 0.0,
                  (0.15, 1.00, 0.35, 1.0), 0.85)
    rt = root("GroundV2_Root")

    rr_prism("part_platform", 26.0, 18.0, 2.8, 0.75, -0.75, P['ground'], rt)
    rr_prism("part_deck", 25.2, 17.2, 2.7, 0.06, 0.0, P['dark'], rt)
    rr_prism("part_gold_band", 26.35, 18.35, 2.95, 0.07, -0.50, P['gy'], rt)
    perimeter_dots("part_gold_dot", 26.9, 18.9, 3.05, P['gy'], rt,
                   y=-0.30, size=0.085, spacing=0.65)

    # —— 4 车位整圈框线（充电区）——
    for i, cx in enumerate([-9.9, -7.0, -4.1, -1.2]):
        w2, d2 = 2.6, 4.4
        cy = -2.2  # 世界 z 中心 2.2
        zy = 0.08  # 16:06 修闪烁：deck 顶 0.06 因 doubleSided 会从上方渲染，贴地标钱顶面必须明显高于它
        box("part_slot_%d_l" % i, (cx - w2 / 2, cy, zy), (0.16, d2, 0.03), P['slot'], rt)
        box("part_slot_%d_r" % i, (cx + w2 / 2, cy, zy), (0.16, d2, 0.03), P['slot'], rt)
        box("part_slot_%d_b" % i, (cx, cy - d2 / 2, zy), (w2, 0.16, 0.03), P['slot'], rt)
        box("part_slot_%d_f" % i, (cx, cy + d2 / 2, zy), (w2, 0.16, 0.03), P['slot'], rt)

    # —— 绿色虚线导引：15:09 用户要求去掉，不还原 ——

    # —— 区域角标 ——
    bracket("part_brk_charge", -5.45, -2.3, 12.9, 6.6, P['gc'], rt, y=0.085, L=1.0, t=0.12)
    bracket("part_brk_storage", 5.5, 5.5, 7.2, 6.2, P['gg'], rt, y=0.085, L=1.0, t=0.12)

    # —— 斑马线（前左）——
    for i in range(6):
        x = -11.5 + i * 0.9
        box("part_zebra_%d" % i, (x, -7.2, 0.085), (0.5, 1.8, 0.02), P['line'], rt)

    # —— 花箱绿植（左列 3 + 前右 2）——
    # 16:28 中列花箱 world z 1.0→1.55：给车棚最左立柱（x=-11.35, z=0.5）及柱底环让位
    for i, (x, y) in enumerate([(-11.6, 1.0), (-11.6, -1.55), (-11.6, -3.0),
                                (5.8, -6.9), (7.3, -6.9)]):
        boxb("part_planter_%d" % i, (x, y, 0.28), (1.6, 0.9, 0.56), P['dark'], rt, bw=0.03)
        box("part_hedge_%d" % i, (x, y, 0.68), (1.45, 0.78, 0.30), P['hedge'], rt)

    # —— 防撞柱（前中 6 根，顶微光）——
    for i in range(6):
        x = -2.0 + i * 1.5
        cyl("part_bollard_%d" % i, (x, -6.6, 0.42), 0.10, 0.84, P['body'], rt)
        cyl("part_bollard_cap_%d" % i, (x, -6.6, 0.86), 0.105, 0.06, P['gw'], rt)

    export("ground_park.glb")


build()
print("DONE ground_park v2")
