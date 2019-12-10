from gui.gtk import (
    Gtk, Gdk, Gio,
    ScrolledSceneView, SceneView,
    ScrolledSceneList, SceneList,
    SceneBuffer,
    guidir,
)

from tools import *

import os

###############################################################################
#
# Some overrides
#
###############################################################################

class Button(Gtk.Button):

    @staticmethod
    def getclick(self, kwargs):
        if "onclick" in kwargs:
            onclick = kwargs["onclick"]
            del kwargs["onclick"]
            return onclick
        return None

    def __init__(self, label = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True

        if "icon" in kwargs:
            icon = Gio.ThemedIcon(name=kwargs["icon"])
            image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            kwargs["image"] = image
            del kwargs["icon"]
            kwargs["always-show-image"] = True

        onclick = Button.getclick(self, kwargs)

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

class RadioButton(Gtk.RadioButton):

    def __init__(self, label, group = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(RadioButton, self).__init__(label = label, group = group, **kwargs)
        self.set_relief(Gtk.ReliefStyle.NONE)

#------------------------------------------------------------------------------

class Label(Gtk.Label):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(Label, self).__init__(label, **kwargs)

#------------------------------------------------------------------------------

class Box(Gtk.Box):

    def __init__(self, **kwargs):
        #if "visible" not in kwargs: kwargs["visible"] = True
        super(Box, self).__init__(**kwargs)

class HBox(Gtk.HBox):

    def __init__(self, **kwargs):
        super(HBox, self).__init__(**kwargs)

class VBox(Gtk.VBox):

    def __init__(self, **kwargs):
        super(VBox, self).__init__(**kwargs)

class HSeparator(Gtk.HSeparator):

    def __init__(self, **kwargs):
        super(HSeparator, self).__init__(**kwargs)

class VSeparator(Gtk.VSeparator):

    def __init__(self, **kwargs):
        super(VSeparator, self).__init__(**kwargs)

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
            tooltip_text = "Open document",
            onclick = self.open,
        )
        newbtn = Button(
            icon = "document-new-symbolic",
            tooltip_text = "Create new document",
            onclick = self.new,
        )
          
        start = Box(visible = True)
        start.pack_start(MenuButton("<Workset>"), False, False, 0)
        start.pack_start(self.openbtn, False, False, 1)
        self.set_action_widget(start, Gtk.PackType.START)

        end = Box(visible = True)
        end.pack_start(newbtn, False, False, 1)
        self.set_action_widget(end, Gtk.PackType.END)

        self.connect("switch-page", self.onSwitchPage)

    def get_current_child(self):
        page = self.get_current_page()
        return self.get_nth_page(page)

    def add_page(self, name, child):
        label = HBox()
        label.pack_start(Label(name), True, False, 0)
        label.pack_start(Button(
            icon = "window-close-symbolic",
            tooltip_text = "Close document",
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
            # Unmap first to update pane pos
            child.unmap()
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

        self.style   = Gtk.CssProvider()
        self.context = Gtk.StyleContext()
        self.context.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.style,
           Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.style.load_from_data(
            b"#draftview { background-color: #FFF; }" + 
            b"#draftview:selected { background: #9AB87C; }"
        )

        self.draftbuf  = SceneBuffer(draft)
        self.notesbuf  = SceneBuffer(notes)
        self.draftview = ScrolledSceneView(self.draftbuf, "Times 12")
        self.notesview = ScrolledSceneView(self.notesbuf, "Times 12")
        self.scenelist = ScrolledSceneList(self.draftbuf, self.draftview)
        
        self.pane = Gtk.Paned()
        self.pane.add2(self.create_view())
        self.pane.add1(self.create_index())
        
        self.connect("map", self.onMap)
        self.connect("unmap", self.onUnmap)
        self.connect("key-press-event", self.onKeyPress)
        
        self.add(self.pane)
        self.show_all()
        self.draftview.grab_focus()
    
    def onKeyPress(self, widget, event):
        mods   = event.state & Gtk.accelerator_get_default_mod_mask()
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

    position = -1

    def onMap(self, widget):
        if DocView.position < 0: return
        self.pane.set_position(DocView.position)
        #print("Set pos:", DocView.position)

    def onUnmap(self, widget):
        DocView.position = self.pane.get_position()
        #print("Update pos:", DocView.position)
    
    def create_view(self):

        def toolbar():
            box = HBox()

            selectdraft = RadioButton(
                "Draft", None, draw_indicator = False,
            )
            selectnotes = RadioButton(
                "Notes", group = selectdraft, draw_indicator = False,
            )

            def switchBuffer(self, active, buffer):
                if not active: return
                self.draftview.set_buffer(buffer)
                self.scenelist.set_buffer(buffer)
                
            selectdraft.connect("toggled", lambda w: switchBuffer(self, w.get_active(), self.draftbuf))
            selectnotes.connect("toggled", lambda w: switchBuffer(self, w.get_active(), self.notesbuf))

            box.pack_start(Button(icon = "open-menu-symbolic", tooltip_text = "Open menu"), False, False, 0)
            box.pack_start(VSeparator(), False, False, 2)
            box.pack_start(selectdraft, False, False, 0)
            box.pack_start(selectnotes, False, False, 0)
            box.pack_start(VSeparator(), False, False, 2)

            box.pack_start(Label(""), True, True, 0)

            box.pack_start(VSeparator(), False, False, 2)
            box.pack_start(self.draftbuf.stats.words, False, False, 4)
            box.pack_start(self.draftbuf.stats.chars, False, False, 6)
            return box

        def view():
            text = self.draftview
            text.view.set_name("draftview")
            text.set_min_content_width(400)
            #text.set_max_content_width(800)
            text.set_min_content_height(400)
            text.set_border_width(1)
            text.set_shadow_type(Gtk.ShadowType.IN)
            return text

        def statusbar():
            box = Gtk.HBox()
            return box

        box = VBox()
        box.pack_start(toolbar(), False, False, 0)
        box.pack_start(view(), True, True, 0)
        box.pack_end(statusbar(), False, False, 0)
        return box

    def create_index(self):
        def toolbar(stack):
            box = HBox()
            box.pack_start(Button("Notes", tooltip_text = "Switch to notes"), False, False, 0)
            return box

        def scenelist():
            return self.scenelist

        def notes():
            text = self.notesview

            #text.set_min_content_width(400)
            #text.set_max_content_width(800)
            #text.set_min_content_height(400)

            text.set_border_width(1)
            text.set_shadow_type(Gtk.ShadowType.IN)
            return text

        stack = Gtk.Stack()
        stack.add_titled(scenelist(), "index", "Index")
        stack.add_titled(notes(), "notes", "Notes")

        box = VBox()
        box.pack_start(toolbar(stack), False, False, 1)
        box.pack_start(stack, True, True, 0)
        return box

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

    def __init__(self, workset):
        super(MainWindow, self).__init__()
        
        self.docs = DocNotebook()
        self.add(self.docs)

        self.connect("delete-event", lambda w, e: self.onDestroy(w))

        add_shortcuts(self, [
            ("<Ctrl>Q", lambda *a: self.onDestroy(self)),
            ("<Ctrl>O", lambda *a: self.docs.open()),
        ])

        if "Position" in config["Window"]: pass
        self.resize(config["Window"]["Size"]["X"], config["Window"]["Size"]["Y"])
        DocView.position = config["DocView"]["Pane"]

        if workset:
            for doc in workset: self.load(doc)
        else:
            self.new()

    def load(self, doc):
        self.docs.load(doc)

    def new(self):
        self.docs.new()

    def onDestroy(self, widget):
        try:
            size = self.get_size()
            print("Size:", size)
            config["Window"]["Size"]["X"] = size.width
            config["Window"]["Size"]["Y"] = size.height

            child = self.docs.get_current_child()
            if child: child.unmap()

            print("Pane:", DocView.position)
            config["DocView"]["Pane"] = DocView.position

            config_save()
        except Exception:
            import traceback
            print(traceback.format_exc())
        Gtk.main_quit()

#------------------------------------------------------------------------------

def run(workset = None):
    
    win = MainWindow(workset)
    win.show_all()

    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

