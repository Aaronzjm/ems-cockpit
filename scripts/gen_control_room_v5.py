# -*- coding: utf-8 -*-
"""单独重生成配电室 v5：真实材质（墙面/桌面/椅子/屏幕/金属框架分开）+ 大屏闪烁根治"""
import bpy, bmesh, math, os

OUT = r"D:\1zjm\agent\ems-cockpit\public\models"

# ============================================================
# 基础工具（和v4保持一致）
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

def base_outline(name, w, d, m, parent, y=0.04, t=0.055):
    hw, hd = w / 2.0, d / 2.0
    box("%s_x0" % name, (0.0, -hd, y), (w, t, 0.02), m, parent)
    box("%s_x1" % name, (0.0,  hd, y), (w, t, 0.02), m, parent)
    box("%s_z0" % name, (-hw, 0.0, y), (t, d, 0.02), m, parent)
    box("%s_z1" % name, ( hw, 0.0, y), (t, d, 0.02), m, parent)

# ============================================================
# 配电室v5材质（接近现实）
# ============================================================
def palette_v5():
    return {
        # 结构
        'wall_white': M("WallWhite", (0.90, 0.86, 0.72, 1.0), 0.85, 0.0),  # 浅黄色乳胶漆墙面（现实配电室常见暖白/米黄）
        'floor_light': M("FloorLight", (0.62, 0.64, 0.67, 1.0), 0.75, 0.1),  # 浅灰色防静电地板
        'frame_dark': M("FrameDark", (0.18, 0.20, 0.23, 1.0), 0.45, 0.75),  # 深灰色金属框架/幕墙立柱
        'rim_metal': M("RimMetal", (0.22, 0.25, 0.28, 1.0), 0.40, 0.80),  # 屋顶金属包边
        # 家具
        'desk_metal': M("DeskMetal", (0.38, 0.42, 0.47, 1.0), 0.50, 0.65),  # 操作台金属框架（中灰金属）
        'desk_top': M("DeskTop", (0.15, 0.16, 0.18, 1.0), 0.60, 0.20),  # 黑色防静电台面
        'chair_black': M("ChairBlack", (0.10, 0.10, 0.12, 1.0), 0.70, 0.10),  # 黑色网布办公椅
        'chair_base': M("ChairBase", (0.25, 0.26, 0.28, 1.0), 0.40, 0.70),  # 椅子金属支架
        # 屏幕
        'screen_off': M("ScreenOff", (0.03, 0.04, 0.06, 1.0), 0.20, 0.0, (0.10, 0.35, 0.70, 1.0), 0.85),  # 亮蓝色屏幕（比v4亮一点，看得清）
        'screen_bezel': M("ScreenBezel", (0.08, 0.09, 0.11, 1.0), 0.40, 0.60),  # 屏幕黑色边框
        # 发光
        'glow_green': M("GlowGreen", (0.10, 1.0, 0.45, 1.0), 0.3, 0.0, (0.10, 1.0, 0.45, 1.0), 1.25),  # 底部绿色描边
        'dark': M("DarkMetal", (0.05, 0.06, 0.08, 1.0), 0.55, 0.35),  # 备用深色金属
    }

