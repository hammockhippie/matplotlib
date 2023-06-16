# art3d.py, original mplot3d version by John Porter
# Parts rewritten by Reinier Heeres <reinier@heeres.eu>
# Minor additions by Ben Axelrod <baxelrod@coroware.com>

"""
Module containing 3D artist code and functions to convert 2D
artists into 3D versions which can be added to an Axes3D.
"""

import math
import warnings
from contextlib import contextmanager

import numpy as np
from matplotlib import (artist, cbook, lines, colors as mcolors, path as mpath,
                        text as mtext)
from matplotlib.patches import Patch
from matplotlib.colors import LightSource, Normalize
from matplotlib.collections import (LineCollection, PatchCollection,
                                    PathCollection, PolyCollection)

from . import proj3d


# ---------------------------------------------------------------------------- #
# chosen for backwards-compatibility
CLASSIC_LIGHTSOURCE = LightSource(azdeg=225, altdeg=19.4712)

# Unit cube
# All faces are oriented facing outwards - when viewed from the
# outside, their vertices are in a counterclockwise ordering.
# shape (6, 4, 3)
# panel order:  -x, -y, +x, +y, -z, +z
CUBOID = np.array([
    # -x
    (
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 1),
        (0, 1, 0),
    ),
    # -y
    (
        (0, 0, 0),
        (1, 0, 0),
        (1, 0, 1),
        (0, 0, 1),
    ),
    # +x
    (
        (1, 0, 0),
        (1, 1, 0),
        (1, 1, 1),
        (1, 0, 1),
    ),
    # +y
    (
        (0, 1, 0),
        (0, 1, 1),
        (1, 1, 1),
        (1, 1, 0),
    ),
    # -z
    (
        (0, 0, 0),
        (0, 1, 0),
        (1, 1, 0),
        (1, 0, 0),
    ),
    # +z
    (
        (0, 0, 1),
        (1, 0, 1),
        (1, 1, 1),
        (0, 1, 1),
    ),

])


# Base hexagon for creating prisms (HexBar3DCollection).
# sides are ordered anti-clockwise from left: ['W', 'SW', 'SE', 'E', 'NE', 'NW']
HEXAGON = np.array([
    [-2, 1],
    [-2, -1],
    [0, -2],
    [2, -1],
    [2, 1],
    [0, 2]
]) / 4

# ---------------------------------------------------------------------------- #


def is_none(*args):
    for a in args:
        yield a is None


def _norm_angle(a):
    """Return the given angle normalized to -180 < *a* <= 180 degrees."""
    a = (a + 360) % 360
    if a > 180:
        a = a - 360
    return a


def _norm_text_angle(a):
    """Return the given angle normalized to -90 < *a* <= 90 degrees."""
    a = (a + 180) % 180
    if a > 90:
        a = a - 180
    return a


def get_dir_vector(zdir):
    """
    Return a direction vector.

    Parameters
    ----------
    zdir : {'x', 'y', 'z', None, 3-tuple}
        The direction. Possible values are:

        - 'x': equivalent to (1, 0, 0)
        - 'y': equivalent to (0, 1, 0)
        - 'z': equivalent to (0, 0, 1)
        - *None*: equivalent to (0, 0, 0)
        - an iterable (x, y, z) is converted to an array

    Returns
    -------
    x, y, z : array
        The direction vector.
    """
    if zdir == 'x':
        return np.array((1, 0, 0))
    elif zdir == 'y':
        return np.array((0, 1, 0))
    elif zdir == 'z':
        return np.array((0, 0, 1))
    elif zdir is None:
        return np.array((0, 0, 0))
    elif np.iterable(zdir) and len(zdir) == 3:
        return np.array(zdir)
    else:
        raise ValueError("'x', 'y', 'z', None or vector of length 3 expected")


class Text3D(mtext.Text):
    """
    Text object with 3D position and direction.

    Parameters
    ----------
    x, y, z : float
        The position of the text.
    text : str
        The text string to display.
    zdir : {'x', 'y', 'z', None, 3-tuple}
        The direction of the text. See `.get_dir_vector` for a description of
        the values.

    Other Parameters
    ----------------
    **kwargs
         All other parameters are passed on to `~matplotlib.text.Text`.
    """

    def __init__(self, x=0, y=0, z=0, text='', zdir='z', **kwargs):
        mtext.Text.__init__(self, x, y, text, **kwargs)
        self.set_3d_properties(z, zdir)

    def get_position_3d(self):
        """Return the (x, y, z) position of the text."""
        return self._x, self._y, self._z

    def set_position_3d(self, xyz, zdir=None):
        """
        Set the (*x*, *y*, *z*) position of the text.

        Parameters
        ----------
        xyz : (float, float, float)
            The position in 3D space.
        zdir : {'x', 'y', 'z', None, 3-tuple}
            The direction of the text. If unspecified, the *zdir* will not be
            changed. See `.get_dir_vector` for a description of the values.
        """
        super().set_position(xyz[:2])
        self.set_z(xyz[2])
        if zdir is not None:
            self._dir_vec = get_dir_vector(zdir)

    def set_z(self, z):
        """
        Set the *z* position of the text.

        Parameters
        ----------
        z : float
        """
        self._z = z
        self.stale = True

    def set_3d_properties(self, z=0, zdir='z'):
        """
        Set the *z* position and direction of the text.

        Parameters
        ----------
        z : float
            The z-position in 3D space.
        zdir : {'x', 'y', 'z', 3-tuple}
            The direction of the text. Default: 'z'.
            See `.get_dir_vector` for a description of the values.
        """
        self._z = z
        self._dir_vec = get_dir_vector(zdir)
        self.stale = True

    @artist.allow_rasterization
    def draw(self, renderer):
        position3d = np.array((self._x, self._y, self._z))
        proj = proj3d._proj_trans_points(
            [position3d, position3d + self._dir_vec], self.axes.M)
        dx = proj[0][1] - proj[0][0]
        dy = proj[1][1] - proj[1][0]
        angle = math.degrees(math.atan2(dy, dx))
        with cbook._setattr_cm(self, _x=proj[0][0], _y=proj[1][0],
                               _rotation=_norm_text_angle(angle)):
            mtext.Text.draw(self, renderer)
        self.stale = False

    def get_tightbbox(self, renderer=None):
        # Overwriting the 2d Text behavior which is not valid for 3d.
        # For now, just return None to exclude from layout calculation.
        return None


def text_2d_to_3d(obj, z=0, zdir='z'):
    """
    Convert a `.Text` to a `.Text3D` object.

    Parameters
    ----------
    z : float
        The z-position in 3D space.
    zdir : {'x', 'y', 'z', 3-tuple}
        The direction of the text. Default: 'z'.
        See `.get_dir_vector` for a description of the values.
    """
    obj.__class__ = Text3D
    obj.set_3d_properties(z, zdir)


