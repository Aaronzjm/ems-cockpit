import bpy
import math
import os

OUTPUT_DIR = r"D:\1zjm\agent\ems-cockpit\public\models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_mat(name, color, roughness=0.35, metallic=0.7, emissive=None, emissive_strength=1.0):
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

def build_all():
    # -------------------------------------------------------------
    # 1. 光伏雨棚系统 (photovoltaic_canopy.glb)
    # -------------------------------------------------------------
    reset_scene()
    mat_dark = create_mat("DarkFrame", (0.06, 0.06, 0.08, 1.0), roughness=0.35, metallic=0.9)
    mat_solar = create_mat("SolarCell", (0.01, 0.06, 0.22, 1.0), roughness=0.15, metallic=0.95, emissive=(0.02, 0.15, 0.45, 1.0), emissive_strength=0.8)
    mat_green = create_mat("CanopyGlow", (0.02, 0.95, 0.35, 1.0), roughness=0.1, metallic=0.1, emissive=(0.02, 0.95, 0.35, 1.0), emissive_strength=5.0)

    root = bpy.data.objects.new("Canopy_Root", None)
    bpy.context.scene.collection.objects.link(root)

    # 4根立柱柱基与立柱
    for i, x in enumerate([-2.8, 2.8]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 1.4))
        pillar = bpy.context.active_object
        pillar.name = f"part_pillar_{i+1}"
        pillar.scale = (0.22, 0.22, 2.8)
        pillar.data.materials.append(mat_dark)
        pillar.parent = root

    # 顶部承重桁架横梁
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.85))
    beam = bpy.context.active_object
    beam.name = "part_canopy_frame"
    beam.scale = (6.4, 3.2, 0.15)
    beam.data.materials.append(mat_dark)
    beam.parent = root

    # 边缘发光导光条
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -1.62, 2.87))
    glow_bar1 = bpy.context.active_object
    glow_bar1.name = "part_glow_front"
    glow_bar1.scale = (6.42, 0.05, 0.08)
    glow_bar1.data.materials.append(mat_green)
    glow_bar1.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 1.62, 2.87))
    glow_bar2 = bpy.context.active_object
    glow_bar2.name = "part_glow_back"
    glow_bar2.scale = (6.42, 0.05, 0.08)
    glow_bar2.data.materials.append(mat_green)
    glow_bar2.parent = root

    # 6 组独立太阳能光伏板组 (方便爆炸沿Z轴向上、各向错落飞散)
    cols = 3
    rows = 2
    for r in range(rows):
        for c in range(cols):
            px = (c - 1.0) * 2.05
            py = (r - 0.5) * 1.5
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, 3.0))
            panel = bpy.context.active_object
            panel.name = f"part_panel_{r}_{c}"
            panel.scale = (1.95, 1.4, 0.08)
            panel.data.materials.append(mat_solar)
            panel.parent = root

    # 逆变汇流电箱 (安装在立柱旁)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.8, -0.25, 1.4))
    inverter = bpy.context.active_object
    inverter.name = "part_inverter_box"
    inverter.scale = (0.35, 0.2, 0.6)
    inverter.data.materials.append(mat_dark)
    inverter.parent = root

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "photovoltaic_canopy.glb"), export_format='GLB')
    print("SUCCESS: photovoltaic_canopy.glb")

    # -------------------------------------------------------------
    # 2. 储能电池集装箱 (storage_container.glb)
    # -------------------------------------------------------------
    reset_scene()
    mat_shell = create_mat("CabinetShell", (0.05, 0.05, 0.06, 1.0), roughness=0.3, metallic=0.9)
    mat_rack = create_mat("BatteryRack", (0.12, 0.14, 0.16, 1.0), roughness=0.3, metallic=0.7)
    mat_green_led = create_mat("RackLed", (0.02, 0.95, 0.35, 1.0), roughness=0.1, metallic=0.1, emissive=(0.02, 0.95, 0.35, 1.0), emissive_strength=6.0)

    root = bpy.data.objects.new("Storage_Root", None)
    bpy.context.scene.collection.objects.link(root)

    # 底部基座
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.15))
    base = bpy.context.active_object
    base.name = "part_base_frame"
    base.scale = (4.2, 2.0, 0.3)
    base.data.materials.append(mat_shell)
    base.parent = root

    # 集装箱顶盖外壳 (爆炸时向上推开)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.2))
    roof = bpy.context.active_object
    roof.name = "part_roof_hatch"
    roof.scale = (4.25, 2.05, 0.25)
    roof.data.materials.append(mat_shell)
    roof.parent = root

    # 顶部工业空调机组 (附在顶盖上或单独飞起)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.0, 0, 2.55))
    hvac = bpy.context.active_object
    hvac.name = "part_hvac_unit"
    hvac.scale = (1.2, 1.4, 0.45)
    hvac.data.materials.append(mat_shell)
    hvac.parent = root

    # 侧边护板 (左侧、右侧、后侧)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.98, 1.15))
    back_wall = bpy.context.active_object
    back_wall.name = "part_back_wall"
    back_wall.scale = (4.15, 0.08, 1.8)
    back_wall.data.materials.append(mat_shell)
    back_wall.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-2.05, 0, 1.15))
    left_wall = bpy.context.active_object
    left_wall.name = "part_left_wall"
    left_wall.scale = (0.08, 1.95, 1.8)
    left_wall.data.materials.append(mat_shell)
    left_wall.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(2.05, 0, 1.15))
    right_wall = bpy.context.active_object
    right_wall.name = "part_right_wall"
    right_wall.scale = (0.08, 1.95, 1.8)
    right_wall.data.materials.append(mat_shell)
    right_wall.parent = root

    # 前面透明/发光观察门 (左右两扇，爆炸时向前平移拉开)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.0, -0.98, 1.15))
    door_l = bpy.context.active_object
    door_l.name = "part_door_left"
    door_l.scale = (2.0, 0.06, 1.8)
    door_l.data.materials.append(mat_shell)
    door_l.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.0, -0.98, 1.15))
    door_r = bpy.context.active_object
    door_r.name = "part_door_right"
    door_r.scale = (2.0, 0.06, 1.8)
    door_r.data.materials.append(mat_shell)
    door_r.parent = root

    # 4 组独立电池模组簇 (Battery Racks，内部核心部件，爆炸时向外抽出)
    for i in range(4):
        x = -1.5 + i * 1.0
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0.0, 1.15))
        rack = bpy.context.active_object
        rack.name = f"part_battery_rack_{i+1}"
        rack.scale = (0.8, 1.4, 1.7)
        rack.data.materials.append(mat_rack)
        rack.parent = root

        # 电池簇正面高亮状态灯带
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -0.71, 1.15))
        led = bpy.context.active_object
        led.name = f"part_rack_led_{i+1}"
        led.scale = (0.7, 0.02, 1.5)
        led.data.materials.append(mat_green_led)
        led.parent = rack

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "storage_container.glb"), export_format='GLB')
    print("SUCCESS: storage_container.glb")

    # -------------------------------------------------------------
    # 3. 配电箱与主变压器系统 (transformer_substation.glb)
    # -------------------------------------------------------------
    reset_scene()
    mat_metal = create_mat("TransMetal", (0.08, 0.08, 0.1, 1.0), roughness=0.35, metallic=0.85)
    mat_copper = create_mat("CopperInsulator", (0.8, 0.45, 0.15, 1.0), roughness=0.2, metallic=0.6)
    mat_caution = create_mat("CautionYellow", (0.95, 0.75, 0.05, 1.0), roughness=0.3, metallic=0.2, emissive=(0.95, 0.75, 0.05, 1.0), emissive_strength=1.5)

    root = bpy.data.objects.new("Transformer_Root", None)
    bpy.context.scene.collection.objects.link(root)

    # 槽钢底座
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.12))
    base = bpy.context.active_object
    base.name = "part_base"
    base.scale = (2.2, 1.8, 0.24)
    base.data.materials.append(mat_metal)
    base.parent = root

    # 变压器主箱体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.0))
    body = bpy.context.active_object
    body.name = "part_main_tank"
    body.scale = (1.5, 1.2, 1.5)
    body.data.materials.append(mat_metal)
    body.parent = root

    # 左侧散热翅片板 (Radiator Fins Left)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.95, 0, 1.0))
    rad_l = bpy.context.active_object
    rad_l.name = "part_radiator_left"
    rad_l.scale = (0.35, 1.1, 1.3)
    rad_l.data.materials.append(mat_metal)
    rad_l.parent = root

    # 右侧散热翅片板 (Radiator Fins Right)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.95, 0, 1.0))
    rad_r = bpy.context.active_object
    rad_r.name = "part_radiator_right"
    rad_r.scale = (0.35, 1.1, 1.3)
    rad_r.data.materials.append(mat_metal)
    rad_r.parent = root

    # 顶盖 (爆炸时升起)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.85))
    top_lid = bpy.context.active_object
    top_lid.name = "part_top_lid"
    top_lid.scale = (1.6, 1.3, 0.15)
    top_lid.data.materials.append(mat_metal)
    top_lid.parent = root

    # 3个高压绝缘瓷瓶套管 (High Voltage Bushings)
    for i, x in enumerate([-0.45, 0.0, 0.45]):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.09, depth=0.55, location=(x, 0, 2.18))
        bushing = bpy.context.active_object
        bushing.name = f"part_bushing_{i+1}"
        bushing.data.materials.append(mat_copper)
        bushing.parent = top_lid

    # 变压器核心线圈绕组 (藏在箱体内部，爆炸时升起暴露)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=1.1, location=(0, 0, 1.0))
    core_coil = bpy.context.active_object
    core_coil.name = "part_core_winding"
    core_coil.data.materials.append(mat_caution)
    core_coil.parent = root

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "transformer_substation.glb"), export_format='GLB')
    print("SUCCESS: transformer_substation.glb")

    # -------------------------------------------------------------
    # 4. 园区综合底座与建筑边界 (ground_facility.glb)
    # -------------------------------------------------------------
    reset_scene()
    mat_ground = create_mat("GroundDark", (0.04, 0.04, 0.05, 1.0), roughness=0.55, metallic=0.6)
    mat_curb = create_mat("CurbGold", (0.9, 0.7, 0.1, 1.0), roughness=0.2, metallic=0.5, emissive=(0.9, 0.7, 0.1, 1.0), emissive_strength=4.0)
    mat_lane = create_mat("LaneGreen", (0.02, 0.95, 0.35, 1.0), roughness=0.2, metallic=0.1, emissive=(0.02, 0.95, 0.35, 1.0), emissive_strength=3.0)
    mat_room_wall = create_mat("RoomWall", (0.07, 0.07, 0.09, 1.0), roughness=0.4, metallic=0.8)

    root = bpy.data.objects.new("Ground_Root", None)
    bpy.context.scene.collection.objects.link(root)

    # 园区大底座地台
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.2))
    ground = bpy.context.active_object
    ground.name = "part_main_ground"
    ground.scale = (24.0, 16.0, 0.4)
    ground.data.materials.append(mat_ground)
    ground.parent = root

    # 底部流光金线边缘 (如同参考图左下金色微弧角金边)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.5, -8.02, 0.02))
    curb = bpy.context.active_object
    curb.name = "part_gold_curb"
    curb.scale = (23.0, 0.1, 0.1)
    curb.data.materials.append(mat_curb)
    curb.parent = root

    # 充电车位绿色地面引导虚线框
    for spot in range(3):
        x = -6.0 + spot * 3.5
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -1.0, 0.02))
        slot = bpy.context.active_object
        slot.name = f"part_parking_slot_{spot+1}"
        slot.scale = (2.6, 4.8, 0.01)
        slot.data.materials.append(mat_lane)
        slot.parent = root

    # 右下角【配电监控室】建筑墙体
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(7.5, -3.5, 1.2))
    control_room = bpy.context.active_object
    control_room.name = "part_control_room_frame"
    control_room.scale = (7.5, 6.5, 2.4)
    control_room.data.materials.append(mat_room_wall)
    control_room.parent = root

    # 配电室屋顶发光檐线
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(7.5, -3.5, 2.45))
    room_roof = bpy.context.active_object
    room_roof.name = "part_control_room_glow"
    room_roof.scale = (7.6, 6.6, 0.1)
    room_roof.data.materials.append(mat_lane)
    room_roof.parent = root

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "ground_facility.glb"), export_format='GLB')
    print("SUCCESS: ground_facility.glb")

build_all()
