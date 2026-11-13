# -*- coding: utf-8 -*-
"""EMS 驾驶舱 —— 参考图对齐版建模脚本 v4
Blender 5.2 / 导出 GLB

坐标约定：Blender Z-up 建模，导出 glTF 后 (x,y,z) -> (x, z, -y)
所以 Blender 的 -Y 方向 = gltf 的 +Z 方向 = 场景"前方"。

设计语言（对齐参考图）：
  - 圆角园区平台 + 外缘金色点阵光环
  - 地面青色虚线导航回路、绿色转角括号
  - 立柱/充电桩底部绿色光环（torus）
  - 储能柜整柜强绿发光（这是参考图里唯一的"整机发光"）
  - 配电室玻璃幕墙 + 可见内部操作台与屏幕
"""
import bpy, bmesh, math, os

OUT = r"D:\1zjm\agent\ems-cockpit\public\models"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# 基础工具
# ============================================================
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def M(name, color, rough=0.5, metal=0.3, emis=None, es=1.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs['Base Color'].default_value = color
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        if 'Alpha' in b.inputs:
            b.inputs['Alpha'].default_value = alpha
        if emis is not None:
            k = 'Emission Color' if 'Emission Color' in b.inputs else 'Emission'
            if k in b.inputs:
                b.inputs[k].default_value = emis
            if 'Emission Strength' in b.inputs:
                b.inputs['Emission Strength'].default_value = es
    return m

def palette():
    """统一色板。发光强度经过标定：只有描边/导光条越过 bloom 阈值。"""
    return {
        'dark':   M("DarkMetal",  (0.045, 0.052, 0.065, 1.0), 0.55, 0.35),
        'body':   M("DarkBody",   (0.075, 0.085, 0.105, 1.0), 0.50, 0.30),
        'panel':  M("SolarCell",  (0.020, 0.035, 0.085, 1.0), 0.35, 0.50),
        'copper': M("CoreCopper", (0.520, 0.310, 0.130, 1.0), 0.45, 0.40),
        'wall':   M("WallDark",   (0.060, 0.070, 0.085, 1.0), 0.60, 0.25),
        'ground': M("GroundPlate",(0.030, 0.036, 0.045, 1.0), 0.70, 0.20),
        'paint':  M("CarPaint",   (0.560, 0.600, 0.640, 1.0), 0.32, 0.65),
        'line':   M("FloorLine",  (0.330, 0.400, 0.440, 1.0), 0.75, 0.05),
        'hedge':  M("Hedge",      (0.045, 0.150, 0.085, 1.0), 0.80, 0.00),
        'glass':  M("GlassPane",  (0.030, 0.070, 0.105, 1.0), 0.10, 0.65),
        # —— 发光族 ——
        'gg':     M("GlowGreen",  (0.100, 1.000, 0.450, 1.0), 0.30, 0.0, (0.10, 1.00, 0.45, 1.0), 1.25),
        'gg2':    M("GlowGreenHot",(0.250, 1.000, 0.550, 1.0), 0.30, 0.0, (0.25, 1.00, 0.55, 1.0), 1.40),
        'gb':     M("GlowBlue",   (0.120, 0.650, 1.000, 1.0), 0.30, 0.0, (0.12, 0.65, 1.00, 1.0), 1.10),
        # 屏幕：深底 + 蓝光内容，强度刻意压在 bloom 阈值下方，避免烧成白板
        'scr':    M("ScreenDark", (0.020, 0.055, 0.130, 1.0), 0.45, 0.0, (0.07, 0.30, 0.62, 1.0), 0.55),
        'gy':     M("GlowGold",   (1.000, 0.720, 0.150, 1.0), 0.35, 0.1, (1.00, 0.72, 0.15, 1.0), 1.15),
        'gc':     M("GlowCyan",   (0.050, 0.950, 0.850, 1.0), 0.40, 0.0, (0.05, 0.95, 0.85, 1.0), 0.90),
        'gr':     M("GlowRed",    (1.000, 0.150, 0.120, 1.0), 0.35, 0.0, (1.00, 0.15, 0.12, 1.0), 1.30),
        'gw':     M("GlowWhite",  (0.900, 0.970, 1.000, 1.0), 0.35, 0.0, (0.90, 0.97, 1.00, 1.0), 1.35),
    }

def root(name):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    return o

def box(name, loc, dims, m, parent=None, rz=0.0, rx=0.0, ry=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = dims
    o.rotation_euler = (rx, ry, rz)
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o

def boxb(name, loc, dims, m, parent=None, bw=0.05, seg=2, rz=0.0):
    """带倒角的方块（先应用缩放再倒角，保证倒角均匀）"""
    o = box(name, loc, dims, m, parent, rz=rz)
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    md = o.modifiers.new("bev", 'BEVEL')
    md.width = bw
    md.segments = seg
    md.limit_method = 'ANGLE'
    md.angle_limit = math.radians(50)
    bpy.ops.object.modifier_apply(modifier=md.name)
    return o

def cyl(name, loc, r, d, m, parent=None, rot=(0, 0, 0), verts=20):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, location=loc,
                                        rotation=rot, vertices=verts)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o

def ring(name, loc, major, minor, m, parent=None, rot=(0, 0, 0)):
    """地面光环 / 底部描边环。"""
    bpy.ops.mesh.primitive_torus_add(location=loc, rotation=rot,
                                     major_radius=major, minor_radius=minor,
                                     major_segments=32, minor_segments=6)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o

# --------- 圆角矩形 ---------
def rr_points(w, d, r, seg=8):
    hw, hd = w / 2 - r, d / 2 - r
    pts = []
    for (cx, cy, a0) in [(hw, hd, 0.0), (-hw, hd, math.pi / 2),
                         (-hw, -hd, math.pi), (hw, -hd, 1.5 * math.pi)]:
        for i in range(seg + 1):
            a = a0 + (math.pi / 2) * i / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def rr_prism(name, w, d, r, h, z0, m, parent=None, seg=8):
    pts = rr_points(w, d, r, seg)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, z0)) for (x, y) in pts]
    vt = [bm.verts.new((x, y, z0 + h)) for (x, y) in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([vb[i], vb[j], vt[j], vt[i]])
    bm.faces.new(list(reversed(vb)))
    bm.faces.new(vt)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(m)
    if parent:
        o.parent = parent
    return o

def poly_walk(pts, spacing, closed=True):
    n = len(pts)
    rng = list(range(n)) if closed else list(range(n - 1))
    segs = []
    for i in rng:
        a = pts[i]
        b = pts[(i + 1) % n]
        segs.append((a, b, math.hypot(b[0] - a[0], b[1] - a[1])))
    total = sum(s[2] for s in segs)
    out, cur, i, acc = [], 0.0, 0, 0.0
    while cur < total:
        while i < len(segs) - 1 and acc + segs[i][2] < cur:
            acc += segs[i][2]
            i += 1
        a, b, L = segs[i]
        t = (cur - acc) / L if L > 1e-9 else 0.0
        t = min(max(t, 0.0), 1.0)
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        cur += spacing
    return out

def perimeter_dots(name, w, d, r, m, parent, y=0.03, size=0.07, spacing=0.62):
    pts = poly_walk(rr_points(w, d, r, 8), spacing)
    for i, (x, z) in enumerate(pts):
        box("%s_%d" % (name, i), (x, z, y), (size, size, 0.02), m, parent)

def dash_poly(name, pts, m, parent, y=0.025, w=0.07, dash=0.36, gap=0.26,
              h=0.02, closed=True):
    n = len(pts)
    rng = range(n) if closed else range(n - 1)
    idx = 0
    for i in rng:
        a = pts[i]
        b = pts[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-6:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        ang = math.atan2(uy, ux)
        s = 0.0
        while s < L - 0.02:
            seg = min(dash, L - s)
            mx = a[0] + ux * (s + seg / 2)
            my = a[1] + uy * (s + seg / 2)
            box("%s_%d" % (name, idx), (mx, my, y), (seg, w, h), m, parent, rz=ang)
            idx += 1
            s += dash + gap
    return idx

def bracket(name, cx, cz, w, d, m, parent, y=0.028, L=0.95, t=0.10):
    """区域四角绿色括号（参考图里圈住功能区的角标）"""
    hw, hd = w / 2.0, d / 2.0
    for (sx, sz) in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        x = cx + sx * hw
        z = cz + sz * hd
        box("%s_%d%d_a" % (name, sx, sz), (x - sx * L / 2, z, y), (L, t, 0.02), m, parent)
        box("%s_%d%d_b" % (name, sx, sz), (x, z - sz * L / 2, y), (t, L, 0.02), m, parent)

def base_outline(name, w, d, m, parent, y=0.04, t=0.055):
    """设备底部矩形发光描边（四边细条，沿设备底面轮廓）。
    这是各设备唯一的强发光源：只描底边，本体保持正常材质。"""
    hw, hd = w / 2.0, d / 2.0
    box("%s_x0" % name, (0.0, -hd, y), (w, t, 0.02), m, parent)
    box("%s_x1" % name, (0.0,  hd, y), (w, t, 0.02), m, parent)
    box("%s_z0" % name, (-hw, 0.0, y), (t, d, 0.02), m, parent)
    box("%s_z1" % name, ( hw, 0.0, y), (t, d, 0.02), m, parent)

def export(fn):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, fn), export_format='GLB')
    print("SUCCESS: " + fn)

