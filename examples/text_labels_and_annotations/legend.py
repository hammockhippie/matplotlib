"""
===============================
Legend using pre-defined labels
===============================

Defining legend labels with plots.
"""


import numpy as np
import matplotlib.pyplot as plt

# Make some fake data.
a = b = np.arange(0, 3, .02)
c = np.exp(a)
d = c[::-1]

# Create plots with pre-defined labels.
fig, ax = plt.subplots()
ax.plot(a, c, 'k--', label='Model length')
ax.plot(a, d, 'k:', label='Data length')
ax.plot(a, c + d, 'k', label='Total message length')

# Create an arrow with pre-defined label.
ax.annotate("", xy=(1.5, 4.5), xytext=(1.5, 9.0),
            arrowprops={'arrowstyle': '<->', 'color': 'C7'}, label='Distance')

legend = ax.legend(loc='upper center', shadow=True, fontsize='large')

# Put a nicer background color on the legend.
legend.get_frame().set_facecolor('C0')

plt.show()

#############################################################################
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `matplotlib.axes.Axes.plot` / `matplotlib.pyplot.plot`
#    - `matplotlib.axes.Axes.legend` / `matplotlib.pyplot.legend`
