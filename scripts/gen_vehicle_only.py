# -*- coding: utf-8 -*-
"""只重建 vehicle.glb（复用 gen_all_models_v4.py 里的函数，不执行文件末尾的全量构建）"""
import pathlib

SRC = pathlib.Path(r"D:\1zjm\agent\ems-cockpit\scripts\gen_all_models_v4.py")
src = SRC.read_text(encoding="utf-8")
# 砍掉文件末尾的全量构建调用，避免用旧配电室覆盖 v5
cut = src.rindex("\nbuild_ground()")
src = src[:cut]

g = {"__name__": "v4lib"}
exec(compile(src, str(SRC), "exec"), g)
g["build_vehicle"]()
print("DONE vehicle")
