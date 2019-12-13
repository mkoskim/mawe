from gui.gtk import (
    Gtk, Gdk, Gio,
    ScrolledSceneView, SceneView,
    ScrolledSceneList, SceneList,
    SceneBuffer,
    dialog,
    guidir,
)

from tools import *
from gui.gtk.overrides import *
import project
import os

#------------------------------------------------------------------------------

def run(workset = None):

    MainWindow(workset).show_all()

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

###############################################################################
#
# Notebook to hold workset files
#
###############################################################################

class DocNotebook(Gtk.Notebook):

    def __init__(self):
        super(DocNotebook, self).__init__(name = "DocNotebook")

        self.set_scrollable(True)
        self.popup_enable()

        self.opentab = DocOpen(self)
        self.openbtn = StockButton("gtk-open", onclick = lambda w: self.ui_open())
        self.openbtn.set_property("tooltip_text", "Open document")

        start = Box(visible = True)
        #start.pack_start(MenuButton("<Workset>"), False, False, 0)
        #start.pack_start(newbtn, False, False, 1)
        start.pack_start(IconButton("open-menu-symbolic", "Open menu"), False, False, 0)
        # Menu items
        # - Preferences
        # - Save all
        # - Close all
        # - Quit
        start.pack_start(self.openbtn, False, False, 1)
        start.pack_start(StockButton("gtk-help", onclick = lambda w: self.ui_help()), False, False, 0)

        self.set_action_widget(start, Gtk.PackType.START)

        end = Box(visible = True)
        self.set_action_widget(end, Gtk.PackType.END)

        self.connect_after("switch-page", self.onSwitchPage)

    def get_current_child(self):
        page = self.get_current_page()
        child = self.get_nth_page(page)
        if child and not child.get_visible(): return None
        return child

    def add_page(self, child, prepend = False):
        label = HBox()
        label.pack_start(child.tablabel, True, False, 4)
        label.pack_start(Button(
            icon = "window-close-symbolic",
            name = "round-btn",
            tooltip_text = "Close document",
            image_position = Gtk.PositionType.RIGHT,
            onclick = lambda w: self.ui_close(child),
            ),
            False, False, 0
        )

        if prepend:
            page = self.prepend_page_menu(child, label, child.menulabel)
        else:
            page = self.append_page_menu(child, label, child.menulabel)

        self.set_tab_reorderable(child, True)
        #self.child_set_property(child, "tab-expand", True)
        #self.child_set_property(child, "tab-fill", True)

        child.show_all()
        self.set_current_page(page)
        return page

    def add(self, doc):
        self.add_page(DocView(self, doc))

    def can_close(self):
        #print("Pages:", self.get_n_pages())
        for i in range(self.get_n_pages()):
            child = self.get_nth_page(i)
            if not child.can_close(): return False
        return True

    def save_all(self):
        pass

    def close_all(self):
        pass

    def exit(self):
        pass

    def ui_help(self):
        doc = project.Project.open(os.path.join(guidir, "ui/help.txt")).load()
        doc.name = "Instructions"
        doc.origin = None
        self.add(doc)

    def ui_new(self, filename = None):
        if filename:
            doc = project.Project.open(filename).load()
        else:
            doc = project.Document(tree = project.Document.empty("New Story"))
        self.add(doc)

    def ui_save(self):
        child = self.get_current_child()
        if type(child) is DocView:
            child.ui_save()

    def ui_close(self, child = None):
        if child is None: child = self.get_current_child();
        if child == self.opentab:
            self.opentab.hide()
            self.openbtn.enable()
            return False

        if type(child) is DocView:
            if not child.can_close(): return False
            child.onUnmap(child)

        self._remove_child(child)
        return True

    def _remove_child(self, child):
        page = self.page_num(child)
        if page != -1: self.remove_page(page)

    def ui_open(self):
        page = self.page_num(self.opentab)
        if page < 0:
            self.add_page(self.opentab, prepend = False)
        else:
            self.opentab.show()
            self.reorder_child(self.opentab, -1)
            self.set_current_page(-1)

        self.openbtn.disable()

    def onSwitchPage(self, notebook, child, pagenum):
        if child == self.opentab: return
        if self.page_num(self.opentab) != -1:
            self.opentab.hide()
            self.openbtn.enable()
        self.set_window_title()

    def set_window_title(self):
        child = self.get_current_child()
        name  = child and child.name or None
        self.get_toplevel().set_title((name and name + " - " or "") + "mawe")

###############################################################################
#
# Pages for doc notebook
#
###############################################################################

