# art3d.py, original mplot3d version by John Porter
# Parts rewritten by Reinier Heeres <reinier@heeres.eu>
# Minor additions by Ben Axelrod <baxelrod@coroware.com>

"""
Module containing 3D artist code and functions to convert 2D
artists into 3D versions which can be added to an Axes3D.
"""

import math

import numpy as np

from matplotlib import (
    artist, cbook, colors as mcolors, lines, text as mtext, path as mpath)
from matplotlib.collections import (
    Collection, LineCollection, PolyCollection, PatchCollection,
    PathCollection)
from matplotlib.colors import Normalize
from matplotlib.patches import Patch
from . import proj3d


def norm_angle(a):
    """Return the given angle normalized to -180 < *a* <= 180 degrees."""
    a = (a + 360) % 360
    if a > 180:
        a = a - 360
    return a


def norm_text_angle(a):
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
        - 'y': euqivalent to (0, 1, 0)
        - 'z': equivalent to (0, 0, 1)
        - *None*: euqivalent to (0, 0, 0)
        - an iterable (x, y, z) is returned unchanged.

    Returns
    -------
    x, y, z : array-like
        The direction vector. This is either a numpy.array or *zdir* itself if
        *zdir* is already a length-3 iterable.

    """
    if zdir == 'x':
        return np.array((1, 0, 0))
    elif zdir == 'y':
        return np.array((0, 1, 0))
    elif zdir == 'z':
        return np.array((0, 0, 1))
    elif zdir is None:
        return np.array((0, 0, 0))
    elif cbook.iterable(zdir) and len(zdir) == 3:
        return zdir
    else:
        raise ValueError("'x', 'y', 'z', None or vector of length 3 expected")


def _array_split(arr, indices_or_sections, remove_empty=False):
    """Fix numpy.split to preserve the dimension of empty subarrays."""
    arr_chunks = np.split(arr, indices_or_sections)

    if arr_chunks[-1].size == 0:
        if not remove_empty:
            # Preserve the 2D dimensionality of the last chunk that can be
            # empty (numpy <=1.10 replaces empty chunks by a 1D empty array)

            # TODO: The following can be removed when
            #       support for numpy <=1.10 is dropped.
            arr_chunks[-1] = np.empty(shape=(0, arr.shape[1]), dtype=arr.dtype)
        else:
            del arr_chunks[-1]

    return arr_chunks


class Text3D(mtext.Text):
    """
    Text object with 3D position and direction.

    Parameters
    ----------
    x, y, z
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

    def set_3d_properties(self, z=0, zdir='z'):
        x, y = self.get_position()
        self._position3d = np.array((x, y, z))
        self._dir_vec = get_dir_vector(zdir)
        self.stale = True

    @artist.allow_rasterization
    def draw(self, renderer):
        proj = proj3d.proj_trans_points(
            [self._position3d, self._position3d + self._dir_vec], renderer.M)
        dx = proj[0][1] - proj[0][0]
        dy = proj[1][1] - proj[1][0]
        if dx==0. and dy==0.:
            # atan2 raises ValueError: math domain error on 0,0
            angle = 0.
        else:
            angle = math.degrees(math.atan2(dy, dx))
        self.set_position((proj[0][0], proj[1][0]))
        self.set_rotation(norm_text_angle(angle))
        mtext.Text.draw(self, renderer)
        self.stale = False


def text_2d_to_3d(obj, z=0, zdir='z'):
    """Convert a Text to a Text3D object."""
    obj.__class__ = Text3D
    obj.set_3d_properties(z, zdir)


class Line3D(lines.Line2D):
    """
    3D line object.
    """

    def __init__(self, xs, ys, zs, *args, **kwargs):
        """
        Keyword arguments are passed onto :func:`~matplotlib.lines.Line2D`.
        """
        lines.Line2D.__init__(self, [], [], *args, **kwargs)
        self._verts3d = xs, ys, zs

    def set_3d_properties(self, zs=0, zdir='z'):
        xs = self.get_xdata()
        ys = self.get_ydata()

        zs = np.broadcast_to(zs, len(xs))
        self._verts3d = juggle_axes(xs, ys, zs, zdir)
        self.stale = True

    @artist.allow_rasterization
    def draw(self, renderer):
        xs3d, ys3d, zs3d = self._verts3d
        xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
        self.set_data(xs, ys)
        lines.Line2D.draw(self, renderer)
        self.stale = False


def line_2d_to_3d(line, zs=0, zdir='z'):
    """Convert a 2D line to 3D."""

    line.__class__ = Line3D
    line.set_3d_properties(zs, zdir)


