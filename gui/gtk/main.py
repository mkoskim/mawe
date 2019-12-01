from gui.gtk import Gtk, SceneGroupEdit

#------------------------------------------------------------------------------

def run():
    win = SceneGroupEdit()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

