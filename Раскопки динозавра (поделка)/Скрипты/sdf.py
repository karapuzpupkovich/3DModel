# -*- coding: utf-8 -*-
"""
Мини-библиотека SDF (signed distance field) для лепки костей.

Форма задаётся не треугольниками, а функцией «расстояние до поверхности»:
отрицательно внутри, положительно снаружи. Детали складываются плавным
минимумом (smin) — так сустав перетекает в кость с галтелью, как у живой
кости. Поле считается на сетке numpy, в поверхность его переводит OpenVDB
(он встроен в Blender), дальше — прореживание и STL.

Запускается из Python Blender'а (там есть numpy и openvdb):
    blender -b -P build_skeleton.py

Все размеры в миллиметрах. Кости лежат в плоскости XY, осевая линия на
z = 0; нижняя часть срезается плоскостью z = -CUT и поднимается на стол.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

CUT = 0.5          # срез ниже осевой: деталь чуть выше половины кругляша


# --------------------------------------------------------------------------- #
#  Примитивы. Каждый умеет: габарит (для локального счёта) и расстояние.
# --------------------------------------------------------------------------- #
@dataclass
class Prim:
    op: str = "add"          # add — прибавить, sub — вычесть (лунка)
    k: float = 0.6           # радиус плавного слияния с тем, что уже есть

    def bbox(self):          # (min xyz, max xyz)
        raise NotImplementedError

    def dist(self, x, y, z):
        raise NotImplementedError


@dataclass
class Sphere(Prim):
    c: tuple = (0, 0, 0)
    r: float = 1.0

    def bbox(self):
        c = np.array(self.c, float)
        return c - self.r, c + self.r

    def dist(self, x, y, z):
        return np.sqrt((x - self.c[0]) ** 2 + (y - self.c[1]) ** 2 + (z - self.c[2]) ** 2) - self.r


@dataclass
class Ellipsoid(Prim):
    c: tuple = (0, 0, 0)
    r: tuple = (1, 1, 1)
    ang: float = 0.0         # поворот вокруг Z, градусы

    def bbox(self):
        m = max(self.r)
        c = np.array(self.c, float)
        return c - m, c + m

    def dist(self, x, y, z):
        a = math.radians(self.ang)
        ca, sa = math.cos(a), math.sin(a)
        dx, dy, dz = x - self.c[0], y - self.c[1], z - self.c[2]
        lx = dx * ca + dy * sa
        ly = -dx * sa + dy * ca
        rx, ry, rz = self.r
        # Оценка расстояния до эллипсоида по Иниго Килесу: точна у поверхности
        k0 = np.sqrt((lx / rx) ** 2 + (ly / ry) ** 2 + (dz / rz) ** 2)
        k1 = np.sqrt((lx / rx ** 2) ** 2 + (ly / ry ** 2) ** 2 + (dz / rz ** 2) ** 2)
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


@dataclass
class RoundCone(Prim):
    """Капсула с разными радиусами на концах (конус со сферами на торцах)."""
    a: tuple = (0, 0, 0)
    b: tuple = (1, 0, 0)
    ra: float = 1.0
    rb: float = 1.0

    def bbox(self):
        a, b = np.array(self.a, float), np.array(self.b, float)
        r = max(self.ra, self.rb)
        return np.minimum(a, b) - r, np.maximum(a, b) + r

    def dist(self, x, y, z):
        # точное SDF «round cone» по Иниго Килесу
        a = np.array(self.a, float)
        b = np.array(self.b, float)
        r1, r2 = self.ra, self.rb
        ba = b - a
        l2 = float(ba @ ba)
        rr = r1 - r2
        a2 = l2 - rr * rr
        il2 = 1.0 / l2
        pax, pay, paz = x - a[0], y - a[1], z - a[2]
        yv = pax * ba[0] + pay * ba[1] + paz * ba[2]
        zv = yv - l2
        cx = pax * l2 - ba[0] * yv
        cy = pay * l2 - ba[1] * yv
        cz = paz * l2 - ba[2] * yv
        x2 = cx * cx + cy * cy + cz * cz
        y2 = yv * yv * l2
        z2 = zv * zv * l2
        kk = np.sign(rr) * rr * rr * x2
        out = np.empty_like(x)
        m1 = np.sign(zv) * a2 * z2 > kk
        m2 = (~m1) & (np.sign(yv) * a2 * y2 < kk)
        m3 = ~(m1 | m2)
        out[m1] = np.sqrt(x2[m1] + z2[m1]) * il2 - r2
        out[m2] = np.sqrt(x2[m2] + y2[m2]) * il2 - r1
        out[m3] = (np.sqrt(x2[m3] * a2 * il2) + yv[m3] * rr) * il2 - r1
        return out


def chain(points, radii, op="add", k=0.6):
    """Цепочка RoundCone по точкам — гладкая трубка с плавным сужением."""
    out = []
    for (p, q), (r0, r1) in zip(zip(points, points[1:]), zip(radii, radii[1:])):
        out.append(RoundCone(a=p, b=q, ra=r0, rb=r1, op=op, k=k))
    return out


def bezier(p0, p1, p2, n):
    """Квадратичная кривая Безье на плоскости z=0, n точек."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((x, y, 0.0))
    return pts


# --------------------------------------------------------------------------- #
#  Плавные булевы операции
# --------------------------------------------------------------------------- #
def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


