###############################################################################
#
# Factory functions, derived Gtk objects and so on.
#
###############################################################################

from gui.gtk import (Gtk, Gdk, Gio, GObject)

#------------------------------------------------------------------------------
# Shortcut binding
#------------------------------------------------------------------------------

class ShortCut:

    @staticmethod
    def bind(widget, table):

        def parse_table(table):
            lookup = { }
            for shortcut, item in table.items():
                key = Gtk.accelerator_parse(shortcut)
                if type(item) is dict:
                    lookup[key] = parse_table(item)
                else:
                    lookup[key] = item
            return lookup
            
        widget.combokeys = parse_table(table)
        widget.combokey = None
        widget.connect("key-press-event", ShortCut.onKeyPress)

    @staticmethod
    def onKeyPress(widget, event):
        mod = event.state & Gtk.accelerator_get_default_mod_mask()
        key = (event.keyval, mod)

        # print(Gtk.accelerator_name(event.keyval, mod))

        if widget.combokey is None:
            if not key in widget.combokeys: return False
            if type(widget.combokeys[key]) is dict:
                widget.combokey = widget.combokeys[key]
                return True
            elif widget.combokeys[key] is None:
                #self.parent.emit("key-press-event", event.copy())
                return True
            else:
                return widget.combokeys[key](mod, key)
        else:
            combo = widget.combokey
            widget.combokey = None
            if key in combo:
                return combo[key](mod, key)
            else:
                return False

#------------------------------------------------------------------------------

def _extract_arg(kwargs, name, default = None):
    if name in kwargs:
        result = kwargs[name]
        del kwargs[name]
        return result
    return default

def _set_relief(widget, kwargs):
    relief = _extract_arg(kwargs, "relief", Gtk.ReliefStyle.NONE)
    widget.set_relief(relief)

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
        _set_relief(self, kwargs)
        
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

def MenuButton(label, popover, **kwargs):
    if "visible" not in kwargs: kwargs["visible"] = True
    btn = Gtk.MenuButton(label, **kwargs)
    btn.set_popover(popover)

    #if label:
    #    btn.set_image(Button.icon2image("pan-down-symbolic"))
    #    btn.set_image_position(Gtk.PositionType.RIGHT)
    #btn.set_always_show_image(True)
    _set_relief(btn, kwargs)
    return btn

class ToggleButton(Gtk.ToggleButton):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        Button.geticon(kwargs)
        onclick = Button.getarg(kwargs, "onclick")
        
        super(ToggleButton, self).__init__(label = label, **kwargs)

        if onclick: self.connect("toggled", onclick)
        _set_relief(self, kwargs)

    def disable(self):
        self.set_sensitive(False)
        
    def enable(self):
        self.set_sensitive(True)
        
class RadioButton(Gtk.RadioButton):

    def __init__(self, label, group = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(RadioButton, self).__init__(label = label, group = group, **kwargs)
        _set_relief(self, kwargs)

#------------------------------------------------------------------------------

def _Boxed(box, *widgets, **kwargs):

    def pack(widget, spacing = 0):
        packtype, expand, pad = Gtk.PackType.START, False, spacing
        
        if widget is None:
            return
        elif type(widget) == tuple:
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
            if cell is None:
                continue
            elif type(cell) is tuple:
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

def Popover(widget, **kwargs):
    popover = Gtk.Popover(**kwargs)
    popover.add(widget)
    widget.show_all()
    return popover

#------------------------------------------------------------------------------

def Paned(widget1, widget2, **kwargs):
    pane = Gtk.Paned(**kwargs)
    pane.add1(widget1)
    pane.add2(widget2)
    return pane

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
    return switch

