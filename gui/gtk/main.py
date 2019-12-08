from gui.gtk import (
    Gtk,
    ScrolledSceneView, SceneView, SceneBuffer,
    guidir,
)

import os

#------------------------------------------------------------------------------

def run(workset = None):
    
    draft, notes = len(workset) > 0 and workset[0].load() or (None, None)
    draft = SceneBuffer(draft)
    notes = SceneBuffer(notes)
    
    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(guidir, "glade/mawe.ui"))

    box = builder.get_object("SceneEditBox1")
    box.add(SceneView(notes, "Times 12"))

    tree = Gtk.TreeView(notes.marklist)
    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Name", renderer, text = 0)
    tree.append_column(column)
    
    pane = builder.get_object("SceneList1")
    pane.add(tree)
    
    marks = builder.get_object("MarkList")
    if marks: marks.set_buffer(draft.marklist)

    box = builder.get_object("SceneEditBox2")
    if box: box.add(SceneView(notes, "Times 12"))

    win = builder.get_object("window1")
    win.connect("destroy", Gtk.main_quit)
    win.show_all()

    Gtk.main()

