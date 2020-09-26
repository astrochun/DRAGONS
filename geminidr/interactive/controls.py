"""
Support for keyboard controls.

This is where we bolt on key controls onto Bokeh, which requires
some hackery since they are so unresponsive on this issue.

The controller has a concept of the current "state" of interaction.
It also receives a continuous update of x/y coordinates and
mouse clicks.  In it's default, inactive state, it is waiting for
the user to select a Task by it's key code.  Once a Task is selected,
it becomes the active Task and is handed further keys, mouse moves
and clicks.  Tasks may in turn spawn sub-Tasks to refine their
behavior or may manage some state on their own.  When the task is
finished (or canceled), the controller is returned to the top-level
inactive state.
"""
from abc import ABC, abstractmethod

from bokeh.events import PointEvent

__all__ = ["controller", "Controller"]

from gempy.library.tracing import pinpoint_peaks

""" This is the active controller.  It is activated when it's attached figure sees the mouse enter it's view.

Controller instances will set this to listen to key presses.  The bokeh server will use this to send keys
it recieves from the clients.  Everyone else should leave it alone!
"""
controller = None


class Controller(object):
    """
    Controller is an interaction manager for our custom interfaces.

    We want rich client-server driven interactions and bokeh does a poor job
    of this by itself.  These new interactions are instead routed through here.
    In the case of key presses, this is routed in via a custom URL endpoint in
    the bokeh server from a javascript key listener in index.html.

    This routing can mean that some operations have to happen within a call to
    `add_next_tick_callback`.  That is because our key press is coming in via
    a different path than the normal bokeh interactivity.

    The controler maintains a set of :class:`~Task` instances.  One :class:`~Task` is operating at a time.
    An active task receives all the key presses and when it is done, it returns
    control to the :class:`~Controller`.  The :class:`~Tasks` are also able to update the help
    text to give contextual help.
    """
    def __init__(self, fig, aperture_model, band_model, helptext):
        """
        Create a controller to manage the given aperture and band models on the given GIFigure

        Parameters
        ----------
        fig : :class:`~Figure`
            plot to attach controls to
        aperture_model : :class:`GIApertureModel`
            model for apertures for this plot/dataset, or None
        band_model : :class:`GIBandModel`
            model for bands for this plot/dataset, or None
        helptext : :class:`Div`
            div to update text in to provide help to the user
        """
        self.aperture_model = aperture_model
        self.helptext = helptext
        self.tasks = dict()
        if aperture_model:
            self.tasks['a'] = ApertureTask(aperture_model, helptext)
        if band_model:
            self.tasks['b'] = BandTask(band_model, helptext)
        self.task = None
        self.x = None
        self.y = None
        # we need to always know where the mouse is in case someone
        # starts an Aperture or Band
        fig.on_event('mousemove', self.on_mouse_move)
        fig.on_event('mouseenter', self.on_mouse_enter)
        fig.on_event('mouseleave', self.on_mouse_leave)

        self.set_help_text("")

    def set_help_text(self, text=None):
        """
        Set the text in the help area.

        This updates the text in the help div for the user to
        know the most commonly used commands for the current
        context.

        Parameters
        ----------
        text : str
            html to display in the div
        """
        if text is not None:
            ht = text
        else:
            ht = """While the mouse is over the plot, choose from the following commands:<br/>\n"""
            for key, task in sorted(self.tasks.items()):
                ht = ht + "<b>%s</b> - %s<br/>\n" % (key, task.description())

        # This has to be done via a callback.  During the key press, we are outside the context of
        # the widget's bokeh document
        if self.helptext.document:
            # we now have an associated document, need to do this inside that context
            self.helptext.document.add_next_tick_callback(lambda: self.helptext.update(text=ht))
        else:
            self.helptext.text = ht

    def on_mouse_enter(self, event):
        """
        Handle the mouse entering our related figure by activating this controller.

        Parameters
        ----------
        event
            the mouse event from bokeh, unused

        Returns
        -------

        """
        global controller
        controller = self
        if len(self.tasks) == 1:
            for k, v in self.tasks.items():
                self.task = v
            # self.task = self.tasks.values()[0]
            self.set_help_text(self.task.helptext())
            self.task.start(self.x, self.y)
        else:
            # show selection of available tasks
            self.set_help_text(None)

    def on_mouse_leave(self, event):
        """
        Response to the mouse leaving the connected figure.

        When the mouse leaves, we tell any active task to finish itself
        and we de-register ourselves as the active controller.  We will
        not receive further events until a subsequent mouse enter event.

        Parameters
        ----------
        event
            the mouse event from bokeh, unused
        """
        global controller
        if self == controller:
            self.set_help_text("")
            if self.task:
                self.task.stop()
                self.task = None
            controller = None

    def on_mouse_move(self, event: PointEvent):
        """
        Respond to mouse movement within the figure.

        This is a convenience method where we extract the
        x and y coordinates and call our more generic
        `handle_mouse` method.

        Parameters
        ----------
        event : PointEvent
            the event from bokeh

        """
        self.x = event.x
        self.y = event.y
        self.handle_mouse(self.x, self.y)

    def handle_key(self, key):
        """
        Handle a key press.

        We respond to key presses by passing them to
        the active task.  If there is no active task,
        we check if this key is associated with a
        particular task and, if so, activate that task,

        Parameters
        ----------
        key : char
            Key that was pressed, such as 'a'

        """
        def _ui_loop_handle_key(key):
            if self.task:
                if self.task.handle_key(key):
                    if len(self.tasks) > 1:
                        # only if we have multiple tasks, otherwise no point in offering 1 task option
                        self.task = None
                        self.set_help_text()
            else:
                if key in self.tasks:
                    self.task = self.tasks[key]
                    self.set_help_text(self.task.helptext())
                    self.task.start(self.x, self.y)
        if self.helptext.document:
            # we now have an associated document, need to do this inside that context
            self.helptext.document.add_next_tick_callback(lambda: _ui_loop_handle_key(key=key))

    def handle_mouse(self, x, y):
        """
        Handle mouse movement

        If there is an active task, we let it know aobut the
        mouse move event.  Tasks will handle this in their
        own custom way, perhaps responding to a drag or just
        knowing the mouse position in the event the user
        creates an aperture.

        Parameters
        ----------
        x : float
            x coordinate in data space
        y : float
            y coordinate in data space

        """
        self.x = x
        self.y = y
        if self.task:
            if self.task.handle_mouse(x, y):
                self.task = None
                self.set_help_text()


