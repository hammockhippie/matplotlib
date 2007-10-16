from __future__ import division
import math

import matplotlib as mpl
import numpy as npy
import matplotlib.cbook as cbook
import matplotlib.artist as artist
import matplotlib.colors as colors
import matplotlib.lines as lines
import matplotlib.transforms as transforms
import matplotlib.nxutils as nxutils
import matplotlib.mlab as mlab
import matplotlib.artist as artist
from matplotlib.path import Path

# these are not available for the object inspector until after the
# class is build so we define an initial set here for the init
# function and they will be overridden after object defn
artist.kwdocd['Patch'] = """\
          alpha: float
          animated: [True | False]
          antialiased or aa: [True | False]
          clip_box: a matplotlib.transform.Bbox instance
          clip_on: [True | False]
          edgecolor or ec: any matplotlib color
          facecolor or fc: any matplotlib color
          figure: a matplotlib.figure.Figure instance
          fill: [True | False]
          hatch: unknown
          label: any string
          linewidth or lw: float
          lod: [True | False]
          transform: a matplotlib.transform transformation instance
          visible: [True | False]
          zorder: any number
          """

class Patch(artist.Artist):
    """
    A patch is a 2D thingy with a face color and an edge color

    If any of edgecolor, facecolor, linewidth, or antialiased are
    None, they default to their rc params setting

    """
    zorder = 1
    def __str__(self):
        return str(self.__class__).split('.')[-1]

    def __init__(self,
                 edgecolor=None,
                 facecolor=None,
                 linewidth=None,
                 antialiased = None,
                 hatch = None,
                 fill=1,
                 **kwargs
                 ):
        """
        The following kwarg properties are supported
        %(Patch)s
        """
        artist.Artist.__init__(self)

        if edgecolor is None: edgecolor = mpl.rcParams['patch.edgecolor']
        if facecolor is None: facecolor = mpl.rcParams['patch.facecolor']
        if linewidth is None: linewidth = mpl.rcParams['patch.linewidth']
        if antialiased is None: antialiased = mpl.rcParams['patch.antialiased']

        self._edgecolor = edgecolor
        self._facecolor = facecolor
        self._linewidth = linewidth
        self._antialiased = antialiased
        self._hatch = hatch
        self._combined_transform = transforms.IdentityTransform()
        self.fill = fill
	
        if len(kwargs): artist.setp(self, **kwargs)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd



    def contains(self, mouseevent):
        """Test whether the mouse event occurred in the patch.

        Returns T/F, {}
        """
	# This is a general version of contains should work on any
        # patch with a path.  However, patches that have a faster
        # algebraic solution to hit-testing should override this
        # method.
	if callable(self._contains): return self._contains(self,mouseevent)

        inside = self.get_path().contains_point(
            (mouseevent.x, mouseevent.y), self.get_transform())
        return inside, {}

    def update_from(self, other):
        artist.Artist.update_from(self, other)
        self.set_edgecolor(other.get_edgecolor())
        self.set_facecolor(other.get_facecolor())
        self.set_fill(other.get_fill())
        self.set_hatch(other.get_hatch())
        self.set_linewidth(other.get_linewidth())
        self.set_transform(other.get_transform())
        self.set_figure(other.get_figure())
        self.set_alpha(other.get_alpha())

    def get_transform(self):
        return self._combined_transform

    def set_transform(self, t):
        artist.Artist.set_transform(self, t)
        self._combined_transform = self.get_patch_transform() + \
            artist.Artist.get_transform(self)

    def get_data_transform(self):
        return artist.Artist.get_transform(self)
        
    def get_patch_transform(self):
        return transforms.IdentityTransform()
    
    def get_antialiased(self):
        return self._antialiased

    def get_edgecolor(self):
        return self._edgecolor

    def get_facecolor(self):
        return self._facecolor

    def get_linewidth(self):
        return self._linewidth

    def set_antialiased(self, aa):
        """
        Set whether to use antialiased rendering

        ACCEPTS: [True | False]
        """
        self._antialiased = aa

    def set_edgecolor(self, color):
        """
        Set the patch edge color

        ACCEPTS: any matplotlib color
        """
        self._edgecolor = color

    def set_facecolor(self, color):
        """
        Set the patch face color

        ACCEPTS: any matplotlib color
        """
        self._facecolor = color

    def set_linewidth(self, w):
        """
        Set the patch linewidth in points

        ACCEPTS: float
        """
        self._linewidth = w

    def set_fill(self, b):
        """
        Set whether to fill the patch

        ACCEPTS: [True | False]
        """
        self.fill = b

    def get_fill(self):
        'return whether fill is set'
        return self.fill

    def set_hatch(self, h):
        """
        Set the hatching pattern

        hatch can be one of:
        /   - diagonal hatching
        \   - back diagonal
        |   - vertical
        -   - horizontal
        #   - crossed
        x   - crossed diagonal
        letters can be combined, in which case all the specified
        hatchings are done
        if same letter repeats, it increases the density of hatching
        in that direction

        CURRENT LIMITATIONS:
        1. Hatching is supported in the PostScript
        backend only.

        2. Hatching is done with solid black lines of width 0.
        """
        self._hatch = h

    def get_hatch(self):
        'return the current hatching pattern'
        return self._hatch


    def draw(self, renderer):
        if not self.get_visible(): return
        #renderer.open_group('patch')
        gc = renderer.new_gc()
        gc.set_foreground(self._edgecolor)
        gc.set_linewidth(self._linewidth)
        gc.set_alpha(self._alpha)
        gc.set_antialiased(self._antialiased)
        self._set_gc_clip(gc)
        gc.set_capstyle('projecting')

        if not self.fill or self._facecolor is None: rgbFace = None
        else: rgbFace = colors.colorConverter.to_rgb(self._facecolor)
        
        if self._hatch:
            gc.set_hatch(self._hatch )

        path = self.get_path()
        transform = self.get_transform()
        # MGDTODO: Use a transformed path here?
        tpath = transform.transform_path_non_affine(path)
        affine = transform.get_affine()
        
        renderer.draw_path(gc, tpath, affine, rgbFace)

        #renderer.close_group('patch')

    def get_path(self):
        """
        Return the path of this patch
        """
        raise NotImplementedError('Derived must override')


    def get_window_extent(self, renderer=None):
        return self.get_path().get_extents(self.get_transform())


    def set_lw(self, val):
        'alias for set_linewidth'
        self.set_linewidth(val)


    def set_ec(self, val):
        'alias for set_edgecolor'
        self.set_edgecolor(val)


    def set_fc(self, val):
        'alias for set_facecolor'
        self.set_facecolor(val)


    def get_aa(self):
        'alias for get_antialiased'
        return self.get_antialiased()


    def get_lw(self):
        'alias for get_linewidth'
        return self.get_linewidth()


    def get_ec(self):
        'alias for get_edgecolor'
        return self.get_edgecolor()


    def get_fc(self):
        'alias for get_facecolor'
        return self.get_facecolor()


