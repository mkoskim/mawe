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

Gdk.threads_init()

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

    def __init__(self):
        super(DocNotebook, self).__init__(name = "DocNotebook")

        self.set_scrollable(True)
        self.popup_enable()

        self.opentab = OpenView(self)
        self.openbtn = Button("Open", onclick = lambda w: self.ui_open())

        #self.openbtn = StockButton("gtk-open", onclick = lambda w: self.ui_open())
        #self.openbtn.set_property("tooltip_text", "Open document")

        start = HBox(
            visible = True,
        )

        end = HBox(
            #IconButton("open-menu-symbolic", "Open menu"),
            (self.openbtn, False, 1),
            Button("Help", onclick = lambda w: self.ui_help()),
            visible = True,
        )

        self.set_action_widget(start, Gtk.PackType.START)
        self.set_action_widget(end, Gtk.PackType.END)
        self.connect_after("switch-page", self.onSwitchPage)

        ShortCut.bind(self, {
            "<Ctrl>O": lambda *a: self.ui_open(),
            "<Ctrl>W": lambda *a: self.ui_close(),

            "F1": lambda *a: self.ui_help(),
        })

        self.connect_after("map", lambda w: self.onMap())

    #--------------------------------------------------------------------------

    def onMap(self):
        if len(self.listdocs()) == 0:
            self.ui_open()

    def listdocs(self):
        docs = []
        for pagenum in range(self.get_n_pages()):
            child = self.get_nth_page(pagenum)
            if type(child) is DocView: docs.append(child.doc)
        return docs

    def listfiles(self):
        return list(filter(lambda f: not f is None, [x.origin for x in self.listdocs()]))

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
        # filelist = []

        # Check if we can close
        for pagenum in range(self.get_n_pages()):
            child = self.get_nth_page(pagenum)
            if not child.can_close(): return False

        config["DocNotebook"]["Files"] = self.listfiles()
        
        # Call onUnmap on currently visible page to make it update its configuration
        child = self.get_current_child()
        if not child is None: child.unmap()
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

    def ui_close(self, child = None):
        if child is None: child = self.get_current_child();

        if type(child) is DocView:
            if not child.can_close(): return False
            child.onUnmap(child)
            self._remove_child(child)
            if len(self.listdocs()) == 0:
                self.ui_open()
        elif child == self.opentab:
            if self.get_n_pages() > 1:
                self.opentab.hide()
                self.openbtn.enable()
            return False

        return True

    def _remove_child(self, child):
        page = self.page_num(child)
        if page != -1: self.remove_page(page)

    def ui_open(self):
        page = self.page_num(self.opentab)
        if page < 0:
            self.add_page(self.opentab)
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

class OpenView(DocPage):

    def __init__(self, notebook):
        super(OpenView, self).__init__(notebook, "Open file")

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

###############################################################################
#
# Document view
#
###############################################################################

