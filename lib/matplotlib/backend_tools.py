"""
Abstract base classes define the primitives for Tools.
These tools are used by `NavigationBase`

:class:`ToolBase`
    Simple stateless tool

:class:`ToolToggleBase`
    Tool that has two states, only one Toggle tool can be
    active at any given time for the same `Navigation`
"""


from matplotlib import rcParams
from matplotlib._pylab_helpers import Gcf
import matplotlib.cbook as cbook
from weakref import WeakKeyDictionary
import numpy as np


class Cursors(object):
    """Simple namespace for cursor reference"""
    HAND, POINTER, SELECT_REGION, MOVE = list(range(4))
cursors = Cursors()


class ToolBase(object):
    """Base tool class

    A base tool, only implements `trigger` method or not method at all.
    The tool is instantiated by `matplotlib.backend_bases.NavigationBase`

    Attributes
    ----------
    navigation: `matplotlib.backend_bases.NavigationBase`
        Navigation that controls this Tool
    figure: `FigureCanvas`
        Figure instance that is affected by this Tool
    name: String
        Used as **Id** of the tool, has to be unique among tools of the same
        Navigation
    """

    keymap = None
    """Keymap to associate with this tool

    **String**: List of comma separated keys that will be used to call this
    tool when the keypress event of *self.figure.canvas* is emited
    """

    description = None
    """Description of the Tool

    **String**: If the Tool is included in the Toolbar this text is used
    as a Tooltip
    """

    image = None
    """Filename of the image

    **String**: Filename of the image to use in the toolbar. If None, the
    `name` is used as a label in the toolbar button
    """

    def __init__(self, navigation, name):
        self._name = name
        self.figure = None
        self.navigation = navigation
        self.set_figure(navigation.canvas.figure)

    def trigger(self, sender, event, data=None):
        """Called when this tool gets used

        This method is called by
        `matplotlib.backend_bases.NavigationBase.tool_trigger_event`

        Parameters
        ----------
        event : `Event`
            The Canvas event that caused this tool to be called
        sender: object
            Object that requested the tool to be triggered
        data: object
            Extra data
        """

        pass

    def set_figure(self, figure):
        """Set the figure

        Set the figure to be affected by this tool

        Parameters
        ----------
        figure : `Figure`
        """

        self.figure = figure

    @property
    def name(self):
        """Tool Id"""
        return self._name

    def destroy(self):
        """Destroy the tool

        This method is called when the tool is removed by
        `matplotlib.backend_bases.NavigationBase.remove_tool`
        """
        pass


class ToolToggleBase(ToolBase):
    """Toggleable tool

    Every time it is triggered, it switches between enable and disable
    """

    radio_group = None
    """Attribute to group 'radio' like tools (mutually exclusive)

    **String** that identifies the group or **None** if not belonging to a
    group
    """

    cursor = None
    """Cursor to use when the tool is active"""

    def __init__(self, *args, **kwargs):
        ToolBase.__init__(self, *args, **kwargs)
        self._toggled = False

    def trigger(self, sender, event, data=None):
        """Calls `enable` or `disable` based on `toggled` value"""
        if self._toggled:
            self.disable(event)
        else:
            self.enable(event)
        self._toggled = not self._toggled

    def enable(self, event=None):
        """Enable the toggle tool

        This method is called dby `trigger` when the `toggled` is False
        """

        pass

    def disable(self, event=None):
        """Disable the toggle tool

        This method is called by `trigger` when the `toggled` is True.

        This can happen in different circumstances

        * Click on the toolbar tool button
        * Call to `matplotlib.backend_bases.NavigationBase.tool_trigger_event`
        * Another `ToolToggleBase` derived tool is triggered
          (from the same `Navigation`)
        """

        pass

    @property
    def toggled(self):
        """State of the toggled tool"""

        return self._toggled