class DocPage(Gtk.Frame):

    def __init__(self, notebook, name):
        super(DocPage, self).__init__()

        self.notebook = notebook

        self.name      = name
        self.tablabel  = Label(name, name = "tablabel")
        self.menulabel = Label(name, name = "menulabel")

        self.context = self.get_style_context()
        self.context.add_class("DocPage")

        self.connect_after("map",   lambda w: self.update_title())
        self.connect_after("unmap", lambda w: self.update_title())

    def update_title(self):
        self.notebook.set_window_title()

    def set_name(self, name):
        self.name = name
        self.tablabel.set_text(name)
        self.menulabel.set_text(name)
        self.update_title()

    def can_close(self): return True

###############################################################################
#
# Document open view
#
###############################################################################

class DocOpen(DocPage):

    def __init__(self, notebook):
        super(DocOpen, self).__init__(notebook, "Open file")

        chooser = Gtk.FileChooserWidget()
        chooser.set_create_folders(True)

        chooser.connect("file-activated", self.onChooser)

        self.chooserDir = os.getcwd()
        chooser.connect("map", self.restoreDirectory)
        chooser.connect("unmap", self.storeDirectory)

        #chooser.set_extra_widget(Button("New", onclick = lambda w: self.openNew()))

        text = Gtk.TextView()
        for path in project.Manager.projects:
            text.get_buffer().insert_at_cursor(path + "\n")
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(text)
        manager = scrolled

        stack = Gtk.Stack()
        stack.add_titled(chooser, "files", "Files")
        stack.add_titled(manager, "projects", "Projects")

        toolbar = HBox()
        toolbar.pack_start(StackSwitcher(stack), False, False, 1)
        toolbar.pack_start(StockButton("gtk-new", onclick = self.onNew), False, False, 1)

        box = VBox()
        box.pack_start(toolbar, False, False, 1)
        box.pack_start(stack, True, True, 1)
        self.add(box)
        self.show_all()

    def onNew(self, widget):
        self.notebook.ui_new()

    def onChooser(self, chooser):
        filename = chooser.get_filename()
        self.notebook.ui_new(filename)

    def storeDirectory(self, chooser):
        self.chooserDir = chooser.get_current_folder()

    def restoreDirectory(self, chooser):
        chooser.set_current_folder(self.chooserDir)

###############################################################################
#
# Document view
#
###############################################################################