class Line3D(lines.Line2D):
    """
    3D line object.
    """

    def __init__(self, xs, ys, zs, *args, **kwargs):
        """

        Parameters
        ----------
        xs : array-like
            The x-data to be plotted.
        ys : array-like
            The y-data to be plotted.
        zs : array-like
            The z-data to be plotted.

        Additional arguments are passed onto :func:`~matplotlib.lines.Line2D`.
        """
        super().__init__([], [], *args, **kwargs)
        self.set_data_3d(xs, ys, zs)

    def set_3d_properties(self, zs=0, zdir='z'):
        """
        Set the *z* position and direction of the line.

        Parameters
        ----------
        zs : float or array of floats
            The location along the *zdir* axis in 3D space to position the
            line.
        zdir : {'x', 'y', 'z'}
            Plane to plot line orthogonal to. Default: 'z'.
            See `.get_dir_vector` for a description of the values.
        """
        xs = self.get_xdata()
        ys = self.get_ydata()
        zs = cbook._to_unmasked_float_array(zs).ravel()
        zs = np.broadcast_to(zs, len(xs))
        self._verts3d = juggle_axes(xs, ys, zs, zdir)
        self.stale = True

    def set_data_3d(self, *args):
        """
        Set the x, y and z data

        Parameters
        ----------
        x : array-like
            The x-data to be plotted.
        y : array-like
            The y-data to be plotted.
        z : array-like
            The z-data to be plotted.

        Notes
        -----
        Accepts x, y, z arguments or a single array-like (x, y, z)
        """
        if len(args) == 1:
            args = args[0]
        for name, xyz in zip('xyz', args):
            if not np.iterable(xyz):
                raise RuntimeError(f'{name} must be a sequence')
        self._verts3d = args
        self.stale = True

    def get_data_3d(self):
        """
        Get the current data

        Returns
        -------
        verts3d : length-3 tuple or array-like
            The current data as a tuple or array-like.
        """
        return self._verts3d

    @artist.allow_rasterization
    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, self.axes.M)
        self.set_data(xs, ys)
        super().draw(renderer)
        self.stale = False


def line_2d_to_3d(line, zs=0, zdir='z'):
    """
    Convert a `.Line2D` to a `.Line3D` object.

    Parameters
    ----------
    zs : float
        The location along the *zdir* axis in 3D space to position the line.
    zdir : {'x', 'y', 'z'}
        Plane to plot line orthogonal to. Default: 'z'.
        See `.get_dir_vector` for a description of the values.
    """

    line.__class__ = Line3D
    line.set_3d_properties(zs, zdir)


def _path_to_3d_segment(path, zs=0, zdir='z'):
    """Convert a path to a 3D segment."""

    zs = np.broadcast_to(zs, len(path))
    pathsegs = path.iter_segments(simplify=False, curves=False)
    seg = [(x, y, z) for (((x, y), code), z) in zip(pathsegs, zs)]
    seg3d = [juggle_axes(x, y, z, zdir) for (x, y, z) in seg]
    return seg3d


def _paths_to_3d_segments(paths, zs=0, zdir='z'):
    """Convert paths from a collection object to 3D segments."""

    if not np.iterable(zs):
        zs = np.broadcast_to(zs, len(paths))
    else:
        if len(zs) != len(paths):
            raise ValueError('Number of z-coordinates does not match paths.')

    segs = [_path_to_3d_segment(path, pathz, zdir)
            for path, pathz in zip(paths, zs)]
    return segs


def _path_to_3d_segment_with_codes(path, zs=0, zdir='z'):
    """Convert a path to a 3D segment with path codes."""

    zs = np.broadcast_to(zs, len(path))
    pathsegs = path.iter_segments(simplify=False, curves=False)
    seg_codes = [((x, y, z), code) for ((x, y), code), z in zip(pathsegs, zs)]
    if seg_codes:
        seg, codes = zip(*seg_codes)
        seg3d = [juggle_axes(x, y, z, zdir) for (x, y, z) in seg]
    else:
        seg3d = []
        codes = []
    return seg3d, list(codes)


def _paths_to_3d_segments_with_codes(paths, zs=0, zdir='z'):
    """
    Convert paths from a collection object to 3D segments with path codes.
    """

    zs = np.broadcast_to(zs, len(paths))
    segments_codes = [_path_to_3d_segment_with_codes(path, pathz, zdir)
                      for path, pathz in zip(paths, zs)]
    if segments_codes:
        segments, codes = zip(*segments_codes)
    else:
        segments, codes = [], []
    return list(segments), list(codes)


class Line3DCollection(LineCollection):
    """
    A collection of 3D lines.
    """

    def set_sort_zpos(self, val):
        """Set the position to use for z-sorting."""
        self._sort_zpos = val
        self.stale = True

    def set_segments(self, segments):
        """
        Set 3D segments.
        """
        self._segments3d = segments
        super().set_segments([])

    def do_3d_projection(self):
        """
        Project the points according to renderer matrix.
        """
        xyslist = [proj3d._proj_trans_points(points, self.axes.M)
                   for points in self._segments3d]
        segments_2d = [np.column_stack([xs, ys]) for xs, ys, zs in xyslist]
        LineCollection.set_segments(self, segments_2d)

        # FIXME
        minz = 1e9
        for xs, ys, zs in xyslist:
            minz = min(minz, min(zs))
        return minz


def line_collection_2d_to_3d(col, zs=0, zdir='z'):
    """Convert a `.LineCollection` to a `.Line3DCollection` object."""
    segments3d = _paths_to_3d_segments(col.get_paths(), zs, zdir)
    col.__class__ = Line3DCollection
    col.set_segments(segments3d)


class Patch3D(Patch):
    """
    3D patch object.
    """

    def __init__(self, *args, zs=(), zdir='z', **kwargs):
        """
        Parameters
        ----------
        verts :
        zs : float
            The location along the *zdir* axis in 3D space to position the
            patch.
        zdir : {'x', 'y', 'z'}
            Plane to plot patch orthogonal to. Default: 'z'.
            See `.get_dir_vector` for a description of the values.
        """
        super().__init__(*args, **kwargs)
        self.set_3d_properties(zs, zdir)

    def set_3d_properties(self, verts, zs=0, zdir='z'):
        """
        Set the *z* position and direction of the patch.

        Parameters
        ----------
        verts :
        zs : float
            The location along the *zdir* axis in 3D space to position the
            patch.
        zdir : {'x', 'y', 'z'}
            Plane to plot patch orthogonal to. Default: 'z'.
            See `.get_dir_vector` for a description of the values.
        """
        zs = np.broadcast_to(zs, len(verts))
        self._segment3d = [juggle_axes(x, y, z, zdir)
                           for ((x, y), z) in zip(verts, zs)]

    def get_path(self):
        return self._path2d

    def do_3d_projection(self):
        s = self._segment3d
        xs, ys, zs = zip(*s)
        vxs, vys, vzs, vis = proj3d.proj_transform_clip(xs, ys, zs,
                                                        self.axes.M)
        self._path2d = mpath.Path(np.column_stack([vxs, vys]))
        return min(vzs)


