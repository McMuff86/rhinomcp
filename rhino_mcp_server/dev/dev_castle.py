import sys
from rhinomcp.tools.execute_rhinoscript_python_code import execute_rhinoscript_python_code


CASTLE_CODE = r"""
import rhinoscriptsyntax as rs

# Cube block definition
name = "Cube"
s = 1.0  # cube edge length

if not rs.IsBlock(name):
    p0=(0,0,0); p1=(s,0,0); p2=(s,s,0); p3=(0,s,0)
    p4=(0,0,s); p5=(s,0,s); p6=(s,s,s); p7=(0,s,s)
    box_id = rs.AddBox([p0,p1,p2,p3,p4,p5,p6,p7])
    rs.AddBlock([box_id], (0,0,0), name, True)

# Simple castle parameters
W, D = 20, 14      # footprint in cubes (width, depth)
H_wall = 4         # wall height in cubes
H_tower = 8        # tower height in cubes (above ground)
gate_width = 3     # opening width in cubes (front wall)
gate_height = 3    # opening height in cubes

def insert_cube(ix, iy, iz):
    rs.InsertBlock(name, (ix*s, iy*s, iz*s), (1,1,1), 0.0)

count = 0

# Front and back walls
cx0 = (W - gate_width)//2
cx1 = cx0 + gate_width - 1
for x in range(W):
    for z in range(H_wall):
        # Front wall (y=0) with gate opening
        if not (cx0 <= x <= cx1 and z < gate_height):
            insert_cube(x, 0, z); count += 1
        # Back wall (y=D-1)
        insert_cube(x, D-1, z); count += 1

# Side walls (exclude corners to avoid duplicates)
for y in range(1, D-1):
    for z in range(H_wall):
        insert_cube(0, y, z); count += 1
        insert_cube(W-1, y, z); count += 1

# Corner towers (extend above wall height to avoid duplicates)
for z in range(H_wall, H_tower):
    insert_cube(0, 0, z); count += 1
    insert_cube(W-1, 0, z); count += 1
    insert_cube(0, D-1, z); count += 1
    insert_cube(W-1, D-1, z); count += 1

print("Block 'Cube' ensured. Placed {} block instances for the castle.".format(count))
"""


def main():
    result = execute_rhinoscript_python_code(None, CASTLE_CODE)
    # Print the server-provided message/result so the caller sees output
    print(result)


if __name__ == "__main__":
    sys.exit(main())


