from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import FreeCAD
import Part

from honeycomb_cell.config import DEFAULT_CONFIG, HoneycombConfig


@dataclass
class HoneycombBuildReport:
    holes_by_face: Dict[int, int] = field(default_factory=dict)
    total_holes: int = 0
    valid: bool = False


def _noop(_: str) -> None:
    return None


def _chunked(items: Sequence, chunk_size: int) -> Iterable[Sequence]:
    for index in range(0, len(items), chunk_size):
        yield items[index:index + chunk_size]


def get_face_angle_and_dist(index: int, config: HoneycombConfig) -> Tuple[float, float]:
    theta_0 = math.degrees(math.atan2(config.a_out - config.b_out, config.r_out))
    if index == 0:
        return theta_0, config.a_out * math.cos(math.radians(theta_0))
    if index == 1:
        return 90.0, config.r_out
    if index == 2:
        return 180.0 - theta_0, config.a_out * math.cos(math.radians(theta_0))
    if index == 3:
        return 180.0 + theta_0, config.a_out * math.cos(math.radians(theta_0))
    if index == 4:
        return 270.0, config.r_out
    if index == 5:
        return 360.0 - theta_0, config.a_out * math.cos(math.radians(theta_0))
    raise IndexError(f"Unsupported face index: {index}")


def make_filleted_polygon_with_radii(vertices: Sequence[FreeCAD.Vector], radii: Sequence[float]) -> Part.Wire:
    count = len(vertices)
    p_in: List[FreeCAD.Vector] = [None] * count
    p_out: List[FreeCAD.Vector] = [None] * count
    arcs: List[Part.Shape] = [None] * count

    for index, vertex in enumerate(vertices):
        radius = radii[index]
        if radius > 0.01:
            prev_vertex = vertices[(index - 1) % count]
            next_vertex = vertices[(index + 1) % count]
            tangent_1 = (prev_vertex - vertex).normalize()
            tangent_2 = (next_vertex - vertex).normalize()
            dot_value = max(-1.0, min(1.0, tangent_1.dot(tangent_2)))
            theta = math.acos(dot_value)
            half_theta = theta / 2.0
            distance = radius / math.sin(half_theta)
            cotangent = 1.0 / math.tan(half_theta)
            bisector = (tangent_1 + tangent_2).normalize()
            p_in[index] = vertex + tangent_1 * (radius * cotangent)
            p_out[index] = vertex + tangent_2 * (radius * cotangent)
            pivot = vertex + bisector * (distance - radius)
            arcs[index] = Part.Arc(p_in[index], pivot, p_out[index]).toShape()
        else:
            p_in[index] = vertex
            p_out[index] = vertex
            arcs[index] = None

    edges: List[Part.Shape] = []
    for index in range(count):
        if arcs[index] is not None:
            edges.append(arcs[index])
        line_start = p_out[index]
        line_end = p_in[(index + 1) % count]
        if (line_start - line_end).Length > 1e-5:
            edges.append(Part.makeLine(line_start, line_end))
    return Part.Wire(edges)


def make_filleted_polygon(vertices: Sequence[FreeCAD.Vector], radius: float) -> Part.Face:
    return Part.Face(make_filleted_polygon_with_radii(vertices, [radius] * len(vertices)))


def make_centered_trapezoid_face(
    mid: FreeCAD.Vector,
    alpha_deg: float,
    v1: float,
    v2: float,
    w1: float,
    w2: float,
    r_base: float = 0.0,
    r_tip: float = 0.0,
) -> Part.Face:
    alpha = math.radians(alpha_deg)
    normal = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    tangent = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)
    max_radius = 0.49 * min(abs(v2 - v1), w1, w2)
    r_base = min(r_base, max_radius)
    r_tip = min(r_tip, max_radius)
    p1 = mid - tangent * (w1 / 2.0) + normal * v1
    p2 = mid - tangent * (w2 / 2.0) + normal * v2
    p3 = mid + tangent * (w2 / 2.0) + normal * v2
    p4 = mid + tangent * (w1 / 2.0) + normal * v1
    return Part.Face(
        make_filleted_polygon_with_radii([p1, p2, p3, p4], [r_base, r_tip, r_tip, r_base])
    )