class Shadow(Patch):
    def __str__(self):
        return "Shadow(%s)"%(str(self.patch))

    def __init__(self, patch, ox, oy, props=None, **kwargs):
        """
        Create a shadow of the patch offset by ox, oy.  props, if not None is
        a patch property update dictionary.  If None, the shadow will have
        have the same color as the face, but darkened

        kwargs are
        %(Patch)s
        """
        Patch.__init__(self)
        self.patch = patch
        self.props = props
	self.ox, self.oy = ox, oy
	self._shadow_transform = transforms.Affine2D().translate(self.ox, self.oy)
        self._update()
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def _update(self):
        self.update_from(self.patch)
        if self.props is not None:
            self.update(self.props)
        else:
            r,g,b,a = colors.colorConverter.to_rgba(self.patch.get_facecolor())
            rho = 0.3
            r = rho*r
            g = rho*g
            b = rho*b

            self.set_facecolor((r,g,b,0.5))
            self.set_edgecolor((r,g,b,0.5))
	    
    def get_path(self):
        return self.patch.get_path()

    def get_patch_transform(self):
	return self._shadow_transform
    
class Rectangle(Patch):
    """
    Draw a rectangle with lower left at xy=(x,y) with specified
    width and height

    """

    def __str__(self):
        return str(self.__class__).split('.')[-1] \
            + "(%g,%g;%gx%g)"%(self.xy[0],self.xy[1],self.width,self.height)

    def __init__(self, xy, width, height, **kwargs):
        """
        xy is an x,y tuple lower, left

        width and height are width and height of rectangle

        fill is a boolean indicating whether to fill the rectangle

        Valid kwargs are:
        %(Patch)s
        """

        Patch.__init__(self, **kwargs)

        left, right = self.convert_xunits((xy[0], xy[0] + width))
        bottom, top = self.convert_yunits((xy[1], xy[1] + height))
	self._bbox = transforms.Bbox.from_lbrt(left, bottom, right, top)
	self._rect_transform = transforms.BboxTransform(
	    transforms.Bbox.unit(), self._bbox)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def get_path(self):
        """
        Return the vertices of the rectangle
        """
	return Path.unit_rectangle()

    def get_patch_transform(self):
	return self._rect_transform

    def contains(self, mouseevent):
        x, y = self.get_transform().inverted().transform_point(
            (mouseevent.x, mouseevent.y))
        return (x >= 0.0 and x <= 1.0 and y >= 0.0 and y <= 1.0), {}
    
    def get_x(self):
        "Return the left coord of the rectangle"
        return self._bbox.xmin

    def get_y(self):
        "Return the bottom coord of the rectangle"
        return self._bbox.ymin

    def get_width(self):
        "Return the width of the  rectangle"
        return self._bbox.width

    def get_height(self):
        "Return the height of the rectangle"
        return self._bbox.height

    def set_x(self, x):
        """
        Set the left coord of the rectangle

        ACCEPTS: float
        """
        w = self._bbox.width
        self._bbox.intervalx = (x, x + w)

    def set_y(self, y):
        """
        Set the bottom coord of the rectangle

        ACCEPTS: float
        """
        h = self._bbox.height
        self._bbox.intervaly = (y, y + h)

    def set_width(self, w):
        """
        Set the width rectangle

        ACCEPTS: float
        """
        self._bbox.xmax = self._bbox.xmin + w

    def set_height(self, h):
        """
        Set the width rectangle

        ACCEPTS: float
        """
        self._bbox.ymax = self._bbox.ymin + h

    def set_bounds(self, *args):
        """
        Set the bounds of the rectangle: l,b,w,h

        ACCEPTS: (left, bottom, width, height)
        """
        if len(args)==0:
            l,b,w,h = args[0]
        else:
            l,b,w,h = args
	self._bbox.bounds = l,b,w,h


