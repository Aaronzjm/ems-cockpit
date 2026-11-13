import bpy
import math
import os

OUTPUT_DIR = r"D:\1zjm\agent\ems-cockpit\public\models"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_mat(name, color, roughness=0.45, metallic=0.6, emissive=None, emissive_strength=1.0):
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

def build_charging_pile():
    reset_scene()
    mat_dark = create_mat("DarkMetal", (0.05, 0.06, 0.07, 1.0), roughness=0.45, metallic=0.7)
    mat_dark_body = create_mat("DarkBody", (0.08, 0.09, 0.11, 1.0), roughness=0.4, metallic=0.6)
    mat_blue_glow = create_mat("GlowBlue", (0.1, 0.6, 1.0, 1.0), roughness=0.2, metallic=0.1, emissive=(0.1, 0.6, 1.0, 1.0), emissive_strength=1.5)
    mat_green_glow = create_mat("GlowGreen", (0.05, 0.9, 0.35, 1.0), roughness=0.2, metallic=0.1, emissive=(0.05, 0.9, 0.35, 1.0), emissive_strength=1.5)
    mat_core_copper = create_mat("CoreCopper", (0.6, 0.35, 0.15, 1.0), roughness=0.3, metallic=0.6)

    root = bpy.data.objects.new("ChargingPile_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.08))
    base = bpy.context.active_object
    base.name = "part_base"
    base.scale = (0.6, 0.5, 0.16)
    base.data.materials.append(mat_dark)
    base.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.0))
    body = bpy.context.active_object
    body.name = "part_body_frame"
    body.scale = (0.5, 0.4, 1.7)
    body.data.materials.append(mat_dark_body)
    body.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.22, 1.1))
    front_panel = bpy.context.active_object
    front_panel.name = "part_front_panel"
    front_panel.scale = (0.42, 0.04, 1.1)
    front_panel.data.materials.append(mat_dark)
    front_panel.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.25, 1.3))
    screen = bpy.context.active_object
    screen.name = "part_screen"
    screen.scale = (0.28, 0.02, 0.22)
    screen.data.materials.append(mat_blue_glow)
    screen.parent = front_panel

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.88))
    top_cap = bpy.context.active_object
    top_cap.name = "part_top_cap"
    top_cap.scale = (0.52, 0.42, 0.06)
    top_cap.data.materials.append(mat_green_glow)
    top_cap.parent = root

    for i, x in enumerate([-0.3, 0.3]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 0.95))
        gun = bpy.context.active_object
        gun.name = f"part_gun_{'left' if i==0 else 'right'}"
        gun.scale = (0.1, 0.2, 0.4)
        gun.data.materials.append(mat_dark)
        gun.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.0))
    core = bpy.context.active_object
    core.name = "part_internal_core"
    core.scale = (0.35, 0.25, 1.2)
    core.data.materials.append(mat_core_copper)
    core.parent = root

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "charging_pile.glb"), export_format='GLB')
    print("SUCCESS: charging_pile.glb")

def build_canopy():
    reset_scene()
    mat_dark = create_mat("DarkMetal", (0.05, 0.06, 0.07, 1.0), roughness=0.45, metallic=0.7)
    mat_dark_body = create_mat("DarkBody", (0.08, 0.09, 0.11, 1.0), roughness=0.4, metallic=0.6)
    mat_green_glow = create_mat("GlowGreen", (0.05, 0.9, 0.35, 1.0), roughness=0.2, metallic=0.1, emissive=(0.05, 0.9, 0.35, 1.0), emissive_strength=1.5)
    mat_panel = create_mat("SolarCell", (0.02, 0.04, 0.1, 1.0), roughness=0.25, metallic=0.85)

    root = bpy.data.objects.new("Canopy_Root", None)
    bpy.context.scene.collection.objects.link(root)

    for i, x in enumerate([-2.8, 2.8]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 1.4))
        pillar = bpy.context.active_object
        pillar.name = f"part_pillar_{i+1}"
        pillar.scale = (0.18, 0.18, 2.8)
        pillar.data.materials.append(mat_dark)
        pillar.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.85))
    beam = bpy.context.active_object
    beam.name = "part_canopy_frame"
    beam.scale = (6.2, 3.0, 0.1)
    beam.data.materials.append(mat_dark_body)
    beam.parent = root

    for i, y in enumerate([-1.52, 1.52]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, y, 2.9))
        bar = bpy.context.active_object
        bar.name = f"part_glow_bar_{i+1}"
        bar.scale = (6.2, 0.03, 0.03)
        bar.data.materials.append(mat_green_glow)
        bar.parent = root

    for r in range(2):
        for c in range(3):
            px = (c - 1.0) * 1.95
            py = (r - 0.5) * 1.4
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(px, py, 2.98))
            panel = bpy.context.active_object
            panel.name = f"part_panel_{r}_{c}"
            panel.scale = (1.85, 1.3, 0.05)
            panel.data.materials.append(mat_panel)
            panel.parent = root

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "photovoltaic_canopy.glb"), export_format='GLB')
    print("SUCCESS: photovoltaic_canopy.glb")