def path_to_3d_segment(path, zs=0, zdir='z'):
    """Convert a path to a 3D segment.

    .. versionchanged :: 3.1
       Return type changed from a list to a numpy.array
    """
    zs = np.broadcast_to(zs, len(path))

    pathsegs = path.iter_segments(simplify=False, curves=False)
    if len(path):
        xs, ys = zip(*((x, y) for (x, y), code in pathsegs))
    else:
        xs, ys = [], []

    seg3d = juggle_axes(xs, ys, zs, zdir)
    return np.array(seg3d).T


def paths_to_3d_segments(paths, zs=0, zdir='z'):
    """Convert paths from a collection object to 3D segments.

    .. versionchanged :: 3.1
       Return type changed from a list to a numpy.array
    """

    zs = np.broadcast_to(zs, len(paths))

    segs = [path_to_3d_segment(path, pathz, zdir)
            for path, pathz in zip(paths, zs)]
    return segs


def path_to_3d_segment_with_codes(path, zs=0, zdir='z'):
    """Convert a path to a 3D segment with path codes.

    .. versionchanged :: 3.1
       Return type changed from a list to a numpy.array
    """
    zs = np.broadcast_to(zs, len(path))

    pathsegs = path.iter_segments(simplify=False, curves=False)
    codes = np.empty(len(path))
    xs, ys, codes = zip(*((x, y, code) for (x, y), code in pathsegs))
    seg3d = juggle_axes(xs, ys, zs, zdir)
    return np.array(seg3d).T, codes


def paths_to_3d_segments_with_codes(paths, zs=0, zdir='z'):
    """
    Convert paths from a collection object to 3D segments with path codes.

    .. versionchanged :: 3.1
       Return type changed from a list to a numpy.array
    """

    zs = np.broadcast_to(zs, len(paths))

    path_generator = (path_to_3d_segment_with_codes(path, pathz, zdir)
                      for path, pathz in zip(paths, zs))
    if len(paths) and len(zs):
        segments, codes_list = zip(*path_generator)

        return np.asarray(segments), np.asarray(codes_list)
    else:
        return np.empty((3, 0), dtype='float64'), np.array([], dtype='uint8')


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
        self._segments3d = []
        if len(segments) > 0:
            self._seg_sizes = np.array([len(c) for c in segments])
            # Store the points in a single array for easier projection
            n_segments = np.sum(self._seg_sizes)

            self._segments3d_data = np.empty((n_segments, 4))
            self._segments3d_data[:, :3] = np.vstack(segments)
            self._segments3d_data[:, 3] = 1

            # For convenience, store a view of the array in the original shape
            self._segments3d = _array_split(self._segments3d_data[:, :3],
                                            np.cumsum(self._seg_sizes))

        LineCollection.set_segments(self, [])

    def do_3d_projection(self, renderer):
        """
        Project the points according to renderer matrix.
        """
        if len(self._segments3d) == 0:
            return 1e9
        xys = proj3d.proj_transform_vec(self._segments3d_data.T, renderer.M)
        segments_2d = _array_split(xys[:2].T,
                                   np.cumsum(self._seg_sizes))
        LineCollection.set_segments(self, segments_2d)
        minz = np.min(xys[2])
        return minz

    @artist.allow_rasterization
    def draw(self, renderer, project=False):
        if project:
            self.do_3d_projection(renderer)
        LineCollection.draw(self, renderer)


def line_collection_2d_to_3d(col, zs=0, zdir='z'):
    """Convert a LineCollection to a Line3DCollection object."""
    segments3d = paths_to_3d_segments(col.get_paths(), zs, zdir)
    col.__class__ = Line3DCollection
    col.set_segments(segments3d)


class Patch3D(Patch):
    """
    3D patch object.
    """

    def __init__(self, *args, zs=(), zdir='z', **kwargs):
        Patch.__init__(self, *args, **kwargs)
        self.set_3d_properties(zs, zdir)

    def set_3d_properties(self, verts, zs=0, zdir='z'):
        zs = np.broadcast_to(zs, len(verts))
        xs, ys = verts.T
        self._segment3d = juggle_axes(xs, ys, zs, zdir)
        self._facecolor3d = Patch.get_facecolor(self)

    def get_path(self):
        return self._path2d

    def get_facecolor(self):
        return self._facecolor2d

    def do_3d_projection(self, renderer):
        # pad ones
        if self._segment3d:
            segments_3d_len = len(self._segment3d[0])
        else:
            segments_3d_len = 0
        s = np.vstack(self._segment3d + (np.ones(segments_3d_len),))
        vxyzis = proj3d.proj_transform_vec_clip(s, renderer.M)
        self._path2d = mpath.Path(vxyzis[0:2].T)
        # FIXME: coloring
        self._facecolor2d = self._facecolor3d
        return min(vxyzis[2])