class RegularPolygon(Patch):
    """
    A regular polygon patch.
    """
    def __str__(self):
        return "Poly%d(%g,%g)"%(self.numVertices,self.xy[0],self.xy[1])

    def __init__(self, xy, numVertices, radius=5, orientation=0,
                 **kwargs):
        """
        xy is a length 2 tuple (the center)
        numVertices is the number of vertices.
        radius is the distance from the center to each of the vertices.
        orientation is in radians and rotates the polygon.

        Valid kwargs are:
        %(Patch)s
        """
        self._xy = xy
        self._orientation = orientation
        self._radius = radius
	self._path = Path.unit_regular_polygon(numVertices)
        self._poly_transform = transforms.Affine2D()
        self._update_transform()
        
        Patch.__init__(self, **kwargs)
        
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def _update_transform(self):
        self._poly_transform.clear() \
	    .scale(self.radius) \
	    .rotate(self.orientation) \
	    .translate(*self.xy)

    def _get_xy(self):
        return self._xy
    def _set_xy(self, xy):
        self._xy = xy
        self._update_transform()
    xy = property(_get_xy, _set_xy)

    def _get_orientation(self):
        return self._orientation
    def _set_orientation(self, xy):
        self._orientation = xy
        self._update_transform()
    orientation = property(_get_orientation, _set_orientation)
    
    def _get_radius(self):
        return self._radius
    def _set_radius(self, xy):
        self._radius = xy
        self._update_transform()
    radius = property(_get_radius, _set_radius)
    
    def get_path(self):
	return self._path

    def get_patch_transform(self):
        return self._poly_transform
	