class Task(ABC):
    """
    A Task is a general concept of some interactive behavior where we
    also want keyboard support.

    A task may be connected to a top-level Controller by a key command.
    Once a task is active, the controller will send mouse and key events
    to it.
    """
    @abstractmethod
    def handle_key(self, key):
        """
        Called when the task is active and we have a key press.
        """
        pass

    @abstractmethod
    def handle_mouse(self, x, y):
        """
        Called when we have a mouse move and the task is active.

        Parameters
        ----------
        x : float
            x coordinate of mouse in data space
        y : float
            y coordinate of mouse in data space

        """
        pass

    def helptext(self):
        """
        Override to provide HTML help text to display when this task is active.

        Returns
        -------
            The html to display
        """
        return ""


class ApertureTask(Task):
    """
    Task for controlling apertures.
    """
    def __init__(self, aperture_model, helptext):
        """
        Create aperture task for the given model.

        Parameters
        ----------
        aperture_model : :class:`GIApertureModel`
            The aperture model to operate on
        """
        self.mode = "location"  # location, width, left, right for placing location, width (both) or left/right side
        self.aperture_model = aperture_model
        self.aperture_center = None
        self.left = None
        self.right = None
        self.aperture_id = None
        self.last_x = None
        self.last_y = None
        self.helptext_area = helptext

    def start(self, x, y):
        self.last_x = x
        self.last_y = y
        self.aperture_center = None
        self.left = None
        self.right = None
        self.aperture_id = None
        self.mode = "location"

    def stop(self):
        """
        Stop updating the current aperture.

        This causes the interactivity to end.

        """
        self.stop_aperture()

    def start_aperture(self, x, y):
        """
        Create a new aperture at this x coordinate.

        The aperture is centered at x with a width of 0.  Further
        mouse movement will set the width to the mouse location.

        Parameters
        ----------
        x : float
            x coordinate in data space
        y : float
            y coordinate in data space (unused)
        """
        self.aperture_center = x
        self.left = x
        self.right = x
        self.aperture_id = self.aperture_model.add_aperture(x, x, x)
        self.mode = "width"
        self.update_help(self.mode)

    def stop_aperture(self):
        """
        Stop updating the current aperture.

        This causes the interactivity to end.

        """
        self.aperture_center = None
        self.aperture_id = None
        self.mode = ""
        self.update_help(self.mode)

    def handle_key(self, key):
        """
        Handle a key press.

        This will listen for a press of 'a' to tell the task to stop updating the aperture.

        Parameters
        ----------
        key : char
            key that was pressed

        Returns
        -------
            True if the task is finished and the controller should take over, False if we are not done with the Task
        """
        if key == 'a':
            if self.aperture_center is None:
                self.start_aperture(self.last_x, self.last_y)
                return False
            else:
                self.stop_aperture()
                return True
        if key == 'f':
            if self.aperture_center is None:
                peaks = pinpoint_peaks(self.aperture_model.get_profile(), None, [self.last_x, ], halfwidth=20,
                                       threshold=0)
                if len(peaks) > 0:
                    self.start_aperture(peaks[0], self.last_y)
                else:
                    self.start_aperture(self.last_x, self.last_y)
        if key == '[':
            if self.aperture_center is None:
                # get closest one
                self.aperture_id, self.aperture_center, self.left, self.right \
                    = self.aperture_model.find_closest(self.last_x)
                if self.aperture_id is None:
                    return False
            self.mode = 'left'
            self.update_help(self.mode)
            return False
        if key == ']':
            if self.aperture_center is None:
                # get closest one
                self.aperture_id, self.aperture_center, self.left, self.right \
                    = self.aperture_model.find_closest(self.last_x)
                if self.aperture_id is None:
                    return False
            self.mode = 'right'
            self.update_help(self.mode)
            return False
        if key == 'l':
            if self.aperture_center is None:
                # get closest one
                self.aperture_id, self.aperture_center, self.left, self.right \
                    = self.aperture_model.find_closest(self.last_x)
                if self.aperture_id is None:
                    return False
            self.mode = 'location'
            self.update_help(self.mode)
            return False
        if key == 'd':
            if self.aperture_center is not None:
                self.aperture_model.delete_aperture(self.aperture_id)
            self.stop_aperture()
            return True
        return False

    def handle_mouse(self, x, y):
        """
        Handle a mouse movement.

        We respond to the mouse by continuously updating the active aperture
        around it's center point to a width to match the mouse position.

        Parameters
        ----------
        x : float
            mouse x coordinate in data space
        y : float
            mouse y coordinate in data space
        """
        # we are in aperture mode
        if self.aperture_center:
            width = abs(self.aperture_center - x)
            if self.mode == 'width':
                self.left = self.aperture_center-width
                self.right = self.aperture_center+width
            elif self.mode == 'left':
                self.left = min(self.aperture_center, x)
            elif self.mode == 'right':
                self.right = max(self.aperture_center, x)
            elif self.mode == 'location':
                self.aperture_center = x
                self.right = max(self.right, x)
                self.left = min(self.left, x)
            self.aperture_model.adjust_aperture(self.aperture_id, self.aperture_center, self.left, self.right)

        self.last_x = x
        self.last_y = y
        return False

    def description(self):
        return "Edit <b>apertures</b> interactively"

    def update_help(self, mode):
        if self.mode == 'width':
            self.helptext_area.text = """
              Drag to desired aperture width<br/>
              <b>A</b> to set the aperture<br/>
              <b>[</b> to only edit the left edge (must remain left of the location)<br/>
              <b>]</b> to only edit the right edge (must remain right of the location)<br/>
              <b>L</b> to edit the location<br/>
              <b>D</b> to delete the aperture"""
        elif self.mode == 'left':
            self.helptext_area.text = """
              Drag left side to desired aperture width<br/>
              <b>A</b> to set the aperture<br/>
              <b>]</b> to only edit the right edge (must remain right of the location)<br/>
              <b>L</b> to edit the location<br/>
              <b>D</b> to delete the aperture"""
        elif self.mode == 'right':
            self.helptext_area.text = """
                  Drag right side to desired aperture width<br/>
                  <b>A</b> to set the aperture<br/>
                  <b>[</b> to only edit the left edge (must remain left of the location)<br/>
                  <b>L</b> to edit the location<br/>
                  <b>D</b> to delete the aperture"""
        elif self.mode == 'location':
            self.helptext_area.text = """
                      Drag to desired aperture location<br/>
                      <b>A</b> to set the aperture<br/>
                      <b>[</b> to only edit the left edge (must remain left of the location)<br/>
                      <b>]</b> to only edit the right edge (must remain right of the location)<br/>
                      <b>D</b> to delete the aperture"""
        else:
            self.helptext_area.text = self.helptext()

    def helptext(self):
        return """<b>A</b> to start the aperture<br/>
                  <b>F</b> to find a nearby peak to the cursor to start with<br/>
                  <b>[</b> to only edit the left edge (must remain left of the location)<br/>
                  <b>]</b> to only edit the right edge (must remain right of the location)<br/>
                  <b>L</b> to edit the location<br/>
                  <b>D</b> to delete the aperture"""