def build_storage():
    reset_scene()
    mat_dark = create_mat("DarkMetal", (0.05, 0.06, 0.07, 1.0), roughness=0.45, metallic=0.7)
    mat_dark_body = create_mat("DarkBody", (0.08, 0.09, 0.11, 1.0), roughness=0.4, metallic=0.6)
    mat_green_glow = create_mat("GlowGreen", (0.05, 0.9, 0.35, 1.0), roughness=0.2, metallic=0.1, emissive=(0.05, 0.9, 0.35, 1.0), emissive_strength=1.5)

    root = bpy.data.objects.new("Storage_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.12))
    base = bpy.context.active_object
    base.name = "part_base_frame"
    base.scale = (4.0, 1.9, 0.24)
    base.data.materials.append(mat_dark)
    base.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.1))
    roof = bpy.context.active_object
    roof.name = "part_roof_hatch"
    roof.scale = (4.05, 1.95, 0.15)
    roof.data.materials.append(mat_dark_body)
    roof.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.0, 0, 2.35))
    hvac = bpy.context.active_object
    hvac.name = "part_hvac_unit"
    hvac.scale = (1.0, 1.2, 0.35)
    hvac.data.materials.append(mat_dark)
    hvac.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.92, 1.1))
    bw = bpy.context.active_object
    bw.name = "part_back_wall"
    bw.scale = (3.95, 0.06, 1.7)
    bw.data.materials.append(mat_dark_body)
    bw.parent = root

    for i, x in enumerate([-1.98, 1.98]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 1.1))
        sw = bpy.context.active_object
        sw.name = f"part_{'left' if i==0 else 'right'}_wall"
        sw.scale = (0.06, 1.85, 1.7)
        sw.data.materials.append(mat_dark_body)
        sw.parent = root

    for i, x in enumerate([-0.95, 0.95]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -0.92, 1.1))
        door = bpy.context.active_object
        door.name = f"part_door_{'left' if i==0 else 'right'}"
        door.scale = (1.85, 0.05, 1.7)
        door.data.materials.append(mat_dark)
        door.parent = root

    for i in range(4):
        x = -1.35 + i * 0.9
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0.0, 1.1))
        rack = bpy.context.active_object
        rack.name = f"part_battery_rack_{i+1}"
        rack.scale = (0.75, 1.3, 1.55)
        rack.data.materials.append(mat_dark)
        rack.parent = root

        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, -0.66, 1.1))
        led = bpy.context.active_object
        led.name = f"part_rack_led_{i+1}"
        led.scale = (0.5, 0.02, 0.04)
        led.data.materials.append(mat_green_glow)
        led.parent = rack

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "storage_container.glb"), export_format='GLB')
    print("SUCCESS: storage_container.glb")