class Polygon(Patch):
    """
    A general polygon patch.
    """
    def __str__(self):
        return "Poly(%g, %g)" % tuple(self._path.vertices[0])

    def __init__(self, xy, **kwargs):
        """
        xy is a numpy array with shape Nx2

        Valid kwargs are:
        %(Patch)s
        See Patch documentation for additional kwargs
        """
        Patch.__init__(self, **kwargs)
        self.xy = xy
	self._path = Path(xy, closed=True)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def get_path(self):
	return self._path

    def update(self):
        self._path = Path(self.xy, closed=True)
    
class Wedge(Patch):
    def __str__(self):
        return "Wedge(%g,%g)"%self.xy[0]
    def __init__(self, center, r, theta1, theta2, **kwargs):
        """
        Draw a wedge centered at x,y tuple center with radius r that
        sweeps theta1 to theta2 (angles)

        Valid kwargs are:
        %(Patch)s

        """
        Patch.__init__(self, **kwargs)
        self._path = Path.wedge(theta1, theta2)
        self._patch_transform = transforms.Affine2D() \
            .scale(r).translate(*center)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def get_path(self):
	return self._path

    def get_patch_transform(self):
	return self._patch_transform
        
class Arrow(Polygon):
    """
    An arrow patch
    """
    def __str__(self):
        x1,y1 = self.xy[0]
        x2,y2 = self.xy[1]
        cx,cy = (x1+x2)/2.,(y1+y2)/2.
        return "Arrow(%g,%g)"%(cx,cy)

    _path = Path( [
            [ 0.0,  0.1 ], [ 0.0, -0.1],
            [ 0.8, -0.1 ], [ 0.8, -0.3],
            [ 1.0,  0.0 ], [ 0.8,  0.3],
            [ 0.8,  0.1 ] ] )
    
    def __init__( self, x, y, dx, dy, width=1.0, **kwargs ):
        """Draws an arrow, starting at (x,y), direction and length
        given by (dx,dy) the width of the arrow is scaled by width

        Valid kwargs are:
        %(Patch)s
        """
        L = npy.sqrt(dx**2+dy**2) or 1 # account for div by zero
        cx = float(dx)/L
        sx = float(dy)/L

        trans1 = transforms.Affine2D().scale(L, width)
        trans2 = transforms.Affine2D.from_values(cx, sx, -sx, cx, 0.0, 0.0)
        trans3 = transforms.Affine2d().translate(x, y)
        trans = trans1 + trans2 + trans3
        self._patch_transform = trans.frozen()
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def get_path(self):
        return self._path

    def get_patch_transform(self):
        return self._patch_transform
    
