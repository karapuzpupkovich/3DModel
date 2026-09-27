# -*- coding: utf-8 -*-
"""
Рендер деталей в Blender (Cycles, без окна) — для картинок и проверки форм.

Сцена описывается JSON-файлом:
{
  "out": "путь.png", "size": [1600, 900], "samples": 48,
  "camera": {"target": [x, y, z], "dist": 180, "elev": 50, "azim": -90, "lens": 50},
  "ground": {"size": [300, 220], "color": [0.72, 0.58, 0.40], "sand": true},
  "objects": [
     {"stl": "путь.stl", "loc": [x, y, z], "rot": 0, "color": [r, g, b], "rough": 0.6},
     {"shape": "acorn_man", "loc": [x, y, 0]},
     {"shape": "tray", "size": [250, 180, 30]}
  ]
}
Запуск:  blender -b -P render.py -- сцена.json
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import bpy
import numpy as np


def read_stl(path: Path):
    raw = path.read_bytes()
    n = struct.unpack("<I", raw[80:84])[0]
    rec = np.frombuffer(raw[84:84 + n * 50],
                        dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    tri = rec["v"].reshape(-1, 3).astype(np.float64)
    uniq, inv = np.unique(np.round(tri, 5), axis=0, return_inverse=True)
    return uniq, inv.reshape(-1, 3)


def material(name, color, rough=0.6, bump=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    if bump:
        # песок: шум по цвету и рельефу
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = bump
        tex.inputs["Detail"].default_value = 12.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*[c * 0.78 for c in color], 1)
        ramp.color_ramp.elements[1].color = (*[min(1, c * 1.12) for c in color], 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        bmp = nt.nodes.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = 0.35
        nt.links.new(tex.outputs["Fac"], bmp.inputs["Height"])
        nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def mesh_object(name, verts, faces, mat, loc=(0, 0, 0), rot=0.0, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(rot))
    ob.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def prim(kind, name, mat, loc, scale=(1, 1, 1), rot=(0, 0, 0), **kw):
    if kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1.0, depth=2.0)
    elif kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=2.0)
    ob = bpy.context.active_object
    ob.name = name
    ob.location = loc
    ob.scale = scale
    ob.rotation_euler = rot
    ob.data.materials.append(mat)
    if kind != "cube":
        bpy.ops.object.shade_smooth()
    return ob


def acorn_man(loc):
    """
    Условный человечек из желудей — только для картинки пропорций.
    Размеры как у образца: рост ~70 мм, тело — жёлудь ~26×20 мм,
    голова — орех ~20 мм, шляпа — плюска ~26 мм.
    """
    x, y, z0 = loc
    acorn = material("жёлудь", (0.50, 0.28, 0.12), 0.35)
    cap = material("плюска", (0.42, 0.30, 0.18), 0.9)
    twig = material("веточка", (0.30, 0.20, 0.13), 0.8)
    # ноги-веточки
    for dx in (-5, 5):
        prim("cyl", "нога", twig, (x + dx, y, z0 + 11), (1.4, 1.4, 11))
        prim("sphere", "стопа", acorn, (x + dx, y - 3, z0 + 3.5), (4.5, 6.5, 3.5))
    prim("sphere", "тело", acorn, (x, y, z0 + 34), (10, 9, 13))
    prim("sphere", "голова", acorn, (x, y, z0 + 55), (10, 9.5, 9.5))
    prim("sphere", "плюска", cap, (x, y, z0 + 61), (13, 12.5, 7))
    prim("cyl", "хвостик", twig, (x, y, z0 + 70), (0.9, 0.9, 3))
    for side in (-1, 1):
        prim("cyl", "рука", twig, (x + side * 13, y - 2, z0 + 36), (1.2, 1.2, 9),
             rot=(0, math.radians(side * 55), 0))


def tray(size, mat):
    w, d, h = size
    t = 2.0
    prim("cube", "дно", mat, (0, 0, -t / 2), (w / 2, d / 2, t / 2))
    for sx, sy, ex, ey in ((0, d / 2, w / 2, t / 2), (0, -d / 2, w / 2, t / 2),
                           (w / 2, 0, t / 2, d / 2), (-w / 2, 0, t / 2, d / 2)):
        prim("cube", "борт", mat, (sx, sy, h / 2 - t), (ex, ey, h / 2))


def camera(target, dist, elev, azim, lens=50):
    tx, ty, tz = target
    e, a = math.radians(elev), math.radians(azim)
    loc = (tx + dist * math.cos(e) * math.cos(a),
           ty + dist * math.cos(e) * math.sin(a),
           tz + dist * math.sin(e))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.location = loc
    cam.data.lens = lens
    cam.data.clip_start = 1
    cam.data.clip_end = 5000
    bpy.context.scene.collection.objects.link(cam)
    direction = np.array([tx, ty, tz]) - np.array(loc)
    from mathutils import Vector
    cam.rotation_euler = Vector(direction.tolist()).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam


def lights(target):
    tx, ty, tz = target
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(42), 0, math.radians(-35))
    bpy.context.scene.collection.objects.link(sun)
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA"))
    fill.data.energy = 2.5e5
    fill.data.size = 300
    fill.location = (tx - 150, ty - 250, tz + 300)
    fill.rotation_euler = (math.radians(35), 0, math.radians(-30))
    bpy.context.scene.collection.objects.link(fill)
    w = bpy.context.scene.world or bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.88, 0.85, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.55


def main(cfg_path: Path):
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "NONE"
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = cfg.get("samples", 48)
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = cfg.get("size", [1600, 900])
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"

    g = cfg.get("ground")
    if g:
        m = material("песок", tuple(g.get("color", (0.72, 0.58, 0.40))), 0.95,
                     bump=0.35 if g.get("sand", True) else None)
        gw, gd = g["size"]
        prim("cube", "земля", m, (g.get("x", 0), g.get("y", 0), -1.0), (gw / 2, gd / 2, 1.0))

    for i, o in enumerate(cfg["objects"]):
        if o.get("shape") == "acorn_man":
            acorn_man(o["loc"])
            continue
        if o.get("shape") == "tray":
            tray(o["size"], material("картон", (0.62, 0.48, 0.33), 0.9))
            continue
        v, f = read_stl(Path(o["stl"]))
        mat = material(f"m{i}", tuple(o.get("color", (0.92, 0.87, 0.76))), o.get("rough", 0.6))
        mesh_object(f"o{i}", v, f, mat, tuple(o.get("loc", (0, 0, 0))), o.get("rot", 0.0))

    c = cfg["camera"]
    camera(c["target"], c["dist"], c["elev"], c["azim"], c.get("lens", 50))
    lights(c["target"])
    sc.render.filepath = cfg["out"]
    bpy.ops.render.render(write_still=True)
    print("RENDER", cfg["out"])


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main(Path(argv[0]))