class SetCursorBase(ToolBase):
    """Change to the current cursor while inaxes

    This tool, keeps track of all `ToolToggleBase` derived tools, and calls
    set_cursor when one of these tools is triggered
    """
    def __init__(self, *args, **kwargs):
        ToolBase.__init__(self, *args, **kwargs)
        self._idDrag = self.figure.canvas.mpl_connect(
            'motion_notify_event', self._set_cursor_cbk)
        self._cursor = None
        self._default_cursor = cursors.POINTER
        self._last_cursor = self._default_cursor
        self.navigation.mpl_connect('tool_added_event', self._add_tool_cbk)

        # process current tools
        for tool in self.navigation.tools.values():
            self._add_tool(tool)

    def _tool_trigger_cbk(self, event):
        if event.tool.toggled:
            self._cursor = event.tool.cursor
        else:
            self._cursor = None

        self._set_cursor_cbk(event.canvasevent)

    # If the tool is toggleable, set the cursor when the tool is triggered
    def _add_tool(self, tool):
        if getattr(tool, 'cursor', None) is not None:
            self.navigation.mpl_connect('tool_trigger_%s' % tool.name,
                                        self._tool_trigger_cbk)

    # If tool is added, process it
    def _add_tool_cbk(self, event):
        if event.tool is self:
            return

        self._add_tool(event.tool)

    def _set_cursor_cbk(self, event):
        if not event:
            return

        if not getattr(event, 'inaxes', False) or not self._cursor:
            if self._last_cursor != self._default_cursor:
                self.set_cursor(self._default_cursor)
                self._last_cursor = self._default_cursor
        else:
            if self._cursor:
                cursor = self._cursor
                if cursor and self._last_cursor != cursor:
                    self.set_cursor(cursor)
                    self._last_cursor = cursor

    def set_cursor(self, cursor):
        """Set the cursor

        This method has to be implemented per backend
        """
        pass


class ToolCursorPosition(ToolBase):
    """Send message with the current pointer position

    This tool runs in the background reporting the position of the cursor
    """
    def __init__(self, *args, **kwargs):
        ToolBase.__init__(self, *args, **kwargs)
        self._idDrag = self.figure.canvas.mpl_connect(
            'motion_notify_event', self.send_message)

    def send_message(self, event):
        """Call `matplotlib.backend_bases.NavigationBase.message_event"""
        if self.navigation.messagelock.locked():
            return

        message = ' '

        if event.inaxes and event.inaxes.get_navigate():

            try:
                s = event.inaxes.format_coord(event.xdata, event.ydata)
            except (ValueError, OverflowError):
                pass
            else:
                message = s
        self.navigation.message_event(message, self)


class RubberbandBase(ToolBase):
    """Draw and remove rubberband"""
    def trigger(self, sender, event, data):
        """Call `draw_rubberband` or `remove_rubberband` based on data"""
        if not self.figure.canvas.widgetlock.available(sender):
            return
        if data is not None:
            self.draw_rubberband(*data)
        else:
            self.remove_rubberband()

    def draw_rubberband(self, *data):
        """Draw rubberband

        This method has to be implemented per backend
        """
        pass

    def remove_rubberband(self):
        """Remove rubberband

        This method has to be implemented per backend
        """
        pass


class ToolQuit(ToolBase):
    """Tool to call the figure manager destroy method"""

    description = 'Quit the figure'
    keymap = rcParams['keymap.quit']

    def trigger(self, sender, event, data=None):
        Gcf.destroy_fig(self.figure)


class ToolEnableAllNavigation(ToolBase):
    """Tool to enable all axes for navigation interaction"""

    description = 'Enables all axes navigation'
    keymap = rcParams['keymap.all_axes']

    def trigger(self, sender, event, data=None):
        if event.inaxes is None:
            return

        for a in self.figure.get_axes():
            if event.x is not None and event.y is not None \
                    and a.in_axes(event):
                a.set_navigate(True)


class ToolEnableNavigation(ToolBase):
    """Tool to enable a specific axes for navigation interaction"""

    description = 'Enables one axes navigation'
    keymap = (1, 2, 3, 4, 5, 6, 7, 8, 9)

    def trigger(self, sender, event, data=None):
        if event.inaxes is None:
            return

        n = int(event.key) - 1
        for i, a in enumerate(self.figure.get_axes()):
            # consider axes, in which the event was raised
            # FIXME: Why only this axes?
            if event.x is not None and event.y is not None \
                    and a.in_axes(event):
                    a.set_navigate(i == n)


class ToolGrid(ToolToggleBase):
    """Tool to toggle the grid of the figure"""

    description = 'Toogle Grid'
    keymap = rcParams['keymap.grid']

    def trigger(self, sender, event, data=None):
        if event.inaxes is None:
            return
        ToolToggleBase.trigger(self, sender, event, data)

    def enable(self, event):
        event.inaxes.grid(True)
        self.figure.canvas.draw()

    def disable(self, event):
        event.inaxes.grid(False)
        self.figure.canvas.draw()