class PathPatch3D(Patch3D):
    """
    3D PathPatch object.
    """

    def __init__(self, path, *, zs=(), zdir='z', **kwargs):
        """
        Parameters
        ----------
        path :
        zs : float
            The location along the *zdir* axis in 3D space to position the
            path patch.
        zdir : {'x', 'y', 'z', 3-tuple}
            Plane to plot path patch orthogonal to. Default: 'z'.
            See `.get_dir_vector` for a description of the values.
        """
        # Not super().__init__!
        Patch.__init__(self, **kwargs)
        self.set_3d_properties(path, zs, zdir)

    def set_3d_properties(self, path, zs=0, zdir='z'):
        """
        Set the *z* position and direction of the path patch.

        Parameters
        ----------
        path :
        zs : float
            The location along the *zdir* axis in 3D space to position the
            path patch.
        zdir : {'x', 'y', 'z', 3-tuple}
            Plane to plot path patch orthogonal to. Default: 'z'.
            See `.get_dir_vector` for a description of the values.
        """
        Patch3D.set_3d_properties(self, path.vertices, zs=zs, zdir=zdir)
        self._code3d = path.codes

    def do_3d_projection(self):
        s = self._segment3d
        xs, ys, zs = zip(*s)
        vxs, vys, vzs, vis = proj3d.proj_transform_clip(xs, ys, zs,
                                                        self.axes.M)
        self._path2d = mpath.Path(np.column_stack([vxs, vys]), self._code3d)
        return min(vzs)


def _get_patch_verts(patch):
    """Return a list of vertices for the path of a patch."""
    trans = patch.get_patch_transform()
    path = patch.get_path()
    polygons = path.to_polygons(trans)
    return polygons[0] if len(polygons) else np.array([])


def patch_2d_to_3d(patch, z=0, zdir='z'):
    """Convert a `.Patch` to a `.Patch3D` object."""
    verts = _get_patch_verts(patch)
    patch.__class__ = Patch3D
    patch.set_3d_properties(verts, z, zdir)


def pathpatch_2d_to_3d(pathpatch, z=0, zdir='z'):
    """Convert a `.PathPatch` to a `.PathPatch3D` object."""
    path = pathpatch.get_path()
    trans = pathpatch.get_patch_transform()

    mpath = trans.transform_path(path)
    pathpatch.__class__ = PathPatch3D
    pathpatch.set_3d_properties(mpath, z, zdir)


class Patch3DCollection(PatchCollection):
    """
    A collection of 3D patches.
    """

    def __init__(self, *args, zs=0, zdir='z', depthshade=True, **kwargs):
        """
        Create a collection of flat 3D patches with its normal vector
        pointed in *zdir* direction, and located at *zs* on the *zdir*
        axis. 'zs' can be a scalar or an array-like of the same length as
        the number of patches in the collection.

        Constructor arguments are the same as for
        :class:`~matplotlib.collections.PatchCollection`. In addition,
        keywords *zs=0* and *zdir='z'* are available.

        Also, the keyword argument *depthshade* is available to indicate
        whether to shade the patches in order to give the appearance of depth
        (default is *True*). This is typically desired in scatter plots.
        """
        self._depthshade = depthshade
        super().__init__(*args, **kwargs)
        self.set_3d_properties(zs, zdir)

    def get_depthshade(self):
        return self._depthshade

    def set_depthshade(self, depthshade):
        """
        Set whether depth shading is performed on collection members.

        Parameters
        ----------
        depthshade : bool
            Whether to shade the patches in order to give the appearance of
            depth.
        """
        self._depthshade = depthshade
        self.stale = True

    def set_sort_zpos(self, val):
        """Set the position to use for z-sorting."""
        self._sort_zpos = val
        self.stale = True

    def set_3d_properties(self, zs, zdir):
        """
        Set the *z* positions and direction of the patches.

        Parameters
        ----------
        zs : float or array of floats
            The location or locations to place the patches in the collection
            along the *zdir* axis.
        zdir : {'x', 'y', 'z'}
            Plane to plot patches orthogonal to.
            All patches must have the same direction.
            See `.get_dir_vector` for a description of the values.
        """
        # Force the collection to initialize the face and edgecolors
        # just in case it is a scalarmappable with a colormap.
        self.update_scalarmappable()
        offsets = self.get_offsets()
        if len(offsets) > 0:
            xs, ys = offsets.T
        else:
            xs = []
            ys = []
        self._offsets3d = juggle_axes(xs, ys, np.atleast_1d(zs), zdir)
        self._z_markers_idx = slice(-1)
        self._vzs = None
        self.stale = True

    def do_3d_projection(self):
        xs, ys, zs = self._offsets3d
        vxs, vys, vzs, vis = proj3d.proj_transform_clip(xs, ys, zs,
                                                        self.axes.M)
        self._vzs = vzs
        super().set_offsets(np.column_stack([vxs, vys]))

        if vzs.size > 0:
            return min(vzs)
        else:
            return np.nan

    def _maybe_depth_shade_and_sort_colors(self, color_array):
        color_array = (
            _zalpha(color_array, self._vzs)
            if self._vzs is not None and self._depthshade
            else color_array
        )
        if len(color_array) > 1:
            color_array = color_array[self._z_markers_idx]
        return mcolors.to_rgba_array(color_array, self._alpha)

    def get_facecolor(self):
        return self._maybe_depth_shade_and_sort_colors(super().get_facecolor())

    def get_edgecolor(self):
        # We need this check here to make sure we do not double-apply the depth
        # based alpha shading when the edge color is "face" which means the
        # edge colour should be identical to the face colour.
        if cbook._str_equal(self._edgecolors, 'face'):
            return self.get_facecolor()
        return self._maybe_depth_shade_and_sort_colors(super().get_edgecolor())


