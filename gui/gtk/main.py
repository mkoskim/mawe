from gui.gtk import (
    Gtk,
    ScrolledSceneView, SceneView, SceneBuffer,
    guidir,
)

import os

#------------------------------------------------------------------------------

builder = None

#------------------------------------------------------------------------------

def splitToggled(widget, *args):
    splitpane = builder.get_object("SplitPane")
    splitpane.get_child2().set_visible(widget.get_active())

    sidepane = builder.get_object("EditorPane")
    sidepane.get_child1().set_visible(not widget.get_active())
    
#------------------------------------------------------------------------------

def run(workset = None):
    
    draft, notes = len(workset) > 0 and workset[0].load() or (None, None)
    draft = SceneBuffer(draft)
    notes = SceneBuffer(notes)
    
    global builder

    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(guidir, "glade/mawe.ui"))
    
    box = builder.get_object("SceneEditBox1")
    box.add(SceneView(draft, "Times 12"))

    marks = builder.get_object("MarkList")
    if marks: marks.set_buffer(draft.marklist)

    box = builder.get_object("SceneEditBox2")
    if box: box.add(SceneView(notes, "Times 12"))

    win = builder.get_object("window1")
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    Gtk.main()

