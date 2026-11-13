# -*- coding: utf-8 -*-
"""只重建 ground_facility.glb（v7：车位线提亮加宽 + 补前端线成整圈）

复用 gen_all_models_v4.py 工具函数（exec 加载、砍掉末尾全量构建）。

v7 变化（在 v6 基础上，用户反馈"停车位的一圈线看不到"）：
  - 车位线材质提亮：emis (0.55,0.90,1.00) × 1.0 → 亮度高于已验证可见的
    GlowCyan 导航虚线(ef≈0.85)，合成亮度 0.83 仍低于 bloom 阈值 1.05，不会烧白
  - 线宽 0.12→0.16m，高度 0.02→0.03m
  - y 从 0.028 提到 0.05：横跨 deck 顶面(0.06)。deck 顶面法线朝下被背面剔除、
    实际可见铺装是 platform 顶(z=0)，但骑跨摆放两种情况都保证可见
  - 补 part_slot_%d_f 前端线（z=1.4 开口侧），车位框闭合成完整一圈
其余与 v6 一致。
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


def build_ground_v7():
    reset()
    P = palette()
    # 车位线：亮青白自发光（高于导航虚线亮度、低于 bloom 阈值）
    P['slot'] = M("SlotLineGlow", (0.35, 0.50, 0.60, 1.0), 0.50, 0.0,
                  (0.55, 0.90, 1.00, 1.0), 1.00)
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

    # —— 充电区：3 个宽车位整圈框线（间距3.9m、宽3.0m、含前端线）——
    for i, cx in enumerate([-10.1, -6.2, -2.3]):
        w2, d2 = 3.0, 5.0
        cz = -3.9
        zy = 0.05  # 横跨 deck 顶(0.06)，无论顶面是否渲染都可见
        box("part_slot_%d_l" % i, (cx - w2 / 2, cz, zy), (0.16, d2, 0.03), P['slot'], rt)
        box("part_slot_%d_r" % i, (cx + w2 / 2, cz, zy), (0.16, d2, 0.03), P['slot'], rt)
        box("part_slot_%d_b" % i, (cx, cz - d2 / 2, zy), (w2, 0.16, 0.03), P['slot'], rt)
        box("part_slot_%d_f" % i, (cx, cz + d2 / 2, zy), (w2, 0.16, 0.03), P['slot'], rt)

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

    # —— 区域角标 ——
    bracket("part_brk_pv", -6.2, -3.6, 12.6, 7.6, P['gg'], rt)
    bracket("part_brk_storage", 1.2, 5.6, 11.0, 5.0, P['gg'], rt)
    bracket("part_brk_charge", -6.2, -3.6, 12.6, 7.6, P['gc'], rt, y=0.03, L=0.7, t=0.07)

    export("ground_facility.glb")


build_ground_v7()
print("DONE ground v7")
