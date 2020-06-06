###############################################################################
#
# Document open view
#
###############################################################################

from gui.gtk import Gtk, Gdk, Pango, GtkSource, GObject
from gui.gtk import DocBookPage, ProjectView
from tools import *
from gui.gtk.factory import *

class OpenTab(DocBookPage):

    def __init__(self, notebook):
        super(OpenTab, self).__init__(notebook, "Open file")

        chooser = Gtk.FileChooserWidget()
        chooser.set_create_folders(True)
        chooser.connect("file-activated", self.onChooser)
        chooser.connect("map", self.dir_restore)
        chooser.connect("unmap", self.dir_store)

        #self.dir_restore(chooser)
        #chooser.set_extra_widget(Button("New", onclick = lambda w: self.openNew()))

        manager = ProjectView()
        manager.connect("file-activated", self.onProjectSelect)

        stack    = Gtk.Stack()
        stack.add_titled(chooser, "files", "Files")
        stack.add_titled(manager, "projects", "Projects")
        self.stack = stack

        toolbar = HBox(
            StackSwitcher(stack),
            #(Button("Recent", relief = Gtk.ReliefStyle.NORMAL), False, 6),
            StockButton("gtk-new", relief = Gtk.ReliefStyle.NORMAL, onclick = self.onNew),
            #(VSeparator(), False, 2),
            #(Label("Search:"), False, 6),
            #Gtk.Entry(text = config["ProjectDir"]),
            
            spacing = 6,
        )

        box = VBox(
            toolbar,
            (stack, True),
            
            spacing = 3,
        )
        self.add(box)
        self.show_all()

        if config["Directories"]["Projects"] is None:
            stack.set_visible_child_name("files")
        else:
            stack.set_visible_child_name("projects")

        ShortCut.bind(self, {
            # "<Ctrl>S": lambda *a: self.ui_save(),
            "Escape": lambda *a: self.ui_cancel(),
            "F5": lambda *a: self.ui_refresh(),
        })

    def onNew(self, widget):
        self.notebook.ui_new()

    def onProjectSelect(self, widget, filename):
        self.notebook.ui_new(filename)
        return True

    def onChooser(self, chooser):
        filename = chooser.get_filename()
        self.onProjectSelect(chooser, filename)

    def dir_store(self, chooser):
        config["Directories"]["Open"] = chooser.get_current_folder()

    def dir_restore(self, chooser):
        chooser.set_current_folder(config["Directories"]["Open"])

    def ui_cancel(self):
        self.notebook.ui_close(self)
        return True

    def ui_refresh(self):
        if self.stack.get_visible_child_name() == "projects":
            self.stack.get_visible_child().refresh()
        return True
