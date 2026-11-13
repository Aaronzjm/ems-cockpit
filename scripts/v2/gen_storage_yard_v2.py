# -*- coding: utf-8 -*-
"""v2 储能院 storage_yard_v2.glb（参考图：矮墙围合 + 后排暗柜 + 前排绿光柜）

本地坐标居中，SceneViewV2 摆到世界 (5.5, 0, -5.5)：
  - 围合矮墙 1.0m 高（后/左/右三面 + 前侧两段矮 curb 留出入口）
  - 院内地面绿色细描边环线
  - 后排 3 台暗柜（带竖向绿导光缝）；前排 3 台整柜绿光（参考图的发光柜，
    强度标定 es=0.9、亮度 0.77 < bloom 阈值 1.05，亮但不烧白）
注意：整柜绿光是有意偏离 v1 的"无块状发光"纪律（参考图要求），
check_emissive 会对 CabGlow 报块状警告，属预期。
"""
import pathlib, os

SRC = pathlib.Path(r"D:\1zjm\agent\ems-cockpit\scripts\gen_all_models_v4.py")
src = SRC.read_text(encoding="utf-8")
cut = src.rindex("\nbuild_ground()")
g = {"__name__": "v4lib"}
exec(compile(src[:cut], str(SRC), "exec"), g)
g["OUT"] = r"D:\1zjm\agent\ems-cockpit\public\models-v2"
os.makedirs(g["OUT"], exist_ok=True)

reset = g["reset"]; palette = g["palette"]; M = g["M"]; root = g["root"]
box = g["box"]; base_outline = g["base_outline"]; dash_poly = g["dash_poly"]; export = g["export"]


def build():
    reset()
    P = palette()
    P['cabglow'] = M("CabGlow", (0.05, 0.30, 0.10, 1.0), 0.35, 0.0,
                     (0.15, 1.00, 0.35, 1.0), 0.9)
    rt = root("StorageV2_Root")

    # 围合矮墙（后/左/右 + 前侧两段 curb）
    box("part_yard_wall_b", (0.0, -2.8, 0.5), (7.0, 0.2, 1.0), P['wall'], rt)
    box("part_yard_wall_l", (-3.5, 0.0, 0.5), (0.2, 5.6, 1.0), P['wall'], rt)
    box("part_yard_wall_r", (3.5, 0.0, 0.5), (0.2, 5.6, 1.0), P['wall'], rt)
    box("part_yard_curb_l", (-2.6, 2.8, 0.15), (1.8, 0.2, 0.3), P['wall'], rt)
    box("part_yard_curb_r", (2.6, 2.8, 0.15), (1.8, 0.2, 0.3), P['wall'], rt)
    # 墙顶绿光描边（参考图储能院一圈亮绿轮廓）
    box("part_yard_trim_b", (0.0, -2.8, 1.02), (7.0, 0.06, 0.06), P['gg'], rt)
    box("part_yard_trim_l", (-3.5, 0.0, 1.02), (0.06, 5.6, 0.06), P['gg'], rt)
    box("part_yard_trim_r", (3.5, 0.0, 1.02), (0.06, 5.6, 0.06), P['gg'], rt)

    # 院内虚线描边：15:51/16:06 用户要求去掉（虚线闪烁发白），不还原

    # 暗柜抬高地台（虚线描边已删）
    box("part_plat", (0.0, -1.6, 0.09), (7.4, 2.3, 0.18), P['dark'], rt)

    # 玻璃绿光柜 ×4（半透壳 + 绿光框柱/顶圈 + 内部搁板，截图参考图质感）
    P['cabglass'] = M("CabGlass", (0.10, 0.45, 0.18, 1.0), 0.15, 0.0,
                      (0.15, 1.00, 0.35, 1.0), 0.55, alpha=0.35)
    for i, x in enumerate([-2.55, -0.85, 0.85, 2.55]):
        box("part_cab_glass_%d" % i, (x, 1.2, 1.05), (1.6, 1.0, 1.9), P['cabglass'], rt)
        for j, (px, py) in enumerate([(x - 0.78, 0.72), (x + 0.78, 0.72),
                                      (x - 0.78, 1.68), (x + 0.78, 1.68)]):
            box("part_cab_post_%d_%d" % (i, j), (px, py, 1.05), (0.07, 0.07, 1.9), P['gg'], rt)
        box("part_cab_rim_f_%d" % i, (x, 0.72, 1.98), (1.63, 0.07, 0.07), P['gg'], rt)
        box("part_cab_rim_b_%d" % i, (x, 1.68, 1.98), (1.63, 0.07, 0.07), P['gg'], rt)
        box("part_cab_rim_l_%d" % i, (x - 0.78, 1.2, 1.98), (0.07, 1.03, 0.07), P['gg'], rt)
        box("part_cab_rim_r_%d" % i, (x + 0.78, 1.2, 1.98), (0.07, 1.03, 0.07), P['gg'], rt)
        box("part_cab_shelf_0_%d" % i, (x, 1.2, 0.75), (1.4, 0.85, 0.05), P['dark'], rt)
        box("part_cab_shelf_1_%d" % i, (x, 1.2, 1.35), (1.4, 0.85, 0.05), P['dark'], rt)
        box("part_cab_cap_t_%d" % i, (x, 1.2, 2.06), (1.7, 1.1, 0.12), P['dark'], rt)
        box("part_cab_cap_b_%d" % i, (x, 1.2, 0.10), (1.7, 1.1, 0.12), P['dark'], rt)

    # 暗柜 ×4（暖白双竖缝，截图参考图同款；坐在地台上）
    P['slitw'] = M("SlitWarm", (0.40, 0.30, 0.20, 1.0), 0.5, 0.0,
                   (1.0, 0.72, 0.30, 1.0), 0.8)
    for i, x in enumerate([-2.55, -0.85, 0.85, 2.55]):
        box("part_cab_dark_%d" % i, (x, -1.6, 1.28), (1.6, 1.1, 2.2), P['dark'], rt)
        box("part_cab_seam_0_%d" % i, (x - 0.3, -1.04, 1.28), (0.05, 0.02, 1.9), P['slitw'], rt)
        box("part_cab_seam_1_%d" % i, (x + 0.3, -1.04, 1.28), (0.05, 0.02, 1.9), P['slitw'], rt)
        box("part_cab_top_%d" % i, (x, -1.6, 2.42), (1.7, 1.2, 0.08), P['body'], rt)

    export("storage_yard_v2.glb")


build()
print("DONE storage_yard_v2")