class BandTask(Task):
    """
    Task for operating on the bands.
    """
    def __init__(self, band_model, helptext):
        """
        Create a band task for the given :class:`GIBandModel`

        Parameters
        ----------
        band_model : :class:`GIBandModel`
            The band model to operate on with this task
        """
        self.band_model = band_model
        self.band_edge = None
        self.band_id = None
        self.helptext_area = helptext

    def start(self, x, y):
        """
        Start a new band with the current mouse position.

        This starts a band with one edge at the current x coordinate.

        Parameters
        ----------
        x : float
            x coordinate in dataspace for one edge of the band
        y : float
            y coordinate of the mouse, unused

        """
        (band_id, start, end) = self.band_model.find_band(x)
        if band_id is not None:
            self.band_id = band_id
            if (x-start) < (end-x):
                self.band_edge = end
            else:
                self.band_edge = start
            self.band_model.adjust_band(self.band_id, x, self.band_edge)
        else:
            self.band_edge = x
            self.band_id = self.band_model.band_id
            self.band_model.band_id += 1

    def stop(self):
        """
        Stop modifying the current band.

        """
        self.band_edge = None
        self.band_id = None
        self.band_model.finish_bands()

    def handle_key(self, key):
        """
        Handle a key press.

        For now, the band task only responds to 'b', causing it to stop
        modifying the active band.

        Parameters
        ----------
        key : char
            key that was pressed by the user.

        """
        if key == 'b':
            self.stop()
            return True
        if key == 'd':
            self.band_model.delete_band(self.band_id)
            self.stop()
            return True
        return False

    def handle_mouse(self, x, y):
        """
        Handle a mouse cursor move within the view.

        This receives updates for the mouse movement as long as
        the task is active.  We modify the other edge of the
        active band to this x value.

        Parameters
        ----------
        x : float
            x coordinate of mouse in data space
        y : float
            y coordinate of mouse in data space

        """
        # we are in band mode
        start = x
        end = self.band_edge
        self.band_model.adjust_band(self.band_id, start, end)
        return False

    def description(self):
        """
        Returns the description to use when offering this task from the top-level controller.

        Returns
        -------
            str description of the task
        """
        return "create a <b>band</b> with edge at cursor"

    def helptext(self):
        """
        Returns the help for this task for when it is active

        Returns
        -------
            str HTML help text for the task
        """
        return """Drag to desired band width.<br/>\n<b>b</b> to set the band<bt/>\n<b>d</b> to delete/cancel the band"""
