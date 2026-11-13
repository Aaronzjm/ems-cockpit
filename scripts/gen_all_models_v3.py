import bpy
import math
import os

OUTPUT_DIR = r"D:\1zjm\agent\ems-cockpit\public\models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_mat(name, color, roughness=0.55, metallic=0.3, emissive=None, emissive_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Metallic'].default_value = metallic
        if emissive:
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = emissive
            elif 'Emission' in bsdf.inputs:
                bsdf.inputs['Emission'].default_value = emissive
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = emissive_strength
    return mat

def add_base_outline(root, w, d, mat, cx=0.0, cz=0.0, y=0.03, t=0.06, name="part_base_glow"):
    """在设备底座四周加一圈细发光描边（空心矩形框），这是唯一的强发光源。"""
    hw, hd = w / 2.0, d / 2.0
    specs = [
        (cx, cz - hd, w, t),
        (cx, cz + hd, w, t),
        (cx - hw, cz, t, d),
        (cx + hw, cz, t, d),
    ]
    for i, (x, z, sx, sz) in enumerate(specs):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, z, y))
        o = bpy.context.active_object
        o.name = f"{name}_{i}"
        o.scale = (sx, sz, t)
        o.data.materials.append(mat)
        o.parent = root

# ---- 统一材质：结构件低金属度、高粗糙度，避免镜面高光被 Bloom 捕捉 ----
def mats():
    return {
        'dark':      create_mat("DarkMetal", (0.055, 0.065, 0.08, 1.0), roughness=0.55, metallic=0.35),
        'body':      create_mat("DarkBody", (0.085, 0.095, 0.115, 1.0), roughness=0.5, metallic=0.3),
        'panel':     create_mat("SolarCell", (0.025, 0.045, 0.1, 1.0), roughness=0.4, metallic=0.45),
        'copper':    create_mat("CoreCopper", (0.55, 0.32, 0.14, 1.0), roughness=0.45, metallic=0.35),
        'wall':      create_mat("WallDark", (0.06, 0.07, 0.085, 1.0), roughness=0.6, metallic=0.25),
        'ground':    create_mat("GroundPlate", (0.035, 0.04, 0.05, 1.0), roughness=0.7, metallic=0.2),
        # 发光材质：强度压到 1.15，只作为底部描边和细缝，不烧白
        'glow_g':    create_mat("GlowGreen", (0.06, 0.85, 0.42, 1.0), roughness=0.3, metallic=0.0, emissive=(0.06, 0.85, 0.42, 1.0), emissive_strength=1.15),
        'glow_b':    create_mat("GlowBlue", (0.15, 0.6, 1.0, 1.0), roughness=0.3, metallic=0.0, emissive=(0.15, 0.6, 1.0, 1.0), emissive_strength=1.15),
        'glow_y':    create_mat("GlowGold", (0.85, 0.6, 0.1, 1.0), roughness=0.35, metallic=0.1, emissive=(0.85, 0.6, 0.1, 1.0), emissive_strength=1.0),
        'slot':      create_mat("SlotLine", (0.05, 0.35, 0.2, 1.0), roughness=0.5, metallic=0.0, emissive=(0.03, 0.45, 0.2, 1.0), emissive_strength=0.75),
    }

# =========================================================
# 1. 智能快充桩
# =========================================================
def build_charging_pile():
    reset_scene()
    M = mats()
    root = bpy.data.objects.new("ChargingPile_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.08))
    o = bpy.context.active_object; o.name = "part_base"
    o.scale = (0.6, 0.5, 0.16); o.data.materials.append(M['dark']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.0))
    o = bpy.context.active_object; o.name = "part_body_frame"
    o.scale = (0.5, 0.4, 1.7); o.data.materials.append(M['body']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.22, 1.1))
    o = bpy.context.active_object; o.name = "part_front_panel"
    o.scale = (0.42, 0.04, 1.1); o.data.materials.append(M['dark']); o.parent = root

    # 屏幕（细发光）+ 深色屏框
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.25, 1.32))
    o = bpy.context.active_object; o.name = "part_screen"
    o.scale = (0.26, 0.02, 0.2); o.data.materials.append(M['glow_b']); o.parent = root

    # 顶部：深色顶盖 + 一条细发光缝（不再是整块发光顶盖）
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.88))
    o = bpy.context.active_object; o.name = "part_top_cap"
    o.scale = (0.52, 0.42, 0.06); o.data.materials.append(M['dark']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.215, 1.855))
    o = bpy.context.active_object; o.name = "part_top_edge_glow"
    o.scale = (0.44, 0.02, 0.02); o.data.materials.append(M['glow_g']); o.parent = root

    for i, x in enumerate([-0.3, 0.3]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 0.95))
        o = bpy.context.active_object
        o.name = f"part_gun_{'left' if i==0 else 'right'}"
        o.scale = (0.1, 0.2, 0.4); o.data.materials.append(M['dark']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.0))
    o = bpy.context.active_object; o.name = "part_internal_core"
    o.scale = (0.35, 0.25, 1.2); o.data.materials.append(M['copper']); o.parent = root

    # 底部描边发光
    add_base_outline(root, 0.74, 0.62, M['glow_g'], y=0.02, t=0.05)

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "charging_pile.glb"), export_format='GLB')
    print("SUCCESS: charging_pile.glb")