# ============================================================
# 1. 园区底座（平台 + 金色点环 + 青色虚线回路 + 车位 + 绿化 + 防撞柱）
# ============================================================
def build_ground():
    reset()
    P = palette()
    rt = root("Ground_Root")

    # 圆角平台本体（顶面 z=0）
    rr_prism("part_platform", 26.0, 18.0, 2.8, 0.75, -0.75, P['ground'], rt)
    # 平台顶面深色铺装（略小一圈，露出台阶）
    rr_prism("part_deck", 25.2, 17.2, 2.7, 0.06, 0.0, P['dark'], rt)

    # 外缘金色发光腰带 + 点阵光环
    rr_prism("part_gold_band", 26.35, 18.35, 2.95, 0.07, -0.50, P['gy'], rt)
    perimeter_dots("part_gold_dot", 26.9, 18.9, 3.05, P['gy'], rt,
                   y=-0.30, size=0.085, spacing=0.65)

    # 青色虚线导航回路（外圈 + 内圈）
    dash_poly("part_guide_outer", rr_points(21.0, 13.6, 3.0, 6), P['gc'], rt, y=0.035)
    dash_poly("part_guide_inner", rr_points(13.4, 8.6, 2.2, 6), P['gc'], rt, y=0.035,
              w=0.055, dash=0.28, gap=0.22)

    # —— 充电区：4 个车位框线（前左）——
    for i in range(4):
        cx = -9.3 + i * 2.55
        w2, d2 = 2.3, 5.0
        cz = -3.9
        box("part_slot_%d_l" % i, (cx - w2 / 2, cz, 0.028), (0.10, d2, 0.02), P['line'], rt)
        box("part_slot_%d_r" % i, (cx + w2 / 2, cz, 0.028), (0.10, d2, 0.02), P['line'], rt)
        box("part_slot_%d_b" % i, (cx, cz - d2 / 2, 0.028), (w2, 0.10, 0.02), P['line'], rt)

    # —— 斑马线人行道（前左角，斜向排布用轴向矩形近似）——
    for i in range(7):
        x = -12.0 + i * 0.95
        box("part_zebra_%d" % i, (x, -7.35, 0.03), (0.52, 1.9, 0.02), P['line'], rt)
    box("part_walk_edge", (-8.4, -7.35, 0.03), (0.12, 2.1, 0.02), P['gc'], rt)

    # —— 绿植花箱（沿左侧与后侧边缘）——
    planter = [(-12.3, -5.2), (-12.3, -2.4), (-12.3, 0.4), (-12.3, 3.2),
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

    # —— 区域角标：光伏区 / 储能区 / 充电区 ——
    bracket("part_brk_pv", -6.4, -3.6, 11.4, 7.6, P['gg'], rt)
    bracket("part_brk_storage", 3.2, 5.6, 11.0, 5.0, P['gg'], rt)
    bracket("part_brk_charge", -6.4, -3.6, 11.4, 7.6, P['gc'], rt, y=0.03, L=0.7, t=0.07)

    export("ground_facility.glb")

# ============================================================
# 2. 光伏雨棚（立柱底部绿光环 + 太阳能板阵列）
# ============================================================
def build_canopy():
    reset()
    P = palette()
    rt = root("Canopy_Root")

    for i, (x, y) in enumerate([(-3.3, -1.8), (3.3, -1.8), (-3.3, 1.8), (3.3, 1.8)]):
        cyl("part_pillar_%d" % i, (x, y, 1.55), 0.16, 3.1, P['dark'], rt, verts=16)
        # 立柱底座环：正常金属色（原为绿色发光环）
        ring("part_pillar_ring_%d" % i, (x, y, 0.06), 0.40, 0.055, P['body'], rt)

    box("part_beam", (0.0, 0.0, 3.16), (7.4, 4.2, 0.14), P['body'], rt)
    for i, y in enumerate([-2.12, 2.12]):
        # 檐口线脚：正常深色（原为发光条）
        box("part_beam_glow_%d" % i, (0.0, y, 3.24), (7.4, 0.035, 0.035), P['dark'], rt)

    for r in range(2):
        for c in range(3):
            px = (c - 1.0) * 2.42
            py = (r - 0.5) * 1.9
            box("part_panel_%d_%d" % (r, c), (px, py, 3.30), (2.30, 1.76, 0.06), P['panel'], rt)
            # 组件边框：正常深色（原为发光边）
            box("part_panel_edge_%d_%d" % (r, c), (px, py, 3.36), (2.32, 0.05, 0.02), P['dark'], rt)

    # 线槽
    box("part_trunk", (0.0, 0.0, 3.02), (0.16, 3.4, 0.10), P['dark'], rt)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 7.4, 4.2, P['gg'], rt, y=0.045)

    export("photovoltaic_canopy.glb")

