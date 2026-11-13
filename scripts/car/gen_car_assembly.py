# -*- coding: utf-8 -*-
"""汽车总装精细化模型（2026-10-22）：车身从骨架逐步组装成整车

产出（public/models-car/）：
  stamped_skid.glb  冲压件料架（冲压区输送对象：地板/机盖/顶盖/车门散件）
  car_frame.glb     白车身骨架 + 分步闭合覆盖件（焊装三工位渐进：骨架→地板侧围→全闭合）
  car_body.glb      纯涂装壳体（车身+开放式座舱+滑橇，无轮/玻璃/灯——重生成覆盖旧版）
  car_parts.glb     总装零件组，四工位渐进安装：
                    S1 底盘合装(桥/弹簧/轮/变速箱/排气/电池) → S2 内饰(座椅/仪表/方向盘/玻璃)
                    → S3 车门+保险杠 → S4 灯具/格栅/后视镜/车牌

工艺依据（web_search 2026-10-22，Leuze final assembly / Toyota plant tour / SlideShare）：
  车门分装 → 内饰(线束/地毯/仪表台) → 动力总成+底盘 → Marriage 合装 →
  车轮/车窗/座椅/大灯 → 油液加注 → 终检下线

命名约定（运行时按前缀分组切换可见性）：
  car_frame: part_frame_* 常显骨架；part_panel_floor/side_* 工位2；part_panel_roof/hood/trunk/door_* 工位3
  car_parts: part_axle/spring/wheel/hub/gearbox/exhaust/battery_* = 底盘组
             part_seat/dash/screen/steer/glass_* = 内饰组
             part_door_*/part_bumper_* = 车门组（材质随车身漆色，运行时克隆换色）
             part_lamp/grille/mirror/plate_* = 灯具组
坐标约定同 v4 库：Blender Z-up，导出后 (x,y,z)->(x,z,-y)；world z = -Blender y。
车本地原点=滑橇底面中心，摆在输送床顶（world y=0.5）；车头朝 +x。
"""
import pathlib, os, math, bpy

SRC = pathlib.Path(r"D:\1zjm\agent\ems-cockpit\scripts\gen_all_models_v4.py")
src = SRC.read_text(encoding="utf-8")
cut = src.rindex("\nbuild_ground()")
g = {"__name__": "v4lib"}
exec(compile(src[:cut], str(SRC), "exec"), g)
g["OUT"] = r"D:\1zjm\agent\ems-cockpit\public\models-car"
os.makedirs(g["OUT"], exist_ok=True)

reset = g["reset"]; palette = g["palette"]; root = g["root"]
box = g["box"]; boxb = g["boxb"]; cyl = g["cyl"]; ring = g["ring"]
bracket = g["bracket"]; base_outline = g["base_outline"]; export = g["export"]


# ============================================================
# 1) 冲压件料架：冲压区输送对象（一橇散件，焊装区换成骨架）
# ============================================================
def build_skid():
    reset()
    P = palette()
    rt = root("StampedSkid_Root")

    box("part_skid_base", (0, 0, 0.06), (4.5, 2.0, 0.12), P['dark'], rt)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("part_post_%d%d" % (sx, sy), (sx * 2.05, sy * 0.9, 0.62), (0.08, 0.08, 1.0), P['dark'], rt)
    # 四层冲压覆盖件（银色板料）
    box("part_pan_floor", (0, 0, 0.30), (2.4, 1.4, 0.04), P['paint'], rt)
    box("part_pan_hood", (0.85, 0, 0.50), (1.1, 1.35, 0.04), P['paint'], rt)
    box("part_pan_trunk", (-0.9, 0, 0.50), (0.85, 1.35, 0.04), P['paint'], rt)
    box("part_pan_roof", (0, 0, 0.70), (2.3, 1.4, 0.04), P['paint'], rt)
    di = 0
    for sx in (-0.55, 0.55):
        for sy in (-0.44, 0.44):
            box("part_pan_door_%d" % di, (sx, sy, 0.90), (0.8, 0.42, 0.04), P['paint'], rt)
            di += 1
    box("part_tag", (2.05, -0.93, 0.95), (0.3, 0.02, 0.15), P['gc'], rt)

    export("stamped_skid.glb")
    print("SKID OK")


