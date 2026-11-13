# -*- coding: utf-8 -*-
"""只重建 ground_facility.glb（v6：车位再加宽 + 角标跟随新布局）

复用 gen_all_models_v4.py 工具函数（exec 加载、砍掉末尾全量构建）。

v6 变化（在 v5 基础上）：
  - 车位间距 3.3→3.9m、宽 2.6→3.0m：中心 x = -10.1 / -6.2 / -2.3
    （用户反馈"车位空隙太小还要更大"：相邻车间隙 1.9m，车位内单侧余量 0.5m）
  - part_brk_pv / part_brk_charge 角标加宽到 12.6m 居中 -6.2（框住 12.0m 宽棚）
  - part_brk_storage 角标居中 x=1.2（电池舱左移后的新中心）
其余与 v5 一致（3 车位淡自发光线 SlotLineGlow、左侧前两个花箱已删）。
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
M = g["M"]
root = g["root"]
box = g["box"]
boxb = g["boxb"]
cyl = g["cyl"]
rr_prism = g["rr_prism"]
rr_points = g["rr_points"]
perimeter_dots = g["perimeter_dots"]
dash_poly = g["dash_poly"]
bracket = g["bracket"]
export = g["export"]


def build_ground_v6():
    reset()
    P = palette()
    # 车位线：淡自发光，暗场景里看得见；截面薄，不算块状发光
    P['slot'] = M("SlotLineGlow", (0.30, 0.42, 0.50, 1.0), 0.60, 0.0,
                  (0.45, 0.80, 0.95, 1.0), 0.55)
    rt = root("Ground_Root")

    # 圆角平台本体（顶面 z=0）
    rr_prism("part_platform", 26.0, 18.0, 2.8, 0.75, -0.75, P['ground'], rt)
    rr_prism("part_deck", 25.2, 17.2, 2.7, 0.06, 0.0, P['dark'], rt)

    # 外缘金色发光腰带 + 点阵光环
    rr_prism("part_gold_band", 26.35, 18.35, 2.95, 0.07, -0.50, P['gy'], rt)
    perimeter_dots("part_gold_dot", 26.9, 18.9, 3.05, P['gy'], rt,
                   y=-0.30, size=0.085, spacing=0.65)

    # 青色虚线导航回路（外圈 + 内圈）
    dash_poly("part_guide_outer", rr_points(21.0, 13.6, 3.0, 6), P['gc'], rt, y=0.035)
    dash_poly("part_guide_inner", rr_points(13.4, 8.6, 2.2, 6), P['gc'], rt, y=0.035,
              w=0.055, dash=0.28, gap=0.22)

    # —— 充电区：3 个宽车位框线（间距3.9m，淡自发光）——
    for i, cx in enumerate([-10.1, -6.2, -2.3]):
        w2, d2 = 3.0, 5.0
        cz = -3.9
        box("part_slot_%d_l" % i, (cx - w2 / 2, cz, 0.028), (0.12, d2, 0.02), P['slot'], rt)
        box("part_slot_%d_r" % i, (cx + w2 / 2, cz, 0.028), (0.12, d2, 0.02), P['slot'], rt)
        box("part_slot_%d_b" % i, (cx, cz - d2 / 2, 0.028), (w2, 0.12, 0.02), P['slot'], rt)

    # —— 斑马线人行道（前左角）——
    for i in range(7):
        x = -12.0 + i * 0.95
        box("part_zebra_%d" % i, (x, -7.35, 0.03), (0.52, 1.9, 0.02), P['line'], rt)
    box("part_walk_edge", (-8.4, -7.35, 0.03), (0.12, 2.1, 0.02), P['gc'], rt)

    # —— 绿植花箱（左侧只留后两个）——
    planter = [(-12.3, 0.4), (-12.3, 3.2),
               (-6.0, 8.1), (-3.0, 8.1), (0.0, 8.1), (3.0, 8.1)]
    for i, (x, z) in enumerate(planter):
        boxb("part_planter_%d" % i, (x, z, 0.28), (1.7, 0.9, 0.56), P['dark'], rt, bw=0.03)
        box("part_hedge_%d" % i, (x, z, 0.68), (1.55, 0.78, 0.30), P['hedge'], rt)

    # —— 防撞柱（前缘一排，顶部微光）——
    for i in range(6):
        x = -5.4 + i * 2.4
        cyl("part_bollard_%d" % i, (x, -6.9, 0.42), 0.10, 0.84, P['body'], rt)
        cyl("part_bollard_cap_%d" % i, (x, -6.9, 0.86), 0.105, 0.06, P['gw'], rt)

    # —— 园区立杆灯（左前 + 右后）——
    for i, (x, z) in enumerate([(-13.2, 2.0), (5.6, 7.6)]):
        cyl("part_mast_%d" % i, (x, z, 2.3), 0.13, 4.6, P['dark'], rt)
        box("part_mast_arm_%d" % i, (x + (0.6 if x < 0 else -0.6), z, 4.5), (1.3, 0.16, 0.16), P['dark'], rt)
        box("part_mast_lamp_%d" % i, (x + (1.2 if x < 0 else -1.2), z, 4.34), (0.7, 0.34, 0.12), P['gg'], rt)

    # —— 区域角标（pv/charge 框新停车区；storage 跟电池舱左移）——
    bracket("part_brk_pv", -6.2, -3.6, 12.6, 7.6, P['gg'], rt)
    bracket("part_brk_storage", 1.2, 5.6, 11.0, 5.0, P['gg'], rt)
    bracket("part_brk_charge", -6.2, -3.6, 12.6, 7.6, P['gc'], rt, y=0.03, L=0.7, t=0.07)

    export("ground_facility.glb")


build_ground_v6()
print("DONE ground v6")