# ============================================================
# 3. 储能电池舱（整柜强绿发光 + 前方深色开关柜）
# ============================================================
def build_storage():
    reset()
    P = palette()
    rt = root("Storage_Root")

    boxb("part_base", (0.0, 0.0, 0.14), (8.6, 4.6, 0.28), P['dark'], rt, bw=0.04)

    # 4 台储能柜：柜体为正常深色金属，仅保留竖向导光细缝 + 顶檐细光带
    for i in range(4):
        x = -3.0 + i * 2.0
        box("part_cab_frame_%d" % i, (x, 0.55, 1.45), (1.78, 2.05, 2.90), P['dark'], rt)
        # 柜门：正常金属色（原先是整面强绿发光，造成整机发光）
        box("part_cab_glow_%d" % i, (x, -0.40, 1.45), (1.62, 0.06, 2.72), P['body'], rt)
        # 竖向分缝：正常深色（原为导光细缝）
        for j, dx in enumerate([-0.40, 0.40]):
            box("part_cab_seam_%d_%d" % (i, j), (x + dx, -0.44, 1.45),
                (0.03, 0.02, 2.54), P['dark'], rt)
        # 顶檐压条：正常深色（原为细光带）
        box("part_cab_topline_%d" % i, (x, -0.44, 2.74), (1.60, 0.02, 0.03), P['dark'], rt)
        for k in range(3):
            box("part_cab_split_%d_%d" % (i, k), (x, -0.45, 0.55 + k * 0.90),
                (1.20, 0.02, 0.035), P['dark'], rt)
        box("part_cab_roof_%d" % i, (x, 0.55, 2.95), (1.86, 2.13, 0.10), P['body'], rt)

    # 前方一排深色开关柜
    for i in range(3):
        x = -2.6 + i * 2.6
        boxb("part_switch_%d" % i, (x, -2.30, 1.05), (1.90, 1.30, 2.10), P['body'], rt, bw=0.04)
        # 开关柜面板缝：正常深色
        box("part_switch_led_%d" % i, (x, -2.96, 1.72), (1.50, 0.05, 0.06), P['dark'], rt)
        box("part_switch_led2_%d" % i, (x, -2.96, 1.50), (1.50, 0.05, 0.04), P['dark'], rt)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 8.6, 4.6, P['gg'], rt, y=0.30)

    export("storage_container.glb")

