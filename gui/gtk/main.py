from gui.gtk import (
    Gtk,
    SceneView, SceneBuffer,
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

    buffer = SceneBuffer(content)

    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(guidir, "glade/mawe.ui"))
    
    box = builder.get_object("EditorPane")
    box.add2(SceneView(buffer, "Times 12"))
    #box.add2(SceneEdit(buffer))

    win = builder.get_object("window1")
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

