###############################################################################
#
# Pages for notebook holding opened files
#
###############################################################################

from gui.gtk import Gtk, Gdk, Pango, GtkSource, GObject
from tools import *
from gui.gtk.factory import *

class DocBookPage(Gtk.Frame):

    def __init__(self, notebook, name):
        super(DocBookPage, self).__init__()

        self.notebook = notebook

        self.name      = name
        self.tablabel  = Label(name, name = "tablabel")
        self.menulabel = Label(name, name = "menulabel")

        self.context = self.get_style_context()
        self.context.add_class("DocPage")

        self.connect_after("map",   lambda w: self.update_title())
        self.connect_after("unmap", lambda w: self.update_title())

    def update_title(self):
        self.notebook.set_window_title()

    def set_name(self, name):
        self.name = name
        self.tablabel.set_text(name)
        self.menulabel.set_text(name)
        self.update_title()

    def can_close(self): return True