class ToolFullScreen(ToolToggleBase):
    """Tool to toggle full screen"""

    description = 'Toogle Fullscreen mode'
    keymap = rcParams['keymap.fullscreen']

    def enable(self, event):
        self.figure.canvas.manager.full_screen_toggle()

    def disable(self, event):
        self.figure.canvas.manager.full_screen_toggle()


class AxisScaleBase(ToolToggleBase):
    """Base Tool to toggle between linear and logarithmic"""

    def trigger(self, sender, event, data=None):
        if event.inaxes is None:
            return
        ToolToggleBase.trigger(self, sender, event, data)

    def enable(self, event):
        self.set_scale(event.inaxes, 'log')
        self.figure.canvas.draw()

    def disable(self, event):
        self.set_scale(event.inaxes, 'linear')
        self.figure.canvas.draw()


class ToolYScale(AxisScaleBase):
    """Tool to toggle between linear and logarithmic the Y axis"""

    description = 'Toogle Scale Y axis'
    keymap = rcParams['keymap.yscale']

    def set_scale(self, ax, scale):
        ax.set_yscale(scale)


class ToolXScale(AxisScaleBase):
    """Tool to toggle between linear and logarithmic the X axis"""

    description = 'Toogle Scale X axis'
    keymap = rcParams['keymap.xscale']

    def set_scale(self, ax, scale):
        ax.set_xscale(scale)


class ToolViewsPositions(ToolBase):
    """Auxiliary Tool to handle changes in views and positions

    Runs in the background and is used by all the tools that
    need to access the record of views and positions of the figure

    * `ToolZoom`
    * `ToolPan`
    * `ToolHome`
    * `ToolBack`
    * `ToolForward`
    """

    def __init__(self, *args, **kwargs):
        self.views = WeakKeyDictionary()
        self.positions = WeakKeyDictionary()
        ToolBase.__init__(self, *args, **kwargs)

    def add_figure(self):
        """Add the current figure to the stack of views and positions"""
        if self.figure not in self.views:
            self.views[self.figure] = cbook.Stack()
            self.positions[self.figure] = cbook.Stack()
            # Define Home
            self.push_current()
            # Adding the clear method as axobserver, removes this burden from
            # the backend
            self.figure.add_axobserver(self.clear)

    def clear(self, figure):
        """Reset the axes stack"""
        if figure in self.views:
            self.views[figure].clear()
            self.positions[figure].clear()

    def update_view(self):
        """Update the viewlim and position from the view and
        position stack for each axes
        """

        lims = self.views[self.figure]()
        if lims is None:
            return
        pos = self.positions[self.figure]()
        if pos is None:
            return
        for i, a in enumerate(self.figure.get_axes()):
            xmin, xmax, ymin, ymax = lims[i]
            a.set_xlim((xmin, xmax))
            a.set_ylim((ymin, ymax))
            # Restore both the original and modified positions
            a.set_position(pos[i][0], 'original')
            a.set_position(pos[i][1], 'active')

        self.figure.canvas.draw_idle()

    def push_current(self):
        """push the current view limits and position onto the stack"""

        lims = []
        pos = []
        for a in self.figure.get_axes():
            xmin, xmax = a.get_xlim()
            ymin, ymax = a.get_ylim()
            lims.append((xmin, xmax, ymin, ymax))
            # Store both the original and modified positions
            pos.append((
                a.get_position(True).frozen(),
                a.get_position().frozen()))
        self.views[self.figure].push(lims)
        self.positions[self.figure].push(pos)

    def refresh_locators(self):
        """Redraw the canvases, update the locators"""
        for a in self.figure.get_axes():
            xaxis = getattr(a, 'xaxis', None)
            yaxis = getattr(a, 'yaxis', None)
            zaxis = getattr(a, 'zaxis', None)
            locators = []
            if xaxis is not None:
                locators.append(xaxis.get_major_locator())
                locators.append(xaxis.get_minor_locator())
            if yaxis is not None:
                locators.append(yaxis.get_major_locator())
                locators.append(yaxis.get_minor_locator())
            if zaxis is not None:
                locators.append(zaxis.get_major_locator())
                locators.append(zaxis.get_minor_locator())

            for loc in locators:
                loc.refresh()
        self.figure.canvas.draw_idle()

    def home(self):
        """Recall the first view and position from the stack"""
        self.views[self.figure].home()
        self.positions[self.figure].home()

    def back(self):
        """Back one step in the stack of views and positions"""
        self.views[self.figure].back()
        self.positions[self.figure].back()

    def forward(self):
        """Forward one step in the stack of views and positions"""
        self.views[self.figure].forward()
        self.positions[self.figure].forward()