class DocView(DocPage):

    #--------------------------------------------------------------------------

    def __init__(self, notebook, doc):
        super(DocView, self).__init__(notebook, doc.name)

        self.doc = doc
        self.dirty = False

        print("Filename:", doc.filename)
        print("Origin:", doc.origin)

        self.draftbuf = self.set_buffer(self.doc.root.find("./body/part"))
        self.notesbuf = self.set_buffer(self.doc.root.find("./notes/part"))

        # Try to get rid of these
        self.draftview = ScrolledSceneView(self.draftbuf, "Times 12")
        self.notesview = ScrolledSceneView(self.notesbuf, "Times 12")
        self.scenelist = ScrolledSceneList(self.draftbuf, self.draftview)

        self.pane = Gtk.Paned()
        self.pane.add2(self.create_view())
        self.pane.add1(self.create_index())

        self.add(self.pane)

        self.connect("map", self.onMap)
        self.connect("unmap", self.onUnmap)
        self.connect("key-press-event", self.onKeyPress)

        #self.draftview.grab_focus()

    def set_buffer(self, content):
        def onBufModified(self, buf):
            if buf.get_modified(): self.set_dirty()

        buf = SceneBuffer(content)
        buf.connect("modified-changed", lambda buf: onBufModified(self, buf))
        return buf

    #--------------------------------------------------------------------------

    def onKeyPress(self, widget, event):
        mods = event.state & Gtk.accelerator_get_default_mod_mask()
        key = Gtk.accelerator_name(
            event.keyval,
            mods,
        )
        if key == "<Alt>1": # TODO: <Alt>Left
            self.scenelist.grab_focus()
            return True
        elif key == "<Alt>2": # TODO: <Alt>Right
            self.draftview.grab_focus()
            return True

    #--------------------------------------------------------------------------
    # Paned control
    #--------------------------------------------------------------------------

    position = -1

    def onMap(self, widget):
        if DocView.position < 0: return
        self.pane.set_position(DocView.position)
        #print("Set pos:", DocView.position)

    def onUnmap(self, widget):
        DocView.position = self.pane.get_position()
        #print("Update pos:", DocView.position)

        # Untouched empty files can be removed without questions
        if not self.get_dirty() and self.doc.origin is None:
            self.notebook._remove_child(self)

    #--------------------------------------------------------------------------

    def set_name(self, text = None):
        if text: self.doc.find("./body/head/title").text = text
        super(DocView, self).set_name((self.get_dirty() and "*" or "") + self.doc.name)

    def get_dirty(self): return self.dirty

    def set_dirty(self, status = True):
        if self.dirty != status:
            self.dirty = status
            self.set_name()

    #--------------------------------------------------------------------------
    # Saving
    #--------------------------------------------------------------------------

    def can_close(self):
        if self.get_dirty():
            answer = dialog.SaveOrDiscard(self,
                "'%s' not saved. Save or discard changes?" % self.doc.name
            )
            if answer == Gtk.ResponseType.CANCEL: return False
            if answer == Gtk.ResponseType.YES:
                if not self.ui_save(): return False
        return True

    def ui_save(self):
        if self.doc.filename is None:
            name = dialog.SaveAs(self, self.doc.origin)
            if name is None: return False
            self.doc.filename = name
        self._save()
        return True

    def ui_saveas(self):
        name = self.SaveAs(self, self.doc.origin)
        if name is None: return False
        self.doc.filename = name
        self._save()
        return True

    def _save(self):
        print("Saving as:", self.doc.filename)

        draft = self.draftbuf.to_mawe()
        notes = self.notesbuf.to_mawe()

        self.draftbuf.revert(draft)

        #from project.Document import ET
        #ET.dump(draft)

        self.set_dirty(False)
        self.draftbuf.set_modified(False)
        self.notesbuf.set_modified(False)

        self.doc.origin = self.doc.filename
        self.folderbtn.enable()

    def ui_revert(self):
        if self.get_dirty():
            answer = dialog.YesNo(self,
                "You will loose all modifications since last save.\n" +
                "Do you want to continue?"
            )
            if answer != Gtk.ResponseType.YES: return
        self.draftbuf.revert(self.doc.root.find("./body/part"))
        self.notesbuf.revert(self.doc.root.find("./notes/part"))
        self.set_dirty(False)

    #--------------------------------------------------------------------------

    def create_view(self):

        def titleeditor():
            titleedit = Gtk.Frame()
            #titleedit.set_label("Edit title")
            titleedit.set_shadow_type(Gtk.ShadowType.IN)
            titleedit.set_border_width(1)
            titleedit.add(Label("Title"))
            return titleedit, getHideControl(
                "Title",
                titleedit,
                tooltip_text = "Edit story header info"
            )

        def exportsettings():
            # Add backcover text here. Remember to store it, too.
            titleedit = Gtk.Frame()
            #titleedit.set_label("Edit title")
            titleedit.set_shadow_type(Gtk.ShadowType.IN)
            titleedit.set_border_width(1)
            titleedit.add(Label("Export"))
            return titleedit, getHideControl("Export", titleedit)

        def bottombar():
            box = HBox()
            box.pack_start(Button("..."), False, False, 0)

            box.pack_start(Label(""), True, True, 0)

            box.pack_start(self.draftbuf.stats.words, False, False, 2)
            box.pack_start(self.draftbuf.stats.chars, False, False, 4)

            return box

        def topbar():
            box = HBox()

            dialogs = VBox()
            dialogs.pack_start(box, False, False, 0)

            titleedit,  titleswitch  = titleeditor()
            exportview, exportswitch = exportsettings()

            dialogs.pack_start(titleedit,  False, False, 0)
            dialogs.pack_start(exportview, False, False, 0)

            selectnotes = ToggleButton("Notes")

            def switchBuffer(self, widget):
                if not widget.get_active():
                    self.draftview.set_buffer(self.draftbuf)
                    self.scenelist.set_buffer(self.draftbuf)
                else:
                    self.draftview.set_buffer(self.notesbuf)
                    self.scenelist.set_buffer(self.notesbuf)

            selectnotes = ToggleButton("Notes", onclick = lambda w: switchBuffer(self, w))

            # Menu items. REMEMBER! We can use left side, too, for example for exporting,
            # history entries and so on!
            # - Export
            # - Open containing folder
            # - Save
            # - Save as
            # - Revert
            # - Close

            box.pack_start(IconButton("open-menu-symbolic", "Open menu"), False, False, 1)
            box.pack_start(titleswitch, False, False, 1)
            box.pack_start(exportswitch, False, False, 0)
            #box.pack_start(VSeparator(), False, False, 2)
            #box.pack_start(Button("Save"), False, False, 0)
            box.pack_start(Button("Revert", onclick = lambda w: self.ui_revert()), False, False, 0)
            box.pack_start(VSeparator(), False, False, 2)

            box.pack_start(Label(""), True, True, 0)

            self.folderbtn = Button(
                "Folder",
                tooltip_text="Open document folder",
                onclick = lambda w: xdgfolder(self.doc.filename and self.doc.filename or self.doc.origin)
            )
            if self.doc.filename is None and self.doc.origin is None:
                self.folderbtn.disable()

            box.pack_start(self.folderbtn, False, False, 0)
            box.pack_start(selectnotes, False, False, 0)
            box.pack_start(VSeparator(), False, False, 2)
            return dialogs

        def view():
            text = self.draftview
            text.view.set_name("draftview")
            text.set_min_content_width(400)
            #text.set_max_content_width(800)
            text.set_min_content_height(400)
            text.set_border_width(1)
            text.set_shadow_type(Gtk.ShadowType.IN)
            return text

        box = VBox()
        box.pack_start(topbar(), False, False, 1)
        box.pack_start(view(), True, True, 0)
        box.pack_end(bottombar(), False, False, 0)
        return box

    def create_index(self):

        def topbar(switcher):
            box = HBox()
            box.pack_start(switcher, False, False, 1)
            return box

        def scenelist():
            box = VBox()
            #box.pack_start(toolbar(), False, False, 0)
            box.pack_start(self.scenelist, True, True, 0)
            self.scenelist.set_border_width(1)
            self.scenelist.set_shadow_type(Gtk.ShadowType.IN)
            return box

        def notes():
            text = self.notesview

            #text.set_min_content_width(400)
            #text.set_max_content_width(800)
            #text.set_min_content_height(400)

            text.set_border_width(1)
            text.set_shadow_type(Gtk.ShadowType.IN)
            return text

        def bottombar():
            box = HBox()
            box.pack_start(Button("..."), False, False, 0)
            return box

        stack, switcher = DuoStack("Notes", scenelist(), notes())

        box = VBox()
        box.pack_start(topbar(switcher), False, False, 1)
        box.pack_start(stack, True, True, 0)
        box.pack_end(bottombar(), False, False, 0)
        return box