# ============================================================
# 配电室v5建模
# ============================================================
def build_control_room_v5():
    reset()
    P = palette_v5()
    rt = root("ControlRoom_Root")

    # 1. 底座/基础
    boxb("part_slab", (0.0, 0.0, 0.16), (7.6, 6.2, 0.32), P['frame_dark'], rt, bw=0.04)
    box("part_inner_floor", (0.0, 0.0, 0.32), (6.9, 5.5, 0.04), P['floor_light'], rt)  # 浅灰防静电地板，降低0.02避免共面

    # 2. 三面墙体（白色乳胶漆墙面）
    box("part_wall_back", (0.0, 3.0, 1.72), (7.5, 0.18, 3.10), P['wall_white'], rt)  # 墙厚减0.02
    for i, x in enumerate([-3.65, 3.65]):
        box("part_wall_side_%d" % i, (x, 0.0, 1.72), (0.18, 6.0, 3.10), P['wall_white'], rt)  # 墙厚减0.02

    # 3. 前侧金属幕墙骨架（深灰金属）
    for i in range(4):
        x = -3.6 + i * 2.4
        box("part_mullion_%d" % i, (x, -3.02, 1.72), (0.12, 0.12, 3.10), P['frame_dark'], rt)  # 前移0.02避免和屋顶共面
    box("part_lintel", (0.0, -3.02, 3.20), (7.6, 0.16, 0.18), P['frame_dark'], rt)  # 前移0.02

    # 4. 屋顶金属包边
    box("part_rim_back", (0.0, 3.0, 3.36), (7.6, 0.16, 0.10), P['rim_metal'], rt)
    box("part_rim_front", (0.0, -3.06, 3.36), (7.6, 0.12, 0.10), P['rim_metal'], rt)
    for i, x in enumerate([-3.7, 3.7]):
        box("part_rim_side_%d" % i, (x, 0.0, 3.36), (0.12, 6.12, 0.10), P['rim_metal'], rt)
    box("part_rim_glow", (0.0, -3.06, 3.32), (7.4, 0.02, 0.02), P['glow_green'], rt)  # 檐口小绿灯带

    # 5. 主控操作台（两排）
    for r, (zz, ww) in enumerate([(-1.10, 4.6), (0.55, 3.4)]):
        # 金属桌架
        boxb("part_desk_%d" % r, (0.0, zz, 0.85), (ww, 0.85, 0.85), P['desk_metal'], rt, bw=0.025)
        # 黑色台面
        box("part_desk_top_%d" % r, (0.0, zz, 1.32), (ww + 0.08, 0.95, 0.05), P['desk_top'], rt)
        # 显示器
        n = int(ww / 1.15)
        for k in range(max(n, 2)):
            x = (k - (max(n, 2) - 1) / 2.0) * 1.15
            # 屏幕往前挪0.04，彻底避免和背面/墙共面闪烁
            box("part_mon_%d_%d" % (r, k), (x, zz - 0.38, 1.60), (0.74, 0.04, 0.44), P['screen_off'], rt)
            # 黑色屏幕边框
            box("part_mon_base_%d_%d" % (r, k), (x, zz - 0.32, 1.38), (0.18, 0.16, 0.12), P['screen_bezel'], rt)

    # 6. 办公椅（黑色）
    for k in range(4):
        x = -1.8 + k * 1.2
        box("part_chair_%d" % k, (x, -1.95, 0.55), (0.50, 0.50, 0.10), P['chair_black'], rt)
        box("part_chair_back_%d" % k, (x, -1.68, 0.90), (0.50, 0.10, 0.58), P['chair_black'], rt)
        # 椅子金属支架
        cyl("part_chair_pole_%d" % k, (x, -1.95, 0.32), 0.03, 0.38, P['chair_base'], rt)
        cyl("part_chair_base_ring_%d" % k, (x, -1.95, 0.10), 0.22, 0.03, P['chair_base'], rt)

    # 7. 后墙大屏（数据大屏，根治闪烁：屏幕往前突出0.05，完全离开边框/墙面）
    box("part_bigscreen", (0.0, 2.75, 2.10), (4.70, 0.05, 1.45), P['screen_off'], rt)  # 前移+缩小，完全不共面
    box("part_bigscreen_frame", (0.0, 2.80, 2.00), (4.95, 0.12, 1.65), P['screen_bezel'], rt)  # 边框在后，形成包裹效果

    # 8. 侧墙屏
    for i, x in enumerate([-3.54, 3.54]):
        box("part_sidescreen_%d" % i, (x, 1.10, 1.95), (0.04, 2.05, 1.00), P['screen_off'], rt)  # 微前移避免共面
        box("part_sidescreen_frame_%d" % i, (x, 1.10, 1.92), (0.08, 2.15, 1.05), P['screen_bezel'], rt)

    # 9. 地面防静电地板接缝（浅灰）
    box("part_floor_glow", (0.0, -2.55, 0.37), (6.4, 0.04, 0.02), P['floor_light'], rt)

    # 10. 底部绿色描边（唯一强发光源）
    base_outline("part_base_outline", 7.6, 6.2, P['glow_green'], rt, y=0.34)

    export("control_room.glb")

def export(fn):
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, fn), export_format='GLB')
    print("SUCCESS: " + fn)

if __name__ == "__main__":
    build_control_room_v5()
