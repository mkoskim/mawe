from gui.gtk import Gtk, SceneGroupEdit, GtkSource
import os

#------------------------------------------------------------------------------

def run(filename = None):

    print("Filename:", filename)
    if filename:
        content = open(filename).read()
    else:
        content = None

    win = SceneGroupEdit(content)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