# =========================================================
# 2. 光伏雨棚
# =========================================================
def build_canopy():
    reset_scene()
    M = mats()
    root = bpy.data.objects.new("Canopy_Root", None)
    bpy.context.scene.collection.objects.link(root)

    for i, x in enumerate([-2.8, 2.8]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 1.4))
        o = bpy.context.active_object; o.name = f"part_pillar_{i+1}"
        o.scale = (0.18, 0.18, 2.8); o.data.materials.append(M['dark']); o.parent = root
        # 每根立柱底部一圈细描边
        add_base_outline(root, 0.34, 0.34, M['glow_g'], cx=x, cz=0.0, y=0.02, t=0.05, name=f"part_pillar_glow_{i+1}")

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.85))
    o = bpy.context.active_object; o.name = "part_canopy_frame"
    o.scale = (6.2, 3.0, 0.1); o.data.materials.append(M['body']); o.parent = root

    # 雨棚前后两条极细导光条
    for i, y in enumerate([-1.52, 1.52]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, y, 2.92))
        o = bpy.context.active_object; o.name = f"part_glow_bar_{i+1}"
        o.scale = (6.2, 0.025, 0.025); o.data.materials.append(M['glow_g']); o.parent = root

    for r in range(2):
        for c in range(3):
            px = (c - 1.0) * 1.95
            py = (r - 0.5) * 1.4
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, 2.98))
            o = bpy.context.active_object; o.name = f"part_panel_{r}_{c}"
            o.scale = (1.85, 1.3, 0.05); o.data.materials.append(M['panel']); o.parent = root

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "photovoltaic_canopy.glb"), export_format='GLB')
    print("SUCCESS: photovoltaic_canopy.glb")

# =========================================================
# 3. 储能电池舱
# =========================================================
def build_storage():
    reset_scene()
    M = mats()
    root = bpy.data.objects.new("Storage_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.12))
    o = bpy.context.active_object; o.name = "part_base_frame"
    o.scale = (4.0, 1.9, 0.24); o.data.materials.append(M['dark']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.1))
    o = bpy.context.active_object; o.name = "part_roof_hatch"
    o.scale = (4.05, 1.95, 0.15); o.data.materials.append(M['body']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.0, 0, 2.35))
    o = bpy.context.active_object; o.name = "part_hvac_unit"
    o.scale = (1.0, 1.2, 0.35); o.data.materials.append(M['dark']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.92, 1.1))
    o = bpy.context.active_object; o.name = "part_back_wall"
    o.scale = (3.95, 0.06, 1.7); o.data.materials.append(M['body']); o.parent = root

    for i, x in enumerate([-1.98, 1.98]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 1.1))
        o = bpy.context.active_object; o.name = f"part_{'left' if i==0 else 'right'}_wall"
        o.scale = (0.06, 1.85, 1.7); o.data.materials.append(M['body']); o.parent = root

    for i, x in enumerate([-0.95, 0.95]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -0.92, 1.1))
        o = bpy.context.active_object; o.name = f"part_door_{'left' if i==0 else 'right'}"
        o.scale = (1.85, 0.05, 1.7); o.data.materials.append(M['dark']); o.parent = root

    for i in range(4):
        x = -1.35 + i * 0.9
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0.0, 1.1))
        o = bpy.context.active_object; o.name = f"part_battery_rack_{i+1}"
        o.scale = (0.75, 1.3, 1.55); o.data.materials.append(M['dark']); o.parent = root

        # 只留一条极细状态灯（不再是整面 LED）
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -0.66, 1.72))
        o = bpy.context.active_object; o.name = f"part_rack_led_{i+1}"
        o.scale = (0.5, 0.02, 0.02); o.data.materials.append(M['glow_g']); o.parent = root

    # 底部描边发光（就是这一圈）
    add_base_outline(root, 4.12, 2.02, M['glow_g'], y=0.02, t=0.06)

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "storage_container.glb"), export_format='GLB')
    print("SUCCESS: storage_container.glb")

