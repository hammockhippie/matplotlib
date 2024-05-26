"""
===================
Color line by value
===================

Create a line where the color at each pointed is determined
by a third value (in addition to x and y).
"""

import warnings

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.collections import LineCollection


def colored_line(x, y, c, ax, **lc_kwargs):
    """
    Plot a line with a color specified along the line by a third value. It does this
    by creating a collection of line segments. Each line segment is made up of two
    straight lines each connecting the current (x, y) point to the midpoints of the
    lines connecting the current point with its two neighbors. This creates a smooth
    line with no gaps between the line segments.

    Parameters
    ----------
    x, y : array-like or scalar
        The horizontal and vertical coordinates of the data points.
    c : array-like or scalar
        The color values, which should be the same size as x and y.
    ax : Axes
        Axis object on which to plot the colored line.
    **lc_kwargs
        Any additional arguments to pass to matplotlib.collections.LineCollection
        constructor. This should not include the array keyword argument because
        that is set to the color argument. If provided, it will be overridden.

    Returns
    -------
    matplotlib.collections.LineCollection
        The generated line collection representing the colored line.
    """
    # Give a warning if the user specified an array keyword argument
    if "array" in lc_kwargs:
        warnings.warn('The provided "array" keyword argument will be overridden')

    # Default the capstyle to butt so that the line segments smoothly line up
    default_kwargs = {"capstyle": "butt"}
    default_kwargs.update(lc_kwargs)

    # Compute the midpoints of the line segments. Include the first and last points
    # twice so we don't need any special syntax later to handle them.
    x_midpts = np.hstack((x[0], 0.5 * (x[1:] + x[:-1]), x[-1]))
    y_midpts = np.hstack((y[0], 0.5 * (y[1:] + y[:-1]), y[-1]))

    # Determine the start, middle, and end coordinate pair of each line segment.
    # Use the reshape to add an extra dimension so each pair of points is in its
    # own list. Then concatenate them to create:
    # [
    #   [(x1_start, y1_start), (x1_mid, y1_mid), (x1_end, y1_end)],
    #   [(x2_start, y2_start), (x2_mid, y2_mid), (x2_end, y2_end)],
    #   ...
    # ]
    coord_start = np.column_stack((x_midpts[:-1], y_midpts[:-1])).reshape(x.size, 1, 2)
    coord_mid = np.column_stack((x, y)).reshape(x.size, 1, 2)
    coord_end = np.column_stack((x_midpts[1:], y_midpts[1:])).reshape(x.size, 1, 2)
    segments = np.concatenate((coord_start, coord_mid, coord_end), axis=1)

    # Create the line collection and set the colors of each segment
    lc = LineCollection(segments, **default_kwargs)
    lc.set_array(c)

    # Add the collection to the axis and return the line collection object
    return ax.add_collection(lc)


# Some arbitrary function that gives x, y, and color values
t = np.linspace(-7.4, -0.5, 200)
x = 0.9 * np.sin(t)
y = 0.9 * np.cos(1.6 * t)
color = np.linspace(0, 2, t.size)

# Create a figure and plot the line on it
fig, ax = plt.subplots()
lines = colored_line(x, y, color, ax, linewidth=10, cmap="plasma")
fig.colorbar(lines)  # add a color legend

# Set the axis limits and tick positions
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_xticks((-1, 0, 1))
ax.set_yticks((-1, 0, 1))

plt.show()