class FancyArrow(Polygon):
    """Like Arrow, but lets you set head width and head height independently."""

    def __str__(self):
        x1,y1 = self.xy[0]
        x2,y2 = self.xy[1]
        cx,cy = (x1+x2)/2.,(y1+y2)/2.
        return "FancyArrow(%g,%g)"%(cx,cy)

    def __init__(self, x, y, dx, dy, width=0.001, length_includes_head=False, \
        head_width=None, head_length=None, shape='full', overhang=0, \
        head_starts_at_zero=False,**kwargs):
        """Returns a new Arrow.

        length_includes_head: True if head is counted in calculating the length.

        shape: ['full', 'left', 'right']

        overhang: distance that the arrow is swept back (0 overhang means
        triangular shape).

        head_starts_at_zero: if True, the head starts being drawn at coordinate
        0 instead of ending at coordinate 0.

        Valid kwargs are:
        %(Patch)s

        """
	# MGDTODO: Implement me
        if head_width is None:
            head_width = 3 * width
        if head_length is None:
            head_length = 1.5 * head_width

        distance = npy.sqrt(dx**2 + dy**2)
        if length_includes_head:
            length=distance
        else:
            length=distance+head_length
        if not length:
            verts = [] #display nothing if empty
        else:
            #start by drawing horizontal arrow, point at (0,0)
            hw, hl, hs, lw = head_width, head_length, overhang, width
            left_half_arrow = npy.array([
                [0.0,0.0],                  #tip
                [-hl, -hw/2.0],             #leftmost
                [-hl*(1-hs), -lw/2.0], #meets stem
                [-length, -lw/2.0],          #bottom left
                [-length, 0],
            ])
            #if we're not including the head, shift up by head length
            if not length_includes_head:
                left_half_arrow += [head_length, 0]
            #if the head starts at 0, shift up by another head length
            if head_starts_at_zero:
                left_half_arrow += [head_length/2.0, 0]
            #figure out the shape, and complete accordingly
            if shape == 'left':
                coords = left_half_arrow
            else:
                right_half_arrow = left_half_arrow*[1,-1]
                if shape == 'right':
                    coords = right_half_arrow
                elif shape == 'full':
                    coords=npy.concatenate([left_half_arrow,right_half_arrow[::-1]])
                else:
                    raise ValueError, "Got unknown shape: %s" % shape
            cx = float(dx)/distance
            sx = float(dy)/distance
            M = npy.array([[cx, sx],[-sx,cx]])
            verts = npy.dot(coords, M) + (x+dx, y+dy)

        Polygon.__init__(self, map(tuple, verts), **kwargs)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

class YAArrow(Patch):
    """
    Yet another arrow class

    This is an arrow that is defined in display space and has a tip at
    x1,y1 and a base at x2, y2.
    """
    def __str__(self):
        x1,y1 = self.xy[0]
        x2,y2 = self.xy[1]
        cx,cy = (x1+x2)/2.,(y1+y2)/2.
        return "YAArrow(%g,%g)"%(cx,cy)

    def __init__(self, dpi, xytip, xybase, width=4, frac=0.1, headwidth=12, **kwargs):
        """
        xytip : (x,y) location of arrow tip
        xybase : (x,y) location the arrow base mid point
        dpi : the figure dpi instance (fig.dpi)
        width : the width of the arrow in points
        frac  : the fraction of the arrow length occupied by the head
        headwidth : the width of the base of the arrow head in points

        Valid kwargs are:
        %(Patch)s

        """
        self.dpi = dpi
        self.xytip = xytip
        self.xybase = xybase
        self.width = width
        self.frac = frac
        self.headwidth = headwidth
        Patch.__init__(self, **kwargs)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd

    def get_path(self):
        # MGDTODO: Since this is dpi dependent, we need to recompute
        # the path every time.  Perhaps this can be plugged through the
        # dpi transform instead (if only we know how to get it...)
        
        # the base vertices
        x1, y1 = self.xytip
        x2, y2 = self.xybase
        k1 = self.width*self.dpi/72./2.
        k2 = self.headwidth*self.dpi/72./2.
        xb1, yb1, xb2, yb2 = self.getpoints(x1, y1, x2, y2, k1)

        # a point on the segment 20% of the distance from the tip to the base
        theta = math.atan2(y2-y1, x2-x1)
        r = math.sqrt((y2-y1)**2. + (x2-x1)**2.)
        xm = x1 + self.frac * r * math.cos(theta)
        ym = y1 + self.frac * r * math.sin(theta)
        xc1, yc1, xc2, yc2 = self.getpoints(x1, y1, xm, ym, k1)
        xd1, yd1, xd2, yd2 = self.getpoints(x1, y1, xm, ym, k2)

        xs = self.convert_xunits([xb1, xb2, xc2, xd2, x1, xd1, xc1])
        ys = self.convert_yunits([yb1, yb2, yc2, yd2, y1, yd1, yc1])

        return Path(zip(xs, ys))

    def get_patch_transform(self):
        return transforms.IdentityTransform()
    
    def getpoints(self, x1,y1,x2,y2, k):
        """
        for line segment defined by x1,y1 and x2,y2, return the points on
        the line that is perpendicular to the line and intersects x2,y2
        and the distance from x2,y2 ot the returned points is k
        """
        x1,y1,x2,y2,k = map(float, (x1,y1,x2,y2,k))
        m = (y2-y1)/(x2-x1)
        pm = -1./m
        a = 1
        b = -2*y2
        c = y2**2. - k**2.*pm**2./(1. + pm**2.)

        y3a = (-b + math.sqrt(b**2.-4*a*c))/(2.*a)
        x3a = (y3a - y2)/pm + x2

        y3b = (-b - math.sqrt(b**2.-4*a*c))/(2.*a)
        x3b = (y3b - y2)/pm + x2
        return x3a, y3a, x3b, y3b