def make_female_cutter_face(mid: FreeCAD.Vector, alpha_deg: float, config: HoneycombConfig) -> Part.Face:
    alpha = math.radians(alpha_deg)
    normal = FreeCAD.Vector(math.cos(alpha), math.sin(alpha), 0)
    tangent = FreeCAD.Vector(-math.sin(alpha), math.cos(alpha), 0)

    p1 = mid - tangent * (config.female_w_base / 2.0 + config.female_wing_offset) + normal * config.female_outer_offset
    p2 = mid - tangent * (config.female_w_base / 2.0) + normal * 0.0
    p3 = mid - tangent * (config.female_w_tip / 2.0) + normal * (-config.female_depth)
    p4 = mid + tangent * (config.female_w_tip / 2.0) + normal * (-config.female_depth)
    p5 = mid + tangent * (config.female_w_base / 2.0) + normal * 0.0
    p6 = mid + tangent * (config.female_w_base / 2.0 + config.female_wing_offset) + normal * config.female_outer_offset
    vertices = [p1, p2, p3, p4, p5, p6]
    radii = [0.0, config.female_entry_radius, 0.0, 0.0, config.female_entry_radius, 0.0]
    return Part.Face(make_filleted_polygon_with_radii(vertices, radii))


def make_reinforcement_face(mid: FreeCAD.Vector, alpha_deg: float, config: HoneycombConfig) -> Part.Face:
    return make_centered_trapezoid_face(
        mid,
        alpha_deg,
        config.reinforcement_v1,
        config.reinforcement_v2,
        config.reinforcement_w1,
        config.reinforcement_w2,
        config.reinforcement_root_radius,
        config.reinforcement_tip_radius,
    )


def make_filleted_hex_wire(radius: float, y_pos: float, corner_radius: float) -> Part.Wire:
    points = []
    for index in range(6):
        angle = math.radians(index * 60)
        points.append(FreeCAD.Vector(radius * math.cos(angle), y_pos, radius * math.sin(angle)))
    return make_filleted_polygon_with_radii(points, [corner_radius] * 6)


def make_chamfered_hex_cutter(
    radius: float,
    corner_radius: float,
    y_inner: float,
    y_outer: float,
    chamfer: float,
) -> Part.Shape:
    w1 = make_filleted_hex_wire(radius + chamfer, y_inner - 5.0, corner_radius)
    w2 = make_filleted_hex_wire(radius + chamfer, y_inner, corner_radius)
    w3 = make_filleted_hex_wire(radius, y_inner + chamfer, corner_radius)
    w4 = make_filleted_hex_wire(radius, y_outer - chamfer, corner_radius)
    w5 = make_filleted_hex_wire(radius + chamfer, y_outer, corner_radius)
    w6 = make_filleted_hex_wire(radius + chamfer, y_outer + 5.0, corner_radius)
    return Part.makeLoft([w1, w2, w3, w4, w5, w6], True, True)


def _build_outer_vertices(config: HoneycombConfig) -> List[FreeCAD.Vector]:
    return [
        FreeCAD.Vector(config.a_out, 0, 0),
        FreeCAD.Vector(config.b_out, config.r_out, 0),
        FreeCAD.Vector(-config.b_out, config.r_out, 0),
        FreeCAD.Vector(-config.a_out, 0, 0),
        FreeCAD.Vector(-config.b_out, -config.r_out, 0),
        FreeCAD.Vector(config.b_out, -config.r_out, 0),
    ]


def _collect_end_edges_for_fillet(
    solid: Part.Shape,
    outer_edges: Sequence[Part.Shape],
    inner_edges: Sequence[Part.Shape],
    cell_len: float,
) -> List[Part.Shape]:
    end_edges = []
    for edge in solid.Edges:
        points = [edge.Vertex1.Point, edge.Vertex2.Point]
        if not (
            all(abs(point.z) < 0.01 for point in points)
            or all(abs(point.z - cell_len) < 0.01 for point in points)
        ):
            continue

        v1_xy = FreeCAD.Vector(edge.Vertex1.Point.x, edge.Vertex1.Point.y, 0)
        v2_xy = FreeCAD.Vector(edge.Vertex2.Point.x, edge.Vertex2.Point.y, 0)

        matched = False
        for source_edge in list(outer_edges) + list(inner_edges):
            d1_f = (v1_xy - source_edge.Vertex1.Point).Length
            d2_f = (v2_xy - source_edge.Vertex2.Point).Length
            d1_r = (v1_xy - source_edge.Vertex2.Point).Length
            d2_r = (v2_xy - source_edge.Vertex1.Point).Length
            if (d1_f < 0.01 and d2_f < 0.01) or (d1_r < 0.01 and d2_r < 0.01):
                matched = True
                break
        if matched:
            end_edges.append(edge)
    return end_edges


