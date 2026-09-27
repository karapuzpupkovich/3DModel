# -*- coding: utf-8 -*-
"""
Маленький рендер на numpy: z-буфер, мягкий свет и тени от солнца.

Зачем свой: на этой машине виртуальный процессор без AVX, и Cycles из
Blender 5 на нём падает (EXCEPTION_ILLEGAL_INSTRUCTION), а EEVEE и Workbench
без видеокарты не запускаются. Здесь нужен только numpy.

Как рисуется: каждый треугольник засыпается точками, число которых
пропорционально его площади на экране; ближайшая точка в пикселе побеждает
(z-буфер). Нормали интерполируются по вершинам — гладкое затенение.
Тень — карта глубины из точки солнца. Песок — шум по мировым координатам.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

RNG = np.random.default_rng(7)


# --------------------------------------------------------------------------- #
#  Камера
# --------------------------------------------------------------------------- #
@dataclass
class Camera:
    target: tuple
    dist: float
    elev: float
    azim: float
    fov: float = 30.0          # вертикальный угол обзора, градусы
    W: int = 1500
    H: int = 850

    def __post_init__(self):
        e, a = math.radians(self.elev), math.radians(self.azim)
        t = np.array(self.target, float)
        self.pos = t + self.dist * np.array([math.cos(e) * math.cos(a),
                                             math.cos(e) * math.sin(a), math.sin(e)])
        f = t - self.pos
        self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, [0, 0, 1.0])
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.fpx = (self.H / 2) / math.tan(math.radians(self.fov) / 2)

    def project(self, p):
        d = p - self.pos
        xc, yc, zc = d @ self.r, d @ self.u, d @ self.f
        zc = np.maximum(zc, 1e-6)
        return self.W / 2 + self.fpx * xc / zc, self.H / 2 - self.fpx * yc / zc, zc

    def rays(self):
        ys, xs = np.mgrid[0:self.H, 0:self.W].astype(np.float64)
        d = (self.f[None, None, :]
             + ((xs + 0.5 - self.W / 2) / self.fpx)[..., None] * self.r
             - ((ys + 0.5 - self.H / 2) / self.fpx)[..., None] * self.u)
        return d / np.linalg.norm(d, axis=-1, keepdims=True)


# --------------------------------------------------------------------------- #
#  Засыпка треугольников точками
# --------------------------------------------------------------------------- #
def vertex_normals(V, F):
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    vn = np.zeros_like(V)
    for k in range(3):
        np.add.at(vn, F[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    return vn


def sample(V, F, px_area, density=2.2, cap=4_000_000, smooth=True):
    """Точки на треугольниках: сколько — по площади на экране (или на карте)."""
    k = np.clip(np.ceil(px_area * density), 1, None).astype(np.int64)
    if k.sum() > cap:
        k = np.maximum(1, (k * cap / k.sum()).astype(np.int64))
    idx = np.repeat(np.arange(len(F)), k)
    r1 = RNG.random(len(idx))
    r2 = RNG.random(len(idx))
    s = np.sqrt(r1)
    b = np.stack([1 - s, s * (1 - r2), s * r2], axis=1)
    A, B, C = V[F[idx, 0]], V[F[idx, 1]], V[F[idx, 2]]
    P = b[:, :1] * A + b[:, 1:2] * B + b[:, 2:] * C
    if smooth:
        vn = vertex_normals(V, F)
        N = b[:, :1] * vn[F[idx, 0]] + b[:, 1:2] * vn[F[idx, 1]] + b[:, 2:] * vn[F[idx, 2]]
    else:
        fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
        N = fn[idx]
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    return P, N


def tri_area_2d(x, y, F):
    return 0.5 * np.abs((x[F[:, 1]] - x[F[:, 0]]) * (y[F[:, 2]] - y[F[:, 0]])
                        - (x[F[:, 2]] - x[F[:, 0]]) * (y[F[:, 1]] - y[F[:, 0]]))


def zmerge(buf_d, buf_i, pid, depth, payload_idx):
    """Оставить в каждом пикселе ближайшую точку; вернуть, кого записали."""
    order = np.lexsort((depth, pid))
    pid_s, first = np.unique(pid[order], return_index=True)
    win = order[first]
    better = depth[win] < buf_d[pid_s]
    buf_d[pid_s[better]] = depth[win][better]
    buf_i[pid_s[better]] = payload_idx[win][better]
    return pid_s[better], win[better]


# --------------------------------------------------------------------------- #
#  Шум для песка
# --------------------------------------------------------------------------- #
def value_noise(x, y, scale, seed=3):
    rng = np.random.default_rng(seed)
    g = rng.random((257, 257))
    # Решётка периодична: 257-й ряд и столбец повторяют нулевые. Иначе на
    # стыке периода (в том числе на x = 0 и y = 0) узлы 255->256 и 0 разные,
    # и по песку идёт прямой шов.
    g[256, :], g[:, 256] = g[0, :], g[:, 0]
    fx, fy = x / scale, y / scale
    ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    ix, iy = ix % 256, iy % 256
    a, b = g[ix, iy], g[ix + 1, iy]
    c, d = g[ix, iy + 1], g[ix + 1, iy + 1]
    return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty


def sand(x, y):
    n = (0.55 * value_noise(x, y, 0.35) + 0.30 * value_noise(x, y, 1.3, 5)
         + 0.15 * value_noise(x, y, 6.0, 9))
    return n


# --------------------------------------------------------------------------- #
#  Рендер
# --------------------------------------------------------------------------- #
def render(objects, cam: Camera, ground=None, sun=(-0.62, 0.42, -0.55), ss=2,
           bg=(0.93, 0.91, 0.88), shadow_res=0.35):
    """
    objects: [{"V": (n,3), "F": (m,3), "color": (r,g,b), "spec": 0.25, "smooth": True}]
    ground:  {"z": 0, "color": (r,g,b), "rect": (x0, x1, y0, y1) или None}
    """
    W, H = cam.W * ss, cam.H * ss
    cm = Camera(cam.target, cam.dist, cam.elev, cam.azim, cam.fov, W, H)
    L = -np.array(sun, float)
    L /= np.linalg.norm(L)                       # направление НА солнце

    # ---- камера: точки всех объектов в общий z-буфер
    buf_d = np.full(W * H, np.inf)
    buf_i = np.full(W * H, -1, dtype=np.int64)
    allP, allN, allC, allS = [], [], [], []
    base = 0
    for o in objects:
        V, F = np.asarray(o["V"], float), np.asarray(o["F"], np.int64)
        x, y, _ = cm.project(V)
        P, N = sample(V, F, tri_area_2d(x, y, F), smooth=o.get("smooth", True))
        px, py, pz = cm.project(P)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        P, N, px, py, pz = P[ok], N[ok], px[ok], py[ok], pz[ok]
        pid = py.astype(np.int64) * W + px.astype(np.int64)
        zmerge(buf_d, buf_i, pid, pz, np.arange(len(P)) + base)
        allP.append(P)
        allN.append(N)
        col = np.tile(np.array(o["color"], float), (len(P), 1))
        paint = o.get("paint")
        if paint:
            # «после покраски»: дно канавок — площадки, смотрящие туда же,
            # куда лицевая сторона, но утопленные ниже неё. Боковые стенки
            # (нормаль вбок) не трогаем. dir — нормаль лица таблички, так
            # что работает и для воткнутой в песок, не только для лежащей.
            dvec = np.array(paint.get("dir", (0.0, 0.0, 1.0)), float)
            level = paint.get("level", paint.get("z_below"))
            col[((P @ dvec) < level) & ((N @ dvec) > 0.7)] = paint["color"]
        allC.append(col)
        allS.append(np.full(len(P), o.get("spec", 0.25)))
        base += len(P)
    P = np.concatenate(allP) if allP else np.zeros((0, 3))
    N = np.concatenate(allN) if allN else np.zeros((0, 3))
    C = np.concatenate(allC) if allC else np.zeros((0, 3))
    S = np.concatenate(allS) if allS else np.zeros(0)

    # ---- карта теней из солнца (ортографическая)
    lr = np.cross(L, [0, 0, 1.0])
    lr = lr / np.linalg.norm(lr) if np.linalg.norm(lr) > 1e-6 else np.array([1.0, 0, 0])
    lu = np.cross(lr, L)
    smap = None
    if len(P):
        pts_all = []
        for o in objects:
            V, F = np.asarray(o["V"], float), np.asarray(o["F"], np.int64)
            sx, sy = V @ lr / shadow_res, V @ lu / shadow_res
            Ps, _ = sample(V, F, tri_area_2d(sx, sy, F), density=1.6, smooth=False)
            pts_all.append(Ps)
        Ps = np.concatenate(pts_all)
        sx, sy, sd = Ps @ lr / shadow_res, Ps @ lu / shadow_res, Ps @ L
        x0, y0 = np.floor(sx.min()) - 2, np.floor(sy.min()) - 2
        SW = int(sx.max() - x0) + 3
        SH = int(sy.max() - y0) + 3
        smap = np.full(SW * SH, -np.inf)
        ix = (sx - x0).astype(np.int64)
        iy = (sy - y0).astype(np.int64)
        np.maximum.at(smap, iy * SW + ix, sd)       # ближе к солнцу = больше sd
        smap = smap.reshape(SH, SW)

    def lit(points, normals):
        """
        1 — на солнце, 0 — в тени (PCF 3×3). Сдвиг растёт с наклоном
        поверхности к солнцу: на косых участках соседние тексели той же
        поверхности «выше» точки на tg(угла)·шаг карты, и без поправки
        поверхность затеняет сама себя полосами (shadow acne).
        """
        if smap is None:
            return np.ones(len(points))
        ndl = np.clip(normals @ L, 0.08, 1.0)
        tan = np.sqrt(1 - ndl ** 2) / ndl
        bias = np.minimum(0.15 + 1.8 * shadow_res * tan, 3.0)
        q = points + normals * 0.5 * shadow_res
        sx = q @ lr / shadow_res - x0
        sy = q @ lu / shadow_res - y0
        sd = q @ L
        acc = np.zeros(len(points))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                ix = np.clip((sx + dx).astype(np.int64), 0, smap.shape[1] - 1)
                iy = np.clip((sy + dy).astype(np.int64), 0, smap.shape[0] - 1)
                acc += (smap[iy, ix] <= sd + bias)
        return acc / 9.0

    img = np.zeros((W * H, 3))
    img[:] = bg
    hit = buf_i >= 0
    hit_ground = np.zeros(W * H, dtype=bool)

    # ---- земля
    if ground is not None:
        gz = ground.get("z", 0.0)
        d = cm.rays().reshape(-1, 3)
        t = (gz - cm.pos[2]) / np.where(np.abs(d[:, 2]) < 1e-9, -1e-9, d[:, 2])
        G = cm.pos + t[:, None] * d
        gdepth = t * (d @ cm.f)
        on = (t > 0)
        if ground.get("rect"):
            x0r, x1r, y0r, y1r = ground["rect"]
            on &= (G[:, 0] >= x0r) & (G[:, 0] <= x1r) & (G[:, 1] >= y0r) & (G[:, 1] <= y1r)
        show = on & (~hit | (gdepth < buf_d))
        if show.any():
            gp = G[show]
            nz = sand(gp[:, 0], gp[:, 1])
            col = np.array(ground["color"])[None, :] * (0.82 + 0.36 * nz[:, None])
            sh = lit(gp, np.broadcast_to(np.array([0.0, 0.0, 1.0]), gp.shape))
            dif = max(0.0, L[2])
            img[show] = col * (0.45 + 0.75 * dif * sh[:, None])
            hit_ground = show

    # ---- объекты
    if hit.any():
        vis = hit.copy()
        if ground is not None:
            vis &= ~hit_ground
        ids = buf_i[vis]
        p, n, c, s = P[ids], N[ids], C[ids], S[ids]
        view = cm.pos[None, :] - p
        view /= np.linalg.norm(view, axis=1, keepdims=True)
        n = np.where((np.sum(n * view, axis=1) < 0)[:, None], -n, n)
        sh = lit(p, n)
        ndl = np.clip(n @ L, 0, 1)
        fill_dir = np.array([0.55, -0.6, 0.58]); fill_dir /= np.linalg.norm(fill_dir)
        fill = np.clip(n @ fill_dir, 0, 1)
        h = L[None, :] + view
        h /= np.linalg.norm(h, axis=1, keepdims=True)
        spec = s * np.clip(np.sum(n * h, axis=1), 0, 1) ** 40 * sh
        up = np.clip(n[:, 2], 0, 1)
        shade = 0.20 + 0.10 * up + 0.85 * ndl * sh + 0.18 * fill
        img[vis] = np.clip(c * shade[:, None] + spec[:, None], 0, 1)

    img = img.reshape(H, W, 3)
    if ss > 1:
        img = img.reshape(cam.H, ss, cam.W, ss, 3).mean(axis=(1, 3))
    return img


def save(img, path):
    """PNG или JPEG по расширению. Для рендеров с зернистым песком JPEG
    в разы легче при той же картинке."""
    from PIL import Image
    im = Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8))
    kw = {"quality": 90, "optimize": True} if str(path).lower().endswith((".jpg", ".jpeg")) else {}
    im.save(path, **kw)
