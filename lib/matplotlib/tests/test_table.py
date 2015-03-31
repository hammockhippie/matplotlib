from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.testing.decorators import image_comparison


@image_comparison(baseline_images=['table_zorder'],
                  extensions=['png'],
                  remove_text=True)
def test_zorder():
    data = [[66386, 174296],
            [58230, 381139]]

    colLabels = ('Freeze', 'Wind')
    rowLabels = ['%d year' % x for x in (100, 50)]

    cellText = []
    yoff = np.array([0.0] * len(colLabels))
    for row in reversed(data):
        yoff += row
        cellText.append(['%1.1f' % (x/1000.0) for x in yoff])

    t = np.linspace(0, 2*np.pi, 100)
    plt.plot(t, np.cos(t), lw=4, zorder=2)

    plt.table(cellText=cellText,
              rowLabels=rowLabels,
              colLabels=colLabels,
              loc='center',
              zorder=-2,
              )

    plt.table(cellText=cellText,
              rowLabels=rowLabels,
              colLabels=colLabels,
              loc='upper center',
              zorder=4,
              )
    plt.yticks([])


@image_comparison(baseline_images=['table_labels'],
                  extensions=['png'])
def test_label_colours():
    dim = 3

    c = np.linspace(0, 1, dim)
    colours = plt.cm.RdYlGn(c)
    cellText = [['1'] * dim] * dim

    fig = plt.figure()

    ax1 = fig.add_subplot(4, 1, 1)
    ax1.axis('off')
    ax1.table(cellText=cellText,
              rowColours=colours,
              loc='best')

    ax2 = fig.add_subplot(4, 1, 2)
    ax2.axis('off')
    ax2.table(cellText=cellText,
              rowColours=colours,
              rowLabels=['Header'] * dim,
              loc='best')

    ax3 = fig.add_subplot(4, 1, 3)
    ax3.axis('off')
    ax3.table(cellText=cellText,
              colColours=colours,
              loc='best')

    ax4 = fig.add_subplot(4, 1, 4)
    ax4.axis('off')
    ax4.table(cellText=cellText,
              colColours=colours,
              colLabels=['Header'] * dim,
              loc='best')


@image_comparison(baseline_images=['table_cell_manipulation'],
                  extensions=['png'])
def test_diff_cell_table():
    l1 = ('', 't0', 't1', 't2', 't3 ', 't4', 't5', 't6')
    l2 = ('DLI', 35, 38, 10, 22, 25, 85, 22)
    cells = ('horizontal', 'vertical', 'open', 'closed', 'T', 'R', 'B', 'L')

    fig = plt.figure(figsize=(4, len(cells)+1))
    for i, cell in enumerate(cells, 1):
        ax = fig.add_subplot(8, 1, i)
        ax.plot([1, 2, 3, 4, 5, 6])
        ax.table(
                colWidths=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
                cellText=[l1, l2],
                loc='center',
                colLoc='center',
                rowLoc='center',
                drawLines=cell,
                )
    plt.tight_layout()
