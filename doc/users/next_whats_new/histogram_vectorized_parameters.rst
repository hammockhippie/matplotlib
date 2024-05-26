Vectorize ``hatch``, ``edgecolor``, ``linewidth`` and ``linestyle`` in *hist* methods
---------------------------------------------------------------------------------------

The parameters ``hatch``, ``edgecolor``, ``linewidth`` and ``linestyle`` of the `~matplotlib.axes.Axes.hist` method are now vectorized.
This means that you can pass a list of values to these parameters, and the values will be applied to each dataset in the histogram.
