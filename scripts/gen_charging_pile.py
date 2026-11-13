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

# ==========================================================
# 1. 智能快充桩 (Charging Pile)
# ==========================================================
def build_charging_pile():
    reset_scene()
    
    mat_dark = create_mat("DarkMetal", (0.05, 0.05, 0.07, 1.0), roughness=0.35, metallic=0.85)
    mat_glow = create_mat("CyberGreen", (0.02, 0.95, 0.35, 1.0), roughness=0.1, metallic=0.1, emissive=(0.02, 0.95, 0.35, 1.0), emissive_strength=5.0)
    mat_core = create_mat("CoreCircuit", (0.1, 0.15, 0.2, 1.0), roughness=0.2, metallic=0.9, emissive=(0.0, 0.8, 0.9, 1.0), emissive_strength=2.0)
    
    root = bpy.data.objects.new("ChargingPile_Root", None)
    bpy.context.scene.collection.objects.link(root)
    
    # Base
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.1))
    base = bpy.context.active_object
    base.name = "part_base"
    base.scale = (0.7, 0.6, 0.2)
    base.data.materials.append(mat_dark)
    base.parent = root
    
    # Main Pillar Frame
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.1))
    body = bpy.context.active_object
    body.name = "part_body_frame"
    body.scale = (0.55, 0.45, 1.8)
    body.data.materials.append(mat_dark)
    body.parent = root
    
    # Front Panel
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -0.25, 1.2))
    front_panel = bpy.context.active_object
    front_panel.name = "part_front_panel"
    front_panel.scale = (0.45, 0.06, 1.2)
    front_panel.data.materials.append(mat_dark)
    front_panel.parent = root
    
    # Screen
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, -0.29, 1.35), rotation=(math.radians(90), 0, 0))
    screen = bpy.context.active_object
    screen.name = "part_screen"
    screen.scale = (0.35, 0.25, 1.0)
    screen.data.materials.append(mat_glow)
    screen.parent = root
    
    # Top Cap
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 2.05))
    top_cap = bpy.context.active_object
    top_cap.name = "part_top_cap"
    top_cap.scale = (0.6, 0.5, 0.1)
    top_cap.data.materials.append(mat_dark)
    top_cap.parent = root
    
    # Top Glow Ring
    bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=0.04, location=(0, 0, 2.12))
    glow_ring = bpy.context.active_object
    glow_ring.name = "part_glow_ring"
    glow_ring.data.materials.append(mat_glow)
    glow_ring.parent = root
    
    # Left Gun
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-0.35, 0, 1.0))
    left_gun = bpy.context.active_object
    left_gun.name = "part_gun_left"
    left_gun.scale = (0.12, 0.25, 0.45)
    left_gun.data.materials.append(mat_dark)
    left_gun.parent = root
    
    # Right Gun
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.35, 0, 1.0))
    right_gun = bpy.context.active_object
    right_gun.name = "part_gun_right"
    right_gun.scale = (0.12, 0.25, 0.45)
    right_gun.data.materials.append(mat_dark)
    right_gun.parent = root
    
    # Internal Power Module Core
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 1.1))
    core_module = bpy.context.active_object
    core_module.name = "part_internal_core"
    core_module.scale = (0.42, 0.32, 1.4)
    core_module.data.materials.append(mat_core)
    core_module.parent = root
    
    out_path = os.path.join(OUTPUT_DIR, "charging_pile.glb")
    bpy.ops.export_scene.gltf(filepath=out_path, export_format='GLB')
    print("SUCCESS: charging_pile.glb")

build_charging_pile()