class Path3DCollection(PathCollection):
    """
    A collection of 3D paths.
    """

    def __init__(self, *args, zs=0, zdir='z', depthshade=True, **kwargs):
        """
        Create a collection of flat 3D paths with its normal vector
        pointed in *zdir* direction, and located at *zs* on the *zdir*
        axis. 'zs' can be a scalar or an array-like of the same length as
        the number of paths in the collection.

        Constructor arguments are the same as for
        :class:`~matplotlib.collections.PathCollection`. In addition,
        keywords *zs=0* and *zdir='z'* are available.

        Also, the keyword argument *depthshade* is available to indicate
        whether to shade the patches in order to give the appearance of depth
        (default is *True*). This is typically desired in scatter plots.
        """
        self._depthshade = depthshade
        self._in_draw = False
        super().__init__(*args, **kwargs)
        self.set_3d_properties(zs, zdir)
        self._offset_zordered = None

    def draw(self, renderer):
        with self._use_zordered_offset():
            with cbook._setattr_cm(self, _in_draw=True):
                super().draw(renderer)

    def set_sort_zpos(self, val):
        """Set the position to use for z-sorting."""
        self._sort_zpos = val
        self.stale = True

    def set_3d_properties(self, zs, zdir):
        """
        Set the *z* positions and direction of the paths.

        Parameters
        ----------
        zs : float or array of floats
            The location or locations to place the paths in the collection
            along the *zdir* axis.
        zdir : {'x', 'y', 'z'}
            Plane to plot paths orthogonal to.
            All paths must have the same direction.
            See `.get_dir_vector` for a description of the values.
        """
        # Force the collection to initialize the face and edgecolors
        # just in case it is a scalarmappable with a colormap.
        self.update_scalarmappable()
        offsets = self.get_offsets()
        if len(offsets) > 0:
            xs, ys = offsets.T
        else:
            xs = []
            ys = []
        self._offsets3d = juggle_axes(xs, ys, np.atleast_1d(zs), zdir)
        # In the base draw methods we access the attributes directly which
        # means we cannot resolve the shuffling in the getter methods like
        # we do for the edge and face colors.
        #
        # This means we need to carry around a cache of the unsorted sizes and
        # widths (postfixed with 3d) and in `do_3d_projection` set the
        # depth-sorted version of that data into the private state used by the
        # base collection class in its draw method.
        #
        # Grab the current sizes and linewidths to preserve them.
        self._sizes3d = self._sizes
        self._linewidths3d = np.array(self._linewidths)
        xs, ys, zs = self._offsets3d

        # Sort the points based on z coordinates
        # Performance optimization: Create a sorted index array and reorder
        # points and point properties according to the index array
        self._z_markers_idx = slice(-1)
        self._vzs = None
        self.stale = True

    def set_sizes(self, sizes, dpi=72.0):
        super().set_sizes(sizes, dpi)
        if not self._in_draw:
            self._sizes3d = sizes

    def set_linewidth(self, lw):
        super().set_linewidth(lw)
        if not self._in_draw:
            self._linewidths3d = np.array(self._linewidths)

    def get_depthshade(self):
        return self._depthshade

    def set_depthshade(self, depthshade):
        """
        Set whether depth shading is performed on collection members.

        Parameters
        ----------
        depthshade : bool
            Whether to shade the patches in order to give the appearance of
            depth.
        """
        self._depthshade = depthshade
        self.stale = True

    def do_3d_projection(self):
        xs, ys, zs = self._offsets3d
        vxs, vys, vzs, vis = proj3d.proj_transform_clip(xs, ys, zs,
                                                        self.axes.M)
        # Sort the points based on z coordinates
        # Performance optimization: Create a sorted index array and reorder
        # points and point properties according to the index array
        z_markers_idx = self._z_markers_idx = np.argsort(vzs)[::-1]
        self._vzs = vzs

        # we have to special case the sizes because of code in collections.py
        # as the draw method does
        #      self.set_sizes(self._sizes, self.figure.dpi)
        # so we cannot rely on doing the sorting on the way out via get_*

        if len(self._sizes3d) > 1:
            self._sizes = self._sizes3d[z_markers_idx]

        if len(self._linewidths3d) > 1:
            self._linewidths = self._linewidths3d[z_markers_idx]

        PathCollection.set_offsets(self, np.column_stack((vxs, vys)))

        # Re-order items
        vzs = vzs[z_markers_idx]
        vxs = vxs[z_markers_idx]
        vys = vys[z_markers_idx]

        # Store ordered offset for drawing purpose
        self._offset_zordered = np.column_stack((vxs, vys))

        return np.min(vzs) if vzs.size else np.nan

    @contextmanager
    def _use_zordered_offset(self):
        if self._offset_zordered is None:
            # Do nothing
            yield
        else:
            # Swap offset with z-ordered offset
            old_offset = self._offsets
            super().set_offsets(self._offset_zordered)
            try:
                yield
            finally:
                self._offsets = old_offset

    def _maybe_depth_shade_and_sort_colors(self, color_array):
        color_array = (
            _zalpha(color_array, self._vzs)
            if self._vzs is not None and self._depthshade
            else color_array
        )
        if len(color_array) > 1:
            color_array = color_array[self._z_markers_idx]
        return mcolors.to_rgba_array(color_array, self._alpha)

    def get_facecolor(self):
        return self._maybe_depth_shade_and_sort_colors(super().get_facecolor())

    def get_edgecolor(self):
        # We need this check here to make sure we do not double-apply the depth
        # based alpha shading when the edge color is "face" which means the
        # edge colour should be identical to the face colour.
        if cbook._str_equal(self._edgecolors, 'face'):
            return self.get_facecolor()
        return self._maybe_depth_shade_and_sort_colors(super().get_edgecolor())


def patch_collection_2d_to_3d(col, zs=0, zdir='z', depthshade=True):
    """
    Convert a `.PatchCollection` into a `.Patch3DCollection` object
    (or a `.PathCollection` into a `.Path3DCollection` object).

    Parameters
    ----------
    zs : float or array of floats
        The location or locations to place the patches in the collection along
        the *zdir* axis. Default: 0.
    zdir : {'x', 'y', 'z'}
        The axis in which to place the patches. Default: "z".
        See `.get_dir_vector` for a description of the values.
    depthshade
        Whether to shade the patches to give a sense of depth. Default: *True*.

    """
    if isinstance(col, PathCollection):
        col.__class__ = Path3DCollection
    elif isinstance(col, PatchCollection):
        col.__class__ = Patch3DCollection
    col._depthshade = depthshade
    col._in_draw = False
    col.set_3d_properties(zs, zdir)