class DocView(DocPage):

    #--------------------------------------------------------------------------

    def title(self):
        if self.loaded:
            return self.buffers["./body/head/title"].get_text()
        else:
            return self.doc.root.find("./body/head/title").text

    def __init__(self, notebook, doc):
        self.doc = doc
        self.loaded = False
        self.dirty = False

        super(DocView, self).__init__(notebook, self.title())

        #print("Filename:", doc.filename)
        #print("Origin:", doc.origin)

        self.connect("map", self.onMap)
        self.connect("unmap", self.onUnmap)

    def _load(self):
        print("Loading:", self.title())

        self.buffers = {
            "./body/part": SceneBuffer(),
            "./notes/part": SceneBuffer(),

            "./body/head/title":    EntryBuffer(),
            "./body/head/subtitle": EntryBuffer(),
            "./body/head/author":   EntryBuffer(),
            "./body/head/nickname": EntryBuffer(),
            "./body/head/status":   EntryBuffer(),
            "./body/head/deadline": EntryBuffer(),
        }

        self.buffers_revert()
        self.buffers_connect()

        self.create_stacks()

        self.pane = Gtk.Paned()
        self.pane.add1(self.create_left())
        self.pane.add2(self.create_right())

        self.add(self.pane)

        ShortCut.bind(self, {
            "<Ctrl>S": lambda *a: self.ui_save(),
            #"Escape": lambda *a: self.ui_cancel(),
            #"F5": lambda *a: self.ui_refresh(),
            "<Alt>Left": lambda widget, *a: self.onFocusLeft(widget),
            "<Alt>Right": lambda widget, *a: self.onFocusRight(widget),
        })

        self.right_focus[0].grab_focus()
        self.show_all()

        self.loaded = True

    #--------------------------------------------------------------------------

    def choose_focus(self, focusable):
        for child in focusable:
            if child.get_mapped():
                child.grab_focus()
                break
        return True

    def onFocusLeft(self, widget, *args):
        return self.choose_focus(self.left_focus)
        
    def onFocusRight(self, widget, *args):
        return self.choose_focus(self.right_focus)

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
                buf.connect("changed", lambda buf: self.set_dirty())
            elif type(buf) is EntryBuffer:

                def modified(self, buf):
                    self.set_dirty()
                    self.set_name()
                    
                buf.connect("changed", lambda buf: modified(self, buf))
            else: ERROR("Unknown buffer type: %s", type(buf))

    #--------------------------------------------------------------------------
    # Paned control
    #--------------------------------------------------------------------------

    def onMap(self, widget):
        if not self.loaded: self._load()

        pos = int(config["DocView"]["Pane"])
        if pos < 0: return
        self.pane.set_position(pos)
        #print("Set pos:", DocView.position)

    def onUnmap(self, widget):
        if not self.loaded: return 
        config["DocView"]["Pane"] = self.pane.get_position()
        #print("Update pos:", DocView.position)

    #--------------------------------------------------------------------------
    # Dirty control
    #--------------------------------------------------------------------------
    
    def set_name(self, text = None):
        if text is None: text = self.title()
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
        if self.get_dirty() or self.doc.imported:
            answer = dialog.SaveOrDiscard(self,
                "'%s' not saved. Save or discard changes?" % self.title()
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
                directory = config["Directories"]["Open"]
            else:
                directory = os.path.dirname(suggested)
            name = dialog.SaveAs(self, suggested, directory)
            if name is None: return False
            self._save(name)
        else:
            self._save(self.doc.filename)
        return True

    def ui_saveas(self):
        name = dialog.SaveAs(self, self.doc.origin)
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

    def _export(self):
        #self.buffers_store()
        self.ui_save()
        #TODO: We should ask if we are exporting to an existing file, at
        # first time. The xported file, like RTF, might be the one used to
        # import the project.
        filename = self.doc.export()
        xdgopen(filename)

    def ui_revert(self):
        if self.get_dirty():
            answer = dialog.YesNo(self,
                "You will loose all modifications since last save.\n" +
                "Do you want to continue?"
            )
            if answer != Gtk.ResponseType.YES: return

        self.buffers_revert()

    #--------------------------------------------------------------------------
    # Create stacks for draft & notes (both edit and index)
    #--------------------------------------------------------------------------
    
    def create_stacks(self):

        self.left_focus  = []
        self.right_focus = []

        def view(buf, side):
            text = ScrolledSceneView(buf, "Times 12")
            text.view.set_name("draftview")
            text.set_min_content_width(400)
            #text.set_max_content_width(800)
            text.set_min_content_height(400)
            #text.set_border_width(1)
            #text.set_shadow_type(Gtk.ShadowType.IN)

            text.view.connect("focus-left",  self.onFocusLeft)
            text.view.connect("focus-right", self.onFocusRight)

            side.append(text.view)
            return text
        
        def index(buf, side, view): 
            scenelist = ScrolledSceneList(buf, view)
            #scenelist.set_border_width(1)
            #scenelist.set_shadow_type(Gtk.ShadowType.IN)
            side.append(scenelist.tree)
            return scenelist
        
        draftedit  = view(self.buffers["./body/part"], self.right_focus)
        draftindex = index(self.buffers["./body/part"], self.left_focus, draftedit)
        notesedit  = view(self.buffers["./notes/part"], self.right_focus, )
        notesindex = index(self.buffers["./notes/part"], self.left_focus, notesedit)

        self.editstack = Gtk.Stack()
        self.editstack.add_named(draftedit, "draft")
        self.editstack.add_named(notesedit, "notes")
        
        self.indexstack = Gtk.Stack()
        self.indexstack.add_named(draftindex, "draft")
        self.indexstack.add_named(notesindex, "notes")

        self.notesview = view(self.buffers["./notes/part"], self.left_focus)
        
    #--------------------------------------------------------------------------

    def create_left(self):

        def topbar(switcher):
            return HBox(
                (switcher, 1),
            )

        def bottombar():
            return HBox(
                Button("xxx"),
            )

        stack, switcher = DuoStack("_1 - Notes", self.indexstack, self.notesview, can_focus = False)

        switcher.set_use_underline(True)
        self.left_notes = switcher

        return VBox(
            topbar(switcher),
            (Framed(stack), True),
            bottombar(),
            spacing = 2,
        )

    #--------------------------------------------------------------------------

    def create_right(self):

        #----------------------------------------------------------------------
        
        def titleeditor():
        
            def Edit(key): return Gtk.Entry(buffer = self.buffers[key])
            
            grid = Grid(
                (Label("Title"),    Edit("./body/head/title")),
                (Label("Subtitle"), Edit("./body/head/subtitle")),
                [(HSeparator(), 2, 1)],
                (Label("Author"),   Edit("./body/head/author")),
                (Label("Nickname"), Edit("./body/head/nickname")),
                [(HSeparator(), 2, 1)],
                (Label("Status"),   Edit("./body/head/status")),
                (Label("Deadline"), Edit("./body/head/deadline")),
                column_spacing = 10,
                row_spacing = 2,
                expand_column = 1,
            )
            frame = Gtk.Frame(name = "embeddeddialog")
            frame.add(grid)
            return frame, HideControl(
                "_Title",
                frame,
                use_underline = True,
                tooltip_text = "Edit story header info"
            )

        #----------------------------------------------------------------------
        
        def exportsettings():
            # Add backcover text here. Remember to store it, too.
            # Add selection of author and nickname
            # Add story type (short / long) and other formatting options
            titleedit = Gtk.Frame()
            titleedit.set_shadow_type(Gtk.ShadowType.IN)
            titleedit.set_border_width(1)
            titleedit.add(Label("Export"))
            return titleedit, HideControl("_Export", titleedit, use_underline = True)

        #----------------------------------------------------------------------
        
        def topbar():

            def switchBuffer(self, widget):
                if not widget.get_active():
                    self.editstack.set_visible_child_name("draft")
                    self.indexstack.set_visible_child_name("draft")
                else:
                    self.editstack.set_visible_child_name("notes")
                    self.indexstack.set_visible_child_name("notes")

            self.right_notes = ToggleButton(
                "_2 - Notes",
                use_underline = True,
                onclick = lambda w: switchBuffer(self, w),
                can_focus = False,
            )

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
            #exportview, exportswitch = exportsettings()
            exportswitch = Button("_Export", onclick = lambda w: self._export(), use_underline = True)

            toolbar = HBox(
                #IconButton("open-menu-symbolic", "Open menu"),
                self.right_notes,
                VSeparator(),
                titleswitch,

                (Label(""), True),

                exportswitch,
                VSeparator(),
                self.folderbtn,
                spacing = 1,
            )

            return VBox(
                toolbar,
                titleedit,
                #exportview,
            )

        def bottombar():
            return HBox(
                Button("_Revert", use_underline = True, onclick = lambda w: self.ui_revert()),
                (Label(""), True),
                (self.buffers["./body/part"].stats.words, 2),
                (self.buffers["./body/part"].stats.chars, 4)
            )

        return VBox(
            topbar(),
            (Framed(self.editstack), True),
            bottombar(),
            spacing = 2,
        )

###############################################################################
#
# Main window
#
###############################################################################

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

        ShortCut.bind(self, {
            "<Ctrl>Q": lambda *a: self.onDelete(self),
        })

        settings = config["Window"]
        #print(settings)
        #print(settings["Position"]["X"], settings["Position"]["Y"])
        #print(settings["Size"]["X"], settings["Size"]["Y"])
        if "Position" in settings: self.move(
            settings["Position"]["X"],
            settings["Position"]["Y"]
        )
        self.resize(
            settings["Size"]["X"],
            settings["Size"]["Y"]
        )

        workset = self.docs.open_defaults(workset)
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
