###############################################################################
#
# Document view
#
###############################################################################

from gui.gtk import (
    Gtk, Gdk, Gio, GObject,
    ScrolledSceneView, SceneView,
    ScrolledSceneList, SceneList,
    SceneBuffer, ProjectView,
    DocBookPage,
    dialog,
    guidir,
)

from tools import *
from gui.gtk.factory import *
import project
import os
from project.Document import ET

class DocTab(DocBookPage):

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

        super(DocTab, self).__init__(notebook, self.title())

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

        self.pane = Paned(
            self.create_left(),
            self.create_right()
        )

        self.add(VBox(
            self.create_toolbar(),
            HSeparator(),
            (self.pane, True),
            self.create_statusbar(),
        ))

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
        super(DocTab, self).set_name((self.get_dirty() and "*" or "") + text)

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

    def create_toolbar(self):

        def Edit(key): return Gtk.Entry(buffer = self.buffers[key])
            
        def titleeditor():
        
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
            return Popover(grid)

        self.folderbtn = Button(
            "Folder",
            tooltip_text="Open document folder",
            onclick = lambda w: xdgfolder(self.doc.filename and self.doc.filename or self.doc.origin)
        )
        if self.doc.filename is None and self.doc.origin is None:
            self.folderbtn.disable()

        exportswitch = Button("_Export", onclick = lambda w: self._export(), use_underline = True)

        return HBox(
            MenuButton("_Title", titleeditor(),
                use_underline = True,
                tooltip_text = "Edit story header info",
            ),

            (Label(""), True),
            VSeparator(),

            Button("_Revert", use_underline = True, onclick = lambda w: self.ui_revert()),
            exportswitch,
            self.folderbtn,

            (VSeparator(), 8),

            (self.buffers["./body/part"].stats.words, 2),
            (self.buffers["./body/part"].stats.chars, 4),

            spacing = 1,
            )

    def create_statusbar(self):
        pass

    #--------------------------------------------------------------------------

    def create_left(self):

        def topbar(switcher):
            return HBox(
                (switcher, 1),
            )

        def bottombar(): pass

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

            toolbar = HBox(
                self.right_notes,
                VSeparator(),
                # titleswitch,

                (Label(""), True),

                #VSeparator(),
                spacing = 1,
            )

            return VBox(
                toolbar,
                #titleedit,
                #exportview,
            )

        def bottombar(): pass

        return VBox(
            topbar(),
            (Framed(self.editstack), True),
            bottombar(),
            spacing = 2,
        )
