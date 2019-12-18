###############################################################################
#
# Factory functions, derived Gtk objects and so on.
#
###############################################################################

from gui.gtk import (Gtk, Gdk, Gio, GObject)

#------------------------------------------------------------------------------

def _extract_arg(kwargs, name, default = None):
    if name in kwargs:
        result = kwargs[name]
        del kwargs[name]
        return result
    return default

#------------------------------------------------------------------------------

class EntryBuffer(Gtk.EntryBuffer):

    __gsignals__ = {
        "changed" : (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def __init__(self, key = None):
        super(EntryBuffer, self).__init__()

        self.key = key
        self.connect("deleted-text",  lambda e, pos, n: e.emit("changed"))
        self.connect("inserted-text", lambda e, pos, t, n: e.emit("changed"))


#------------------------------------------------------------------------------

class Button(Gtk.Button):

    @staticmethod
    def getarg(kwargs, name): return _extract_arg(kwargs, name)

    @staticmethod
    def icon2image(name):
        icon = Gio.ThemedIcon(name=name)
        return Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
    
    @staticmethod
    def geticon(kwargs):
        name = Button.getarg(kwargs, "icon")
        if name:
            kwargs["image"] = Button.icon2image(name)
            kwargs["always-show-image"] = True

    def __init__(self, label = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True

        Button.geticon(kwargs)
        onclick = Button.getarg(kwargs, "onclick")
        
        super(Button, self).__init__(label, **kwargs)

        if onclick: self.connect("clicked", onclick)
        if "relief" in kwargs:
            self.set_relief(kwargs["relief"])
        else:
            self.set_relief(Gtk.ReliefStyle.NONE)

    def disable(self):
        self.set_sensitive(False)
        
    def enable(self):
        self.set_sensitive(True)
        
def StockButton(label, **kwargs):
    kwargs["use_stock"] = True
    btn = Button(label, **kwargs)
    btn.set_always_show_image(True)
    return btn

def IconButton(icon, tooltip, **kwargs):
    return Button(None, icon = icon, tooltip_text = tooltip, **kwargs)

def MenuButton(label, **kwargs):
    if "visible" not in kwargs: kwargs["visible"] = True
    btn = Gtk.MenuButton(label, **kwargs)

    if label:
        btn.set_image(Button.icon2image("pan-down-symbolic"))
        btn.set_image_position(Gtk.PositionType.RIGHT)

    btn.set_relief(Gtk.ReliefStyle.NONE)
    btn.set_always_show_image(True)
    return btn

class ToggleButton(Gtk.ToggleButton):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        Button.geticon(kwargs)
        onclick = Button.getarg(kwargs, "onclick")
        
        super(ToggleButton, self).__init__(label = label, **kwargs)

        if onclick: self.connect("toggled", onclick)
        self.set_relief(Gtk.ReliefStyle.NONE)

    def disable(self):
        self.set_sensitive(False)
        
    def enable(self):
        self.set_sensitive(True)
        
class RadioButton(Gtk.RadioButton):

    def __init__(self, label, group = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(RadioButton, self).__init__(label = label, group = group, **kwargs)
        self.set_relief(Gtk.ReliefStyle.NONE)

#------------------------------------------------------------------------------

def _Boxed(box, *widgets, **kwargs):

    def pack(widget, spacing = 0):
        packtype, expand, pad = Gtk.PackType.START, False, spacing
        
        if type(widget) == tuple:
            widget, args = widget[0], widget[1:]

            for arg in args:
                if   type(arg) == Gtk.PackType: packtype = arg
                elif type(arg) == int:  pad = arg
                elif type(arg) == bool: expand = arg
                else: pass

        if packtype == Gtk.PackType.START:
            box.pack_start(widget, expand, expand, pad)
        else:
            box.pack_end(widget, expand, expand, pad)

    spacing = _extract_arg(kwargs, "spacing", 0)

    if len(widgets):
        for widget in widgets[:-1]: pack(widget, spacing)
        pack(widgets[-1])
    
    return box

def HBox(*widgets, **kwargs): return _Boxed(Gtk.HBox(**kwargs), *widgets)
def VBox(*widgets, **kwargs): return _Boxed(Gtk.VBox(**kwargs), *widgets)

def Grid(*widgets, **kwargs):
    grid = Gtk.Grid()

    if "column_spacing" in kwargs:
        grid.set_column_spacing(kwargs["column_spacing"])

    if "row_spacing" in kwargs:
        grid.set_row_spacing(kwargs["row_spacing"])

    if "expand_column" in kwargs:
        expand_column = kwargs["expand_column"]

    for y, row in enumerate(widgets):
        for x, cell in enumerate(row):
            if type(cell) is tuple:
                cell, width, height = cell
            else:
                cell, width, height = (cell, 1, 1)
            grid.attach(cell, x, y, width, height)

            if x == expand_column:
                cell.set_hexpand(True)
                cell.set_halign(Gtk.Align.FILL)

    return grid

#------------------------------------------------------------------------------

# Create dual page stack: return stack & switcher
def DuoStack(label, page1, page2, **kwargs):

    stack = Gtk.Stack()
    stack.add_named(page1, "1")
    stack.add_named(page2, "2")

    def switchStack(button, stack):
        name  = button.get_active() and "2" or "1"
        child = stack.get_child_by_name(name)
        stack.set_visible_child(child)
        
    switcher = ToggleButton(label, **kwargs)
    switcher.connect("toggled", lambda w: switchStack(w, stack))

    return stack, switcher

#------------------------------------------------------------------------------

def Framed(widget, **kwargs):
    frame = Gtk.Frame(**kwargs)
    frame.add(widget)
    #frame.set_border_width(1)
    #frame.set_shadow_type(Gtk.ShadowType.IN)
    return frame

#------------------------------------------------------------------------------

def Label(label, **kwargs):
    if "visible" not in kwargs: kwargs["visible"] = True
    widget = Gtk.Label(label, **kwargs)
    widget.set_xalign(0.0)
    return widget

#------------------------------------------------------------------------------

class HSeparator(Gtk.HSeparator):

    def __init__(self, **kwargs):
        super(HSeparator, self).__init__(**kwargs)

class VSeparator(Gtk.VSeparator):

    def __init__(self, **kwargs):
        super(VSeparator, self).__init__(**kwargs)

#------------------------------------------------------------------------------

def HideControl(name, widget, **kwargs):

    def togglehide(button):
        if button.get_active():
            widget.show()
        else:
            widget.hide()

    button = ToggleButton(name, **kwargs)
    button.connect("toggled", togglehide)
    button.connect("map", togglehide)

    return button

def StackSwitcher(stack, **kwargs):
    if "visible" not in kwargs: kwargs["visible"] = True
    switch = Gtk.StackSwitcher(**kwargs)
    switch.set_stack(stack)
    #self.set_relief(Gtk.ReliefStyle.NONE)
    return switch

