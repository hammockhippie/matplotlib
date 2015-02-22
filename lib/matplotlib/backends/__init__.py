from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six

import matplotlib
import inspect
import warnings


backend = matplotlib.get_backend()

def get_backend_name(name=None):
    '''converts the name of the backend into the module to load
    name : str, optional
    
    Parameters
    ----------
        The name of the backend to use.  If `None`, falls back to
        ``matplotlib.get_backend()`` (which return ``rcParams['backend']``)
    '''

    if name is None:
        # validates, to match all_backends
        name = matplotlib.get_backend()
    if name.startswith('module://'):
        backend_name = name[9:]
    else:
        backend_name = 'matplotlib.backends.backend_' + name.lower()

    return backend_name


def get_backends():
    backend_name = get_backend_name()
    _temp = __import__(backend_name, globals(), locals(),
                       ['Window', 'Toolbar2', 'FigureCanvas', 'MainLoop',
                        'new_figure_manager'], 0)
    FigureCanvas = _temp.FigureCanvas
    try:
        Window = _temp.Window
        Toolbar2 = _temp.Toolbar2
        MainLoop = _temp.MainLoop
        old_new_figure_manager = None
    except AttributeError:
        Window = None
        Toolbar2 = None
        MainLoop = getattr(_temp, 'show', do_nothing_show)
        old_new_figure_manager = _temp.new_figure_manager

    return FigureCanvas, Window, Toolbar2, MainLoop, old_new_figure_manager


def pylab_setup(name=None):
    '''return new_figure_manager, draw_if_interactive and show for pyplot

    This provides the backend-specific functions that are used by
    pyplot to abstract away the difference between interactive backends.

    Parameters
    ----------
    name : str, optional
        The name of the backend to use.  If `None`, falls back to
        ``matplotlib.get_backend()`` (which return ``rcParams['backend']``)

    Returns
    -------
    backend_mod : module
        The module which contains the backend of choice

    new_figure_manager : function
        Create a new figure manager (roughly maps to GUI window)

    draw_if_interactive : function
        Redraw the current figure if pyplot is interactive

    show : function
        Show (and possibly block) any unshown figures.

    '''
    # Import the requested backend into a generic module object
    backend_name = get_backend_name(name)
    # the last argument is specifies whether to use absolute or relative
    # imports. 0 means only perform absolute imports.
    backend_mod = __import__(backend_name, globals(), locals(),
                             [backend_name], 0)

    # Things we pull in from all backends
    new_figure_manager = backend_mod.new_figure_manager

    # image backends like pdf, agg or svg do not need to do anything
    # for "show" or "draw_if_interactive", so if they are not defined
    # by the backend, just do nothing

    def do_nothing(*args, **kwargs):
        pass

    backend_version = getattr(backend_mod, 'backend_version', 'unknown')

    show = None if hasattr(backend_mod, 'show') else do_nothing_show

    draw_if_interactive = getattr(backend_mod, 'draw_if_interactive',
                                  do_nothing)

    matplotlib.verbose.report('backend %s version %s' %
                              (name, backend_version))

    # need to keep a global reference to the backend for compatibility
    # reasons. See https://github.com/matplotlib/matplotlib/issues/6092
    global backend
    backend = name
    return backend_mod, new_figure_manager, draw_if_interactive, show

def do_nothing_show(*args, **kwargs):
    frame = inspect.currentframe()
    fname = frame.f_back.f_code.co_filename
    if fname in ('<stdin>', '<ipython console>'):
        warnings.warn("""
Your currently selected backend, '%s' does not support show().
Please select a GUI backend in your matplotlibrc file ('%s')
or with matplotlib.use()""" %
                          (name, matplotlib.matplotlib_fname()))