class ViewsPositionsBase(ToolBase):
    """Base class for `ToolHome`, `ToolBack` and `ToolForward`"""

    _on_trigger = None

    def trigger(self, sender, event, data=None):
        self.navigation.get_tool('viewpos').add_figure()
        getattr(self.navigation.get_tool('viewpos'), self._on_trigger)()
        self.navigation.get_tool('viewpos').update_view()


class ToolHome(ViewsPositionsBase):
    """Restore the original view lim"""

    description = 'Reset original view'
    image = 'home.png'
    keymap = rcParams['keymap.home']
    _on_trigger = 'home'


class ToolBack(ViewsPositionsBase):
    """Move back up the view lim stack"""

    description = 'Back to  previous view'
    image = 'back.png'
    keymap = rcParams['keymap.back']
    _on_trigger = 'back'


class ToolForward(ViewsPositionsBase):
    """Move forward in the view lim stack"""

    description = 'Forward to next view'
    image = 'forward.png'
    keymap = rcParams['keymap.forward']
    _on_trigger = 'forward'


class ConfigureSubplotsBase(ToolBase):
    """Base tool for the configuration of subplots"""

    description = 'Configure subplots'
    image = 'subplots.png'


class SaveFigureBase(ToolBase):
    """Base tool for figure saving"""

    description = 'Save the figure'
    image = 'filesave.png'
    keymap = rcParams['keymap.save']


class ZoomPanBase(ToolToggleBase):
    """Base class for `ToolZoom` and `ToolPan`"""
    def __init__(self, *args):
        ToolToggleBase.__init__(self, *args)
        self._button_pressed = None
        self._xypress = None
        self._idPress = None
        self._idRelease = None

    def enable(self, event):
        """Connect press/release events and lock the canvas"""
        self.figure.canvas.widgetlock(self)
        self._idPress = self.figure.canvas.mpl_connect(
            'button_press_event', self._press)
        self._idRelease = self.figure.canvas.mpl_connect(
            'button_release_event', self._release)

    def disable(self, event):
        """Release the canvas and disconnect press/release events"""
        self._cancel_action()
        self.figure.canvas.widgetlock.release(self)
        self.figure.canvas.mpl_disconnect(self._idPress)
        self.figure.canvas.mpl_disconnect(self._idRelease)

    def trigger(self, sender, event, data=None):
        self.navigation.get_tool('viewpos').add_figure()
        ToolToggleBase.trigger(self, sender, event, data)


