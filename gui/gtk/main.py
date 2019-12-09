from gui.gtk import (
    Gtk, Gdk, Gio,
    ScrolledSceneView, SceneView, SceneBuffer,
    guidir,
)

import os

###############################################################################
#
# Some overrides
#
###############################################################################

class Button(Gtk.Button):

    def __init__(self, label = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True

        if "icon" in kwargs:
            icon = Gio.ThemedIcon(name=kwargs["icon"])
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            kwargs["image"] = image
            del kwargs["icon"]
            kwargs["always-show-image"] = True

        onclick = None
        if "onclick" in kwargs:
            onclick = kwargs["onclick"]
            del kwargs["onclick"]

        super(Button, self).__init__(label, **kwargs)

        if onclick: self.connect("clicked", lambda w: onclick())
        self.set_relief(Gtk.ReliefStyle.NONE)
        
class StockButton(Button):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        kwargs["use_stock"] = True
        super(StockButton, self).__init__(label, **kwargs)
        self.set_always_show_image(True)

class MenuButton(Gtk.MenuButton):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(MenuButton, self).__init__(label, **kwargs)

        if label:
            icon = Gio.ThemedIcon(name="pan-down-symbolic")
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            self.set_image(image)
            self.set_image_position(Gtk.PositionType.RIGHT)

        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_always_show_image(True)

class Label(Gtk.Label):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(Label, self).__init__(label, **kwargs)

class Box(Gtk.Box):

    def __init__(self, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(Box, self).__init__(**kwargs)

class HBox(Gtk.HBox):

    def __init__(self, **kwargs):
        #if "visible" not in kwargs: kwargs["visible"] = True
        super(HBox, self).__init__(**kwargs)

#------------------------------------------------------------------------------

def add_shortcuts(widget, table):
    accel = Gtk.AccelGroup()
    widget.add_accel_group(accel)

    for shortcut, fn in table:
        key, mod = Gtk.accelerator_parse(shortcut)
        accel.connect(key, mod, 0, fn)

###############################################################################
#
# Notebook to hold workset files
#
###############################################################################

class DocNotebook(Gtk.Notebook):

    def __init__(self):
        super(DocNotebook, self).__init__()

        self.set_scrollable(True)
        
        self.opentab = DocOpen()
        #self.openbtn = StockButton("gtk-open", onclick = self.open)
        self.openbtn = Button(
            icon = "document-open-symbolic",
            tooltip_text = "Open file",
            onclick = self.open,
        )
        newbtn = Button(
            icon = "document-new-symbolic",
            tooltip_text = "New file",
            onclick = self.new,
        )
          
        start = Box()
        start.pack_start(MenuButton("<Workset>"), False, False, 0)
        start.pack_start(self.openbtn, False, False, 1)
        self.set_action_widget(start, Gtk.PackType.START)

        end = Box()
        end.pack_start(newbtn, False, False, 1)
        self.set_action_widget(end, Gtk.PackType.END)

        self.connect("switch-page", self.onSwitchPage)

    def add_page(self, name, child):
        label = HBox()
        label.pack_start(Label(name), True, False, 0)
        label.pack_start(Button(
            icon = "window-close-symbolic",
            image_position = Gtk.PositionType.RIGHT,
            onclick = lambda: self.close(child),
        ), False, False, 0)

        page = self.append_page(child, label)
        self.set_tab_reorderable(child, True)
        self.child_set_property(child, "tab-expand", True)
        self.child_set_property(child, "tab-fill", True)
        child.show()
        self.set_current_page(page)

    def load(self, doc):
        self.add_page(doc.name, DocView(doc))

    def new(self):
        self.add_page("New story", DocView())

    def close(self, child):
        if child == self.opentab:
            self.opentab.hide()
            self.openbtn.show()
        else:
            page = self.page_num(child)
            self.remove_page(page)

    def open(self):
        page = self.page_num(self.opentab)
        if page < 0:
            self.add_page("Open file...", self.opentab)
        else:
            self.opentab.show()
            
        self.reorder_child(self.opentab, 0)
        self.set_current_page(0)
            
        self.openbtn.hide()

    def onSwitchPage(self, notebook, child, pagenum):
        if child == self.opentab: return
        if self.page_num(self.opentab):
            self.opentab.hide()
            self.openbtn.show()

###############################################################################
#
# Document view
#
###############################################################################

class DocView(Gtk.Frame):

    def __init__(self, doc = None):
        super(DocView, self).__init__()
        
        if doc:
            draft, notes = doc.load()
        else:
            draft, notes = (None, None)

        self.draftbuf = SceneBuffer(draft)
        self.notesbuf = SceneBuffer(notes)

        text = ScrolledSceneView(self.draftbuf, "Times 12")
        text.view.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(65535, 65535, 65535))
        text.set_min_content_width(400)
        #text.set_max_content_width(800)
        text.set_min_content_height(400)

        pane = Gtk.Paned()
        pane.add2(text)
        
        tree = Gtk.TreeView(self.draftbuf.marklist)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text = 0)
        tree.append_column(column)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(tree)
        scrolled.set_min_content_width(200)
        
        pane.add1(scrolled)
        self.add(pane)
        self.show_all()

###############################################################################
#
# Document open view
#
###############################################################################

class DocOpen(Gtk.Frame):

    def __init__(self):
        super(DocOpen, self).__init__()

###############################################################################
#
# Main window
#
###############################################################################

class MainWindow(Gtk.Window):

    def __init__(self, docs):
        super(MainWindow, self).__init__()
        
        self.docs = DocNotebook()
        self.add(self.docs)

        self.connect("destroy", Gtk.main_quit)

        add_shortcuts(self, [
            ("<Ctrl>Q", Gtk.main_quit),
            ("<Ctrl>O", lambda a, w, key, mod: self.docs.open()),
        ])

        if docs:
            for doc in docs: self.load(doc)
        else:
            self.new()

    def load(self, doc):
        self.docs.load(doc)

    def new(self):
        self.docs.new()

#------------------------------------------------------------------------------

def _load(filename, workset):

    draft, notes = len(workset) > 0 and workset[0].load() or (None, None)
    draft = SceneBuffer(draft)
    notes = SceneBuffer(notes)
    
    builder = Gtk.Builder()
    builder.add_from_file(os.path.join(guidir, filename))

    box = builder.get_object("SceneEditBox1")
    box.add(SceneView(draft, "Times 12"))
    
    tree = Gtk.TreeView(draft.marklist)
    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Name", renderer, text = 0)
    tree.append_column(column)
    
    pane = builder.get_object("SceneList1")
    pane.add(tree)
    
    marks = builder.get_object("MarkList")
    if marks: marks.set_buffer(draft.marklist)

    box = builder.get_object("SceneEditBox2")
    if box: box.add(SceneView(notes, "Times 12"))

    return builder.get_object("window1")

#------------------------------------------------------------------------------

def run(workset = None):
    
    #win = _load("glade/mawe.ui", workset)
    win = MainWindow(workset)
    win.show_all()

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

