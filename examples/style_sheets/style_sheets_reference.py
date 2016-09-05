"""
This example demonstrates different available style sheets on a common example.

The different plots are heavily similar to the other ones in the style sheet
gallery.
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_scatter(ax, prng, nb_samples=100):
    """ Scatter plot.
    """
    for mu, sigma, marker in [(-.5, 0.75, 'o'), (0.75, 1., 's')]:
        x, y = prng.normal(loc=mu, scale=sigma, size=(2, nb_samples))
        ax.plot(x, y, ls='none', marker=marker)
    ax.set_xlabel('X-label')
    ax.set_ylabel('Y-label')
    return ax


def plot_colored_sinusoidal_lines(ax):
    """ Plots sinusoidal lines with colors following the style color cycle.
    """
    L = 2*np.pi
    x = np.linspace(0, L)
    nb_colors = len(plt.rcParams['axes.prop_cycle'])
    shift = np.linspace(0, L, nb_colors, endpoint=False)
    for s in shift:
        ax.plot(x, np.sin(x + s), '-')
    ax.margins(0)
    return ax


def plot_bar_graphs(ax, prng, min_value=5, max_value=25, nb_samples=5):
    """ Plots two bar graphs side by side, with letters as xticklabels.
    """
    x = np.arange(nb_samples)
    ya, yb = prng.randint(min_value, max_value, size=(2, nb_samples))
    width = 0.25
    ax.bar(x, ya, width)
    ax.bar(x + width, yb, width, color='C2')
    ax.set_xticks(x + width)
    ax.set_xticklabels(['a', 'b', 'c', 'd', 'e'])
    return ax


def plot_colored_circles(ax, prng, nb_samples=15):
    """ Plots circle patches.

    NB: draws a fixed amount of samples, rather than using the length of
    the color cycle, because different styles may have different numbers
    of colors.
    """
    for sty_dict, j in zip(plt.rcParams['axes.prop_cycle'], range(nb_samples)):
        ax.add_patch(plt.Circle(prng.normal(scale=3, size=2),
                                radius=1.0, color=sty_dict['color']))
    # Force the limits to be the same across the styles (because different
    # styles may have different numbers of available colors).
    ax.set_xlim([-4, 7])
    ax.set_ylim([-5, 6])
    ax.set_aspect('equal', adjustable='box')  # to plot circles as circles
    return ax


def plot_image_and_patch(ax, prng, size=(20, 20)):
    """ Plots an image with random values and superimposes a circular patch.
    """
    values = prng.random_sample(size=size)
    ax.imshow(values, interpolation='none')
    c = plt.Circle((5, 5), radius=5, label='patch')
    ax.add_patch(c)


def plot_histograms(ax, prng, nb_samples=10000):
    """ Plots 4 histograms and a text annotation.
    """
    params = ((10, 10), (4, 12), (50, 12), (6, 55))
    for a, b in params:
        values = prng.beta(a, b, size=nb_samples)
        ax.hist(values, histtype="stepfilled", bins=30, alpha=0.8, normed=True)
    # Add a small annotation.
    ax.annotate('Annotation', xy=(0.25, 4.25), xycoords='data',
                xytext=(0.9, 0.9), textcoords='axes fraction',
                va="top", ha="right",
                bbox=dict(boxstyle="round", alpha=0.2),
                arrowprops=dict(
                          arrowstyle="->",
                          connectionstyle="angle,angleA=-95,angleB=35,rad=10"),
                )
    return ax


def plot_figure(style_label=None):
    """
    Sets up and plots the demonstration figure with the style `style_label`.
    If `style_label` is None, fall back to the `default` style.
    """
    if style_label is None:
        style_label = 'default'

    # Use a dedicated RandomState instance to draw the same "random" values
    # across the different figures.
    prng = np.random.RandomState(96917002)

    fig, axes = plt.subplots(ncols=3, nrows=2, num=style_label)
    fig.suptitle(style_label)

    plot_scatter(axes[0, 0], prng)
    plot_image_and_patch(axes[0, 1], prng)
    plot_bar_graphs(axes[0, 2], prng)
    plot_colored_circles(axes[1, 0], prng)
    plot_colored_sinusoidal_lines(axes[1, 1])
    plot_histograms(axes[1, 2], prng)

    fig.tight_layout()

    return fig


if __name__ == "__main__":

    # Plot a demonstration figure for every available style sheet.
    for style_label in plt.style.available:
        with plt.style.context(style_label):
            fig = plot_figure(style_label=style_label)

    plt.show()
