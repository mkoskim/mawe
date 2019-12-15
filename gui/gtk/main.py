from gui.gtk import (
    Gtk, Gdk, Gio, GObject,
    ScrolledSceneView, SceneView,
    ScrolledSceneList, SceneList,
    SceneBuffer, ProjectView,
    dialog,
    guidir,
)

from tools import *
from gui.gtk.factory import *
import project
import os
from project.Document import ET

#------------------------------------------------------------------------------

def run(workset = None, new = False):
    global mainwindow
    MainWindow(workset, new = new).show_all()

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

###############################################################################
#
# Notebook to hold workset files
#
###############################################################################

class DocNotebook(Gtk.Notebook):

    # TODO: When last file is closed, choose open tab? Without close button?

    def __init__(self):
        super(DocNotebook, self).__init__(name = "DocNotebook")

        self.set_scrollable(True)
        self.popup_enable()

        self.opentab = OpenView(self)
        self.openbtn = StockButton("gtk-open", onclick = lambda w: self.ui_open())
        self.openbtn.set_property("tooltip_text", "Open document")

        start = HBox(
            IconButton("open-menu-symbolic", "Open menu"),
            (self.openbtn, False, 1),
            StockButton("gtk-help", onclick = lambda w: self.ui_help()),
            visible = True,
        )

        end = HBox(visible = True)

        self.set_action_widget(start, Gtk.PackType.START)
        self.set_action_widget(end, Gtk.PackType.END)
        self.connect_after("switch-page", self.onSwitchPage)

    #--------------------------------------------------------------------------
    
    def listfiles(self):
        files = []
        for pagenum in range(self.get_n_pages()):
            child = self.get_nth_page(pagenum)
            if not type(child) is DocView: continue
            if child.doc.origin: files.append(child.doc.origin)
        return files

    def findpage(self, filename):
        if filename is None: return None
        for pagenum in range(self.get_n_pages()):
            child = self.get_nth_page(pagenum)
            if not type(child) is DocView: continue
            if child.doc.origin == filename: return pagenum
        return None
        
    def findchild(self, filename):
        pagenum = self.findpage(filename)
        if not pagenum is None: return self.get_nth_page(pagenum)
        return None
    
    def get_current_child(self):
        page = self.get_current_page()
        child = self.get_nth_page(page)
        if child and not child.get_visible(): return None
        return child

    #--------------------------------------------------------------------------
    
    def add_page(self, child, prepend = False):
        label = HBox(
            (child.tablabel, True, 4),
            Button(
                icon = "window-close-symbolic",
                name = "round-btn",
                tooltip_text = "Close document",
                image_position = Gtk.PositionType.RIGHT,
                onclick = lambda w: self.ui_close(child),
            ),
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
        if type(doc) is str:
            filename = doc
        else:
            filename = doc.origin
            
        child = self.findchild(filename)
        if child:
            self.reorder_child(child, -1)
            self.set_current_page(-1)
        else:
            if type(doc) is str:
                doc = project.Project.open(filename).load()            
            self.add_page(DocView(self, doc))

    def open_defaults(self, extras):
        for filename in (config["DocNotebook"]["Files"] + extras):
            try:
                self.add(filename)
            except Exception as e:
                log_exception(e)
        return self.listfiles()
        
    #--------------------------------------------------------------------------
    
    def save_all(self):
        pass

    def close_all(self):
        pass

    def exit(self):
        filelist = []

        for pagenum in range(self.get_n_pages()):
            child = self.get_nth_page(pagenum)
            if not child.can_close(): return False

        config["DocNotebook"]["Files"] = self.listfiles()
        
        # Call onUnmap to get pane position updated
        child = self.get_current_child()
        if type(child) is DocView: child.onUnmap(child)
        config["DocView"]["Pane"] = DocView.position
        return True

    def ui_help(self):
        doc = project.Project.open(os.path.join(guidir, "ui/guide.mawe")).load()
        doc.filename = None
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

    def ui_refresh(self):
        child = self.get_current_child()
        child.ui_refresh()

    def ui_revert(self):
        child = self.get_current_child()
        if type(child) is DocView:
            child.ui_revert()

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

    def ui_refresh(self): pass

###############################################################################
#
# Document open view
#
###############################################################################

class OpenView(DocPage):

    def __init__(self, notebook):
        super(OpenView, self).__init__(notebook, "Open file")

        self.config = config["OpenView"]

        chooser = Gtk.FileChooserWidget()
        chooser.set_create_folders(True)
        chooser.connect("file-activated", self.onChooser)
        chooser.connect("map", self.dir_restore)
        chooser.connect("unmap", self.dir_store)

        #chooser.set_extra_widget(Button("New", onclick = lambda w: self.openNew()))

        manager = ProjectView()
        manager.connect("file-activated", self.onProjectSelect)

        stack    = Gtk.Stack()
        switcher = StackSwitcher(stack)
        stack.add_titled(manager, "projects", "Projects")
        stack.add_titled(chooser, "files", "Files")

        toolbar = HBox(
            (switcher, False, 1),
            Button("Recent"),
            (StockButton("gtk-new", onclick = self.onNew), False, 1),
        )

        box = VBox(
            (toolbar, False, 1),
            (stack, True, 1),
        )
        self.add(box)
        self.show_all()

        if len(project.Manager.projects):
            stack.set_visible_child_name("projects")
        else:
            stack.set_visible_child_name("files")

        self.stack = stack

    def onNew(self, widget):
        self.notebook.ui_new()

    def onProjectSelect(self, widget, filename):
        self.notebook.ui_new(filename)

    def onChooser(self, chooser):
        filename = chooser.get_filename()
        self.onProjectSelect(chooser, filename)

    def dir_store(self, chooser):
        self.config["Directory"] = chooser.get_current_folder()

    def dir_restore(self, chooser):
        chooser.set_current_folder(self.config["Directory"])

    def ui_refresh(self):
        if self.stack.get_visible_child_name() == "projects":
            self.stack.get_visible_child().refresh()

###############################################################################
#
# Document view
#
###############################################################################

class DocView(DocPage):

    #--------------------------------------------------------------------------

    def __init__(self, notebook, doc):
        super(DocView, self).__init__(
            notebook,
            doc.root.find("./body/head/title").text
        )

        self.doc = doc
        self.dirty = False

        #print("Filename:", doc.filename)
        #print("Origin:", doc.origin)

        self.buffers = {
            "./body/part": SceneBuffer(),
            "./notes/part": SceneBuffer(),

            "./body/head/title":    EntryBuffer("./body/head/title"),
            "./body/head/subtitle": EntryBuffer(),
            "./body/head/author":   EntryBuffer(),
            "./body/head/status":   EntryBuffer(),
            "./body/head/deadline": EntryBuffer(),
        }

        self.buffers_revert()
        self.buffers_connect()

        # Try to get rid of these
        self.draftview = ScrolledSceneView(self.buffers["./body/part"], "Times 12")
        self.notesview = ScrolledSceneView(self.buffers["./notes/part"], "Times 12")
        self.scenelist = ScrolledSceneList(self.buffers["./body/part"], self.draftview)

        self.pane = Gtk.Paned()
        self.pane.add2(self.create_view())
        self.pane.add1(self.create_index())

        self.add(self.pane)

        self.connect("map", self.onMap)
        self.connect("unmap", self.onUnmap)
        self.connect("key-press-event", self.onKeyPress)

        #self.draftview.grab_focus()

    #--------------------------------------------------------------------------
    # Buffers to XML tree. TODO: This does not work with multi-part bodies.
    #--------------------------------------------------------------------------
    
    def buffers_revert(self):
        for key, buf in self.buffers.items():
            child = self.doc.root.find(key)
            if child is None:
                child = self.doc.create(key)
            if type(buf) is SceneBuffer:
                buf.revert(child)
                buf.set_modified(False)
            elif type(buf) is EntryBuffer:
                text = child.text
                if text is None: text = ""
                buf.set_text(text, -1)
            else: ERROR("Unknown buffer type: %s", type(buf))

        self.set_dirty(False)

    def buffers_store(self):
        for key, buf in self.buffers.items():
            child = self.doc.root.find(key)
            if type(buf) is SceneBuffer:
                self.doc.replace(key, buf.to_mawe())
            elif type(buf) is EntryBuffer:
                child.text = buf.get_text()
            else: ERROR("Unknown buffer type: %s", type(buf))

        self.set_dirty(False)

    def buffers_connect(self):
        for key, buf in self.buffers.items():
            if type(buf) is SceneBuffer:

                def modified1(self, buf): self.set_dirty()

                buf.connect("changed", lambda buf: modified1(self, buf))

            elif type(buf) is EntryBuffer:

                def modified2(self, buf):
                    self.set_dirty()
                    if buf.key == "./body/head/title": self.set_name(buf.get_text())

                buf.connect("changed", lambda e: modified2(self, e))

            else: ERROR("Unknown buffer type: %s", type(buf))

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
        # if not self.get_dirty() and self.doc.origin is None:
        #    self.notebook._remove_child(self)

    #--------------------------------------------------------------------------

    def set_name(self, text = None):
        if text is None: text = self.buffers["./body/head/title"].get_text()
        super(DocView, self).set_name((self.get_dirty() and "*" or "") + text)

    def get_dirty(self): return self.dirty

    def set_dirty(self, status = True):
        if self.dirty != status:
            self.dirty = status
            self.set_name()

    #--------------------------------------------------------------------------
    # Saving. TODO: Warn if file was deleted?
    #--------------------------------------------------------------------------

    def can_close(self):
        if self.get_dirty():
            answer = dialog.SaveOrDiscard(self,
                "'%s' not saved. Save or discard changes?" % self.buffers["./body/head/title"].get_text()
            )
            if answer == Gtk.ResponseType.CANCEL: return False
            if answer == Gtk.ResponseType.YES:
                if not self.ui_save(): return False
        return True

    def ui_save(self):
        if self.doc.filename is None:
            suggested = self.doc.origin
            if suggested is None:
                suggested = self.buffers["./body/head/title"].get_text()
            name = dialog.SaveAs(self, suggested)
            if name is None: return False
            self._save(name)
        else:
            self._save(self.doc.filename)
        return True

    def ui_saveas(self):
        name = self.SaveAs(self, self.doc.origin)
        if name is None: return False
        self._save(name)
        return True

    def _save(self, filename):
        #print("Saving as:", filename)

        self.buffers_store()
        
        buf = self.buffers["./body/part"]

        words, chars, comments, missing = buf.wordcount(*buf.get_bounds(), True)
        wordcount = ET.Element("words")
        ET.SubElement(wordcount, "text").text = str(words)
        ET.SubElement(wordcount, "comments").text = str(comments)
        ET.SubElement(wordcount, "missing").text = str(missing)
        self.doc.replace("./body/head/words", wordcount)

        self.doc.save(filename)

        #self.draftbuf.revert(draft)
        
        #from project.Document import ET
        #ET.dump(draft)

        self.folderbtn.enable()

    def ui_revert(self):
        if self.get_dirty():
            answer = dialog.YesNo(self,
                "You will loose all modifications since last save.\n" +
                "Do you want to continue?"
            )
            if answer != Gtk.ResponseType.YES: return

        self.buffers_revert()

    #--------------------------------------------------------------------------

    def create_view(self):

        #----------------------------------------------------------------------
        
        def titleeditor():
        
            def Edit(key): return Gtk.Entry(buffer = self.buffers[key])
            
            grid = Grid(
                (Label("Title"), Edit("./body/head/title")),
                (Label("Subtitle"), Edit("./body/head/subtitle")),
                [(HSeparator(), 2, 1)],
                (Label("Author"), Edit("./body/head/author")),
                [(HSeparator(), 2, 1)],
                (Label("Status"), Edit("./body/head/status")),
                (Label("Deadline"), Edit("./body/head/deadline")),
                column_spacing = 10,
                row_spacing = 2,
                expand_column = 1,
            )
            frame = Gtk.Frame(name = "embeddeddialog")
            frame.add(grid)
            return frame, HideControl(
                "Title",
                frame,
                tooltip_text = "Edit story header info"
            )

        #----------------------------------------------------------------------
        
        def exportsettings():
            # Add backcover text here. Remember to store it, too.
            titleedit = Gtk.Frame()
            #titleedit.set_label("Edit title")
            titleedit.set_shadow_type(Gtk.ShadowType.IN)
            titleedit.set_border_width(1)
            titleedit.add(Label("Export"))
            return titleedit, HideControl("Export", titleedit)

        #----------------------------------------------------------------------
        
        def topbar():

            selectnotes = ToggleButton("Notes")

            def switchBuffer(self, widget):
                pass
                # TODO: Fix
                #if not widget.get_active():
                #    self.draftview.set_buffer(self.draftbuf)
                #    self.scenelist.set_buffer(self.draftbuf)
                #else:
                #    self.draftview.set_buffer(self.notesbuf)
                #    self.scenelist.set_buffer(self.notesbuf)

            selectnotes = ToggleButton("Notes", onclick = lambda w: switchBuffer(self, w))

            self.folderbtn = Button(
                "Folder",
                tooltip_text="Open document folder",
                onclick = lambda w: xdgfolder(self.doc.filename and self.doc.filename or self.doc.origin)
            )
            if self.doc.filename is None and self.doc.origin is None:
                self.folderbtn.disable()


            # Menu items. REMEMBER! We can use left side, too, for example for exporting,
            # history entries and so on!
            # - Export
            # - Open containing folder
            # - Save
            # - Save as
            # - Revert
            # - Close
            
            titleedit,  titleswitch  = titleeditor()
            exportview, exportswitch = exportsettings()

            toolbar = HBox(
                IconButton("open-menu-symbolic", "Open menu"),
                titleswitch,
                selectnotes,
                (VSeparator(), False, 2),

                (Label(""), True),

                (VSeparator(), False, 2),
                exportswitch,
                self.folderbtn,
            )

            return VBox(
                toolbar,
                titleedit,
                exportview,
            )

        def bottombar():
            return HBox(
                Button("Revert", onclick = lambda w: self.ui_revert()),
                (Label(""), True, 2),
                (self.buffers["./body/part"].stats.words, False, 2),
                (self.buffers["./body/part"].stats.chars, False, 4)
            )

        def view():
            text = self.draftview
            text.view.set_name("draftview")
            text.set_min_content_width(400)
            #text.set_max_content_width(800)
            text.set_min_content_height(400)
            text.set_border_width(1)
            text.set_shadow_type(Gtk.ShadowType.IN)
            return text

        return VBox(
            topbar(),
            (view(), True),
            bottombar(),
        )

    def create_index(self):

        def topbar(switcher):
            return HBox(
                (switcher, False, 1),
            )

        def scenelist():
            self.scenelist.set_border_width(1)
            self.scenelist.set_shadow_type(Gtk.ShadowType.IN)
            return self.scenelist
            #return VBox(
            #    (self.scenelist, True ),
            #)

        def notes():
            text = self.notesview

            #text.set_min_content_width(400)
            #text.set_max_content_width(800)
            #text.set_min_content_height(400)

            text.set_border_width(1)
            text.set_shadow_type(Gtk.ShadowType.IN)
            return text

        def bottombar():
            return HBox(
                Button("..."),
            )

        stack, switcher = DuoStack("Notes", scenelist(), notes())

        return VBox(
            topbar(switcher),
            (stack, True),
            bottombar(),
        )

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

    def __init__(self, workset, new = False):
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
            
            ("<Alt>R",  lambda *a: self.docs.ui_revert()),

            ("F1", lambda *a: self.docs.ui_help()),
            ("F5", lambda *a: self.docs.ui_refresh()),
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

        workset = self.docs.open_defaults(workset)
        if workset:
            pass
        elif len(project.Manager.projects):
            self.docs.ui_open()
        else:
            new = True
            
        if new: self.docs.ui_new()

    #--------------------------------------------------------------------------
    
    def onDelete(self, widget):

        if not self.docs.exit(): return True

        try:
            settings = config["Window"]

            size = self.get_size()
            settings["Size"] = { "X": size.width, "Y": size.height }

            pos = self.get_position()
            settings["Position"] = { "X": pos.root_x, "Y": pos.root_y }

            config_save()
        except Exception:
            import traceback
            print(traceback.format_exc())
        Gtk.main_quit()

