###############################################################################
#
# Notebook to hold files
#
###############################################################################

from gui.gtk import (
    Gtk, Gdk, Pango, GtkSource, GObject,
    OpenTab, DocTab,
    guidir,
)
from tools import *
from gui.gtk.factory import *
import project
import os

class DocBook(Gtk.Notebook):

    def __init__(self):
        super(DocBook, self).__init__(name = "DocBook")

        self.set_scrollable(True)
        self.popup_enable()

        self.opentab = OpenTab(self)
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
            if type(child) is DocTab: docs.append(child.doc)
        return docs

    def listfiles(self):
        return list(filter(lambda f: not f is None, [x.origin for x in self.listdocs()]))

    def findpage(self, filename):
        if filename is None: return None
        for pagenum in range(self.get_n_pages()):
            child = self.get_nth_page(pagenum)
            if not type(child) is DocTab: continue
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
            self.add_page(DocTab(self, doc))

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

        if type(child) is DocTab:
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