# ============================================================
# 2) 白车身骨架 + 分步闭合覆盖件（焊装渐进）
#    part_frame_* 常显；panel_floor/side 工位2 闭合；panel_roof/hood/trunk/door 工位3 闭合
# ============================================================
def build_frame():
    reset()
    P = palette()
    rt = root("CarFrame_Root")

    box("part_skid", (0, 0, 0.06), (4.5, 2.0, 0.12), P['dark'], rt)
    # 骨架（灰钢）：纵梁×2 + 横梁×5 + 前后围 + A/B/C 柱×3对 + 顶盖纵梁×2
    for s in (-1, 1):
        box("part_frame_rail_%d" % s, (0, s * 0.72, 0.30), (4.2, 0.12, 0.12), P['line'], rt)
    for i, x in enumerate([-1.8, -0.9, 0.0, 0.9, 1.8]):
        box("part_frame_cross_%d" % i, (x, 0, 0.30), (0.12, 1.44, 0.12), P['line'], rt)
    box("part_frame_firewall", (0.6, 0, 0.58), (0.08, 1.44, 0.5), P['line'], rt)
    box("part_frame_rear", (-2.0, 0, 0.58), (0.1, 1.44, 0.5), P['line'], rt)
    for px in (1.0, -0.3, -1.3):
        for s in (-1, 1):
            box("part_frame_pil_%d_%d" % (int(px * 10), s), (px, s * 0.72, 0.87), (0.1, 0.1, 1.08), P['line'], rt)
    for s in (-1, 1):
        box("part_frame_roof_%d" % s, (-0.15, s * 0.72, 1.40), (2.4, 0.1, 0.1), P['line'], rt)

    # 工位2 闭合：地板 + 左右侧围
    box("part_panel_floor", (0, 0, 0.36), (3.6, 1.44, 0.05), P['paint'], rt)
    for s in (-1, 1):
        box("part_panel_side_%d" % s, (-0.1, s * 0.78, 0.575), (2.8, 0.05, 0.45), P['paint'], rt)
    # 工位3 闭合：顶盖 + 机盖 + 尾门 + 四门壳
    box("part_panel_roof", (-0.15, 0, 1.455), (2.4, 1.5, 0.05), P['paint'], rt)
    box("part_panel_hood", (1.5, 0, 0.845), (1.0, 1.4, 0.05), P['paint'], rt)
    box("part_panel_trunk", (-1.6, 0, 0.845), (0.75, 1.4, 0.05), P['paint'], rt)
    for dx in (0.35, -0.65):
        for s in (-1, 1):
            box("part_panel_door_%d_%d" % (int(dx * 100), s), (dx, s * 0.8, 0.56), (0.85, 0.04, 0.46), P['paint'], rt)

    export("car_frame.glb")
    print("FRAME OK")


# ============================================================
# 3) 涂装壳体（重生成）：下车体 + 开放式座舱（4柱+顶盖）+ 滑橇
#    无轮/玻璃/灯/门——全部移到 car_parts 渐进安装；座舱开放让内饰安装可见
# ============================================================
def build_body():
    reset()
    P = palette()
    rt = root("CarBody_Root")

    box("part_skid", (0, 0, 0.06), (4.5, 2.0, 0.12), P['dark'], rt)
    boxb("part_body", (0, 0, 0.55), (4.3, 1.85, 0.50), P['paint'], rt, bw=0.08)
    boxb("part_cabin", (-0.15, 0, 1.435), (2.5, 1.65, 0.07), P['paint'], rt, bw=0.03)
    for px in (1.0, -0.3, -1.3):
        for s in (-1, 1):
            box("part_pillar_%d_%d" % (int(px * 10), s), (px, s * 0.76, 1.10), (0.12, 0.12, 0.60), P['paint'], rt)

    export("car_body.glb")
    print("BODY OK")


