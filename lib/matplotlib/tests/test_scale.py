from __future__ import print_function

from matplotlib.testing.decorators import image_comparison
import matplotlib.pyplot as plt


@image_comparison(baseline_images=['log_scales'])
def test_complete():
    ax = plt.subplot(122, yscale='log', xscale='symlog')
    
    ax.axvline(24.1)
    ax.axhline(24.1)
    plt.show()