class Poly3DCollection(PolyCollection):
    """
    A collection of 3D polygons.

    .. note::
        **Filling of 3D polygons**

        There is no simple definition of the enclosed surface of a 3D polygon
        unless the polygon is planar.

        In practice, Matplotlib fills the 2D projection of the polygon. This
        gives a correct filling appearance only for planar polygons. For all
        other polygons, you'll find orientations in which the edges of the
        polygon intersect in the projection. This will lead to an incorrect
        visualization of the 3D area.

        If you need filled areas, it is recommended to create them via
        `~mpl_toolkits.mplot3d.axes3d.Axes3D.plot_trisurf`, which creates a
        triangulation and thus generates consistent surfaces.
    """

    def __init__(self, verts, *args, zsort='average', shade=False,
                 lightsource=None, **kwargs):
        """
        Parameters
        ----------
        verts : list of (N, 3) array-like
            The sequence of polygons [*verts0*, *verts1*, ...] where each
            element *verts_i* defines the vertices of polygon *i* as a 2D
            array-like of shape (N, 3).
        zsort : {'average', 'min', 'max'}, default: 'average'
            The calculation method for the z-order.
            See `~.Poly3DCollection.set_zsort` for details.
        shade : bool, default: False
            Whether to shade *facecolors* and *edgecolors*. When activating
            *shade*, *facecolors* and/or *edgecolors* must be provided.

            .. versionadded:: 3.7

        lightsource : `~matplotlib.colors.LightSource`, optional
            The lightsource to use when *shade* is True.

            .. versionadded:: 3.7

        *args, **kwargs
            All other parameters are forwarded to `.PolyCollection`.

        Notes
        -----
        Note that this class does a bit of magic with the _facecolors
        and _edgecolors properties.
        """
        if shade:
            normals = _generate_normals(verts)
            facecolors = kwargs.get('facecolors', None)
            if facecolors is not None:
                kwargs['facecolors'] = _shade_colors(
                    facecolors, normals, lightsource
                )

            edgecolors = kwargs.get('edgecolors', None)
            if edgecolors is not None:
                kwargs['edgecolors'] = _shade_colors(
                    edgecolors, normals, lightsource
                )
            if facecolors is None and edgecolors in None:
                raise ValueError(
                    "You must provide facecolors, edgecolors, or both for "
                    "shade to work.")
        super().__init__(verts, *args, **kwargs)
        if isinstance(verts, np.ndarray):
            if verts.ndim != 3:
                raise ValueError('verts must be a list of (N, 3) array-like')
        else:
            if any(len(np.shape(vert)) != 2 for vert in verts):
                raise ValueError('verts must be a list of (N, 3) array-like')
        self.set_zsort(zsort)
        self._codes3d = None

    _zsort_functions = {
        'average': np.average,
        'min': np.min,
        'max': np.max,
    }

    def set_zsort(self, zsort):
        """
        Set the calculation method for the z-order.

        Parameters
        ----------
        zsort : {'average', 'min', 'max'}
            The function applied on the z-coordinates of the vertices in the
            viewer's coordinate system, to determine the z-order.
        """
        self._zsortfunc = self._zsort_functions[zsort]
        self._sort_zpos = None
        self.stale = True

    def get_vector(self, segments3d):
        """Optimize points for projection."""
        if len(segments3d):
            xs, ys, zs = np.row_stack(segments3d).T
        else:  # row_stack can't stack zero arrays.
            xs, ys, zs = [], [], []
        ones = np.ones(len(xs))
        self._vec = np.array([xs, ys, zs, ones])

        indices = [0, *np.cumsum([len(segment) for segment in segments3d])]
        self._segslices = [*map(slice, indices[:-1], indices[1:])]

    def set_verts(self, verts, closed=True):
        """
        Set 3D vertices.

        Parameters
        ----------
        verts : list of (N, 3) array-like
            The sequence of polygons [*verts0*, *verts1*, ...] where each
            element *verts_i* defines the vertices of polygon *i* as a 2D
            array-like of shape (N, 3).
        closed : bool, default: True
            Whether the polygon should be closed by adding a CLOSEPOLY
            connection at the end.
        """
        self.get_vector(verts)
        # 2D verts will be updated at draw time
        super().set_verts([], False)
        self._closed = closed

    def set_verts_and_codes(self, verts, codes):
        """Set 3D vertices with path codes."""
        # set vertices with closed=False to prevent PolyCollection from
        # setting path codes
        self.set_verts(verts, closed=False)
        # and set our own codes instead.
        self._codes3d = codes

    def set_3d_properties(self):
        # Force the collection to initialize the face and edgecolors
        # just in case it is a scalarmappable with a colormap.
        self.update_scalarmappable()
        self._sort_zpos = None
        self.set_zsort('average')
        self._facecolor3d = PolyCollection.get_facecolor(self)
        self._edgecolor3d = PolyCollection.get_edgecolor(self)
        self._alpha3d = PolyCollection.get_alpha(self)
        self.stale = True

    def set_sort_zpos(self, val):
        """Set the position to use for z-sorting."""
        self._sort_zpos = val
        self.stale = True

    def do_3d_projection(self):
        """
        Perform the 3D projection for this object.
        """
        if self._A is not None:
            # force update of color mapping because we re-order them
            # below.  If we do not do this here, the 2D draw will call
            # this, but we will never port the color mapped values back
            # to the 3D versions.
            #
            # We hold the 3D versions in a fixed order (the order the user
            # passed in) and sort the 2D version by view depth.
            self.update_scalarmappable()
            if self._face_is_mapped:
                self._facecolor3d = self._facecolors
            if self._edge_is_mapped:
                self._edgecolor3d = self._edgecolors
        txs, tys, tzs = proj3d._proj_transform_vec(self._vec, self.axes.M)
        xyzlist = [(txs[sl], tys[sl], tzs[sl]) for sl in self._segslices]

        # This extra fuss is to re-order face / edge colors
        cface = self._facecolor3d
        cedge = self._edgecolor3d
        if len(cface) != len(xyzlist):
            cface = cface.repeat(len(xyzlist), axis=0)
        if len(cedge) != len(xyzlist):
            if len(cedge) == 0:
                cedge = cface
            else:
                cedge = cedge.repeat(len(xyzlist), axis=0)

        if xyzlist:
            # sort by depth (furthest drawn first)
            z_segments_2d = sorted(
                ((self._zsortfunc(zs), np.column_stack([xs, ys]), fc, ec, idx)
                 for idx, ((xs, ys, zs), fc, ec)
                 in enumerate(zip(xyzlist, cface, cedge))),
                key=lambda x: x[0], reverse=True)

            _, segments_2d, self._facecolors2d, self._edgecolors2d, idxs = \
                zip(*z_segments_2d)
        else:
            segments_2d = []
            self._facecolors2d = np.empty((0, 4))
            self._edgecolors2d = np.empty((0, 4))
            idxs = []

        if self._codes3d is not None:
            codes = [self._codes3d[idx] for idx in idxs]
            PolyCollection.set_verts_and_codes(self, segments_2d, codes)
        else:
            PolyCollection.set_verts(self, segments_2d, self._closed)

        if len(self._edgecolor3d) != len(cface):
            self._edgecolors2d = self._edgecolor3d

        # Return zorder value
        if self._sort_zpos is not None:
            zvec = np.array([[0], [0], [self._sort_zpos], [1]])
            ztrans = proj3d._proj_transform_vec(zvec, self.axes.M)
            return ztrans[2][0]
        elif tzs.size > 0:
            # FIXME: Some results still don't look quite right.
            #        In particular, examine contourf3d_demo2.py
            #        with az = -54 and elev = -45.
            return np.min(tzs)
        else:
            return np.nan

    def set_facecolor(self, colors):
        # docstring inherited
        super().set_facecolor(colors)
        self._facecolor3d = PolyCollection.get_facecolor(self)

    def set_edgecolor(self, colors):
        # docstring inherited
        super().set_edgecolor(colors)
        self._edgecolor3d = PolyCollection.get_edgecolor(self)

    def set_alpha(self, alpha):
        # docstring inherited
        artist.Artist.set_alpha(self, alpha)
        try:
            self._facecolor3d = mcolors.to_rgba_array(
                self._facecolor3d, self._alpha)
        except (AttributeError, TypeError, IndexError):
            pass
        try:
            self._edgecolors = mcolors.to_rgba_array(
                self._edgecolor3d, self._alpha)
        except (AttributeError, TypeError, IndexError):
            pass
        self.stale = True

    def get_facecolor(self):
        # docstring inherited
        # self._facecolors2d is not initialized until do_3d_projection
        if not hasattr(self, '_facecolors2d'):
            self.axes.M = self.axes.get_proj()
            self.do_3d_projection()
        return np.asarray(self._facecolors2d)

    def get_edgecolor(self):
        # docstring inherited
        # self._edgecolors2d is not initialized until do_3d_projection
        if not hasattr(self, '_edgecolors2d'):
            self.axes.M = self.axes.get_proj()
            self.do_3d_projection()
        return np.asarray(self._edgecolors2d)


