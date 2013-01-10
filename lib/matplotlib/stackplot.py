"""
Stacked area plot for 1D arrays inspired by Douglas Y'barbo's stackoverflow
answer:
http://stackoverflow.com/questions/2225995/how-can-i-create-stacked-line-graph-with-matplotlib

(http://stackoverflow.com/users/66549/doug)

"""
import numpy as np

__all__ = ['stackplot']


def stackplot(axes, x, *args, **kwargs):
    """Draws a stacked area plot.

    *x* : 1d array of dimension N

    *y* : 2d array of dimension MxN, OR any number 1d arrays each of dimension
          1xN. The data is assumed to be unstacked. Each of the following
          calls is legal::

            stackplot(x, y)               # where y is MxN
            stackplot(x, y1, y2, y3, y4)  # where y1, y2, y3, y4, are all 1xNm

    Keyword arguments:

    *baseline* : ['zero', 'sym', 'wiggle', 'weighted_wiggle']
                Method use to calculate to baseline. 'zero' is just a
                simple stacked plot. 'sym' is symmetric around zero and
                is sometimes called `ThemeRiver`.  'wiggle' minimizes the
                sum of the squared slopes. 'weighted_wiggle' does the
                same but weights to account for size of each layer.
                It is also called `Streamgraph`-layout. More details
                can be found in http://www.leebyron.com/else/streamgraph/.


    *colors* : A list or tuple of colors. These will be cycled through and
               used to colour the stacked areas.
               All other keyword arguments are passed to
               :func:`~matplotlib.Axes.fill_between`

    Returns *r* : A list of
    :class:`~matplotlib.collections.PolyCollection`, one for each
    element in the stacked area plot.
    """

    if len(args) == 1:
        y = np.atleast_2d(*args)
    elif len(args) > 1:
        y = np.row_stack(args)

    colors = kwargs.pop('colors', None)
    if colors is not None:
        axes.set_color_cycle(colors)

    baseline = kwargs.pop('baseline', 'zero')
    # Assume data passed has not been 'stacked', so stack it here.
    stack = np.cumsum(y, axis=0)

    r = []
    if baseline == 'zero':
        first_line = 0.

    elif baseline == 'sym':
        first_line = -np.sum(y, 0) * 0.5
        stack += first_line[None, :]

    elif baseline == 'wiggle':
        m = y.shape[0]
        first_line = (y * (m - 0.5 - np.arange(0, m)[:, None])).sum(0)
        first_line /= -m
        stack += first_line

    elif baseline == 'weighted_wiggle':
        #TODO: Vectorize this stuff.
        m, n = y.shape
        center = np.zeros(n)
        total = np.sum(y, 0)
        for i in range(n):
            if i > 0:
                center[i] = center[i - 1]
            for j in range(m):
                if i == 0:
                    increase = y[j, i]
                    move_up = 0.5
                else:
                    below_size = 0.5 * y[j, i]
                    for k in range(j + 1, m):
                        below_size += y[k, i]
                    increase = y[j, i] - y[j, i - 1]
                    move_up = below_size / total[i]
                center[i] += (move_up - 0.5) * increase
        first_line = center - 0.5 * total
        stack += first_line
    else:
        errstr = "Baseline method %s not recognised. " % baseline
        errstr += "Expected 'zero', 'sym', 'wiggle' or 'weighted_wiggle'"
        raise ValueError(errstr)

    # Color between x = 0 and the first array.
    r.append(axes.fill_between(x, first_line, stack[0, :],
                               facecolor=axes._get_lines.color_cycle.next(),
                               **kwargs))

    # Color between array i-1 and array i
    for i in xrange(len(y) - 1):
        color = axes._get_lines.color_cycle.next()
        r.append(axes.fill_between(x, stack[i, :], stack[i + 1, :],
                                   facecolor= color,
                                   **kwargs))
    return r