def _collect_all_end_edges(solid: Part.Shape, cell_len: float) -> List[Part.Shape]:
    end_edges = []
    for edge in solid.Edges:
        p1 = edge.Vertex1.Point
        p2 = edge.Vertex2.Point
        if abs(p1.z) < 0.01 and abs(p2.z) < 0.01:
            end_edges.append(edge)
        elif abs(p1.z - cell_len) < 0.01 and abs(p2.z - cell_len) < 0.01:
            end_edges.append(edge)
    return end_edges


def _collect_longitudinal_edges(solid: Part.Shape, cell_len: float) -> List[Part.Shape]:
    longitudinal_edges: List[Part.Shape] = []
    for edge in solid.Edges:
        p1 = edge.Vertex1.Point
        p2 = edge.Vertex2.Point
        if abs(p1.z - p2.z) < cell_len - 0.01:
            continue
        if not (
            (abs(p1.z) < 0.01 and abs(p2.z - cell_len) < 0.01)
            or (abs(p2.z) < 0.01 and abs(p1.z - cell_len) < 0.01)
        ):
            continue
        if FreeCAD.Vector(p1.x - p2.x, p1.y - p2.y, 0).Length > 0.01:
            continue
        longitudinal_edges.append(edge)
    return longitudinal_edges


def _collect_face_zone_longitudinal_edges(
    solid: Part.Shape,
    face_index: int,
    vertices_out: Sequence[FreeCAD.Vector],
    config: HoneycombConfig,
    cell_len: float,
    *,
    u_min_abs: float,
    u_max_abs: float,
    v_min: float,
    v_max: float,
) -> List[Part.Shape]:
    alpha_deg, _ = get_face_angle_and_dist(face_index, config)
    alpha_rad = math.radians(alpha_deg)
    tangent = FreeCAD.Vector(-math.sin(alpha_rad), math.cos(alpha_rad), 0)
    normal = FreeCAD.Vector(math.cos(alpha_rad), math.sin(alpha_rad), 0)
    face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5

    matched_edges: List[Part.Shape] = []
    for edge in solid.Edges:
        p1 = edge.Vertex1.Point
        p2 = edge.Vertex2.Point
        if abs(p1.z - p2.z) < cell_len - 5.0:
            continue
        if not (
            (abs(p1.z) < 2.0 and abs(p2.z - cell_len) < 2.0)
            or (abs(p2.z) < 2.0 and abs(p1.z - cell_len) < 2.0)
        ):
            continue
        if FreeCAD.Vector(p1.x - p2.x, p1.y - p2.y, 0).Length > 0.01:
            continue

        midpoint = (p1 + p2) * 0.5
        rel = midpoint - FreeCAD.Vector(face_mid.x, face_mid.y, midpoint.z)
        u = abs(rel.dot(tangent))
        v = rel.dot(normal)
        if u_min_abs - 0.01 <= u <= u_max_abs + 0.01 and v_min - 0.01 <= v <= v_max + 0.01:
            matched_edges.append(edge)
    return matched_edges


def _build_u_positions(max_u: float, row: int, spacing_u: float) -> List[float]:
    values: List[float] = []
    if row % 2 == 0:
        current = 0.0
        while current <= max_u + 0.1:
            values.append(current)
            if current > 0.01:
                values.append(-current)
            current += spacing_u
    else:
        current = spacing_u / 2.0
        while current <= max_u + 0.1:
            values.append(current)
            values.append(-current)
            current += spacing_u
    return values


def _filter_u_positions(
    max_u: float,
    row: int,
    spacing_u: float,
    *,
    min_abs_u: float = 0.0,
) -> List[float]:
    filtered: List[float] = []
    seen = set()
    for value in _build_u_positions(max_u, row, spacing_u):
        if abs(value) + 1e-6 < min_abs_u:
            continue
        rounded = round(value, 4)
        if rounded in seen:
            continue
        seen.add(rounded)
        filtered.append(value)
    return filtered