class CirclePolygon(RegularPolygon):
    """
    A circle patch
    """
    def __str__(self):
        return "CirclePolygon(%d,%d)"%self.center

    def __init__(self, xy, radius=5,
                 resolution=20,  # the number of vertices
                 **kwargs):
        """
        Create a circle at xy=(x,y) with radius given by 'radius'

        Valid kwargs are:
        %(Patch)s

        """
        self.center = xy
        self.radius = radius
        RegularPolygon.__init__(self, xy,
                                resolution,
                                radius,
                                orientation=0,
                                **kwargs)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd


class Ellipse(Patch):
    """
    A scale-free ellipse
    """
    def __str__(self):
        return "Ellipse(%d,%d;%dx%d)"%(self.center[0],self.center[1],self.width,self.height)

    def __init__(self, xy, width, height, angle=0.0, **kwargs):
        """
        xy - center of ellipse
        width - length of horizontal axis
        height - length of vertical axis
        angle - rotation in degrees (anti-clockwise)

        Valid kwargs are:
        %(Patch)s
        """
        Patch.__init__(self, **kwargs)

        self.center = xy
        self.width, self.height = width, height
        self.angle = angle
	self._patch_transform = transforms.Affine2D() \
	    .scale(self.width * 0.5, self.height * 0.5) \
	    .rotate_deg(angle) \
	    .translate(*xy)
        
    def get_path(self):
        """
        Return the vertices of the rectangle
        """
	return Path.unit_circle()

    def get_patch_transform(self):
        return self._patch_transform
        
    def contains(self,ev):
        if ev.x is None or ev.y is None: return False,{}
        x, y = self.get_transform().inverted().transform_point((ev.x, ev.y))
        return (x*x + y*y) <= 1.0, {}
                              

class Circle(Ellipse):
    """
    A circle patch
    """
    def __str__(self):
        return "Circle((%g,%g),r=%g)"%(self.center[0],self.center[1],self.radius)

    def __init__(self, xy, radius=5,
                 **kwargs):
        """
        Create true circle at center xy=(x,y) with given radius;
        unlike circle polygon which is a polygonal approcimation, this
        uses splines and is much closer to a scale free circle

        Valid kwargs are:
        %(Patch)s

        """
        if kwargs.has_key('resolution'):
            import warnings
            warnings.warn('Circle is now scale free.  Use CirclePolygon instead!', DeprecationWarning)
            kwargs.pop('resolution')

        self.radius = radius
        Ellipse.__init__(self, xy, radius*2, radius*2, **kwargs)
    __init__.__doc__ = cbook.dedent(__init__.__doc__) % artist.kwdocd