class PathPatch3D(Patch3D):
    """
    3D PathPatch object.
    """

    def __init__(self, path, *, zs=(), zdir='z', **kwargs):
        Patch.__init__(self, **kwargs)
        self.set_3d_properties(path, zs, zdir)

    def set_3d_properties(self, path, zs=0, zdir='z'):
        Patch3D.set_3d_properties(self, path.vertices, zs=zs, zdir=zdir)
        self._code3d = path.codes

    def do_3d_projection(self, renderer):
        # pad ones
        if self._segment3d:
            segments_3d_len = len(self._segment3d[0])
        else:
            segments_3d_len = 0
        s = np.vstack(self._segment3d + (np.ones(segments_3d_len),))
        vxyzis = proj3d.proj_transform_vec_clip(s, renderer.M)
        self._path2d = mpath.Path(vxyzis[0:2].T, self._code3d)
        # FIXME: coloring
        self._facecolor2d = self._facecolor3d
        return min(vxyzis[2])


def get_patch_verts(patch):
    """Return a list of vertices for the path of a patch."""
    trans = patch.get_patch_transform()
    path =  patch.get_path()
    polygons = path.to_polygons(trans)
    if len(polygons):
        return polygons[0]
    else:
        return []


def patch_2d_to_3d(patch, z=0, zdir='z'):
    """Convert a Patch to a Patch3D object."""
    verts = get_patch_verts(patch)
    patch.__class__ = Patch3D
    patch.set_3d_properties(verts, z, zdir)


def pathpatch_2d_to_3d(pathpatch, z=0, zdir='z'):
    """Convert a PathPatch to a PathPatch3D object."""
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

        Also, the keyword argument "depthshade" is available to
        indicate whether or not to shade the patches in order to
        give the appearance of depth (default is *True*).
        This is typically desired in scatter plots.
        """
        self._depthshade = depthshade
        super().__init__(*args, **kwargs)
        self.set_3d_properties(zs, zdir)

    def set_sort_zpos(self, val):
        """Set the position to use for z-sorting."""
        self._sort_zpos = val
        self.stale = True

    def set_3d_properties(self, zs, zdir):
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
        self._facecolor3d = self.get_facecolor()
        self._edgecolor3d = self.get_edgecolor()
        self.stale = True

    def do_3d_projection(self, renderer):
        # pad ones
        s = np.vstack(self._offsets3d, np.ones(self._offsets3d.shape[1]))
        vxyzis = proj3d.proj_transform_vec_clip(s, renderer.M)
        vzs = vxyzis[2]

        fcs = (zalpha(self._facecolor3d, vzs) if self._depthshade else
               self._facecolor3d)
        fcs = mcolors.to_rgba_array(fcs, self._alpha)
        self.set_facecolors(fcs)

        ecs = (zalpha(self._edgecolor3d, vzs) if self._depthshade else
               self._edgecolor3d)
        ecs = mcolors.to_rgba_array(ecs, self._alpha)
        self.set_edgecolors(ecs)
        PatchCollection.set_offsets(self, vxyzis[0:2].T)

        if vzs.size > 0:
            return min(vzs)
        else:
            return np.nan


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

        Also, the keyword argument "depthshade" is available to
        indicate whether or not to shade the patches in order to
        give the appearance of depth (default is *True*).
        This is typically desired in scatter plots.
        """
        self._depthshade = depthshade
        super().__init__(*args, **kwargs)
        self.set_3d_properties(zs, zdir)

    def set_sort_zpos(self, val):
        """Set the position to use for z-sorting."""
        self._sort_zpos = val
        self.stale = True

    def set_3d_properties(self, zs, zdir):
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
        self._facecolor3d = self.get_facecolor()
        self._edgecolor3d = self.get_edgecolor()
        self.stale = True

    def do_3d_projection(self, renderer):
        xs, ys, zs = self._offsets3d
        vxyzis = proj3d.proj_transform_clip(xs, ys, zs, renderer.M)
        vzs = vxyzis[2]

        fcs = (zalpha(self._facecolor3d, vzs) if self._depthshade else
               self._facecolor3d)
        fcs = mcolors.to_rgba_array(fcs, self._alpha)
        self.set_facecolors(fcs)

        ecs = (zalpha(self._edgecolor3d, vzs) if self._depthshade else
               self._edgecolor3d)
        ecs = mcolors.to_rgba_array(ecs, self._alpha)
        self.set_edgecolors(ecs)
        PathCollection.set_offsets(self, vxyzis[0:2].T)

        if vzs.size > 0:
            return min(vzs)
        else:
            return np.nan