# ============================================================
# 4. 智能快充桩（底部绿光环 + 屏幕 + 枪线）
# ============================================================
def build_pile():
    reset()
    P = palette()
    rt = root("Pile_Root")

    boxb("part_base", (0.0, 0.0, 0.10), (0.68, 0.56, 0.20), P['dark'], rt, bw=0.03)

    boxb("part_body", (0.0, 0.0, 1.05), (0.52, 0.44, 1.78), P['body'], rt, bw=0.05)
    # 正面面板：正常深色；屏幕为暗底发光（非大块炫光）
    box("part_face", (0.0, -0.235, 1.15), (0.44, 0.04, 1.50), P['dark'], rt)
    box("part_led_side_l", (-0.20, -0.255, 1.15), (0.035, 0.03, 1.40), P['dark'], rt)
    box("part_led_side_r", (0.20, -0.255, 1.15), (0.035, 0.03, 1.40), P['dark'], rt)
    box("part_screen", (0.0, -0.26, 1.44), (0.28, 0.02, 0.24), P['scr'], rt)
    box("part_screen2", (0.0, -0.26, 1.05), (0.28, 0.02, 0.10), P['scr'], rt)

    # 顶盖 + 顶面压条（正常深色）
    boxb("part_cap", (0.0, 0.0, 1.98), (0.56, 0.48, 0.10), P['dark'], rt, bw=0.03)
    box("part_cap_glow", (0.0, -0.245, 1.96), (0.44, 0.025, 0.025), P['dark'], rt)

    # 双充电枪 + 线缆（枪柄正常色）
    for i, x in enumerate([-0.34, 0.34]):
        box("part_holster_%d" % i, (x, 0.02, 1.05), (0.10, 0.16, 0.34), P['dark'], rt)
        box("part_gun_%d" % i, (x, -0.06, 1.34), (0.075, 0.24, 0.10), P['dark'], rt)
        cyl("part_cable_%d" % i, (x, 0.24, 0.72), 0.035, 1.30, P['dark'], rt, verts=10)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 0.68, 0.56, P['gg'], rt, y=0.215)

    export("charging_pile.glb")