class Bar3DCollection(Poly3DCollection):
    """
    Bars (rectangular prisms) with constant square cross section, bases located
    on z-plane at *z0*, arranged in a regular grid at *x*, *y* locations and
    with height *z - z0*.
    """

    _n_faces = 6

    def __init__(self, x, y, z, dxy='0.8', z0=0, shade=True, lightsource=None,
                 cmap=None, **kws):
        #
        x, y, z, z0 = np.ma.atleast_1d(x, y, z, z0)
        assert x.shape == y.shape == z.shape

        # array for bar positions, height (x, y, z)
        self._xyz = np.empty((3, *x.shape))
        for i, p in enumerate((x, y, z)):
            if p is not None:
                self._xyz[i] = p

        # bar width and breadth
        self.dxy = dxy
        self.dx, self.dy = self._resolve_dx_dy(dxy)

        if z0 is not None:
            self.z0 = float(z0)

        # Shade faces by angle to light source
        self._original_alpha = kws.pop('alpha', 1)
        self._shade = bool(shade)
        if lightsource is None:
            # chosen for backwards-compatibility
            lightsource = CLASSIC_LIGHTSOURCE
        else:
            assert isinstance(lightsource, LightSource)
        self._lightsource = lightsource

        COLOR_KWS = {'color', 'facecolor', 'facecolors'}
        if not (no_cmap := (cmap is None)) and (ckw := COLOR_KWS.intersection(kws)):
            warnings.warn(f'Ignoring cmap since {ckw!r} provided.')
            kws.pop('cmap', None)

        # init Poly3DCollection
        #                               rectangle side panel vertices
        Poly3DCollection.__init__(self, self._compute_verts(), **kws)

        if not no_cmap:
            self.set_array(self.z.ravel())

    def _resolve_dx_dy(self, dxy):

        d = list(cbook.duplicate_if_scalar(dxy))

        for i, xy in enumerate(self.xy):
            # if dxy a number -> use it directly else if str,
            # scale dxy to data step.
            # get x/y step along axis -1/-2 (x/y considered constant along axis
            # -2/-1)
            data_step = _get_data_step(xy, -i - 1) if isinstance(d[i], str) else 1
            d[i] = float(d[i]) * data_step

        dx, dy = d
        assert (dx != 0)
        assert (dy != 0)

        return dx, dy

    @property
    def x(self):
        return self._xyz[0]

    @x.setter
    def x(self, x):
        self.set_data(x=x)

    @property
    def y(self):
        return self._xyz[1]

    @y.setter
    def y(self, y):
        self.set_data(y=y)

    @property
    def xy(self):
        return self._xyz[:2]

    @property
    def z(self):
        return self._xyz[2]

    def set_z(self, z, z0=None, clim=None):
        self.set_data(z=z, z0=z0, clim=clim)

    def set_z0(self, z0):
        self.z0 = float(z0)
        super().set_verts(self._compute_verts())

    def set_data(self, x=None, y=None, z=None, z0=None, clim=None):
        # self._xyz = np.atleast_3d(xyz)
        assert not all(is_none(x, y, z, z0))

        if (x is not None) or (y is not None):
            self._resolve_dx_dy(self.dxy)

        for i, p in enumerate((x, y, z)):
            if p is not None:
                self._xyz[i] = p

        if z0 is not None:
            self.z0 = float(z0)

        # compute points
        super().set_verts(self._compute_verts())
        self.set_array(z := self.z.ravel())

        if clim is None or clim is True:
            clim = (z.min(), z.max())

        if clim is not False:
            self.set_clim(*clim)

        if not self.axes:
            return

        if self.axes.M is not None:
            self.do_3d_projection()

    def _compute_verts(self):

        x, y = self.xy
        z = np.full(x.shape, self.z0)

        # indexed by [bar, face, vertex, axis]
        xyz = np.expand_dims(np.moveaxis([x, y, z], 0, -1), (-2, -3))
        dxyz = np.empty_like(xyz)
        dxyz[..., :2] = np.array([[[self.dx]], [[self.dy]]]).T
        dxyz[..., 2] = np.array([[self.z - self.z0]]).T
        polys = xyz + dxyz * CUBOID[None, :]  # (n, 6, 4, 3)

        # collapse the first two axes
        return polys.reshape((-1, 4, 3))  # *polys.shape[-2:]

    def do_3d_projection(self):
        """
        Perform the 3D projection for this object.
        """
        if self._A is not None:
            # force update of color mapping because we re-order them
            # below.  If we do not do this here, the 2D draw will call
            # this, but we will never port the color mapped values back
            # to the 3D versions.
            #
            # We hold the 3D versions in a fixed order (the order the user
            # passed in) and sort the 2D version by view depth.
            self.update_scalarmappable()
            if self._face_is_mapped:
                self._facecolor3d = self._facecolors
            if self._edge_is_mapped:
                self._edgecolor3d = self._edgecolors

        txs, tys, tzs = proj3d._proj_transform_vec(self._vec, self.axes.M)
        xyzlist = [(txs[sl], tys[sl], tzs[sl]) for sl in self._segslices]

        # get panel facecolors
        cface, cedge = self._compute_colors(xyzlist, self._lightsource)

        if xyzlist:
            zorder = self._compute_zorder()
            occluded = np.isnan(zorder)

            z_segments_2d = sorted(
                ((zo, np.column_stack([xs, ys]), fc, ec, idx)
                 for idx, (ok, zo, (xs, ys, _), fc, ec)
                 in enumerate(zip(~occluded, zorder, xyzlist, cface, cedge))
                 if ok),
                key=lambda x: x[0], reverse=True)

            _, segments_2d, self._facecolors2d, self._edgecolors2d, idxs = \
                zip(*z_segments_2d)
        else:
            segments_2d = []
            self._facecolors2d = np.empty((0, 4))
            self._edgecolors2d = np.empty((0, 4))
            idxs = []

        if self._codes3d is None:
            PolyCollection.set_verts(self, segments_2d, self._closed)
        else:
            codes = [self._codes3d[idx] for idx in idxs]
            PolyCollection.set_verts_and_codes(self, segments_2d, codes)

        if len(self._edgecolor3d) != len(cface):
            self._edgecolors2d = self._edgecolor3d

        # Return zorder value
        if self._sort_zpos is not None:
            zvec = np.array([[0], [0], [self._sort_zpos], [1]])
            ztrans = proj3d._proj_transform_vec(zvec, self.axes.M)
            return ztrans[2][0]

        return np.min(tzs) if tzs.size > 0 else np.nan

    def _compute_colors(self, xyzlist, lightsource):
        # This extra fuss is to re-order face / edge colors
        cface = self._facecolor3d
        cedge = self._edgecolor3d
        n, nc = len(xyzlist), len(cface)

        if (nc == 1) or (nc * self._n_faces == n):
            cface = cface.repeat(n // nc, axis=0)
            if self._shade:
                verts = self._compute_verts()
                normals = _generate_normals(verts)
                cface = _shade_colors(cface, normals, lightsource)

            if self._original_alpha is not None:
                cface[:, -1] = self._original_alpha

        if len(cface) != n:
            raise ValueError
            # cface = cface.repeat(n, axis=0)

        if len(cedge) != n:
            cedge = cface if len(cedge) == 0 else cedge.repeat(n, axis=0)

        return cface, cedge

    def _compute_zorder(self):
        # sort by depth (furthest drawn first)
        zorder = camera_distance(self.axes, *self.xy)
        zorder = (zorder - zorder.min()) / (zorder.ptp() or 1)
        zorder = zorder.ravel() * len(zorder)
        face_zorder = get_prism_face_zorder(self.axes,
                                            self._original_alpha == 1,
                                            self._n_faces - 2)
        return (zorder[..., None] + face_zorder).ravel()


class HexBar3DCollection(Bar3DCollection):
    """
    Hexagonal prisms with uniform cross section, bases located on z-plane at *z0*,
    aranged in a regular grid at *x*, *y* locations and height *z - z0*.
    """
    _n_faces = 8

    def _compute_verts(self):

        # scale the base hexagon
        hexagon = np.array([self.dx, self.dy * np.sqrt(3)]).T * HEXAGON
        xy_pairs = np.moveaxis([hexagon, np.roll(hexagon, -1, 0)], 0, 1)
        xy_sides = xy_pairs[np.newaxis] + self.xy[:, None, None].T  # (n,6,2,2)

        # sides (rectangle faces)
        # Array of vertices of the faces composing the prism moving counter
        # clockwise when looking from above starting at west (-x) facing panel.
        # Vertex sequence is counter-clockwise when viewed from outside.
        # shape:     (n, [...], 6,    4,      3)
        # indexed by [bars...,  face, vertex, axis]
        data_shape = np.shape(self.z)
        shape = (*data_shape, 6, 2, 1)
        z0 = np.full(shape, self.z0)
        z1 = self.z0 + (self.z * np.ones(shape[::-1])).T
        sides = np.concatenate(
            [np.concatenate([xy_sides, z0], -1),
             np.concatenate([xy_sides, z1], -1)[..., ::-1, :]],
            axis=-2)  # (n, [...], 6, 4, 3)

        # endcaps (hexagons) # (n, [...], 6, 3)
        xy_ends = (self.xy[..., None] + hexagon.T[:, None])
        z0 = self.z0 * np.ones((1, *data_shape, 6))
        z1 = z0 + self.z[None, ..., None]
        base = np.moveaxis(np.vstack([xy_ends, z0]), 0, -1)
        top = np.moveaxis(np.vstack([xy_ends, z1]), 0, -1)

        # get list of arrays of polygon vertices
        verts = []
        for s, b, t in zip(sides, base, top):
            verts.extend([*s, b, t])

        return verts


def poly_collection_2d_to_3d(col, zs=0, zdir='z'):
    """
    Convert a `.PolyCollection` into a `.Poly3DCollection` object.

    Parameters
    ----------
    zs : float or array of floats
        The location or locations to place the polygons in the collection along
        the *zdir* axis. Default: 0.
    zdir : {'x', 'y', 'z'}
        The axis in which to place the patches. Default: 'z'.
        See `.get_dir_vector` for a description of the values.
    """
    segments_3d, codes = _paths_to_3d_segments_with_codes(
        col.get_paths(), zs, zdir)
    col.__class__ = Poly3DCollection
    col.set_verts_and_codes(segments_3d, codes)
    col.set_3d_properties()


def juggle_axes(xs, ys, zs, zdir):
    """
    Reorder coordinates so that 2D *xs*, *ys* can be plotted in the plane
    orthogonal to *zdir*. *zdir* is normally 'x', 'y' or 'z'. However, if
    *zdir* starts with a '-' it is interpreted as a compensation for
    `rotate_axes`.
    """
    if zdir == 'x':
        return zs, xs, ys
    elif zdir == 'y':
        return xs, zs, ys
    elif zdir[0] == '-':
        return rotate_axes(xs, ys, zs, zdir)
    else:
        return xs, ys, zs


def rotate_axes(xs, ys, zs, zdir):
    """
    Reorder coordinates so that the axes are rotated with *zdir* along
    the original z axis. Prepending the axis with a '-' does the
    inverse transform, so *zdir* can be 'x', '-x', 'y', '-y', 'z' or '-z'.
    """
    if zdir in ('x', '-y'):
        return ys, zs, xs
    elif zdir in ('-x', 'y'):
        return zs, xs, ys
    else:
        return xs, ys, zs


def _zalpha(colors, zs):
    """Modify the alphas of the color list according to depth."""
    # FIXME: This only works well if the points for *zs* are well-spaced
    #        in all three dimensions. Otherwise, at certain orientations,
    #        the min and max zs are very close together.
    #        Should really normalize against the viewing depth.
    if len(colors) == 0 or len(zs) == 0:
        return np.zeros((0, 4))
    norm = Normalize(min(zs), max(zs))
    sats = 1 - norm(zs) * 0.7
    rgba = np.broadcast_to(mcolors.to_rgba_array(colors), (len(zs), 4))
    return np.column_stack([rgba[:, :3], rgba[:, 3] * sats])


def _generate_normals(polygons):
    """
    Compute the normals of a list of polygons, one normal per polygon.

    Normals point towards the viewer for a face with its vertices in
    counterclockwise order, following the right hand rule.

    Uses three points equally spaced around the polygon. This method assumes
    that the points are in a plane. Otherwise, more than one shade is required,
    which is not supported.

    Parameters
    ----------
    polygons : list of (M_i, 3) array-like, or (..., M, 3) array-like
        A sequence of polygons to compute normals for, which can have
        varying numbers of vertices. If the polygons all have the same
        number of vertices and array is passed, then the operation will
        be vectorized.

    Returns
    -------
    normals : (..., 3) array
        A normal vector estimated for the polygon.
    """
    if isinstance(polygons, np.ndarray):
        # optimization: polygons all have the same number of points, so can
        # vectorize
        n = polygons.shape[-2]
        i1, i2, i3 = 0, n // 3, 2 * n // 3
        v1 = polygons[..., i1, :] - polygons[..., i2, :]
        v2 = polygons[..., i2, :] - polygons[..., i3, :]
    else:
        # The subtraction doesn't vectorize because polygons is jagged.
        v1 = np.empty((len(polygons), 3))
        v2 = np.empty((len(polygons), 3))
        for poly_i, ps in enumerate(polygons):
            n = len(ps)
            i1, i2, i3 = 0, n // 3, 2 * n // 3
            v1[poly_i, :] = ps[i1, :] - ps[i2, :]
            v2[poly_i, :] = ps[i2, :] - ps[i3, :]
    return np.cross(v1, v2)


def _shade_colors(color, normals, lightsource=None):
    """
    Shade *color* using normal vectors given by *normals*,
    assuming a *lightsource* (using default position if not given).
    *color* can also be an array of the same length as *normals*.
    """
    if lightsource is None:
        # chosen for backwards-compatibility
        lightsource = mcolors.LightSource(azdeg=225, altdeg=19.4712)

    with np.errstate(invalid="ignore"):
        shade = ((normals / np.linalg.norm(normals, axis=1, keepdims=True))
                 @ lightsource.direction)
    mask = ~np.isnan(shade)

    if mask.any():
        # convert dot product to allowed shading fractions
        in_norm = mcolors.Normalize(-1, 1)
        out_norm = mcolors.Normalize(0.3, 1).inverse

        def norm(x):
            return out_norm(in_norm(x))

        shade[~mask] = 0

        color = mcolors.to_rgba_array(color)
        # shape of color should be (M, 4) (where M is number of faces)
        # shape of shade should be (M,)
        # colors should have final shape of (M, 4)
        alpha = color[:, 3]
        colors = norm(shade)[:, np.newaxis] * color
        colors[:, 3] = alpha
    else:
        colors = np.asanyarray(color).copy()

    return colors


def camera_distance(ax, x, y, z=None):
    z = np.zeros_like(x) if z is None else z
    return np.sqrt(np.square(
        # location of points
        [x, y, z] -
        # camera position in xyz
        np.array(sph2cart(*_camera_position(ax)), ndmin=x.ndim + 1).T
    ).sum(0))


def sph2cart(r, theta, phi):
    """Spherical to cartesian transform."""
    r_sinθ = r * np.sin(theta)
    return (r_sinθ * np.cos(phi),
            r_sinθ * np.sin(phi),
            r * np.cos(theta))


def _camera_position(ax):
    """
    Returns the camera position for 3D axes in spherical coordinates.
    """
    r = np.square(np.max([ax.get_xlim(),
                          ax.get_ylim()], 1)).sum()
    theta, phi = np.radians((90 - ax.elev, ax.azim))
    return r, theta, phi


def _get_data_step(x, axis=0):
    # for data arange in a regular grid, get the size of the data step by
    # looking for the first non-zero step along an axis.
    # If axis is singular, return 1

    # deal with singular dimension (this ignores axis param)
    if x.ndim == 1:
        if d := next(filter(None, map(np.diff, cbook.pairwise(x))), None):
            return d

    if x.shape[axis % x.ndim] == 1:
        return 1

    key = [0] * x.ndim
    key[axis] = np.s_[:2]
    return np.diff(x[tuple(key)]).item()


def get_prism_face_zorder(ax, mask_occluded=True, nfaces=4):
    # compute panel sequence based on camera position

    # these index positions are determined by the order of the faces returned
    # by `_compute_verts`
    base, top = nfaces, nfaces + 1
    if ax.elev < 0:
        base, top = top, base

    # this is to figure out which of the vertical faces to draw first
    angle_step = 360 / nfaces
    zero = -angle_step / 2
    flip = (np.abs(ax.elev) % 180 > 90)
    sector = (((ax.azim - zero + 180 * flip) % 360) / angle_step) % nfaces

    # get indices for panels in plot order
    first = int(sector)
    second = (first + 1) % nfaces
    third = (first + nfaces - 1) % nfaces
    if (sector - first) < 0.5:
        second, third = third, second

    sequence = [base, first, second, third]
    sequence = [*sequence, *np.setdiff1d(np.arange(nfaces), sequence), top]

    # reverse the panel sequence if elevation has flipped the axes by 180 multiple
    if np.abs(ax.elev) % 360 > 180:
        sequence = sequence[::-1]

    # normalize zorder to < 1
    zorder = np.argsort(sequence) / len(sequence)

    if mask_occluded:
        #  we don't need to draw back panels since they are behind others
        zorder[zorder < 0.5] = np.nan

    # This order is determined by the ordering of `CUBOID` and `HEXAGON` globals
    # names = {4: ['+x', '+y', '-x', '-y', '-z', '+z'],
    #          6: ['W', 'SW', 'SE', 'E', 'NE', 'NW', 'BASE', 'TOP']}[nfaces]
    # print('',
    #       f'Panel draw sequence ({ax.azim = :}, {ax.elev = :}):',
    #       f'{sector = :}',
    #       f'{sequence = :}',
    #       f'names = {list(np.take(names, sequence))}',
    #       f'{zorder = :}',
    #       f'zorder = {pformat(dict(zip(*cosort(zorder, names)[::-1])))}',
    #       sep='\n')

    return zorder