# =========================================================
# 4. 配电变压器
# =========================================================
def build_transformer():
    reset_scene()
    M = mats()
    root = bpy.data.objects.new("Transformer_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.1))
    o = bpy.context.active_object; o.name = "part_base"
    o.scale = (2.0, 1.6, 0.2); o.data.materials.append(M['dark']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.95))
    o = bpy.context.active_object; o.name = "part_main_tank"
    o.scale = (1.4, 1.1, 1.4); o.data.materials.append(M['body']); o.parent = root

    for i, x in enumerate([-0.85, 0.85]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 0.95))
        o = bpy.context.active_object; o.name = f"part_radiator_{'left' if i==0 else 'right'}"
        o.scale = (0.25, 1.0, 1.2); o.data.materials.append(M['dark']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.72))
    o = bpy.context.active_object; o.name = "part_top_lid"
    o.scale = (1.5, 1.2, 0.12); o.data.materials.append(M['dark']); o.parent = root

    for i, x in enumerate([-0.4, 0.0, 0.4]):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.42, location=(x, 0, 2.0))
        o = bpy.context.active_object; o.name = f"part_bushing_{i+1}"
        o.data.materials.append(M['copper']); o.parent = root

    # 底部描边发光（变压器本体保持正常颜色）
    add_base_outline(root, 2.12, 1.72, M['glow_g'], y=0.02, t=0.06)

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "transformer_substation.glb"), export_format='GLB')
    print("SUCCESS: transformer_substation.glb")

# =========================================================
# 5. 园区底座
# =========================================================
def build_ground():
    reset_scene()
    M = mats()
    root = bpy.data.objects.new("Ground_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.15))
    o = bpy.context.active_object; o.name = "part_main_ground"
    o.scale = (24.0, 16.0, 0.3); o.data.materials.append(M['ground']); o.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.5, -7.95, 0.01))
    o = bpy.context.active_object; o.name = "part_gold_curb"
    o.scale = (23.0, 0.05, 0.035); o.data.materials.append(M['glow_y']); o.parent = root

    for spot in range(3):
        x = -6.0 + spot * 3.4
        for li, (lx, ly, sx, sy) in enumerate([
            (x, -3.2, 2.4, 0.035),
            (x, 0.8, 2.4, 0.035),
            (x - 1.18, -1.2, 0.035, 4.0),
            (x + 1.18, -1.2, 0.035, 4.0),
        ]):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(lx, ly, 0.01))
            o = bpy.context.active_object; o.name = f"part_slot_{spot+1}_line_{li}"
            o.scale = (sx, sy, 0.018); o.data.materials.append(M['slot']); o.parent = root

    # 配电室：放到园区后方正中央，避开设备区
    # 注意 Blender Z-up 导出 glTF 会变成 Y-up（x,y,z → x,z,-y），
    # 所以 Blender (0, 6.5, 1.1) => 世界坐标 (0, 1.1, -6.5)，即后方中央
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 6.5, 1.1))
    o = bpy.context.active_object; o.name = "part_control_room_frame"
    o.scale = (5.0, 3.2, 2.2); o.data.materials.append(M['wall']); o.parent = root

    # 檐口只做四边细描边，绝不能是整块发光平板（否则 Bloom 会烧成一个白面）
    add_base_outline(root, 5.1, 3.3, M['glow_g'], cx=0.0, cz=6.5, y=2.22, t=0.04, name="part_control_room_glow")

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "ground_facility.glb"), export_format='GLB')
    print("SUCCESS: ground_facility.glb")

build_charging_pile()
build_canopy()
build_storage()
build_transformer()
build_ground()
