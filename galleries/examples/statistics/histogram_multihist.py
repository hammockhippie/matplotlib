"""
=====================================================
The histogram (hist) function with multiple data sets
=====================================================

Plot histogram with multiple sample sets and demonstrate:

* Use of legend with multiple sample sets
* Stacked bars
* Step curve with no fill
* Data sets of different sample sizes

Selecting different bin counts and sizes can significantly affect the
shape of a histogram. The Astropy docs have a great section on how to
select these parameters:
http://docs.astropy.org/en/stable/visualization/histogram.html
"""
# %%
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(19680801)

n_bins = 10
x = np.random.randn(1000, 3)

fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2)

colors = ['red', 'tan', 'lime']
ax0.hist(x, n_bins, density=True, histtype="bar", color=colors, label=colors)
ax0.legend(prop={'size': 10})
ax0.set_title('bars with legend')

ax1.hist(x, n_bins, density=True, histtype="bar", stacked=True)
ax1.set_title('stacked bar')

ax2.hist(x, n_bins, histtype="step", stacked=True, fill=False)
ax2.set_title('stack step (unfilled)')

# Make a multiple-histogram of data-sets with different length.
x_multi = [np.random.randn(n) for n in [10000, 5000, 2000]]
ax3.hist(x_multi, n_bins, histtype="bar")
ax3.set_title('different sample sizes')

fig.tight_layout()
plt.show()

# %%
# Setting properties for each sample set
# ------------
#
# Plotting a bar chart with sample sets differentiated using:
# * edgecolors
# * hatches
# * linewidths
# * linestyles
#
# Also, these parameters can be specified for all types of
# histograms (stacked, step, etc.) and not just for the *bar*
# type histogram as shown in the example.

hatches = ["-", ".", "x"]
linewidths = [1, 2, 3]
edgecolors = ["green", "red", "blue"]
linestyles = ["-", ":", "--"]

fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(nrows=2, ncols=2)

ax0.hist(
    x, n_bins, density=True, fill=False, histtype="bar",
    edgecolor=edgecolors, label=edgecolors
)
ax0.legend(prop={"size": 10})
ax0.set_title("Bars with Edgecolors")

ax1.hist(
    x, n_bins, density=True, histtype="bar",
    hatch=hatches, label=hatches
)
ax1.legend(prop={"size": 10})
ax1.set_title("Bars with Hatches")

ax2.hist(
    x, n_bins, density=True, fill=False, histtype="bar",
    linewidth=linewidths, edgecolor=edgecolors, label=linewidths
)
ax2.legend(prop={"size": 10})
ax2.set_title("Bars with Linewidths")

ax3.hist(
    x, n_bins, density=True, fill=False, histtype="bar",
    linestyle=linestyles, edgecolor=edgecolors, label=linestyles
)
ax3.legend(prop={"size": 10})
ax3.set_title("Bars with Linestyles")

fig.tight_layout()
plt.show()

# %%
#
# .. admonition:: References
#
#    The use of the following functions, methods, classes and modules is shown
#    in this example:
#
#    - `matplotlib.axes.Axes.hist` / `matplotlib.pyplot.hist`