# ============================================================
# 5. 配电变压器（本体保持深色金属，仅底部描边发光）
# ============================================================
def build_transformer():
    reset()
    P = palette()
    rt = root("Transformer_Root")

    boxb("part_base", (0.0, 0.0, 0.12), (2.30, 1.80, 0.24), P['dark'], rt, bw=0.03)
    boxb("part_tank", (0.0, 0.0, 1.10), (1.60, 1.24, 1.66), P['body'], rt, bw=0.05)
    for i, x in enumerate([-0.98, 0.98]):
        box("part_radiator_%d" % i, (x, 0.0, 1.10), (0.26, 1.14, 1.40), P['dark'], rt)
        for k in range(5):
            box("part_fin_%d_%d" % (i, k), (x, -0.50 + k * 0.25, 1.10),
                (0.30, 0.06, 1.34), P['dark'], rt)
    box("part_lid", (0.0, 0.0, 2.00), (1.74, 1.38, 0.14), P['dark'], rt)
    for i, x in enumerate([-0.45, 0.0, 0.45]):
        cyl("part_bushing_%d" % i, (x, 0.0, 2.32), 0.075, 0.50, P['copper'], rt, verts=12)
        ring("part_bushing_ring_%d" % i, (x, 0.0, 2.10), 0.11, 0.02, P['copper'], rt)
    # 警示标牌：正常色（原为金色发光）
    box("part_sign", (0.0, -0.64, 1.35), (0.44, 0.03, 0.34), P['copper'], rt)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 2.30, 1.80, P['gg'], rt, y=0.26)

    export("transformer_substation.glb")

