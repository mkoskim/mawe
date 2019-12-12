###############################################################################
#
# Some overrides
#
###############################################################################

from gui.gtk import (Gtk, Gdk, Gio)

class Button(Gtk.Button):

    @staticmethod
    def getarg(kwargs, name):
        if name in kwargs:
            result = kwargs[name]
            del kwargs[name]
            return result
        return None

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
        self.set_relief(Gtk.ReliefStyle.NONE)

    def disable(self):
        self.set_sensitive(False)
        
    def enable(self):
        self.set_sensitive(True)
        
class StockButton(Button):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        kwargs["use_stock"] = True
        super(StockButton, self).__init__(label, **kwargs)
        self.set_always_show_image(True)

class IconButton(Button):

    def __init__(self, icon, tooltip, **kwargs):
        super(IconButton, self).__init__(None, icon = icon, tooltip_text = tooltip, **kwargs)

class MenuButton(Gtk.MenuButton):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(MenuButton, self).__init__(label, **kwargs)

        if label:
            self.set_image(Button.icon2image("pan-down-symbolic"))
            self.set_image_position(Gtk.PositionType.RIGHT)

        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_always_show_image(True)

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

class Box(Gtk.Box):

    def __init__(self, **kwargs):
        super(Box, self).__init__(**kwargs)

class HBox(Gtk.HBox):

    def __init__(self, **kwargs):
        super(HBox, self).__init__(**kwargs)

class VBox(Gtk.VBox):

    def __init__(self, **kwargs):
        super(VBox, self).__init__(**kwargs)

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

class Label(Gtk.Label):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(Label, self).__init__(label, **kwargs)
        self.set_xalign(0.0)

#------------------------------------------------------------------------------

class HSeparator(Gtk.HSeparator):

    def __init__(self, **kwargs):
        super(HSeparator, self).__init__(**kwargs)

class VSeparator(Gtk.VSeparator):

    def __init__(self, **kwargs):
        super(VSeparator, self).__init__(**kwargs)

#------------------------------------------------------------------------------

def getHideControl(name, widget, **kwargs):

    def togglehide(button):
        if button.get_active():
            widget.show()
        else:
            widget.hide()

    button = ToggleButton(name, **kwargs)
    button.connect("toggled", togglehide)
    button.connect("map", togglehide)

    return button

class StackSwitcher(Gtk.StackSwitcher):

    def __init__(self, stack, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(StackSwitcher, self).__init__(**kwargs)
        self.set_stack(stack)
        #self.set_relief(Gtk.ReliefStyle.NONE)


