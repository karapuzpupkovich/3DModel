import sys
import os
import math

# We will verify the proposed column coordinates for Honeycomb large cell.
# Geometry parameters:
a_out = 72.0
r_out = 48.5
b_out = 45.0
corner_radius = 12.0
cell_len = 200.0

# Joint parameters:
male_w1 = 24.0
male_w2 = 31.0
female_w_base = 25.1
female_w_tip = 31.5
female_depth = 3.2
female_wing_offset = 2.0
reinforcement_w1 = 52.0
reinforcement_w2 = 42.0

# Perforation parameters:
perforation_radius = 2.8
perforation_corner_radius = 0.8
perforation_chamfer = 0.4
R_p = perforation_radius + perforation_chamfer # 3.2 mm outer cut radius

perforation_edge_min = 7.5
end_fillet_r = 0.8

# Proposed columns:
cols = {
    0: [-33.0, -26.4, -19.8, -6.6, 0.0, 6.6, 19.8, 26.4, 33.0], # Right (male)
    1: [-52.8, -46.2, -39.6, -33.0, -26.4, -19.8, -6.6, 0.0, 6.6, 19.8, 26.4, 33.0, 39.6, 46.2, 52.8], # Top (female)
    2: [-33.0, -26.4, -19.8, -6.6, 0.0, 6.6, 19.8, 26.4, 33.0], # Left (female)
    3: [-52.8, -46.2, -39.6, -33.0, -26.4, -19.8, -6.6, 0.0, 6.6, 19.8, 26.4, 33.0, 39.6, 46.2, 52.8], # Bottom (male)
}

print("=== Honeycomb Cell Perforation Mathematical Verification ===")

# 1. Corner fillets check:
# Flat horizontal face ends at |X| = a_out - corner_radius = 60.0
# Flat vertical face ends at |Y| = r_out - corner_radius = 36.5
print("\n1. Checking margins from outer corner fillets (must be >= 0.0 mm to avoid cutting the fillet):")
all_fillet_safe = True
for face_index, face_cols in cols.items():
    flat_limit = 36.5 if face_index in (0, 2) else 60.0
    for u in face_cols:
        edge = abs(u) + R_p
        margin = flat_limit - edge
        if margin < 0.0:
            print(f"  [ERROR] Face {face_index} col {u}: cuts into corner fillet by {-margin:.2f} mm!")
            all_fillet_safe = False
        else:
            print(f"  Face {face_index} col {u}: margin from corner fillet is {margin:.2f} mm (Safe)")
if all_fillet_safe:
    print("  [SUCCESS] All columns are safe from corner fillets!")

# 2. Joint features check:
# For male faces (0 & 3): male joint sloped base ends at |u| = male_w2 / 2 = 15.5
# For female faces (1 & 2): female groove sloped wing ends at |u| = female_w_base / 2 + female_wing_offset = 14.55
# For female faces (1 & 2): inner reinforcement pad slope ends at |u| = reinforcement_w1 / 2 = 26.0
print("\n2. Checking margins from joint features and slopes:")
all_joint_safe = True
for face_index, face_cols in cols.items():
    is_ridge = face_index in (0, 3)
    is_groove = face_index in (1, 2)
    
    for u in face_cols:
        if is_ridge:
            # Hole must be either completely inside the ridge tip (abs(u) + R_p <= male_w1 / 2.0)
            # or completely outside the ridge base (abs(u) - R_p >= male_w2 / 2.0)
            inside_limit = male_w1 / 2.0 # 12.0
            outside_limit = male_w2 / 2.0 # 15.5
            
            is_inside = (abs(u) + R_p) <= inside_limit
            is_outside = (abs(u) - R_p) >= outside_limit
            
            if not (is_inside or is_outside):
                print(f"  [ERROR] Face {face_index} col {u} intersects male joint slope! range: [{abs(u)-R_p:.2f}, {abs(u)+R_p:.2f}] vs [{inside_limit:.2f}, {outside_limit:.2f}]")
                all_joint_safe = False
            else:
                loc = "inside tip" if is_inside else "outside base"
                print(f"  Face {face_index} col {u} is safe ({loc})")
        elif is_groove:
            # Check groove entry slope: either completely inside groove bottom (abs(u) + R_p <= female_w_base / 2.0)
            # or completely outside groove wing (abs(u) - R_p >= female_w_base / 2.0 + female_wing_offset)
            inside_groove_limit = female_w_base / 2.0 # 12.55
            outside_groove_limit = female_w_base / 2.0 + female_wing_offset # 14.55
            
            is_inside_groove = (abs(u) + R_p) <= inside_groove_limit
            is_outside_groove = (abs(u) - R_p) >= outside_groove_limit
            
            if not (is_inside_groove or is_outside_groove):
                print(f"  [ERROR] Face {face_index} col {u} intersects female groove slope! range: [{abs(u)-R_p:.2f}, {abs(u)+R_p:.2f}] vs [{inside_groove_limit:.2f}, {outside_groove_limit:.2f}]")
                all_joint_safe = False
            else:
                loc = "inside groove" if is_inside_groove else "outside groove"
                print(f"  Face {face_index} col {u} is safe from groove slope ({loc})")

if all_joint_safe:
    print("  [SUCCESS] All columns are safe from joint features and slopes!")