# ============================================================
# 6. 配电室（玻璃幕墙 + 可见内部操作台/大屏，开顶便于俯视）
# ============================================================
def build_control_room():
    reset()
    P = palette()
    rt = root("ControlRoom_Root")

    boxb("part_slab", (0.0, 0.0, 0.16), (7.6, 6.2, 0.32), P['dark'], rt, bw=0.04)
    box("part_inner_floor", (0.0, 0.0, 0.34), (6.9, 5.5, 0.06), P['body'], rt)

    # 后墙 + 两侧墙
    box("part_wall_back", (0.0, 3.0, 1.72), (7.5, 0.20, 3.10), P['wall'], rt)
    for i, x in enumerate([-3.65, 3.65]):
        box("part_wall_side_%d" % i, (x, 0.0, 1.72), (0.20, 6.0, 3.10), P['wall'], rt)

    # 前侧只留竖向幕墙骨架（不做整块玻璃，保证内部操作台可见，与参考图剖视感一致）
    for i in range(4):
        x = -3.6 + i * 2.4
        box("part_mullion_%d" % i, (x, -3.0, 1.72), (0.12, 0.16, 3.10), P['dark'], rt)
    box("part_lintel", (0.0, -3.0, 3.20), (7.6, 0.20, 0.18), P['dark'], rt)

    # 顶部只留一圈细框（不做整块屋面板，否则俯视看不到内部）
    box("part_rim_back", (0.0, 3.0, 3.34), (7.6, 0.20, 0.10), P['dark'], rt)
    box("part_rim_front", (0.0, -3.05, 3.34), (7.6, 0.14, 0.10), P['dark'], rt)
    for i, x in enumerate([-3.7, 3.7]):
        box("part_rim_side_%d" % i, (x, 0.0, 3.34), (0.14, 6.1, 0.10), P['dark'], rt)
    # 檐口压条：正常深色（原为绿色发光）
    box("part_rim_glow", (0.0, -3.06, 3.30), (7.4, 0.03, 0.03), P['dark'], rt)

    # —— 内部设备 ——
    # 主控操作台（两排）
    for r, (zz, ww) in enumerate([(-1.10, 4.6), (0.55, 3.4)]):
        boxb("part_desk_%d" % r, (0.0, zz, 0.85), (ww, 0.90, 0.90), P['dark'], rt, bw=0.03)
        box("part_desk_top_%d" % r, (0.0, zz, 1.32), (ww + 0.10, 1.00, 0.06), P['body'], rt)
        # 台面显示器
        n = int(ww / 1.15)
        for k in range(max(n, 2)):
            x = (k - (max(n, 2) - 1) / 2.0) * 1.15
            box("part_mon_%d_%d" % (r, k), (x, zz - 0.34, 1.60), (0.78, 0.05, 0.46), P['scr'], rt)
            box("part_mon_base_%d_%d" % (r, k), (x, zz - 0.28, 1.38), (0.16, 0.14, 0.10), P['dark'], rt)
    # 座椅
    for k in range(4):
        x = -1.8 + k * 1.2
        box("part_chair_%d" % k, (x, -1.95, 0.60), (0.52, 0.52, 0.22), P['dark'], rt)
        box("part_chair_back_%d" % k, (x, -1.68, 0.92), (0.52, 0.12, 0.60), P['dark'], rt)

    # 后墙大屏（数据大屏）
    box("part_bigscreen", (0.0, 2.88, 2.05), (4.80, 0.06, 1.50), P['scr'], rt)
    box("part_bigscreen_frame", (0.0, 2.86, 2.05), (5.00, 0.10, 1.72), P['dark'], rt)
    # 侧墙屏
    for i, x in enumerate([-3.53, 3.53]):
        box("part_sidescreen_%d" % i, (x, 1.10, 1.90), (0.06, 2.10, 1.05), P['scr'], rt)

    # 地面压条：正常深色（原为导光带）
    box("part_floor_glow", (0.0, -2.55, 0.40), (6.4, 0.06, 0.04), P['dark'], rt)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 7.6, 6.2, P['gg'], rt, y=0.34)

    export("control_room.glb")

