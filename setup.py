"""
You will need to have freetype, libpng and zlib installed to compile
matplotlib, inlcuding the *-devel versions of these libraries if you
are using a package manager like RPM or debian.

matplotlib has added some extension module code which can optionally
be built by setting the appropriate flag below.

The GTKAgg and TkAgg will try to build if they detect pygtk or Tkinter
respectively; set them to 0 if you do not want to build them
"""

# build the image support module - requires agg and Numeric or
# numarray.  You can build the image module with either Numeric or
# numarray or both.  By default, matplotlib will build support for
# whatever array packages you have installed.
BUILD_IMAGE = 1

# Build the antigrain geometry toolkit.  Agg makes heavy use of
# templates, so it probably requires a fairly recent compiler to build
# it.  It makes very nice antialiased output and also supports alpha
# blending
BUILD_AGG = 1

# Render Agg to the GTK canvas
#BUILD_GTKAGG       = 0
BUILD_GTKAGG       = 'auto'

# build TK GUI with Agg renderer ; requires Tkinter Python extension
# and Tk includes
# Use False or 0 if you don't want to build
#BUILD_TKAGG        = 0
BUILD_TKAGG        = 'auto'

# build a small extension to manage the focus on win32 platforms.
#BUILD_WINDOWING        = 0
BUILD_WINDOWING        = 'auto'

VERBOSE = False  # insert lots of diagnostic prints in extension code





## You shouldn't need to customize below this point

from distutils.core import setup
import sys,os
import glob
from distutils.core import Extension
from setupext import build_agg, build_gtkagg, build_tkagg, \
     build_ft2font, build_image, build_windowing, build_transforms
import distutils.sysconfig

for line in file('lib/matplotlib/__init__.py').readlines():
    if line[:11] == '__version__':
        exec(line)
        break

data = []

data.extend(glob.glob('fonts/afm/*.afm'))
data.extend(glob.glob('fonts/ttf/*.ttf'))
data.extend(glob.glob('images/*.xpm'))
data.extend(glob.glob('images/*.svg'))
data.extend(glob.glob('images/*.png'))
data.extend(glob.glob('images/*.ppm'))
data.append('.matplotlibrc')

data_files=[('share/matplotlib', data),]

# Figure out which array packages to provide binary support for
# and define the NUMERIX value: Numeric, numarray, or both.
try:
    import Numeric
    HAVE_NUMERIC=1
except ImportError:
    HAVE_NUMERIC=0
try:
    import numarray
    HAVE_NUMARRAY=1
except ImportError:
    HAVE_NUMARRAY=0
    
NUMERIX=["neither", "Numeric","numarray","both"][HAVE_NUMARRAY*2+HAVE_NUMERIC]

if NUMERIX == "neither":
    raise RuntimeError("You must install Numeric, numarray, or both to build matplotlib")

# This print interers with --version, which license depends on
#print "Compiling matplotlib for:", NUMERIX

ext_modules = []

BUILD_FT2FONT = 1
packages = [
    'matplotlib',
    'matplotlib/backends',
    ]


try: import datetime
except ImportError: havedate = False
else: havedate = True

if havedate: # dates require python23 datetime
    # only install pytz and dateutil if the user hasn't got them
    try: import dateutil
    except ImportError:
        packages.append('dateutil')

    try: import pytz
    except ImportError:
        packages.append('pytz')

        # install pytz subdirs
        for dirpath, dirname, filenames in os.walk(os.path.join('lib', 'pytz','zoneinfo')):
            packages.append('/'.join(dirpath.split(os.sep)[1:]))



build_transforms(ext_modules, packages, NUMERIX)

if BUILD_GTKAGG:
    try:
        import gtk
    except ImportError:
        print 'GTKAgg requires pygtk'
        BUILD_GTKAGG=0
    except RuntimeError:
        print 'pygtk present but import failed'
if BUILD_GTKAGG:
    BUILD_AGG = 1
    build_gtkagg(ext_modules, packages)

if BUILD_TKAGG:
    try: import Tkinter
    except ImportError: print 'TKAgg requires TkInter'
    else:
        BUILD_AGG = 1
        build_tkagg(ext_modules, packages)


if BUILD_AGG:
    build_agg(ext_modules, packages)

if BUILD_FT2FONT:
    build_ft2font(ext_modules, packages)

if BUILD_WINDOWING and sys.platform=='win32':
   build_windowing(ext_modules, packages)

if BUILD_IMAGE:
    build_image(ext_modules, packages, NUMERIX)

for mod in ext_modules:
    if VERBOSE:
        mod.extra_compile_args.append('-DVERBOSE')
    
setup(name="matplotlib",
      version= __version__,
      description = "Matlab(TM) style python plotting package",
      author = "John D. Hunter",
      author_email="jdhunter@ace.bsd.uchicago.edu",
      url = "http://matplotlib.sourceforge.net",
      long_description = """
      matplotlib strives to produce publication quality 2D graphics
      using matlab plotting for inspiration.  Although the main lib is
      object oriented, there is a functional interface "pylab"
      for people coming from Matlab.
      """,
      packages = packages,
      platforms='any',
      py_modules = ['pylab'],
      ext_modules = ext_modules, 
      data_files = data_files,
      package_dir = {'': 'lib'},
      )
