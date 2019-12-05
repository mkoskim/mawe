from gui.gtk import (
    Gtk,
    SceneGroupEdit, SceneGroupBuffer,
    guidir,
)

import os

#------------------------------------------------------------------------------

def run(filename = None):

    print("Filename:", filename)
    if filename:
        content = open(filename).read()
    else:
        content = None

    buffer = SceneGroupBuffer(content)

    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(guidir, "glade/mawe.glade"))
    
    box = builder.get_object("paned1")
    box.add1(SceneGroupEdit(buffer))
    box.add2(SceneGroupEdit(buffer))

    win = builder.get_object("window1")
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

