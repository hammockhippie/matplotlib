"""
Plot the sparsity pattern of arrays
"""

from pylab import figure, show, nx

fig = figure()
ax1 = fig.add_subplot(221)
ax2 = fig.add_subplot(222)
ax3 = fig.add_subplot(223)
ax4 = fig.add_subplot(224)

x = nx.mlab.randn(20,20)
x[5] = 0.
x[:,12] = 0.

ax1.spy(x, markersize=5)
ax2.spy(x, precision=0.1, markersize=5)

ax3.spy2(x, aspect='auto', origin='lower')
ax4.spy2(x, precision=0.1, aspect='auto', origin='lower')

show()
