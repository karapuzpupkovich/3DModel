import FreeCAD
import Part
import math

step_path = r"c:\3DModel\Шкафчик Никиты (Сказка м.г.)\Shoerack_honeycomb.STEP"
print("Loading STEP file...")
shape = Part.Shape()
shape.read(step_path)
print("Loaded. Finding all faces...")

# Let's group holes by their orientation or coordinate
# In the STEP file, we can look at the center of the bounding box of each small face
holes = []
for i, f in enumerate(shape.Faces):
    # Holes are small faces. Let's filter by area or bounding box size
    if f.Area < 100.0: # A hole face usually has small area
        bbox = f.BoundBox
        center = bbox.Center
        holes.append((i, center, f.Area))

print(f"Total small faces found: {len(holes)}")
# Let's print a few of them to see their coordinates
for i, c, a in holes[:30]:
    print(f"Face {i}: Center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), Area={a:.2f}")

# Let's group hole centers by their face index or rotation angle in XY plane
# Let's project the center to XY plane and calculate angle
angles = []
for idx, center, area in holes:
    angle = math.degrees(math.atan2(center.y, center.x))
    if angle < 0:
        angle += 360.0
    angles.append((idx, center, angle))

# Let's see what angles we have
angle_buckets = {}
for idx, center, angle in angles:
    # Round to nearest 10 degrees for grouping
    bucket = round(angle / 10.0) * 10
    if bucket not in angle_buckets:
        angle_buckets[bucket] = []
    angle_buckets[bucket].append((idx, center))

print("\nHoles grouped by angle:")
for bucket, items in sorted(angle_buckets.items()):
    print(f"Angle ~{bucket} deg: {len(items)} faces")
    # Let's check the U coordinates (projection on the face tangent)
    # For a face at angle alpha, the tangent vector is (-sin(alpha), cos(alpha), 0)
    alpha_rad = math.radians(bucket)
    tangent = FreeCAD.Vector(-math.sin(alpha_rad), math.cos(alpha_rad), 0)
    normal = FreeCAD.Vector(math.cos(alpha_rad), math.sin(alpha_rad), 0)
    
    # Let's print unique U values for this face
    u_values = []
    for idx, center in items:
        # Calculate U relative to some reference (or just absolute projection)
        u = center.dot(tangent)
        u_values.append(u)
    
    # Find unique U values (with some tolerance)
    unique_u = []
    for u in sorted(u_values):
        if not any(abs(u - uu) < 0.5 for uu in unique_u):
            unique_u.append(u)
    print(f"  Unique U coordinates (tangential): {[round(u, 2) for u in unique_u]}")