def patch_collection_2d_to_3d(col, zs=0, zdir='z', depthshade=True):
    """
    Convert a :class:`~matplotlib.collections.PatchCollection` into a
    :class:`Patch3DCollection` object
    (or a :class:`~matplotlib.collections.PathCollection` into a
    :class:`Path3DCollection` object).

    Parameters
    ----------
    za
        The location or locations to place the patches in the collection along
        the *zdir* axis. Default: 0.
    zdir
        The axis in which to place the patches. Default: "z".
    depthshade
        Whether to shade the patches to give a sense of depth. Default: *True*.

    """
    if isinstance(col, PathCollection):
        col.__class__ = Path3DCollection
    elif isinstance(col, PatchCollection):
        col.__class__ = Patch3DCollection
    col._depthshade = depthshade
    col.set_3d_properties(zs, zdir)


class Poly3DCollection(PolyCollection):
    """
    A collection of 3D polygons.
    """

    def __init__(self, verts, *args, zsort=True, **kwargs):
        """
        Create a Poly3DCollection.

        *verts* should contain 3D coordinates.

        Keyword arguments:
        zsort, see set_zsort for options.

        Note that this class does a bit of magic with the _facecolors
        and _edgecolors properties.
        """
        super().__init__(verts, *args, **kwargs)
        self.set_zsort(zsort)
        self._codes3d = None

    _zsort_functions = {
        'average': np.average,
        'min': np.min,
        'max': np.max,
    }

    def set_zsort(self, zsort):
        """
        Sets the calculation method for the z-order.

        Parameters
        ----------
        zsort : bool or {'average', 'min', 'max'}
            For 'average', 'min', 'max' the z-order is determined by applying
            the function to the z-coordinates of the vertices in the viewer's
            coordinate system. *True* is equivalent to 'average'.
        """

        if zsort is True:
            zsort = 'average'

        if zsort is not False:
            if zsort in self._zsort_functions:
                zsortfunc = self._zsort_functions[zsort]
            else:
                return False
        else:
            zsortfunc = None

        self._zsort = zsort
        self._sort_zpos = None
        self._zsortfunc = zsortfunc
        self.stale = True

    def get_vector(self, segments3d):
        """Optimize points for projection"""

        self._seg_sizes = np.array([len(c) for c in segments3d])
        self._vec = []
        if len(segments3d) > 0:
            # Store the points in a single array for easier projection
            n_segments = np.sum(self._seg_sizes)
            # Put all segments in a big array
            _vec = np.vstack(segments3d)
            # Add a fourth dimension
            self._vec = np.hstack([_vec, np.ones((n_segments, 1))]).T

    def set_verts(self, verts, closed=True):
        """Set 3D vertices."""
        self.get_vector(verts)
        # 2D verts will be updated at draw time
        PolyCollection.set_verts(self, [], False)
        self._closed = closed

    def set_verts_and_codes(self, verts, codes):
        """Sets 3D vertices with path codes."""
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
        self.set_zsort(True)
        self._facecolors3d = PolyCollection.get_facecolor(self)
        self._edgecolors3d = PolyCollection.get_edgecolor(self)
        self._alpha3d = PolyCollection.get_alpha(self)
        self.stale = True

    def set_sort_zpos(self, val):
        """Set the position to use for z-sorting."""
        self._sort_zpos = val
        self.stale = True

    def do_3d_projection(self, renderer):
        """
        Perform the 3D projection for this object.
        """
        # FIXME: This may no longer be needed?
        if self._A is not None:
            self.update_scalarmappable()
            self._facecolors3d = self._facecolors

        xys = proj3d.proj_transform_vec(self._vec, renderer.M).T

        xyzlist = _array_split(xys[:, :3],
                               np.cumsum(self._seg_sizes),
                               remove_empty=True)

        # This extra fuss is to re-order face / edge colors
        cface = self._facecolors3d
        cedge = self._edgecolors3d
        if len(cface) != len(xyzlist):
            cface = cface.repeat(len(xyzlist), axis=0)
        if len(cedge) != len(xyzlist):
            if len(cedge) == 0:
                cedge = cface
            else:
                cedge = cedge.repeat(len(xyzlist), axis=0)

        # if required sort by depth (furthest drawn first)
        if self._zsort:
            z_argsort = np.argsort(
                [self._zsortfunc(xyz[:, 2]) for xyz in xyzlist])[::-1]
        else:
            raise ValueError("whoops")

        segments_2d = [xyzlist[i][:, 0:2] for i in z_argsort]
        if self._codes3d is not None:
            codes = self._codes3d[z_argsort]
            PolyCollection.set_verts_and_codes(self, segments_2d, codes)
        else:
            PolyCollection.set_verts(self, segments_2d, self._closed)

        self._facecolors2d = cface[z_argsort]
        if len(self._edgecolors3d) == len(cface):
            self._edgecolors2d = cedge[z_argsort]
        else:
            self._edgecolors2d = self._edgecolors3d

        # Return zorder value
        if self._sort_zpos is not None:
            zvec = np.array([[0], [0], [self._sort_zpos], [1]])
            ztrans = proj3d.proj_transform_vec(zvec, renderer.M)
            return ztrans[2][0]
        elif xys[:, 2].size > 0:
            # FIXME: Some results still don't look quite right.
            #        In particular, examine contourf3d_demo2.py
            #        with az = -54 and elev = -45.
            return np.min(xys[:, 2])
        else:
            return np.nan

    def set_facecolor(self, colors):
        PolyCollection.set_facecolor(self, colors)
        self._facecolors3d = PolyCollection.get_facecolor(self)

    def set_edgecolor(self, colors):
        PolyCollection.set_edgecolor(self, colors)
        self._edgecolors3d = PolyCollection.get_edgecolor(self)

    def set_alpha(self, alpha):
        """
        Set the alpha transparencies of the collection.

        Parameters
        ----------
        alpha : float or None
        """
        if alpha is not None:
            try:
                float(alpha)
            except TypeError:
                raise TypeError('alpha must be a float or None')
        artist.Artist.set_alpha(self, alpha)
        try:
            self._facecolors = mcolors.to_rgba_array(
                self._facecolors3d, self._alpha)
        except (AttributeError, TypeError, IndexError):
            pass
        try:
            self._edgecolors = mcolors.to_rgba_array(
                    self._edgecolors3d, self._alpha)
        except (AttributeError, TypeError, IndexError):
            pass
        self.stale = True

    def get_facecolor(self):
        return self._facecolors2d

    def get_edgecolor(self):
        return self._edgecolors2d


