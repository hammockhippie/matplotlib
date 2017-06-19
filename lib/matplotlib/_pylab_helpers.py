"""
Manage figures for pyplot interface.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six
import sys
import gc
import atexit

from matplotlib import is_interactive


def error_msg(msg):
    print(msg, file=sys.stderr)


class Gcf(object):
    """
    Singleton to manage a set of integer-numbered figures.

    This class is never instantiated; it consists of two class
    attributes (a list and a dictionary), and a set of static
    methods that operate on those attributes, accessing them
    directly as class attributes.

    Attributes:

        *figs*:
          dictionary of the form {*num*: *manager*, ...}

        *_activeQue*:
          list of *managers*, with active one at the end

    """
    _activeQue = []
    figs = {}

    @classmethod
    def add_figure_manager(cls, manager):
        cls.figs[manager.num] = manager
        try:  # TODO remove once all backends converted to use the new manager.
            manager.mpl_connect('window_destroy_event', cls.destroy_cbk)
        except:
            pass

        cls.set_active(manager)

    @classmethod
    def get_fig_manager(cls, num):
        """
        If figure manager *num* exists, make it the active
        figure and return the manager; otherwise return *None*.
        """
        manager = cls.figs.get(num, None)
        if manager is not None:
            cls.set_active(manager)
        return manager

    @classmethod
    def show_all(cls, block=None):
        """
        Show all figures.  If *block* is not None, then
        it is a boolean that overrides all other factors
        determining whether show blocks by calling mainloop().
        The other factors are:
        it does not block if run inside ipython's "%pylab" mode
        it does not block in interactive mode.
        """

        managers = cls.get_all_fig_managers()
        if not managers:
            return

        for manager in managers:
            manager.show()

        if block is True:
            # Start the mainloop on the last manager, so we don't have a
            # mainloop starting for each manager. Not ideal, but works for now.
            manager._mainloop()
            return
        elif block is False:
            return

        # Hack: determine at runtime whether we are
        # inside ipython in pylab mode.
        from matplotlib import pyplot
        try:
            ipython_pylab = not pyplot.show._needmain
            # IPython versions >= 0.10 tack the _needmain
            # attribute onto pyplot.show, and always set
            # it to False, when in %pylab mode.
            ipython_pylab = ipython_pylab and manager.backend_name != 'webagg'
            # TODO: The above is a hack to get the WebAgg backend
            # working with ipython's `%pylab` mode until proper
            # integration is implemented.
        except AttributeError:
            ipython_pylab = False

        # Leave the following as a separate step in case we
        # want to control this behavior with an rcParam.
        if ipython_pylab:
            return

        # If not interactive we need to block
        if not is_interactive() or manager.backend_name == 'webagg':
            manager._mainloop()

    @classmethod
    def destroy(cls, num):
        """
        Try to remove all traces of figure *num*.

        In the interactive backends, this is bound to the
        window "destroy" and "delete" events.
        """
        if not cls.has_fignum(num):
            return
        manager = cls.figs[num]
        manager.canvas.mpl_disconnect(manager._cidgcf)

        # There must be a good reason for the following careful
        # rebuilding of the activeQue; what is it?
        oldQue = cls._activeQue[:]
        cls._activeQue = []
        for f in oldQue:
            if f != manager:
                cls._activeQue.append(f)

        del cls.figs[num]
        manager.destroy()  # Unneeded with MEP27 remove later
        gc.collect(1)

    @classmethod
    def destroy_fig(cls, fig):
        "*fig* is a Figure instance"
        num = None
        for manager in six.itervalues(cls.figs):
            if manager.canvas.figure == fig:
                num = manager.num
                break
        if num is not None:
            cls.destroy(num)

    @classmethod
    def destroy_all(cls):
        # this is need to ensure that gc is available in corner cases
        # where modules are being torn down after install with easy_install
        import gc  # noqa
        for manager in list(cls.figs.values()):
            manager.canvas.mpl_disconnect(manager._cidgcf)
            manager.destroy()

        cls._activeQue = []
        cls.figs.clear()
        gc.collect(1)

    @classmethod
    def has_fignum(cls, num):
        """
        Return *True* if figure *num* exists.
        """
        return num in cls.figs

    @classmethod
    def get_all_fig_managers(cls):
        """
        Return a list of figure managers.
        """
        return list(cls.figs.values())

    @classmethod
    def get_num_fig_managers(cls):
        """
        Return the number of figures being managed.
        """
        return len(cls.figs)

    @classmethod
    def get_active(cls):
        """
        Return the manager of the active figure, or *None*.
        """
        if len(cls._activeQue) == 0:
            return None
        else:
            return cls._activeQue[-1]

    @classmethod
    def set_active(cls, manager):
        """
        Make the figure corresponding to *manager* the active one.
        """
        oldQue = cls._activeQue[:]
        cls._activeQue = []
        for m in oldQue:
            if m != manager:
                cls._activeQue.append(m)
        cls._activeQue.append(manager)

    @classmethod
    def draw_all(cls, force=False):
        """
        Redraw all figures registered with the pyplot
        state machine.
        """
        for f_mgr in cls.get_all_fig_managers():
            if force or f_mgr.canvas.figure.stale:
                f_mgr.canvas.draw_idle()

    @classmethod
    def destroy_cbk(cls, event):
        cls.destroy(event.figure_manager.num)

atexit.register(Gcf.destroy_all)
