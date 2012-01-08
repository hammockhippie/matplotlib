import numpy as np
import matplotlib.pyplot as plt

Y, X = np.mgrid[-3:3:100j, -3:3:100j]
U = -1 - X**2 + Y
V = 1 + X - Y**2
speed = np.sqrt(U*U + V*V)

f, (ax1, ax2) = plt.subplots(ncols=2)
ax1.streamplot(X, Y, U, V)

lw = 5*speed/speed.max()
ax2.streamplot(X, Y, U, V, density=0.6,
               color=U, cmap=plt.cm.autumn, linewidth=lw)

plt.show()

