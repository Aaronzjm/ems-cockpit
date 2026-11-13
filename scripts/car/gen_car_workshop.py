# -*- coding: utf-8 -*-
"""汽车车间场景 models-car（2026-10-22 新增：汽车工厂车间 + 四大工艺流程）

工艺流程（汽车制造通行四大工艺；web_search/web_fetch 当时不可用，按标准工业常识实现）：
  冲压 STAMPING → 焊装 WELDING → 涂装 PAINTING → 总装 ASSEMBLY

布局（世界坐标，厂房 56×24m，产线沿 x 轴，输送床顶 y=0.5）：
  - 冲压区 [-26,-14]：3 台压力机 press.glb（运行时摆 x=-24/-20/-16, z=-4.5）
    + 钢卷上料机、覆盖件料架（烘焙进 shell）
  - 焊装区 [-12,0]：3 个焊接工位 × 2 台机器人 weld_robot.glb（x=-10/-6/-2, z=±2.3）
    + 安全围栏（烘焙）
  - 涂装区 [2,12]：喷漆房隧道 paint_booth.glb（x=7，车身进入隐藏、出来换漆色）
  - 总装区 [14,26]：龙门工位/零件架/轮胎堆（烘焙），成品车从东大门 (x=28, z∈[-3,3]) 驶出
  - 区域角标四色：冲压 gb 蓝 / 焊装 gy 金 / 涂装 gg 绿 / 总装 gw 白

坐标约定同 v4 库：Blender Z-up，导出后 (x,y,z)->(x,z,-y)；world z = -Blender y。
发光纪律：只有描边/灯带/灯珠发光（es≤1.4），本体正常材质；贴地贴片高出表面 ≥0.04。
关节机器人用嵌套 empty（pivot_*）导出为节点，运行时 getObjectByName 驱动。
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


def empty(name, loc, parent=None):
    """关节枢轴（导出为 glTF 节点，运行时旋转驱动）"""
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
    return o


# ============================================================
# 1) 厂房外壳 + 输送线 + 分区标记 + 静态布景
# ============================================================
def build_shell():
    reset()
    P = palette()
    rt = root("Workshop_Root")

    # 地坪（顶面 z=0）+ 四周蓝色灯带（半埋入，顶面高出 0.03）
    box("part_floor", (0, 0, -0.15), (57.4, 25.4, 0.3), P['ground'], rt)
    box("part_edge_0", (0, -12.64, 0.0), (57.4, 0.12, 0.06), P['gb'], rt)
    box("part_edge_1", (0, 12.64, 0.0), (57.4, 0.12, 0.06), P['gb'], rt)
    box("part_edge_2", (-28.64, 0, 0.0), (0.12, 25.4, 0.06), P['gb'], rt)
    box("part_edge_3", (28.64, 0, 0.0), (0.12, 25.4, 0.06), P['gb'], rt)

    # 矮墙（高 1.2m；东侧留 world z∈[-3,3] 出口 = Blender y∈[-3,3]）
    box("part_wall_n", (0, -12, 0.6), (56.5, 0.25, 1.2), P['wall'], rt)
    box("part_wall_s", (0, 12, 0.6), (56.5, 0.25, 1.2), P['wall'], rt)
    box("part_wall_w", (-28.1, 0, 0.6), (0.25, 24.5, 1.2), P['wall'], rt)
    box("part_wall_e0", (28.1, -7.6, 0.6), (0.25, 9.2, 1.2), P['wall'], rt)
    box("part_wall_e1", (28.1, 7.6, 0.6), (0.25, 9.2, 1.2), P['wall'], rt)

    # 立柱（7×2）+ 桁架 + 檩条
    xs = [-24, -16, -8, 0, 8, 16, 24]
    for i, x in enumerate(xs):
        for s in (-1, 1):
            box("part_col_%d_%d" % (i, s), (x, s * 11.0, 4.5), (0.4, 0.4, 9.0), P['dark'], rt)
        box("part_truss_%d" % i, (x, 0, 8.7), (0.3, 22.4, 0.6), P['body'], rt)
    box("part_purlin_0", (0, -5.5, 9.15), (56.4, 0.2, 0.35), P['dark'], rt)
    box("part_purlin_1", (0, 5.5, 9.15), (56.4, 0.2, 0.35), P['dark'], rt)

    # 吊灯（两排 ×7，白光微 bloom）
    li = 0
    for x in xs:
        for y in (-5.5, 5.5):
            cyl("part_lamp_rod_%d" % li, (x, y, 8.72), 0.03, 0.5, P['dark'], rt, verts=6)
            cyl("part_lamp_%d" % li, (x, y, 8.44), 0.28, 0.07, P['gw'], rt, verts=16)
            li += 1

    # 输送床（顶 0.5）+ 两侧青色灯条 + 床面流向箭头（>，指向 +x）
    box("part_conv_bed", (0, 0, 0.25), (52.0, 2.2, 0.5), P['dark'], rt)
    box("part_conv_edge_0", (0, -1.12, 0.54), (52.0, 0.05, 0.07), P['gc'], rt)
    box("part_conv_edge_1", (0, 1.12, 0.54), (52.0, 0.05, 0.07), P['gc'], rt)
    ai = 0
    x0 = -25.0
    while x0 <= 25.01:
        box("part_arrow_%d_a" % ai, (x0 - 0.2, 0.14, 0.53), (0.48, 0.07, 0.02), P['gc'], rt,
            rz=math.pi - 0.62)
        box("part_arrow_%d_b" % ai, (x0 - 0.2, -0.14, 0.53), (0.48, 0.07, 0.02), P['gc'], rt,
            rz=-(math.pi - 0.62))
        ai += 1
        x0 += 2.5

    # 分区横线（x=-13/1/13）+ 四区角标（四色）
    for i, x in enumerate([-13.0, 1.0, 13.0]):
        box("part_zoneline_%d" % i, (x, 0, 0.05), (0.1, 20.0, 0.02), P['line'], rt)
    bracket("part_brk_stamp", -20.0, 0, 12.4, 19.0, P['gb'], rt, y=0.06, L=1.4, t=0.14)
    bracket("part_brk_weld", -6.0, 0, 12.4, 19.0, P['gy'], rt, y=0.06, L=1.4, t=0.14)
    bracket("part_brk_paint", 7.0, 0, 10.4, 19.0, P['gg'], rt, y=0.06, L=1.4, t=0.14)
    bracket("part_brk_asm", 20.0, 0, 12.4, 19.0, P['gw'], rt, y=0.06, L=1.4, t=0.14)

    # —— 冲压区布景（world z=+5 → Blender y=-5）——
    # 钢卷上料机
    box("part_cradle", (-25.5, -5.0, 0.4), (1.8, 0.5, 0.8), P['dark'], rt)
    cyl("part_coil", (-25.5, -5.0, 1.35), 1.05, 1.5, P['body'], rt, rot=(math.pi / 2, 0, 0), verts=28)
    cyl("part_coil_cu", (-25.5, -5.78, 1.35), 1.07, 0.06, P['copper'], rt, rot=(math.pi / 2, 0, 0), verts=28)
    # 覆盖件料架 ×3（world z=+5.5）
    for i, x in enumerate([-24.0, -21.0, -18.0]):
        box("part_rack_%d" % i, (x, -5.5, 0.95), (2.2, 0.9, 1.9), P['dark'], rt)
        for k, zz in enumerate([0.55, 1.10, 1.65]):
            box("part_rack_%d_sh%d" % (i, k), (x, -5.5, zz), (2.3, 1.0, 0.05), P['body'], rt)
            box("part_rack_%d_p%d" % (i, k), (x, -5.5, zz + 0.055), (1.7, 0.75, 0.05), P['paint'], rt)

    # —— 焊装区安全围栏（world z=±3.4 → Blender y=∓3.4）——
    fi = 0
    fx = -12.5
    while fx <= 0.51:
        for s in (-1, 1):
            box("part_fence_post_%d_%d" % (fi, s), (fx, s * 3.4, 0.575), (0.07, 0.07, 1.15), P['dark'], rt)
        fi += 1
        fx += 2.6
    ri = 0
    for s in (-1, 1):
        for zz in (0.55, 1.02):
            box("part_fence_rail_%d" % ri, (-6.0, s * 3.4, zz), (13.0, 0.035, 0.035), P['line'], rt)
            ri += 1

    # —— 总装区布景 ——
    # 龙门工位 ×4（x=15.5/18.5/21.5/24.5 对应底盘合装/内饰/车门/灯具终检）
    # 每座带升降工具臂：part_toolguide 固定导套 + part_tool 滑杆 + part_toolhead 工具头（运行时下降 0.45）
    for i, x in enumerate([15.5, 18.5, 21.5, 24.5]):
        for s in (-1, 1):
            box("part_gantry_%d_col%d" % (i, s), (x, s * 1.5, 1.3), (0.18, 0.18, 2.6), P['dark'], rt)
        box("part_gantry_%d_beam" % i, (x, 0, 2.68), (0.16, 3.16, 0.16), P['body'], rt)
        box("part_gantry_%d_lamp" % i, (x, 0, 2.55), (0.09, 0.09, 0.09), P['gw'], rt)
        ty = 1.15 if i % 2 == 0 else -1.15
        box("part_toolguide_%d" % i, (x, ty, 2.35), (0.15, 0.15, 0.7), P['dark'], rt)
        box("part_tool_%d" % i, (x, ty, 2.0), (0.09, 0.09, 1.2), P['line'], rt)
        box("part_toolhead_%d" % i, (x, ty, 1.33), (0.26, 0.30, 0.14), P['body'], rt)
        box("part_toolstrip_%d" % i, (x, ty, 1.245), (0.20, 0.22, 0.03), P['gc'], rt)
    # 零件架 ×4（world z=-6 → Blender y=6）+ 彩色料盒
    bins = [P['gg'], P['gy'], P['gb'], P['gr']]
    for i, x in enumerate([15.0, 18.5, 22.0, 25.5]):
        box("part_prack_%d" % i, (x, 6.0, 1.0), (2.4, 0.9, 2.0), P['dark'], rt)
        for k, zz in enumerate([0.55, 1.15, 1.75]):
            box("part_prack_%d_sh%d" % (i, k), (x, 6.0, zz), (2.5, 1.0, 0.05), P['body'], rt)
            box("part_prack_%d_bin%d" % (i, k), (x - 0.55 + (k % 2) * 1.1, 6.0, zz + 0.175),
                (0.5, 0.55, 0.3), bins[(i + k) % 4], rt)
    # 轮胎堆 ×3（world z=+6 → Blender y=-6）
    for i, x in enumerate([17.0, 21.0, 25.0]):
        for k in range(4):
            cyl("part_wstack_%d_%d" % (i, k), (x, -6.0, 0.13 + k * 0.27), 0.36, 0.26, P['dark'], rt, verts=24)
        cyl("part_wstack_%d_hub" % i, (x, -6.0, 1.095), 0.18, 0.05, P['paint'], rt, verts=16)

    # 东出口龙门（world x=27.8，跨 z∈[-3.3,3.3]）
    for s in (-1, 1):
        box("part_exit_col_%d" % s, (27.8, s * 3.3, 2.6), (0.3, 0.3, 5.2), P['dark'], rt)
    box("part_exit_beam", (27.8, 0, 5.35), (0.35, 7.0, 0.45), P['body'], rt)
    box("part_exit_strip", (27.6, 0, 5.05), (0.08, 6.4, 0.07), P['gw'], rt)

    export("workshop_shell.glb")
    print("SHELL OK")


# ============================================================
# 2) 冲压压力机（part_ram 运行时上下冲压，part_beacon 闪烁）
#    本地原点=地面中心，正面（Blender -Y）朝输送线
# ============================================================
def build_press():
    reset()
    P = palette()
    rt = root("Press_Root")

    boxb("part_base", (0, 0, 0.25), (4.2, 3.2, 0.5), P['dark'], rt, bw=0.04)
    boxb("part_bed", (0, 0, 0.68), (3.0, 2.0, 0.35), P['body'], rt, bw=0.03)
    box("part_die", (0, 0, 1.06), (2.2, 1.4, 0.4), P['copper'], rt)
    for s in (-1, 1):
        box("part_upright_%d" % s, (s * 1.55, 0, 2.5), (0.55, 0.7, 4.0), P['dark'], rt)
        box("part_strip_%d" % s, (s * 1.55, -0.37, 2.5), (0.07, 0.05, 3.4), P['gb'], rt)
    boxb("part_crown", (0, 0, 4.85), (4.2, 1.8, 0.9), P['body'], rt, bw=0.05)
    box("part_ram", (0, 0, 3.7), (2.4, 1.3, 0.8), P['dark'], rt)
    cyl("part_beacon", (1.7, 0.6, 5.42), 0.1, 0.24, P['gy'], rt, verts=12)
    box("part_panel_stand", (-2.5, -0.9, 0.6), (0.5, 0.4, 1.2), P['dark'], rt)
    box("part_panel_screen", (-2.5, -1.12, 1.35), (0.42, 0.06, 0.34), P['scr'], rt)
    base_outline("part_outline", 4.2, 3.2, P['gb'], rt, y=0.06)

    export("press.glb")
    print("PRESS OK")


# ============================================================
# 3) 焊接机器人（嵌套 empty 关节：pivot_yaw/shoulder/elbow/wrist）
#    part_tip = 焊枪尖端（运行时挂火花+点光源）
# ============================================================
def build_robot():
    reset()
    P = palette()
    rt = root("Robot_Root")

    cyl("part_baseplate", (0, 0, 0.06), 0.45, 0.12, P['dark'], rt, verts=24)
    ring("part_basering", (0, 0, 0.07), 0.5, 0.04, P['gy'], rt)
    cyl("part_pedestal", (0, 0, 0.4), 0.32, 0.55, P['body'], rt, verts=20)

    yaw = empty("pivot_yaw", (0, 0, 0.68), rt)
    cyl("part_yawhouse", (0, 0, 0.17), 0.26, 0.34, P['dark'], yaw, verts=20)
    sh = empty("pivot_shoulder", (0, 0, 0.34), yaw)
    box("part_arm1", (0, 0, 0.62), (0.24, 0.26, 1.24), P['body'], sh)
    box("part_arm1_cap", (0, 0, 1.20), (0.28, 0.30, 0.12), P['dark'], sh)
    el = empty("pivot_elbow", (0, 0, 1.26), sh)
    box("part_arm2", (0, 0, 0.50), (0.18, 0.20, 1.00), P['body'], el)
    wr = empty("pivot_wrist", (0, 0, 1.02), el)
    cyl("part_torch", (0, 0, 0.16), 0.05, 0.30, P['dark'], wr, verts=10)
    box("part_tip", (0, 0, 0.34), (0.07, 0.07, 0.07), P['gw'], wr)

    export("weld_robot.glb")
    print("ROBOT OK")


# ============================================================
# 4) 涂装喷漆房（隧道沿 x，输送线从两端开口穿过；侧墙不透明——
#    车身进洞隐藏、出洞换漆色，模拟喷涂过程）
# ============================================================
def build_booth():
    reset()
    P = palette()
    rt = root("Booth_Root")

    for sx in (-1, 1):
        for sy in (-1, 1):
            box("part_col_%d%d" % (sx, sy), (sx * 2.9, sy * 2.1, 1.8), (0.22, 0.22, 3.6), P['dark'], rt)
    boxb("part_roof", (0, 0, 3.72), (6.3, 4.6, 0.22), P['body'], rt, bw=0.04)
    # 顶内灯带（运行时克隆材质做喷涂脉冲）
    for s in (-1, 1):
        box("part_light_%d" % s, (0, s * 0.9, 3.50), (5.6, 0.12, 0.06), P['gw'], rt)
    # 侧墙（深色玻璃质感，不透明）+ 绿色灯带 ×2
    for s in (-1, 1):
        box("part_wall_%d" % s, (0, s * 2.15, 1.7), (5.9, 0.10, 3.4), P['glass'], rt)
        for zz in (0.62, 2.95):
            box("part_wallband_%d_%d" % (s, int(zz * 100)), (0, s * 2.21, zz), (5.95, 0.04, 0.07), P['gg'], rt)
    # 端框（留 2.3m 宽 × 2.7m 高洞口给车身通过）
    for sx in (-1, 1):
        for s in (-1, 1):
            box("part_end_%d_%d" % (sx, s), (sx * 3.0, s * 1.65, 1.7), (0.18, 1.0, 3.4), P['dark'], rt)
        box("part_endtop_%d" % sx, (sx * 3.0, 0, 3.15), (0.18, 4.4, 0.9), P['dark'], rt)
    # 内部喷杆 + 微光条（洞口可见）
    ni = 0
    for sx in (-1.5, 0.0, 1.5):
        for s in (-1, 1):
            cyl("part_nozzle_%d" % ni, (sx, s * 1.3, 1.9), 0.04, 2.6, P['dark'], rt, verts=8)
            box("part_nozstrip_%d" % ni, (sx, s * 1.3, 1.9), (0.05, 0.05, 2.2), P['gc'], rt)
            ni += 1
    # 屋顶风机 + 信标
    cyl("part_fan", (1.8, 1.2, 3.98), 0.35, 0.3, P['dark'], rt, verts=16)
    cyl("part_beacon", (-1.8, -1.2, 3.92), 0.09, 0.18, P['gg'], rt, verts=10)
    base_outline("part_outline", 6.3, 4.6, P['gg'], rt, y=0.06)

    export("paint_booth.glb")
    print("BOOTH OK")


# ============================================================
# 5) 车身模型已移到 gen_car_assembly.py（白车身骨架/涂装壳体/总装零件组分步组装）
# ============================================================

build_shell()
build_press()
build_robot()
build_booth()
print("DONE car_workshop shell+press+robot+booth")