def poly_collection_2d_to_3d(col, zs=0, zdir='z'):
    """Convert a PolyCollection to a Poly3DCollection object."""
    segments_3d, codes = paths_to_3d_segments_with_codes(col.get_paths(),
                                                         zs, zdir)
    col.__class__ = Poly3DCollection
    col.set_verts_and_codes(segments_3d, codes)
    col.set_3d_properties()


def juggle_axes(xs, ys, zs, zdir):
    """
    Reorder coordinates so that 2D xs, ys can be plotted in the plane
    orthogonal to zdir. zdir is normally x, y or z. However, if zdir
    starts with a '-' it is interpreted as a compensation for rotate_axes.
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
    Reorder coordinates so that the axes are rotated with zdir along
    the original z axis. Prepending the axis with a '-' does the
    inverse transform, so zdir can be x, -x, y, -y, z or -z
    """
    if zdir == 'x':
        return ys, zs, xs
    elif zdir == '-x':
        return zs, xs, ys
    elif zdir == 'y':
        return zs, xs, ys
    elif zdir == '-y':
        return ys, zs, xs
    else:
        return xs, ys, zs


def get_colors(c, num):
    """Stretch the color argument to provide the required number *num*."""
    if not len(c):
        return np.zeros((num, 4))
    elif len(c) < num:
        return np.broadcast_to(mcolors.to_rgba_array(c), (num, 4))
    else:
        return mcolors.to_rgba_array(c)


def zalpha(colors, zs):
    """Modify the alphas of the color list according to depth."""
    # FIXME: This only works well if the points for *zs* are well-spaced
    #        in all three dimensions. Otherwise, at certain orientations,
    #        the min and max zs are very close together.
    #        Should really normalize against the viewing depth.
    colors = get_colors(colors, len(zs))
    if len(zs):
        norm = Normalize(min(zs), max(zs))
        sats = 1 - norm(zs) * 0.7
        colors = [(c[0], c[1], c[2], c[3] * s) for c, s in zip(colors, sats)]
    return colors
