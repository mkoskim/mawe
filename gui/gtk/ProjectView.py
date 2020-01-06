###############################################################################
#
# Projects on file open view
#
###############################################################################

from gui.gtk import (
    Gtk, Gdk, Gio, GObject,
    dialog,
    guidir,
)

from tools import *
from gui.gtk.factory import *
from project import *
from project.Document import ET
from tools.config import *

import os, time

#------------------------------------------------------------------------------

class ProjectView(Gtk.Frame):

    __gsignals__ = {
        "file-activated" : (GObject.SIGNAL_RUN_LAST, None, (str,)),
    }

    def __init__(self, **kwargs):
        super(ProjectView, self).__init__(**kwargs)

        self.set_shadow_type(Gtk.ShadowType.NONE)

        self.store = Gtk.ListStore(str, str, str, str, str, int, int, int, str, str)

        projectlist = ProjectList(self.store) 
        projectlist.connect("row-activated", self.onRowActivated)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(projectlist)

        box = VBox(
            (scrolled, True),
        )
        self.add(box)

        self.worker = None
        self.refresh()

    def onRowActivated(self, tree, path, col, *args):
        filename = tree.get_model()[path][0]
        self.emit("file-activated", filename)
        
    def refresh(self):
        if not config["ProjectDir"]: return

        Manager._scan(config["ProjectDir"])

        searchdir = config["ProjectDir"]
        self.store.clear()
        for path, doc in Manager.projects.items():
            self.store.append([
                path,
                doc.title,
                doc.status, doc.deadline, doc.year,
                doc.words[0], doc.words[1], doc.words[2],
                doc.editor, os.path.relpath(path, searchdir),
            ])

#------------------------------------------------------------------------------

class ProjectList(Gtk.TreeView):

    def __init__(self, store, **kwargs):
        sorter = Gtk.TreeModelSort(store)
        sorter.set_sort_column_id(2, Gtk.SortType.DESCENDING)
        #self.treesorter.set_sort_func(0, self.cbSort)
        
        super(ProjectList, self).__init__(sorter, **kwargs)

        def dfNonZeros(col, cell, store, itr, args):
            words = store.get_value(itr, args)
            if words:
                cell.set_property("text", str(words))
            else:
                cell.set_property("text", "")

        def dfZeroAsMinus(col, cell, store, itr, args):
            words = store.get_value(itr, args)
            if words:
                cell.set_property("text", str(words))
            else:
                cell.set_property("text", "-")

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", renderer, text = 1)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Status", renderer, text = 2)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Deadline", renderer, text = 3)
        self.append_column(column)

        column = Gtk.TreeViewColumn("Words")
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1.0, 0.5)
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, dfZeroAsMinus, 5)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1.0, 0.5)
        renderer.set_property("foreground", "green")
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, dfNonZeros, 6)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1.0, 0.5)
        renderer.set_property("foreground", "red")
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, dfNonZeros, 7)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Year", renderer, text = 4)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Editor", renderer, text = 8)
        self.append_column(column)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Path", renderer, text = 9)
        column.set_property("expand", True)
        self.append_column(column)