# --------------------------------------------------------------------------- #
#  Деталь: набор примитивов -> поле на сетке -> сетка треугольников
# --------------------------------------------------------------------------- #
@dataclass
class Part:
    name: str
    prims: list = field(default_factory=list)

    def add(self, *ps):
        for p in ps:
            if isinstance(p, (list, tuple)):
                self.prims.extend(p)
            else:
                self.prims.append(p)
        return self

    def bounds(self, pad=1.0):
        lo = np.full(3, np.inf)
        hi = np.full(3, -np.inf)
        for p in self.prims:
            if p.op != "add":
                continue
            a, b = p.bbox()
            lo = np.minimum(lo, a)
            hi = np.maximum(hi, b)
        return lo - pad, hi + pad

    def field(self, voxel=0.1):
        """
        Поле на сетке. Каждый примитив считается только в своём габарите
        плюс зона слияния — иначе 60 деталей на 10 млн точек считались бы
        минутами.
        """
        lo, hi = self.bounds(pad=1.5)
        lo[2] = -CUT - 2 * voxel          # ниже среза считать незачем
        shape = np.ceil((hi - lo) / voxel).astype(int) + 1
        f = np.full(shape, 10.0, dtype=np.float32)
        for p in self.prims:
            a, b = p.bbox()
            pad = p.k + 2 * voxel
            i0 = np.clip(np.floor((a - pad - lo) / voxel).astype(int), 0, shape - 1)
            i1 = np.clip(np.ceil((b + pad - lo) / voxel).astype(int) + 1, 1, shape)
            if np.any(i1 <= i0):
                continue
            ax = [lo[d] + voxel * np.arange(i0[d], i1[d]) for d in range(3)]
            X, Y, Z = np.meshgrid(*ax, indexing="ij")
            d = p.dist(X, Y, Z).astype(np.float32)
            sl = (slice(i0[0], i1[0]), slice(i0[1], i1[1]), slice(i0[2], i1[2]))
            if p.op == "add":
                f[sl] = smin(f[sl], d, p.k)
            else:
                f[sl] = smax(f[sl], -d, p.k)
        # плоское дно: всё, что ниже z = -CUT, отрезается ровной плоскостью
        zs = lo[2] + voxel * np.arange(shape[2])
        f = np.maximum(f, (-(zs + CUT))[None, None, :].astype(np.float32))
        return f, lo, voxel

    def polygons(self, voxel=0.1):
        """Поле -> многоугольники через OpenVDB (volumeToMesh)."""
        import openvdb as vdb
        f, lo, vx = self.field(voxel)
        grid = vdb.FloatGrid(background=10.0)
        grid.copyFromArray(f)
        pts, tris, quads = grid.convertToPolygons(isovalue=0.0, adaptivity=0.0)
        pts = np.asarray(pts, dtype=np.float64) * vx + lo
        pts[:, 2] += CUT                  # срез поднимается на стол: z = 0
        # OpenVDB кладёт вершины среза ровно на плоскость с точностью float;
        # подтягиваем только этот шум. Широкий допуск (0.02 мм) схлопывал
        # мелкие треугольники у кромки дна в вырожденные и рвал сетку.
        pts[np.abs(pts[:, 2]) < 1e-4, 2] = 0.0
        return (pts,
                np.asarray(tris, dtype=np.int64).reshape(-1, 3),
                np.asarray(quads, dtype=np.int64).reshape(-1, 4))

    def mesh(self, voxel=0.1, max_tris=120_000, smooth=4):
        """
        Готовая сетка: чистка и прореживание в Blender (bmesh), проверка
        на многообразность. Возвращает (точки, треугольники, отчёт).
        """
        import bmesh
        pts, tris, quads = self.polygons(voxel)
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in pts]
        for fc in list(tris) + list(quads):
            try:
                bm.faces.new([vs[i] for i in fc])
            except ValueError:
                pass                      # дубль грани — пропускаем
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # Рябь сетки: поверхность из вокселей 0.1 мм идёт мелкой «стиральной
        # доской». Принтеру она безразлична, но на картинках шумит. Лапласово
        # сглаживание с сохранением объёма; вершины дна не трогаем — оно
        # обязано остаться идеально плоским.
        free = [v for v in bm.verts if v.co.z > 1e-3]
        for _ in range(smooth):
            bmesh.ops.smooth_laplacian_vert(bm, verts=free, lambda_factor=0.6,
                                            lambda_border=0.0, use_x=True, use_y=True,
                                            use_z=True, preserve_volume=True)
        if len(bm.faces) > max_tris:
            decimate(bm, max_tris)
        bm.verts.ensure_lookup_table()
        out_pts = np.array([v.co[:] for v in bm.verts])
        idx = {v: i for i, v in enumerate(bm.verts)}
        out_faces = np.array([[idx[v] for v in fc.verts] for fc in bm.faces])
        bad = sum(1 for e in bm.edges if not e.is_manifold)
        report = {"tris": len(out_faces), "non_manifold_edges": bad}
        bm.free()
        return out_pts, out_faces, report


def decimate(bm, max_tris):
    """Прореживание коллапсом рёбер через модификатор Decimate."""
    import bpy
    me = bpy.data.meshes.new("tmp")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("tmp", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = max_tris / max(1, len(me.polygons))
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm.clear()
    bm.from_mesh(me2)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    bpy.data.meshes.remove(me2)
    import bmesh
    bmesh.ops.triangulate(bm, faces=bm.faces)


def write_stl(path: Path, pts, faces, header=b"dino-dig") -> None:
    tri = pts[faces]                                   # (n, 3, 3)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(ln == 0, 1, ln)
    rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"] = n
    rec["v"] = tri
    with open(path, "wb") as fh:
        fh.write(header.ljust(80, b"\0")[:80])
        fh.write(struct.pack("<I", len(tri)))
        fh.write(rec.tobytes())