# ============================================================
# 4) 总装零件组（四工位渐进；门/保险杠材质=CarPaint，运行时随漆色克隆换色）
# ============================================================
def build_parts():
    reset()
    P = palette()
    rt = root("CarParts_Root")

    # —— S1 底盘合装：前后桥/弹簧/变速箱/排气/电池 + 车轮×4 ——
    for sx in (1.4, -1.4):
        box("part_axle_%d" % int(sx * 10), (sx, 0, 0.22), (0.14, 1.5, 0.12), P['dark'], rt)
    wi = 0
    for sx in (1.4, -1.4):
        for sy in (0.6, -0.6):
            cyl("part_spring_%d" % wi, (sx, sy, 0.24), 0.07, 0.22, P['copper'], rt, verts=10)
            wi += 1
    box("part_gearbox", (0.1, 0, 0.21), (0.55, 0.45, 0.16), P['dark'], rt)
    cyl("part_exhaust", (-0.3, 0.55, 0.19), 0.045, 3.0, P['line'], rt, rot=(0, math.pi / 2, 0), verts=10)
    box("part_battery", (-0.4, -0.15, 0.19), (0.8, 0.7, 0.10), P['dark'], rt)
    box("part_battstrip", (-0.4, -0.15, 0.25), (0.7, 0.6, 0.02), P['gc'], rt)
    wi = 0
    for sx in (1.4, -1.4):
        for sy in (0.90, -0.90):
            cyl("part_wheel_%d" % wi, (sx, sy, 0.45), 0.33, 0.24, P['dark'], rt,
                rot=(math.pi / 2, 0, 0), verts=20)
            cyl("part_hub_%d" % wi, (sx, sy, 0.45), 0.15, 0.27, P['line'], rt,
                rot=(math.pi / 2, 0, 0), verts=12)
            wi += 1

    # —— S2 内饰：前排座椅×2 + 后排 + 仪表台 + 屏幕 + 方向盘 + 玻璃×4 ——
    for s in (-1, 1):
        box("part_seat_f%d" % s, (0.3, s * 0.42, 0.84), (0.45, 0.44, 0.08), P['line'], rt)
        box("part_seat_fb%d" % s, (0.06, s * 0.42, 1.09), (0.08, 0.44, 0.42), P['line'], rt)
    box("part_seat_r", (-0.75, 0, 0.84), (0.45, 1.24, 0.08), P['line'], rt)
    box("part_seat_rb", (-0.99, 0, 1.09), (0.08, 1.24, 0.42), P['line'], rt)
    box("part_dash", (0.92, 0, 0.90), (0.22, 1.4, 0.20), P['dark'], rt)
    box("part_screen", (1.02, 0, 1.02), (0.03, 0.5, 0.15), P['scr'], rt)
    cyl("part_steer", (0.74, 0.42, 1.00), 0.15, 0.03, P['dark'], rt, rot=(math.pi / 2.4, 0, 0), verts=16)

    # —— S3 车门×4 + 前后保险杠 + 车窗玻璃（内饰装完后闭合座舱）——
    for dx in (0.35, -0.65):
        for s in (-1, 1):
            box("part_door_%d_%d" % (int(dx * 100), s), (dx, s * 0.945, 0.56), (0.85, 0.05, 0.48), P['paint'], rt)
    box("part_bumper_f", (2.12, 0, 0.44), (0.18, 1.75, 0.26), P['paint'], rt)
    box("part_bumper_r", (-2.12, 0, 0.44), (0.18, 1.75, 0.26), P['paint'], rt)
    # 车窗玻璃：填满立柱间整个开口（z 0.80→1.40），消除“悬浮温室”缝隙
    box("part_glass_f", (1.04, 0, 1.10), (0.05, 1.6, 0.60), P['glass'], rt)
    box("part_glass_b", (-1.34, 0, 1.10), (0.05, 1.6, 0.60), P['glass'], rt)
    for s in (-1, 1):
        box("part_glass_s%d" % s, (-0.15, s * 0.84, 1.10), (2.34, 0.04, 0.60), P['glass'], rt)

    # —— S4 灯具/格栅/后视镜/车牌 ——
    for s in (-1, 1):
        box("part_lamp_f%d" % s, (2.17, s * 0.62, 0.62), (0.06, 0.28, 0.12), P['gw'], rt)
        box("part_lamp_r%d" % s, (-2.17, s * 0.62, 0.62), (0.06, 0.28, 0.12), P['gr'], rt)
        box("part_mirror_%d" % s, (0.95, s * 0.99, 0.98), (0.14, 0.05, 0.09), P['dark'], rt)
    box("part_grille", (2.16, 0, 0.40), (0.05, 1.0, 0.16), P['dark'], rt)
    box("part_plate", (-2.18, 0, 0.42), (0.02, 0.42, 0.14), P['gw'], rt)

    export("car_parts.glb")
    print("PARTS OK")


build_skid()
build_frame()
build_body()
build_parts()
print("DONE car_assembly all 4")
