from gui.gtk import (
    Gtk, Gdk, Gio, GObject,
    DocBook,
    dialog,
    guidir,
)

from tools import *
from gui.gtk.factory import *
import os

###############################################################################
#
# Main window
#
###############################################################################

class MainWindow(Gtk.Window):

    def __init__(self, workset, new = False):
        super(MainWindow, self).__init__()

        self.style   = Gtk.CssProvider()
        self.context = Gtk.StyleContext()
        self.context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.style,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.style.load_from_path(os.path.join(guidir, "ui/mawe.css"))

        self.docs = DocBook()
        self.add(self.docs)

        self.connect("delete-event", lambda w, e: self.onDelete(w))

        ShortCut.bind(self, {
            "<Ctrl>Q": lambda *a: self.onDelete(self),
        })

        settings = config["Window"]
        #print(settings)
        #print(settings["Position"]["X"], settings["Position"]["Y"])
        #print(settings["Size"]["X"], settings["Size"]["Y"])
        if "Position" in settings: self.move(
            settings["Position"]["X"],
            settings["Position"]["Y"]
        )
        self.resize(
            settings["Size"]["X"],
            settings["Size"]["Y"]
        )

        workset = self.docs.open_defaults(workset)
        if new: self.docs.ui_new()

    #--------------------------------------------------------------------------
    
    def onDelete(self, widget):

        if not self.docs.exit(): return True

        try:
            settings = config["Window"]

            size = self.get_size()
            settings["Size"] = { "X": size.width, "Y": size.height }

            pos = self.get_position()
            settings["Position"] = { "X": pos.root_x, "Y": pos.root_y }

            config_save()
        except Exception:
            import traceback
            print(traceback.format_exc())
        Gtk.main_quit()

#------------------------------------------------------------------------------

def run(workset = None, new = False):
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    Gdk.threads_init()

    MainWindow(workset, new = new).show_all()

    Gtk.main()