class ToolZoom(ZoomPanBase):
    """Zoom to rectangle"""

    description = 'Zoom to rectangle'
    image = 'zoom_to_rect.png'
    keymap = rcParams['keymap.zoom']
    cursor = cursors.SELECT_REGION
    radio_group = 'default'

    def __init__(self, *args):
        ZoomPanBase.__init__(self, *args)
        self._ids_zoom = []

    def _cancel_action(self):
        for zoom_id in self._ids_zoom:
            self.figure.canvas.mpl_disconnect(zoom_id)
        self.navigation.tool_trigger_event('rubberband', self)
        self.navigation.get_tool('viewpos').refresh_locators()
        self._xypress = None
        self._button_pressed = None
        self._ids_zoom = []
        return

    def _press(self, event):
        """the _press mouse button in zoom to rect mode callback"""

        # If we're already in the middle of a zoom, pressing another
        # button works to "cancel"
        if self._ids_zoom != []:
            self._cancel_action()

        if event.button == 1:
            self._button_pressed = 1
        elif event.button == 3:
            self._button_pressed = 3
        else:
            self._cancel_action()
            return

        x, y = event.x, event.y

        self._xypress = []
        for i, a in enumerate(self.figure.get_axes()):
            if (x is not None and y is not None and a.in_axes(event) and
                    a.get_navigate() and a.can_zoom()):
                self._xypress.append((x, y, a, i, a.viewLim.frozen(),
                                      a.transData.frozen()))

        id1 = self.figure.canvas.mpl_connect(
            'motion_notify_event', self._mouse_move)
        id2 = self.figure.canvas.mpl_connect(
            'key_press_event', self._switch_on_zoom_mode)
        id3 = self.figure.canvas.mpl_connect(
            'key_release_event', self._switch_off_zoom_mode)

        self._ids_zoom = id1, id2, id3
        self._zoom_mode = event.key

    def _switch_on_zoom_mode(self, event):
        self._zoom_mode = event.key
        self._mouse_move(event)

    def _switch_off_zoom_mode(self, event):
        self._zoom_mode = None
        self._mouse_move(event)

    def _mouse_move(self, event):
        """the drag callback in zoom mode"""

        if self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, _ind, _lim, _trans = self._xypress[0]

            # adjust x, last, y, last
            x1, y1, x2, y2 = a.bbox.extents
            x, lastx = max(min(x, lastx), x1), min(max(x, lastx), x2)
            y, lasty = max(min(y, lasty), y1), min(max(y, lasty), y2)

            if self._zoom_mode == "x":
                x1, y1, x2, y2 = a.bbox.extents
                y, lasty = y1, y2
            elif self._zoom_mode == "y":
                x1, y1, x2, y2 = a.bbox.extents
                x, lastx = x1, x2

            self.navigation.tool_trigger_event('rubberband',
                                               self,
                                               data=(x, y, lastx, lasty))

    def _release(self, event):
        """the release mouse button callback in zoom to rect mode"""

        for zoom_id in self._ids_zoom:
            self.figure.canvas.mpl_disconnect(zoom_id)
        self._ids_zoom = []

        if not self._xypress:
            self._cancel_action()
            return

        last_a = []

        for cur_xypress in self._xypress:
            x, y = event.x, event.y
            lastx, lasty, a, _ind, lim, _trans = cur_xypress
            # ignore singular clicks - 5 pixels is a threshold
            if abs(x - lastx) < 5 or abs(y - lasty) < 5:
                self._cancel_action()
                return

            x0, y0, x1, y1 = lim.extents

            # zoom to rect
            inverse = a.transData.inverted()
            lastx, lasty = inverse.transform_point((lastx, lasty))
            x, y = inverse.transform_point((x, y))
            Xmin, Xmax = a.get_xlim()
            Ymin, Ymax = a.get_ylim()

            # detect twinx,y axes and avoid double zooming
            twinx, twiny = False, False
            if last_a:
                for la in last_a:
                    if a.get_shared_x_axes().joined(a, la):
                        twinx = True
                    if a.get_shared_y_axes().joined(a, la):
                        twiny = True
            last_a.append(a)

            if twinx:
                x0, x1 = Xmin, Xmax
            else:
                if Xmin < Xmax:
                    if x < lastx:
                        x0, x1 = x, lastx
                    else:
                        x0, x1 = lastx, x
                    if x0 < Xmin:
                        x0 = Xmin
                    if x1 > Xmax:
                        x1 = Xmax
                else:
                    if x > lastx:
                        x0, x1 = x, lastx
                    else:
                        x0, x1 = lastx, x
                    if x0 > Xmin:
                        x0 = Xmin
                    if x1 < Xmax:
                        x1 = Xmax

            if twiny:
                y0, y1 = Ymin, Ymax
            else:
                if Ymin < Ymax:
                    if y < lasty:
                        y0, y1 = y, lasty
                    else:
                        y0, y1 = lasty, y
                    if y0 < Ymin:
                        y0 = Ymin
                    if y1 > Ymax:
                        y1 = Ymax
                else:
                    if y > lasty:
                        y0, y1 = y, lasty
                    else:
                        y0, y1 = lasty, y
                    if y0 > Ymin:
                        y0 = Ymin
                    if y1 < Ymax:
                        y1 = Ymax

            if self._button_pressed == 1:
                if self._zoom_mode == "x":
                    a.set_xlim((x0, x1))
                elif self._zoom_mode == "y":
                    a.set_ylim((y0, y1))
                else:
                    a.set_xlim((x0, x1))
                    a.set_ylim((y0, y1))
            elif self._button_pressed == 3:
                if a.get_xscale() == 'log':
                    alpha = np.log(Xmax / Xmin) / np.log(x1 / x0)
                    rx1 = pow(Xmin / x0, alpha) * Xmin
                    rx2 = pow(Xmax / x0, alpha) * Xmin
                else:
                    alpha = (Xmax - Xmin) / (x1 - x0)
                    rx1 = alpha * (Xmin - x0) + Xmin
                    rx2 = alpha * (Xmax - x0) + Xmin
                if a.get_yscale() == 'log':
                    alpha = np.log(Ymax / Ymin) / np.log(y1 / y0)
                    ry1 = pow(Ymin / y0, alpha) * Ymin
                    ry2 = pow(Ymax / y0, alpha) * Ymin
                else:
                    alpha = (Ymax - Ymin) / (y1 - y0)
                    ry1 = alpha * (Ymin - y0) + Ymin
                    ry2 = alpha * (Ymax - y0) + Ymin

                if self._zoom_mode == "x":
                    a.set_xlim((rx1, rx2))
                elif self._zoom_mode == "y":
                    a.set_ylim((ry1, ry2))
                else:
                    a.set_xlim((rx1, rx2))
                    a.set_ylim((ry1, ry2))

        self._zoom_mode = None
        self.navigation.get_tool('viewpos').push_current()
        self._cancel_action()


