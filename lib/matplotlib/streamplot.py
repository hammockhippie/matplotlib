"""
Streamline plotting like Mathematica.
Copyright (c) 2011 Tom Flannaghan.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""
from operator import mul
from itertools import imap

import numpy as np
import matplotlib
import matplotlib.patches as mpp


__all__ = ['streamplot']


def streamplot(axes, x, y, u, v, density=1, linewidth=1, color='k', cmap=None,
               arrowsize=1, arrowstyle='-|>', minlength=0.1, integrator='RK4'):
    """Draws streamlines of a vector flow.

    Parameters
    ----------
    x, y : 1d arrays
        an *evenly spaced* grid.
    u, v : 2d arrays
        x and y-velocities. Number of rows should match length of y, and
        the number of columns should match x.
    density : float or 2-tuple
        Controls the closeness of streamlines. When `density = 1`, the domain
        is divided into a 25x25 grid---`density` linearly scales this grid.
        Each cell in the grid can have, at most, one traversing streamline.
        For different densities in each direction, use [density_x, density_y].
    linewidth : numeric or 2d array
        vary linewidth when given a 2d array with the same shape as velocities.
    color : matplotlib color code, or 2d array
        Streamline color. When given an array with the same shape as
        velocities, values are converted to color using cmap, norm, vmin and
        vmax args.
    cmap : Colormap
        Colormap used to plot streamlines and arrows. Only necessary when using
        an array input for `color`.
    arrowsize : float
        Factor scale arrow size.
    arrowstyle : str
        Arrow style specification. See `matplotlib.patches.FancyArrowPatch`.
    minlength : float
        Minimum length of streamline in axes coordinates.
    integrator : {'RK4'|'RK45'}
        Integration scheme.
            RK4 = 4th-order Runge-Kutta
            RK45 = adaptive-step Runge-Kutta-Fehlberg
    """
    grid = Grid(x, y)
    mask = StreamMask(density)
    dmap = DomainMap(grid, mask)

    if color is None:
        color = matplotlib.rcParams['lines.color']
    elif type(color) == np.ndarray:
        assert color.shape == grid.shape

    if linewidth is None:
        linewidth = matplotlib.rcParams['lines.linewidth']
    elif type(linewidth) == np.ndarray:
        assert linewidth.shape == grid.shape

    ## Sanity checks.
    assert u.shape == grid.shape
    assert v.shape == grid.shape

    integrate = get_integrator(u, v, dmap, minlength, integrator)

    trajectories = []
    for xm, ym in _gen_starting_points(mask.shape):
        if mask[ym, xm] == 0:
            xg, yg = dmap.mask2grid(xm, ym)
            t = integrate(xg, yg)
            if t != None:
                trajectories.append(t)

    # Load up the defaults - needed to get the color right.
    if type(color) == np.ndarray:
        norm = matplotlib.colors.normalize(color.min(), color.max())
        if cmap == None: cmap = matplotlib.cm.get_cmap(
            matplotlib.rcParams['image.cmap'])

    line_kw = {}
    arrow_kw = dict(arrowstyle=arrowstyle, mutation_scale=10*arrowsize)

    for t in trajectories:
        tgx = np.array(t[0])
        tgy = np.array(t[1])

        if type(linewidth) == np.ndarray:
            line_kw['linewidth'] = interpgrid(linewidth, tgx, tgy)[:-1]
            arrow_kw['linewidth'] = line_kw['linewidth'][len(tgx) / 2]
        else:
            line_kw['linewidth'] = linewidth
            arrow_kw['linewidth'] = linewidth

        if type(color) == np.ndarray:
            line_kw['color'] = cmap(norm(interpgrid(color, tgx, tgy)[:-1]))
            arrow_kw['color'] = line_kw['color'][len(tgx) / 2]
        else:
            line_kw['color'] = color
            arrow_kw['color'] = color

        # Rescale from grid-coordinates to data-coordinates.
        tx = np.array(t[0]) * grid.dx + grid.x_origin
        ty = np.array(t[1]) * grid.dy + grid.y_origin

        points = np.transpose([tx, ty]).reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        lc = matplotlib.collections.LineCollection(segments, **line_kw)
        axes.add_collection(lc)

        ## Add arrows half way along each trajectory.
        s = np.cumsum(np.sqrt(np.diff(tx)**2 + np.diff(ty)**2))
        n = np.searchsorted(s, s[-1] / 2.)
        arrow_tail = (tx[n], ty[n])
        arrow_head = (np.mean(tx[n:n+2]), np.mean(ty[n:n+2]))
        p = mpp.FancyArrowPatch(arrow_tail, arrow_head, **arrow_kw)
        axes.add_patch(p)

    axes.update_datalim(((x.min(), y.min()), (x.max(), y.max())))
    axes.autoscale_view(tight=True)


# Coordinate definitions
#========================

class DomainMap(object):
    """Map representing different coordinate systems.

    Coordinate definitions:

    * axes-coordinates goes from 0 to 1 in the domain.
    * data-coordinates are specified by the input x-y coordinates.
    * grid-coordinates goes from 0 to N and 0 to M for an N x M grid,
      where N and M match the shape of the input data.
    * mask-coordinates goes from 0 to N and 0 to M for an N x M mask,
      where N and M are user-specified to control the density of streamlines.

    This class also has methods for adding trajectories to the StreamMask.
    Before adding a trajectory, run `start_trajectory` to keep track of regions
    crossed by a given trajectory. Later, if you decide the trajectory is bad
    (e.g. if the trajectory is very short) just call `undo_trajectory`.
    """

    def __init__(self, grid, mask):
        self.grid = grid
        self.mask = mask
        ## Constants for conversion between grid- and mask-coordinates
        self.x_grid2mask = float(mask.nx - 1) / grid.nx
        self.y_grid2mask = float(mask.ny - 1) / grid.ny

        self.x_mask2grid = 1. / self.x_grid2mask
        self.y_mask2grid = 1. / self.y_grid2mask

        self.x_data2grid = grid.nx / grid.width
        self.y_data2grid = grid.ny / grid.height

    def grid2mask(self, xi, yi):
        """Return nearest space in mask-coords from given grid-coords."""
        return int((xi * self.x_grid2mask) + 0.5), \
               int((yi * self.y_grid2mask) + 0.5)

    def mask2grid(self, xm, ym):
        return xm * self.x_mask2grid, ym * self.y_mask2grid

    def data2grid(self, xd, yd):
        return xd * self.x_data2grid, yd * self.y_data2grid

    def start_trajectory(self, xg, yg):
        xm, ym = self.grid2mask(xg, yg)
        self.mask._start_trajectory(xm, ym)

    def reset_start_point(self, xg, yg):
        xm, ym = self.grid2mask(xg, yg)
        self.mask._current_xy = (xm, ym)

    def update_trajectory(self, xg, yg):
        if not self.grid.valid_index(xg, yg):
            raise InvalidIndexError
        xm, ym = self.grid2mask(xg, yg)
        self.mask._update_trajectory(xm, ym)

    def undo_trajectory(self):
        self.mask._undo_trajectory()


class Grid(object):
    """Grid of data."""
    def __init__(self, x, y):

        if len(x.shape) == 2:
            x_row = x[0]
            assert np.allclose(x_row, x)
            x = x_row
        else:
            assert len(x.shape) == 1

        if len(y.shape) == 2:
            y_col = y[:, 0]
            assert np.allclose(y_col, y.T)
            y = y_col
        else:
            assert len(y.shape) == 1

        self.nx = len(x)
        self.ny = len(y)

        self.dx = x[1] - x[0]
        self.dy = y[1] - y[0]

        self.x_origin = x[0]
        self.y_origin = y[0]

        self.width = x[-1] - x[0]
        self.height = y[-1] - y[0]

    @property
    def shape(self):
        return self.ny, self.nx

    def valid_index(self, xi, yi):
        """Return True if point is a valid index of grid."""
        return xi >= 0 and xi <= self.nx-1 and yi >= 0 and yi <= self.ny-1


class StreamMask(object):
    """Mask to keep track of discrete regions crossed by streamlines.

    The resolution of this grid determines the approximate spacing between
    trajectories. Streamlines are only allowed to pass through zeroed cells:
    When a streamline enters a cell, that cell is set to 1, and no new
    streamlines are allowed to enter.
    """

    def __init__(self, density):
        if type(density) == float or type(density) == int:
            assert density > 0
            self.nx = self.ny = int(30 * density)
        else:
            assert len(density) > 0
            self.nx = int(25 * density[0])
            self.ny = int(25 * density[1])
        self._mask = np.zeros((self.ny, self.nx))
        self.shape = self._mask.shape

        self._current_xy = None

    def __getitem__(self, *args):
        return self._mask.__getitem__(*args)

    def _start_trajectory(self, xm, ym):
        """Start recording streamline trajectory"""
        self._traj = []
        self._update_trajectory(xm, ym)

    def _undo_trajectory(self):
        """Remove current trajectory from mask"""
        for t in self._traj:
            self._mask.__setitem__(t, 0)

    def _update_trajectory(self, xm, ym):
        """Update current trajectory position in mask.

        If the new position has already been filled, raise `InvalidIndexError`.
        """
        if self._current_xy != (xm, ym):
            if self[ym, xm] == 0:
                self._traj.append((ym, xm))
                self._mask[ym, xm] = 1
                self._current_xy = (xm, ym)
            else:
                raise InvalidIndexError


class InvalidIndexError(Exception):
    pass


# Integrator definitions
#========================

def get_integrator(u, v, dmap, minlength, integrator):

    # rescale velocity onto grid-coordinates for integrations.
    u, v = dmap.data2grid(u, v)

    # speed (path length) will be in axes-coordinates
    u_ax = u / dmap.grid.nx
    v_ax = v / dmap.grid.ny
    speed = np.sqrt(u_ax**2 + v_ax**2)

    def forward_time(xi, yi):
        ds_dt = interpgrid(speed, xi, yi)
        dt_ds = 0 if ds_dt == 0 else 1. / ds_dt
        ui = interpgrid(u, xi, yi)
        vi = interpgrid(v, xi, yi)
        return ui * dt_ds, vi * dt_ds

    def backward_time(xi, yi):
        dxi, dyi = forward_time(xi, yi)
        return -dxi, -dyi

    if integrator == 'RK4':
        _integrate = _rk4
    elif integrator == 'RK45':
        _integrate = _rk45
    elif integrator == 'RK12':
        _integrate = _rk12

    def rk4_integrate(x0, y0):
        """Return x, y coordinates of trajectory based on starting point.

        Integrate both forward and backward in time from starting point.
        Integration is terminated when a trajectory reaches a domain boundary
        or when it crosses into an already occupied cell in the StreamMask. The
        resulting trajectory is None if it is shorter than `minlength`.
        """

        dmap.start_trajectory(x0, y0)
        sf, xf_traj, yf_traj = _integrate(x0, y0, dmap, forward_time)
        dmap.reset_start_point(x0, y0)
        sb, xb_traj, yb_traj = _integrate(x0, y0, dmap, backward_time)
        # combine forward and backward trajectories
        stotal = sf + sb
        x_traj = xb_traj[::-1] + xf_traj[1:]
        y_traj = yb_traj[::-1] + yf_traj[1:]

        if stotal > minlength:
            return x_traj, y_traj
        else: # reject short trajectories
            dmap.undo_trajectory()
            return None

    return rk4_integrate


def _rk12(x0, y0, dmap, f):
    """2nd-order Runge-Kutta algorithm with adaptive step size.

    This method is also referred to as the improved Euler's method, or Heun's
    method. This method is favored over higher-order methods because:

    1. To get decent looking trajectories and to sample every mask cell
       on the trajectory we need a small timestep, so a lower order
       solver doesn't hurt us unless the data is *very* high resolution.
       In fact, for cases where the user inputs
       data smaller or of similar grid size to the mask grid, the higher
       order corrections are negligible because of the very fast linear
       interpolation used in `interpgrid`.

    2. For high resolution input data (i.e. beyond the mask
       resolution), we must reduce the timestep. Therefore, an adaptive
       timestep is more suited to the problem as this would be very hard
       to judge automatically otherwise.

    This integrator is about 1.5 - 2x as fast as both the RK4 and RK45
    solvers in most setups on my machine. I would recommend removing the
    other two to keep things simple.
    """
    ## This error is below that needed to match the RK4 integrator. It
    ## is set for visual reasons -- too low and corners start
    ## appearing ugly and jagged. Can be tuned.
    maxerror = 0.003

    ## This limit is important (for all integrators) to avoid the
    ## trajectory skipping some mask cells. We could relax this
    ## condition if we use the code which is commented out below to
    ## increment the location gradually. However, due to the efficient
    ## nature of the interpolation, this doesn't boost speed by much
    ## for quite a bit of complexity.
    maxds = min(1./dmap.mask.nx, 1./dmap.mask.ny, 0.1)

    ds = maxds
    stotal = 0
    xi = x0
    yi = y0
    xf_traj = []
    yf_traj = []

    while dmap.grid.valid_index(xi, yi):
        xf_traj.append(xi)
        yf_traj.append(yi)
        try:
            k1x, k1y = f(xi, yi)
            k2x, k2y = f(xi + ds * k1x,
                         yi + ds * k1y)
        except IndexError:
            # Out of the domain on one of the intermediate integration steps.
            # Take an Euler step to the boundary to improve neatness.
            ds, xf_traj, yf_traj = _euler_step(xf_traj, yf_traj, dmap, f)
            stotal += ds
            break

        dx1 = ds * k1x
        dy1 = ds * k1y
        dx2 = ds * 0.5 * (k1x + k2x)
        dy2 = ds * 0.5 * (k1y + k2y)

        nx, ny = dmap.grid.shape
        # Error is normalized to the axes coordinates
        error = np.sqrt(((dx2-dx1)/nx)**2 + ((dy2-dy1)/ny)**2)

        # Only save step if within error tolerance
        if error < maxerror:
            xi += dx2
            yi += dy2
            try:
                dmap.update_trajectory(xi, yi)
            except InvalidIndexError:
                break
            if (stotal + ds) > 2:
                break
            stotal += ds

        # recalculate stepsize based on step error
        ds = min(maxds, 0.85 * ds * (maxerror/error)**0.2)

    return stotal, xf_traj, yf_traj


def _euler_step(xf_traj, yf_traj, dmap, f):
    """Simple Euler integration step."""
    nx, ny = dmap.grid.shape
    xi = xf_traj[-1]
    yi = yf_traj[-1]
    cx, cy = f(xi, yi) # ds.cx is in data coordinates, ds in axis coord.
    if cx > 0:
        dsx = (nx - 1 - xi) / cx
    else:
        dsx = xi / -cx
    if cy > 0:
        dsy = (ny - 1 - yi) / cy
    else:
        dsy = yi / -cy
    ds = min(dsx, dsy)
    xf_traj.append(xi + cx*ds)
    yf_traj.append(yi + cy*ds)
    return ds, xf_traj, yf_traj


def _rk4(x0, y0, dmap, f):
    """4th-order Runge-Kutta algorithm with fixed step size"""
    ds = min(1./dmap.mask.nx, 1./dmap.mask.ny, 0.01)
    stotal = 0
    xi = x0
    yi = y0
    xf_traj = []
    yf_traj = []

    while dmap.grid.valid_index(xi, yi):
        # Time step. First save the point.
        xf_traj.append(xi)
        yf_traj.append(yi)
        # Next, advance one using RK4
        try:
            k1x, k1y = f(xi, yi)
            k2x, k2y = f(xi + .5*ds*k1x, yi + .5*ds*k1y)
            k3x, k3y = f(xi + .5*ds*k2x, yi + .5*ds*k2y)
            k4x, k4y = f(xi + ds*k3x, yi + ds*k3y)
        except IndexError:
            # Out of the domain on one of the intermediate steps
            break
        xi += ds*(k1x+2*k2x+2*k3x+k4x) / 6.
        yi += ds*(k1y+2*k2y+2*k3y+k4y) / 6.
        # Final position might be out of the domain

        try:
            dmap.update_trajectory(xi, yi)
        except InvalidIndexError:
            break
        if (stotal + ds) > 2:
            break
        stotal += ds

    return stotal, xf_traj, yf_traj


def _rk45(x0, y0, dmap, f):
    """5th-order Runge-Kutta algorithm with adaptive step size"""
    maxerror = 0.001
    maxds = min(1./dmap.mask.nx, 1./dmap.mask.ny, 0.03)
    ds = maxds
    stotal = 0
    xi = x0
    yi = y0
    xf_traj = []
    yf_traj = []

    # RK45 coefficients (Runge-Kutta-Fehlberg method)
    a2 = 0.25
    a3 = (3./32, 9./32)
    a4 = (1932./2197, -7200./2197, 7296./2197)
    a5 = (439./216, -8, 3680./513, -845./4104)
    a6 = (-8./27, 2, -3544./2565, 1859./4104, -11./40)

    b4 = (25./216, 1408./2565, 2197./4104, -1./5)
    b5 = (16./135, 6656./12825, 28561./56430, -9./50, 2./55)

    while dmap.grid.valid_index(xi, yi):
        xf_traj.append(xi)
        yf_traj.append(yi)

        try:
            k1x, k1y = f(xi, yi)
            k2x, k2y = f(xi + ds * a2 * k1x,
                         yi + ds * a2 * k1y)
            k3x, k3y = f(xi + ds * dot(a3, (k1x, k2x)),
                         yi + ds * dot(a3, (k1y, k2y)))
            k4x, k4y = f(xi + ds * dot(a4, (k1x, k2x, k3x)),
                         yi + ds * dot(a4, (k1y, k2y, k3y)))
            k5x, k5y = f(xi + ds * dot(a5, (k1x, k2x, k3x, k4x)),
                         yi + ds * dot(a5, (k1y, k2y, k3y, k4y)))
            k6x, k6y = f(xi + ds * dot(a6, (k1x, k2x, k3x, k4x, k5x)),
                         yi + ds * dot(a6, (k1y, k2y, k3y, k4y, k5y)))
        except IndexError:
            # Out of the domain on one of the intermediate steps
            break

        dx4 = ds * dot(b4, (k1x, k3x, k4x, k5x))
        dy4 = ds * dot(b4, (k1y, k3y, k4y, k5y))
        dx5 = ds * dot(b5, (k1x, k3x, k4x, k5x, k6x))
        dy5 = ds * dot(b5, (k1y, k3y, k4y, k5y, k6y))

        nx, ny = dmap.grid.shape
        # Error is normalized to the axes coordinates
        error = np.sqrt(((dx5-dx4)/nx)**2 + ((dy5-dy4)/ny)**2)

        # Only save step if within error tolerance
        if error < maxerror:
            xi += dx5
            yi += dy5
            try:
                dmap.update_trajectory(xi, yi)
            except InvalidIndexError:
                break
            if (stotal + ds) > 2:
                break
            stotal += ds

        # recalculate stepsize based on Runge-Kutta-Fehlberg method
        ds = min(maxds, 0.85 * ds * (maxerror/error)**0.2)
    return stotal, xf_traj, yf_traj

# Utility functions
#========================

def interpgrid(a, xi, yi):
    """Fast 2D, linear interpolation on an integer grid"""
    if type(xi) == np.ndarray:
        x = xi.astype(np.int)
        y = yi.astype(np.int)
    else:
        x = np.int(xi)
        y = np.int(yi)
    a00 = a[y, x]
    a01 = a[y, x + 1]
    a10 = a[y + 1, x]
    a11 = a[y + 1, x + 1]
    xt = xi - x
    yt = yi - y
    a0 = a00 * (1 - xt) + a01 * xt
    a1 = a10 * (1 - xt) + a11 * xt
    return a0 * (1 - yt) + a1 * yt


def dot(seq1, seq2):
    """Dot product of two sequences.

    For short sequences, this is faster than transforming to numpy arrays.
    """
    return sum(imap(mul, seq1, seq2))


def _gen_starting_points(shape):
    """Yield starting points for streamlines.

    Trying points on the boundary first gives higher quality streamlines.
    This algorithm starts with a point on the mask corner and spirals inward.
    This algorithm is inefficient, but fast compared to rest of streamplot.
    """
    ny, nx = shape
    xfirst = 0
    yfirst = 1
    xlast = nx - 1
    ylast = ny - 1
    x, y = 0, 0
    i = 0
    direction = 'right'
    for i in xrange(nx * ny):

        yield x, y

        if direction == 'right':
            x += 1
            if x >= xlast:
                xlast -=1
                direction = 'up'
        elif direction == 'up':
            y += 1
            if y >= ylast:
                ylast -=1
                direction = 'left'
        elif direction == 'left':
            x -= 1
            if x <= xfirst:
                xfirst +=1
                direction = 'down'
        elif direction == 'down':
            y -= 1
            if y <= yfirst:
                yfirst +=1
                direction = 'right'

