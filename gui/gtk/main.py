from gui.gtk import (
    Gtk,
    SceneView, SceneBuffer,
    guidir,
)

import os

#------------------------------------------------------------------------------

def run(content = None):

    buffer = SceneBuffer(content)

    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(guidir, "glade/mawe.ui"))
    
    box = builder.get_object("SceneEditBox1")
    box.pack_start(SceneView(buffer, "Times 12"), True, True, 0)
    #box.add(SceneView(buffer, "Times 12"))

    #box = builder.get_object("SceneEditBox2")
    #box.pack_start(SceneView(buffer, "Times 12"), True, True, 0)

    marks = builder.get_object("MarkList")
    marks.set_buffer(buffer.marklist)

    win = builder.get_object("window1")
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

