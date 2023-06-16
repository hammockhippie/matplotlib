"""
Function to support histogramming over hexagonal tesselations.
"""

import math

import numpy as np
import matplotlib.transforms as mtransforms


def hexbin(x, y, C=None, gridsize=100,
           xscale='linear', yscale='linear', extent=None,
           reduce_C_function=np.mean, mincnt=None):

    # Set the size of the hexagon grid
    if np.iterable(gridsize):
        nx, ny = gridsize
    else:
        nx = gridsize
        ny = int(nx / math.sqrt(3))

    # Will be log()'d if necessary, and then rescaled.
    tx = x
    ty = y

    if xscale == 'log':
        if np.any(x <= 0.0):
            raise ValueError(
                "x contains non-positive values, so cannot be log-scaled")
        tx = np.log10(tx)
    if yscale == 'log':
        if np.any(y <= 0.0):
            raise ValueError(
                "y contains non-positive values, so cannot be log-scaled")
        ty = np.log10(ty)
    if extent is not None:
        xmin, xmax, ymin, ymax = extent
    else:
        xmin, xmax = (tx.min(), tx.max()) if len(x) else (0, 1)
        ymin, ymax = (ty.min(), ty.max()) if len(y) else (0, 1)

        # to avoid issues with singular data, expand the min/max pairs
        xmin, xmax = mtransforms.nonsingular(xmin, xmax, expander=0.1)
        ymin, ymax = mtransforms.nonsingular(ymin, ymax, expander=0.1)

    nx1 = nx + 1
    ny1 = ny + 1
    nx2 = nx
    ny2 = ny
    n = nx1 * ny1 + nx2 * ny2

    # In the x-direction, the hexagons exactly cover the region from
    # xmin to xmax. Need some padding to avoid roundoff errors.
    padding = 1.e-9 * (xmax - xmin)
    xmin -= padding
    xmax += padding
    sx = (xmax - xmin) / nx
    sy = (ymax - ymin) / ny
    # Positions in hexagon index coordinates.
    ix = (tx - xmin) / sx
    iy = (ty - ymin) / sy
    ix1 = np.round(ix).astype(int)
    iy1 = np.round(iy).astype(int)
    ix2 = np.floor(ix).astype(int)
    iy2 = np.floor(iy).astype(int)
    # flat indices, plus one so that out-of-range points go to position 0.
    i1 = np.where((0 <= ix1) & (ix1 < nx1) & (0 <= iy1) & (iy1 < ny1),
                  ix1 * ny1 + iy1 + 1, 0)
    i2 = np.where((0 <= ix2) & (ix2 < nx2) & (0 <= iy2) & (iy2 < ny2),
                  ix2 * ny2 + iy2 + 1, 0)

    d1 = (ix - ix1) ** 2 + 3.0 * (iy - iy1) ** 2
    d2 = (ix - ix2 - 0.5) ** 2 + 3.0 * (iy - iy2 - 0.5) ** 2
    bdist = (d1 < d2)

    if C is None:  # [1:] drops out-of-range points.
        counts1 = np.bincount(i1[bdist], minlength=1 + nx1 * ny1)[1:]
        counts2 = np.bincount(i2[~bdist], minlength=1 + nx2 * ny2)[1:]
        accum = np.concatenate([counts1, counts2]).astype(float)
        if mincnt is not None:
            accum[accum < mincnt] = np.nan

    else:
        # store the C values in a list per hexagon index
        Cs_at_i1 = [[] for _ in range(1 + nx1 * ny1)]
        Cs_at_i2 = [[] for _ in range(1 + nx2 * ny2)]
        for i in range(len(x)):
            if bdist[i]:
                Cs_at_i1[i1[i]].append(C[i])
            else:
                Cs_at_i2[i2[i]].append(C[i])
        if mincnt is None:
            mincnt = 0
        accum = np.array(
            [reduce_C_function(acc) if len(acc) >= mincnt else np.nan
                for Cs_at_i in [Cs_at_i1, Cs_at_i2]
                for acc in Cs_at_i[1:]],  # [1:] drops out-of-range points.
            float)

    good_idxs = ~np.isnan(accum)

    offsets = np.zeros((n, 2), float)
    offsets[:nx1 * ny1, 0] = np.repeat(np.arange(nx1), ny1)
    offsets[:nx1 * ny1, 1] = np.tile(np.arange(ny1), nx1)
    offsets[nx1 * ny1:, 0] = np.repeat(np.arange(nx2) + 0.5, ny2)
    offsets[nx1 * ny1:, 1] = np.tile(np.arange(ny2), nx2) + 0.5
    offsets[:, 0] *= sx
    offsets[:, 1] *= sy
    offsets[:, 0] += xmin
    offsets[:, 1] += ymin
    # remove accumulation bins with no data
    offsets = offsets[good_idxs, :]
    accum = accum[good_idxs]

    return (*offsets.T, accum), (xmin, xmax), (ymin, ymax), (nx, ny)