###############################################################################
#
# Main window
#
###############################################################################

def add_shortcuts(widget, table):
    accel = Gtk.AccelGroup()
    widget.add_accel_group(accel)

    for shortcut, fn in table:
        key, mod = Gtk.accelerator_parse(shortcut)
        accel.connect(key, mod, 0, fn)

class MainWindow(Gtk.Window):

    def __init__(self, workset):
        super(MainWindow, self).__init__()

        self.style   = Gtk.CssProvider()
        self.context = Gtk.StyleContext()
        self.context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.style,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.style.load_from_path(os.path.join(guidir, "ui/mawe.css"))

        self.docs = DocNotebook()
        self.add(self.docs)

        self.connect("delete-event", lambda w, e: self.onDelete(w))

        add_shortcuts(self, [
            ("<Ctrl>Q", lambda *a: self.onDelete(self)),

            ("<Ctrl>O", lambda *a: self.docs.ui_open()),
            ("<Ctrl>S", lambda *a: self.docs.ui_save()),
            ("<Ctrl>W", lambda *a: self.docs.ui_close()),

            ("F1", lambda *a: self.docs.ui_help()),
        ])

        settings = config["Window"]
        if "Position" in settings: self.move(
            settings["Position"]["X"],
            settings["Position"]["Y"]
        )
        self.resize(
            settings["Size"]["X"],
            settings["Size"]["Y"]
        )

        DocView.position = config["DocView"]["Pane"]

        if workset:
            for p in workset: self.docs.add(p.load())
        elif len(project.Manager.projects):
            self.docs.ui_open()
        else:
            self.docs.ui_new()

    def onDelete(self, widget):

        if not self.docs.can_close(): return True

        try:
            settings = config["Window"]

            size = self.get_size()
            settings["Size"] = { "X": size.width, "Y": size.height }

            pos = self.get_position()
            settings["Position"] = { "X": pos.root_x, "Y": pos.root_y }

            # Call onUnmap to get pane position updated
            child = self.docs.get_current_child()
            if type(child) is DocView: child.onUnmap(child)
            config["DocView"]["Pane"] = DocView.position

            config_save()
        except Exception:
            import traceback
            print(traceback.format_exc())
        Gtk.main_quit()