def _append_perforation_cutters(
    target: List[Part.Shape],
    positions: Sequence[float],
    *,
    face_mid: FreeCAD.Vector,
    tangent: FreeCAD.Vector,
    z_pos: float,
    rotation: float,
    y_inner: float,
    y_outer: float,
    config: HoneycombConfig,
) -> None:
    for u in positions:
        cutter = make_chamfered_hex_cutter(
            config.perforation_radius,
            config.perforation_corner_radius,
            y_inner,
            y_outer,
            config.perforation_chamfer,
        )
        if abs(rotation) > 0.001:
            cutter.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), rotation)
        cutter.translate(tangent * u + face_mid + FreeCAD.Vector(0, 0, z_pos))
        target.append(cutter)


def _build_perforation_cutters(
    vertices_out: Sequence[FreeCAD.Vector],
    config: HoneycombConfig,
    log: Callable[[str], None],
) -> Tuple[Dict[int, List[Part.Shape]], HoneycombBuildReport]:
    report = HoneycombBuildReport()
    face_half_lengths: Dict[int, float] = {}
    for index in range(6):
        current = vertices_out[index]
        nxt = vertices_out[(index + 1) % 6]
        face_half_lengths[index] = (current - nxt).Length / 2.0

    ridge_half_width = config.male_w1 / 2.0
    perforation_half_span = config.perforation_radius + config.perforation_chamfer
    joint_center_margin = config.perforation_joint_edge_min + perforation_half_span
    cutters_by_face: Dict[int, List[Part.Shape]] = {}

    for face_index in range(6):
        alpha_deg, _ = get_face_angle_and_dist(face_index, config)
        alpha_rad = math.radians(alpha_deg)
        tangent = FreeCAD.Vector(-math.sin(alpha_rad), math.cos(alpha_rad), 0)
        face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
        max_u = face_half_lengths[face_index] - config.perforation_edge_min
        is_ridge = face_index in (0, 5)
        is_groove = face_index in (2, 3)
        face_cutters: List[Part.Shape] = []
        rotation = alpha_deg - 90.0

        wall_min_abs_u = 0.0
        if is_ridge:
            wall_min_abs_u = config.male_w2 / 2.0 + joint_center_margin

        ridge_max_abs_u = max(0.0, ridge_half_width - joint_center_margin)
        for row in range(config.perforation_rows):
            z_pos = config.perforation_z_start + row * config.perforation_spacing_z
            u_positions = _build_u_positions(max_u, row, config.perforation_spacing_u)
            seen = set()
            for u in u_positions:
                if abs(u) > max_u:
                    continue
                rounded_u = round(u, 4)
                if rounded_u in seen:
                    continue
                seen.add(rounded_u)

                if is_groove:
                    R_p = config.perforation_radius + config.perforation_chamfer
                    is_inside_groove = (abs(u) + R_p <= config.female_w_base / 2.0)
                    is_outside_groove = (abs(u) - R_p >= config.female_w_tip / 2.0)
                    if not (is_inside_groove or is_outside_groove):
                        continue
                    if abs(u) <= config.reinforcement_w1 / 2.0:
                        y_inner = config.reinforcement_v2
                    else:
                        y_inner = -config.wall_t
                    y_outer = 0.0
                elif is_ridge:
                    if abs(u) <= ridge_max_abs_u:
                        y_inner = -config.wall_t
                        y_outer = config.male_v2
                    elif abs(u) >= wall_min_abs_u:
                        y_inner = -config.wall_t
                        y_outer = 0.0
                    else:
                        continue
                else:
                    y_inner = -config.wall_t
                    y_outer = 0.0

                _append_perforation_cutters(
                    face_cutters,
                    [u],
                    face_mid=face_mid,
                    tangent=tangent,
                    z_pos=z_pos,
                    rotation=rotation,
                    y_inner=y_inner,
                    y_outer=y_outer,
                    config=config,
                )

        cutters_by_face[face_index] = face_cutters
        report.holes_by_face[face_index] = len(face_cutters)
        report.total_holes += len(face_cutters)
        face_name = "flat" if face_index in (1, 4) else ("ridge" if is_ridge else "groove")
        log(f"Perforation face {face_index} ({face_name}): {len(face_cutters)} holes")

    return cutters_by_face, report


