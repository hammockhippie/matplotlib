"""
====================
Generate 3D polygons
====================

Demonstrate how to create polygons in 3D. Here we stack 3 hexagons, somewhat
like a traffic light.
"""

import matplotlib.pyplot as plt
import numpy as np

from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Coordinates of a hexagon
angles = np.linspace(0, 2 * np.pi, 6, endpoint=False)
x = np.cos(angles)
y = np.sin(angles)
zs = [0, 1, 2]

# Close the hexagon by repeating the first vertex
x = np.append(x, x[0])
y = np.append(y, y[0])

verts = []
for z in zs:
    verts.append(list(zip(x, y, np.full_like(x, z))))

ax = plt.figure().add_subplot(projection='3d')

poly = Poly3DCollection(verts, facecolors=['g', 'y', 'r'], alpha=.7)
ax.add_collection3d(poly)
ax.auto_scale_xyz(x, y, zs)
ax.set_aspect('equal')

plt.show()