# ============================================================
# 7. 新能源汽车（参考图里复用同一台车）
# ============================================================
def build_vehicle():
    reset()
    P = palette()
    rt = root("Vehicle_Root")

    # 车身：下层宽体 + 上层收窄，形成真实腰线（长边沿 Y，车头朝 -Y）
    boxb("part_body_lower", (0.0, 0.0, 0.60), (1.90, 4.30, 0.52), P['paint'], rt, bw=0.14, seg=3)
    boxb("part_body_upper", (0.0, 0.05, 1.02), (1.82, 4.00, 0.40), P['paint'], rt, bw=0.18, seg=3)
    # 车头下压的引擎盖
    boxb("part_hood", (0.0, -1.60, 1.00), (1.72, 1.16, 0.24), P['paint'], rt, bw=0.12, seg=3)
    # 座舱：比车身窄、后移，顶部微收
    boxb("part_cabin", (0.0, 0.40, 1.42), (1.64, 2.10, 0.56), P['paint'], rt, bw=0.22, seg=4)
    boxb("part_roof", (0.0, 0.46, 1.70), (1.50, 1.86, 0.10), P['paint'], rt, bw=0.06, seg=2)
    # 玻璃
    box("part_windshield", (0.0, -0.62, 1.46), (1.50, 0.06, 0.52), P['glass'], rt, rx=math.radians(-26))
    box("part_rear_glass", (0.0, 1.42, 1.46), (1.46, 0.06, 0.46), P['glass'], rt, rx=math.radians(20))
    for i, x in enumerate([-0.83, 0.83]):
        box("part_side_glass_%d" % i, (x, 0.44, 1.46), (0.05, 1.94, 0.44), P['glass'], rt)
    # 后视镜
    for i, x in enumerate([-1.00, 1.00]):
        box("part_mirror_%d" % i, (x, -0.60, 1.30), (0.20, 0.10, 0.09), P['dark'], rt)
    # 腰线亮条（细，车身不发整片光）
    for i, x in enumerate([-0.955, 0.955]):
        box("part_beltline_%d" % i, (x, 0.10, 0.86), (0.03, 3.90, 0.035), P['gw'], rt)
    # 底盘 + 轮眉
    box("part_skirt", (0.0, 0.0, 0.40), (1.84, 4.06, 0.18), P['dark'], rt)
    for i, (x, y) in enumerate([(-0.90, -1.38), (0.90, -1.38), (-0.90, 1.38), (0.90, 1.38)]):
        box("part_arch_%d" % i, (x, y, 0.62), (0.24, 1.12, 0.46), P['dark'], rt)
    # 轮（轮胎 + 轮毂 + 中心盖）
    for i, (x, y) in enumerate([(-0.94, -1.42), (0.94, -1.42), (-0.94, 1.42), (0.94, 1.42)]):
        cyl("part_wheel_%d" % i, (x, y, 0.44), 0.44, 0.26, P['dark'], rt,
            rot=(0, math.radians(90), 0), verts=24)
        cyl("part_rim_%d" % i, (x * 1.03, y, 0.44), 0.26, 0.28, P['body'], rt,
            rot=(0, math.radians(90), 0), verts=20)
        cyl("part_hub_%d" % i, (x * 1.06, y, 0.44), 0.09, 0.30, P['dark'], rt,
            rot=(0, math.radians(90), 0), verts=12)
    # 贯穿式 LED 灯带（现代电车特征）
    box("part_head", (0.0, -2.13, 0.94), (1.62, 0.06, 0.07), P['gw'], rt)
    box("part_tail", (0.0, 2.13, 1.02), (1.66, 0.06, 0.08), P['gr'], rt)
    # 充电口（车身右后侧）
    box("part_port", (0.93, 1.30, 0.82), (0.06, 0.20, 0.14), P['gg'], rt)

    export("vehicle.glb")

# ============================================================
# 8. 园区信息亭
# ============================================================
def build_kiosk():
    reset()
    P = palette()
    rt = root("Kiosk_Root")

    boxb("part_base", (0.0, 0.0, 0.12), (1.70, 1.00, 0.24), P['dark'], rt, bw=0.03)
    boxb("part_body", (0.0, 0.0, 1.55), (1.50, 0.86, 2.62), P['body'], rt, bw=0.05)
    # 正面大屏（暗底发光）；边缘与标识为正常色
    box("part_screen", (0.0, -0.45, 1.72), (1.16, 0.03, 1.28), P['scr'], rt)
    box("part_screen_edge", (0.0, -0.47, 1.72), (1.26, 0.03, 1.40), P['dark'], rt)
    box("part_logo", (0.0, -0.45, 0.72), (0.70, 0.03, 0.14), P['body'], rt)
    boxb("part_cap", (0.0, 0.0, 2.94), (1.62, 0.96, 0.16), P['dark'], rt, bw=0.03)
    # 顶面压条：正常深色
    box("part_cap_glow", (0.0, -0.47, 2.90), (1.30, 0.03, 0.03), P['dark'], rt)

    # 底部矩形发光描边（本模型唯一发光源）
    base_outline("part_base_outline", 1.70, 1.00, P['gg'], rt, y=0.26)

    export("kiosk.glb")

# ============================================================
build_ground()
build_canopy()
build_storage()
build_pile()
build_transformer()
build_control_room()
build_vehicle()
build_kiosk()
print("ALL MODELS EXPORTED")
