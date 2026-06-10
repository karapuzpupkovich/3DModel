from dataclasses import dataclass


@dataclass(frozen=True)
class HoneycombConfig:
    # Locked overall geometry. Do not change these without explicit instruction.
    r_out: float = 48.0
    b_out: float = 15.0
    a_out: float = 62.5
    corner_radius: float = 6.0
    cell_len: float = 200.0
    wall_t: float = 2.3

    # Male joint.
    male_v1: float = -0.5
    male_v2: float = 3.0
    male_w1: float = 24.0
    male_w2: float = 31.0
    male_tip_radius: float = 0.8

    # Female joint.
    female_w_base: float = 25.6
    female_w_tip: float = 32.0
    female_depth: float = 3.2
    female_entry_radius: float = 1.0
    female_wing_offset: float = 2.0
    female_outer_offset: float = 1.0

    # Reinforcement pad behind the female groove.
    reinforcement_v1: float = -2.3
    reinforcement_v2: float = -4.8
    reinforcement_w1: float = 52.0
    reinforcement_w2: float = 42.0
    reinforcement_root_radius: float = 0.0
    reinforcement_tip_radius: float = 0.0
    reinforcement_edge_fillet: float = 1.2

    # Perforation.
    perforation_radius: float = 2.5
    perforation_corner_radius: float = 0.8
    perforation_spacing_u: float = 7.0
    perforation_spacing_z: float = 7.0
    perforation_rows: int = 27
    perforation_z_start: float = 9.0
    perforation_edge_min: float = 7.5
    perforation_joint_edge_min: float = 1.5
    perforation_groove_clearance: float = 13.5
    perforation_chamfer: float = 0.4
    perforation_batch_size: int = 24

    # Safety.
    end_fillet_r: float = 0.8


DEFAULT_CONFIG = HoneycombConfig()
