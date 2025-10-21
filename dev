import sys
import random
from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code


ART_CODE = r"""
import rhinoscriptsyntax as rs
import random
import math

# 1) Remove existing castle by deleting the 'Cube' block definition (deletes its instances too)
try:
    if rs.IsBlock("Cube"):
        rs.DeleteBlock("Cube")
except Exception as e:
    print("Delete Cube block warning:", e)

# 2) Define or ensure base blocks/shapes
name_cube = "Cube"
name_sphere = "SphereProto"
s = 1.0

def ensure_cube_block():
    if not rs.IsBlock(name_cube):
        p0=(0,0,0); p1=(s,0,0); p2=(s,s,0); p3=(0,s,0)
        p4=(0,0,s); p5=(s,0,s); p6=(s,s,s); p7=(0,s,s)
        box_id = rs.AddBox([p0,p1,p2,p3,p4,p5,p6,p7])
        rs.AddBlock([box_id], (0,0,0), name_cube, True)

def ensure_sphere_block():
    if not rs.IsBlock(name_sphere):
        sid = rs.AddSphere((0,0,0), 0.5)
        rs.AddBlock([sid], (0,0,0), name_sphere, True)

ensure_cube_block()
ensure_sphere_block()

# 3) Create colorful 3D artwork of cubes and spheres
random.seed(42)

def rand_color():
    return (random.randint(30,255), random.randint(30,255), random.randint(30,255))

def place_block(name, pt, scale=(1,1,1), angle=0.0):
    bid = rs.InsertBlock(name, pt, scale, angle)
    return bid

def colorize(obj_id, color):
    try:
        rs.ObjectColor(obj_id, color)
    except: pass

# Layout parameters
N = 220  # total elements
spread = 25.0
z_layers = [0.0, 2.5, 5.0, 8.0, 13.0]

placed = []

# 3a) A twisting helix of spheres
turns = 3
steps = 120
radius = 8.0
height = 14.0
for i in range(steps):
    t = float(i)/steps
    angle = t * turns * 2.0 * 3.14159
    x = radius * (1.0 + 0.2*random.random()) * math.cos(angle)
    y = radius * (1.0 + 0.2*random.random()) * math.sin(angle)
    z = t * height
    k = 0.6 + 0.6*random.random()
    sid = place_block(name_sphere, (x,y,z), (k,k,k), angle=0.0)
    colorize(sid, rand_color())
    placed.append(sid)

# 3b) Floating voxel clouds of cubes in several layers
for z in z_layers:
    for _ in range(25):
        x = random.uniform(-spread, spread)
        y = random.uniform(-spread, spread)
        u = random.uniform(0.6, 2.4)
        bid = place_block(name_cube, (x,y,z + random.uniform(-0.6,0.6)), (u,u,u), angle=0.0)
        colorize(bid, rand_color())
        placed.append(bid)

# 3c) A gradient arc of alternating cube/sphere elements
arc_R = 15.0
for i in range(40):
    t = i/39.0
    ang = (t*1.2 - 0.6) * 3.14159
    x = arc_R * math.cos(ang)
    y = arc_R * math.sin(ang)
    z = 1.0 + 8.0*(t**2)
    if i % 2 == 0:
        s = 0.9 + 0.9*t
        oid = place_block(name_cube, (x,y,z), (s,s,s), angle=0.0)
    else:
        s = 0.6 + 0.8*t
        oid = place_block(name_sphere, (x,y,z), (s,s,s), angle=0.0)
    # soft color gradient
    color = (int(255*t), int(180*(1-t)+40), int(255*(1-t)))
    colorize(oid, color)
    placed.append(oid)

print("Artwork placed objects:", len(placed))
"""


def main():
    result = execute_rhinoscript_python_code(None, ART_CODE)
    print(result)


if __name__ == "__main__":
    sys.exit(main())