def build_transformer():
    reset_scene()
    mat_dark = create_mat("DarkMetal", (0.05, 0.06, 0.07, 1.0), roughness=0.45, metallic=0.7)
    mat_dark_body = create_mat("DarkBody", (0.08, 0.09, 0.11, 1.0), roughness=0.4, metallic=0.6)
    mat_core_copper = create_mat("CoreCopper", (0.6, 0.35, 0.15, 1.0), roughness=0.3, metallic=0.6)

    root = bpy.data.objects.new("Transformer_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.1))
    base = bpy.context.active_object
    base.name = "part_base"
    base.scale = (2.0, 1.6, 0.2)
    base.data.materials.append(mat_dark)
    base.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.95))
    tank = bpy.context.active_object
    tank.name = "part_main_tank"
    tank.scale = (1.4, 1.1, 1.4)
    tank.data.materials.append(mat_dark_body)
    tank.parent = root

    for i, x in enumerate([-0.85, 0.85]):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, 0, 0.95))
        rad = bpy.context.active_object
        rad.name = f"part_radiator_{'left' if i==0 else 'right'}"
        rad.scale = (0.25, 1.0, 1.2)
        rad.data.materials.append(mat_dark)
        rad.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.72))
    lid = bpy.context.active_object
    lid.name = "part_top_lid"
    lid.scale = (1.5, 1.2, 0.12)
    lid.data.materials.append(mat_dark)
    lid.parent = root

    for i, x in enumerate([-0.4, 0.0, 0.4]):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.45, location=(x, 0, 2.0))
        bush = bpy.context.active_object
        bush.name = f"part_bushing_{i+1}"
        bush.data.materials.append(mat_core_copper)
        bush.parent = lid

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "transformer_substation.glb"), export_format='GLB')
    print("SUCCESS: transformer_substation.glb")

def build_ground():
    reset_scene()
    mat_ground = create_mat("GroundPlate", (0.03, 0.035, 0.045, 1.0), roughness=0.6, metallic=0.5)
    mat_slot_line = create_mat("SlotLine", (0.05, 0.35, 0.2, 1.0), roughness=0.4, metallic=0.1, emissive=(0.02, 0.4, 0.18, 1.0), emissive_strength=1.0)
    mat_wall = create_mat("WallDark", (0.05, 0.06, 0.075, 1.0), roughness=0.5, metallic=0.7)
    mat_gold_glow = create_mat("GlowGold", (0.8, 0.55, 0.08, 1.0), roughness=0.3, metallic=0.2, emissive=(0.8, 0.55, 0.08, 1.0), emissive_strength=1.2)
    mat_green_glow = create_mat("GlowGreen", (0.05, 0.9, 0.35, 1.0), roughness=0.2, metallic=0.1, emissive=(0.05, 0.9, 0.35, 1.0), emissive_strength=1.2)

    root = bpy.data.objects.new("Ground_Root", None)
    bpy.context.scene.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.15))
    g = bpy.context.active_object
    g.name = "part_main_ground"
    g.scale = (24.0, 16.0, 0.3)
    g.data.materials.append(mat_ground)
    g.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.5, -7.95, 0.01))
    curb = bpy.context.active_object
    curb.name = "part_gold_curb"
    curb.scale = (23.0, 0.06, 0.04)
    curb.data.materials.append(mat_gold_glow)
    curb.parent = root

    for spot in range(3):
        x = -6.0 + spot * 3.4
        for line_idx, (lx, ly, sx, sy) in enumerate([
            (x, -3.2, 2.4, 0.04),
            (x, 0.8, 2.4, 0.04),
            (x - 1.18, -1.2, 0.04, 4.0),
            (x + 1.18, -1.2, 0.04, 4.0)
        ]):
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(lx, ly, 0.01))
            slot_line = bpy.context.active_object
            slot_line.name = f"part_slot_{spot+1}_line_{line_idx}"
            slot_line.scale = (sx, sy, 0.02)
            slot_line.data.materials.append(mat_slot_line)
            slot_line.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(7.5, -3.5, 1.1))
    room = bpy.context.active_object
    room.name = "part_control_room_frame"
    room.scale = (7.5, 6.5, 2.2)
    room.data.materials.append(mat_wall)
    room.parent = root

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(7.5, -3.5, 2.22))
    roof_line = bpy.context.active_object
    roof_line.name = "part_control_room_glow"
    roof_line.scale = (7.55, 6.55, 0.04)
    roof_line.data.materials.append(mat_green_glow)
    roof_line.parent = root

    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIR, "ground_facility.glb"), export_format='GLB')
    print("SUCCESS: ground_facility.glb")

build_charging_pile()
build_canopy()
build_storage()
build_transformer()
build_ground()
