#!/usr/bin/env python
from pylab import *

delta = 0.025
x = y = arange(-3.0, 3.0, delta)
X, Y = meshgrid(x, y)
Z1 = bivariate_normal(X, Y, 1.0, 1.0, 0.0, 0.0)
Z2 = bivariate_normal(X, Y, 1.5, 0.5, 1, 1)

# difference of Gaussians
#im = imshow(Z2-Z1, interpolation='bilinear', origin='lower', cmap=cm.bone)
#axis('off')
# see contour_demo2.py for a colorbar example
levels, colls = contour(Z2-Z1, levels=6,
                        linewidths=arange(.5, 4, .5),
                        colors=('r', 'green', 'blue', (1,1,0), '#afeeee', 0.5),
                        origin='lower')
legend(loc='lower left')
savefig('test')
show()