class ToolPan(ZoomPanBase):
    """Pan axes with left mouse, zoom with right"""

    keymap = rcParams['keymap.pan']
    description = 'Pan axes with left mouse, zoom with right'
    image = 'move.png'
    cursor = cursors.MOVE
    radio_group = 'default'

    def __init__(self, *args):
        ZoomPanBase.__init__(self, *args)
        self._idDrag = None

    def _cancel_action(self):
        self._button_pressed = None
        self._xypress = []
        self.figure.canvas.mpl_disconnect(self._idDrag)
        self.navigation.messagelock.release(self)
        self.navigation.get_tool('viewpos').refresh_locators()

    def _press(self, event):
        if event.button == 1:
            self._button_pressed = 1
        elif event.button == 3:
            self._button_pressed = 3
        else:
            self._cancel_action()
            return

        x, y = event.x, event.y

        self._xypress = []
        for i, a in enumerate(self.figure.get_axes()):
            if (x is not None and y is not None and a.in_axes(event) and
                    a.get_navigate() and a.can_pan()):
                a.start_pan(x, y, event.button)
                self._xypress.append((a, i))
                self.navigation.messagelock(self)
                self._idDrag = self.figure.canvas.mpl_connect(
                    'motion_notify_event', self._mouse_move)

    def _release(self, event):
        if self._button_pressed is None:
            self._cancel_action()
            return

        self.figure.canvas.mpl_disconnect(self._idDrag)
        self.navigation.messagelock.release(self)

        for a, _ind in self._xypress:
            a.end_pan()
        if not self._xypress:
            self._cancel_action()
            return

        self.navigation.get_tool('viewpos').push_current()
        self._cancel_action()

    def _mouse_move(self, event):
        for a, _ind in self._xypress:
            # safer to use the recorded button at the _press than current
            # button: # multiple button can get pressed during motion...
            a.drag_pan(self._button_pressed, event.key, event.x, event.y)
        self.navigation.canvas.draw_idle()


tools = [['navigation', [(ToolHome, 'home'),
                         (ToolBack, 'back'),
                         (ToolForward, 'forward')]],

         ['zoompan', [(ToolZoom, 'zoom'),
                      (ToolPan, 'pan')]],

         ['layout', [('ToolConfigureSubplots', 'subplots'), ]],

         ['io', [('ToolSaveFigure', 'save'), ]],

         [None, [(ToolGrid, 'grid'),
                 (ToolFullScreen, 'fullscreen'),
                 (ToolQuit, 'quit'),
                 (ToolEnableAllNavigation, 'allnav'),
                 (ToolEnableNavigation, 'nav'),
                 (ToolXScale, 'xscale'),
                 (ToolYScale, 'yscale'),
                 (ToolCursorPosition, 'position'),
                 (ToolViewsPositions, 'viewpos'),
                 ('ToolSetCursor', 'cursor'),
                 ('ToolRubberband', 'rubberband')]]]
"""Default tools"""