def create_honeycomb_cell_shape(
    config: HoneycombConfig | None = None,
    enable_perforation: bool = True,
    log: Callable[[str], None] | None = None,
) -> Tuple[Part.Shape, HoneycombBuildReport]:
    cfg = config or DEFAULT_CONFIG
    writer = log or _noop
    vertices_out = _build_outer_vertices(cfg)

    writer("Stage 1/6: building shell with reinforcement pads integrated")
    outer_face = make_filleted_polygon(vertices_out, cfg.corner_radius)
    inner_face = outer_face.makeOffset2D(-cfg.wall_t)
    
    # Create reinforcement faces in 2D
    reinf_faces = []
    for face_index in (2, 3):
        alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
        face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
        rf = make_reinforcement_face(face_mid, alpha_deg, cfg)
        reinf_faces.append(rf)
    
    # Cut reinforcement from inner face (void) to thicken the wall
    inner_face_reinf = inner_face
    for rf in reinf_faces:
        inner_face_reinf = inner_face_reinf.cut(rf)
    inner_face_reinf = inner_face_reinf.removeSplitter()
    
    # Final cell face
    cell_face = outer_face.cut(inner_face_reinf).removeSplitter()
    cell_solid = cell_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))

    writer("Stage 2/6: applying end and longitudinal fillets")
    # Apply end fillets to the entire cell ends (before male/female joints to keep geometry clean)
    end_edges = _collect_end_edges_for_fillet(
        cell_solid,
        cell_face.Wires[0].Edges,
        cell_face.Wires[1].Edges,
        cfg.cell_len,
    )
    if end_edges:
        try:
            cell_solid = cell_solid.makeFillet(cfg.end_fillet_r, end_edges)
        except Exception as e:
            writer(f"Error: failed to apply end fillets: {e}")
            raise

    # Apply longitudinal fillets to the reinforcement pad edges
    if cfg.reinforcement_edge_fillet > 0.0:
        reinforcement_edges: List[Part.Shape] = []
        for face_index in (2, 3):
            reinforcement_edges.extend(
                _collect_face_zone_longitudinal_edges(
                    cell_solid,
                    face_index,
                    vertices_out,
                    cfg,
                    cfg.cell_len,
                    u_min_abs=cfg.female_w_base / 2.0,
                    u_max_abs=cfg.reinforcement_w1 / 2.0,
                    v_min=cfg.reinforcement_v2,
                    v_max=0.0,
                )
            )
        if reinforcement_edges:
            try:
                cell_solid = cell_solid.makeFillet(cfg.reinforcement_edge_fillet, reinforcement_edges)
            except Exception as e:
                writer(f"Warning: failed to apply longitudinal fillets: {e}")

    writer("Stage 3/6: adding male joints")
    for face_index in (0, 5):
        alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
        face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
        male_face = make_centered_trapezoid_face(
            FreeCAD.Vector(0, 0, 0),
            90.0,
            cfg.male_v1,
            cfg.male_v2,
            cfg.male_w1,
            cfg.male_w2,
            0.0,
            cfg.male_tip_radius,
        )
        male_solid = male_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))

        male_solid.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), alpha_deg - 90.0)
        male_solid.translate(face_mid)
        cell_solid = cell_solid.fuse(male_solid).removeSplitter()

    writer("Stage 4/6: cutting female grooves")
    for face_index in (2, 3):
        alpha_deg, _ = get_face_angle_and_dist(face_index, cfg)
        face_mid = (vertices_out[face_index] + vertices_out[(face_index + 1) % 6]) * 0.5
        female_face = make_female_cutter_face(face_mid, alpha_deg, cfg)
        female_solid = female_face.extrude(FreeCAD.Vector(0, 0, cfg.cell_len))
        cell_solid = cell_solid.cut(female_solid).removeSplitter()

    writer("Stage 5/6: verifying shape integrity")

    report = HoneycombBuildReport()
    if enable_perforation:
        writer("Stage 6/6: cutting perforation in batches")
        cutters_by_face, report = _build_perforation_cutters(vertices_out, cfg, writer)
        for face_index, face_cutters in cutters_by_face.items():
            chunks = list(_chunked(face_cutters, cfg.perforation_batch_size))
            for batch_index, chunk in enumerate(chunks, start=1):
                writer(
                    f"Cutting face {face_index} batch {batch_index}/{len(chunks)} with {len(chunk)} holes"
                )
                compound = Part.makeCompound(list(chunk))
                cell_solid = cell_solid.cut(compound)
            cell_solid = cell_solid.removeSplitter()
    else:
        writer("Stage 6/6: perforation skipped")

    report.valid = cell_solid.isValid()
    return cell_solid, report