class PolygonInteractor:
    """
    An polygon editor.

    Key-bindings

      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them

      'd' delete the vertex under point

      'i' insert a vertex at point.  You must be within epsilon of the
          line connecting two existing vertices

    """

    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit

    def __str__(self):
        return "PolygonInteractor"

    def __init__(self, poly):
        if poly.figure is None:
            raise RuntimeError('You must first add the polygon to a figure or canvas before defining the interactor')
        canvas = poly.figure.canvas
        self.poly = poly
        self.poly.verts = list(self.poly.verts)
        x, y = zip(*self.poly.verts)
        self.line = lines.Line2D(x,y,marker='o', markerfacecolor='r')
        #self._update_line(poly)

        cid = self.poly.add_callback(self.poly_changed)
        self._ind = None # the active vert

        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('key_press_event', self.key_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas = canvas


    def poly_changed(self, poly):
        'this method is called whenever the polygon object is called'
        # only copy the artist props to the line (except visibility)
        vis = self.line.get_visible()
        artist.Artist.update_from(self.line, poly)
        self.line.set_visible(vis)  # don't use the poly visibility state


    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'
        x, y = zip(*self.poly.verts)

        # display coords
        xt, yt = self.poly.get_transform().numerix_x_y(x, y)
        d = npy.sqrt((xt-event.x)**2 + (yt-event.y)**2)
        ind, = npy.nonzero(npy.equal(d, npy.amin(d)))

        if d[ind]>=self.epsilon:
            ind = None

        return ind

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if not self.showverts: return
        if event.inaxes==None: return
        if event.button != 1: return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if not self.showverts: return
        if event.button != 1: return
        self._ind = None

    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes: return
        if event.key=='t':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts: self._ind = None
        elif event.key=='d':
            ind = self.get_ind_under_point(event)
            if ind is not None:
                self.poly.verts = [tup for i,tup in enumerate(self.poly.verts) if i!=ind]
                self.line.set_data(zip(*self.poly.verts))
        elif event.key=='i':
            xys = self.poly.get_transform().seq_xy_tups(self.poly.verts)
            p = event.x, event.y # display coords
            for i in range(len(xys)-1):
                s0 = xys[i]
                s1 = xys[i+1]
                d = mlab.dist_point_to_segment(p, s0, s1)
                if d<=self.epsilon:
                    self.poly.verts.insert(i+1, (event.xdata, event.ydata))
                    self.line.set_data(zip(*self.poly.verts))
                    break


        self.canvas.draw()

    def motion_notify_callback(self, event):
        'on mouse movement'
        if not self.showverts: return
        if self._ind is None: return
        if event.inaxes is None: return
        if event.button != 1: return
        x,y = event.xdata, event.ydata
        self.poly.verts[self._ind] = x,y
        self.line.set_data(zip(*self.poly.verts))
        self.canvas.draw_idle()


def bbox_artist(artist, renderer, props=None, fill=True):
    """
    This is a debug function to draw a rectangle around the bounding
    box returned by get_window_extent of an artist, to test whether
    the artist is returning the correct bbox

    props is a dict of rectangle props with the additional property
    'pad' that sets the padding around the bbox in points
    """
    if props is None: props = {}
    props = props.copy() # don't want to alter the pad externally
    pad = props.pop('pad', 4)
    pad = renderer.points_to_pixels(pad)
    bbox = artist.get_window_extent(renderer)
    l,b,w,h = bbox.bounds
    l-=pad/2.
    b-=pad/2.
    w+=pad
    h+=pad
    r = Rectangle(xy=(l,b),
                  width=w,
                  height=h,
                  fill=fill,
                  )
    r.set_clip_on( False )
    r.update(props)
    r.draw(renderer)


def draw_bbox(bbox, renderer, color='k', trans=None):
    """
    This is a debug function to draw a rectangle around the bounding
    box returned by get_window_extent of an artist, to test whether
    the artist is returning the correct bbox
    """

    l,b,w,h = bbox.get_bounds()
    r = Rectangle(xy=(l,b),
                  width=w,
                  height=h,
                  edgecolor=color,
                  fill=False,
                  )
    if trans is not None: r.set_transform(trans)
    r.set_clip_on( False )
    r.draw(renderer)

artist.kwdocd['Patch'] = patchdoc = artist.kwdoc(Patch)

for k in ('Rectangle', 'Circle', 'RegularPolygon', 'Polygon', 'Wedge', 'Arrow',
          'FancyArrow', 'YAArrow', 'CirclePolygon', 'Ellipse'):
    artist.kwdocd[k] = patchdoc


