from gui.gtk import (
    Gtk, Gdk, Gio,
    ScrolledSceneView, SceneView,
    ScrolledSceneList, SceneList,
    SceneBuffer,
    guidir,
)

from tools import *
import project
import os

###############################################################################
#
# Some overrides
#
###############################################################################

class Button(Gtk.Button):

    @staticmethod
    def getarg(kwargs, name):
        if name in kwargs:
            result = kwargs[name]
            del kwargs[name]
            return result
        return None

    @staticmethod
    def geticon(kwargs):
        name = Button.getarg(kwargs, "icon")
        if name:
            icon = Gio.ThemedIcon(name=name)
            kwargs["image"] = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
            kwargs["always-show-image"] = True

    def __init__(self, label = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True

        Button.geticon(kwargs)
        onclick = Button.getarg(kwargs, "onclick")
        
        super(Button, self).__init__(label, **kwargs)

        if onclick: self.connect("clicked", lambda w: onclick())
        self.set_relief(Gtk.ReliefStyle.NONE)

    def disable(self):
        self.set_sensitive(False)
        
    def enable(self):
        self.set_sensitive(True)
        
class StockButton(Button):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        kwargs["use_stock"] = True
        super(StockButton, self).__init__(label, **kwargs)
        self.set_always_show_image(True)

class IconButton(Button):

    def __init__(self, icon, tooltip, **kwargs):
        super(IconButton, self).__init__(None, icon = icon, tooltip_text = tooltip, **kwargs)

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

class ToggleButton(Gtk.ToggleButton):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(ToggleButton, self).__init__(label = label, **kwargs)
        self.set_relief(Gtk.ReliefStyle.NONE)

class RadioButton(Gtk.RadioButton):

    def __init__(self, label, group = None, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(RadioButton, self).__init__(label = label, group = group, **kwargs)
        self.set_relief(Gtk.ReliefStyle.NONE)

#------------------------------------------------------------------------------

class Box(Gtk.Box):

    def __init__(self, **kwargs):
        super(Box, self).__init__(**kwargs)

class HBox(Gtk.HBox):

    def __init__(self, **kwargs):
        super(HBox, self).__init__(**kwargs)

class VBox(Gtk.VBox):

    def __init__(self, **kwargs):
        super(VBox, self).__init__(**kwargs)

#------------------------------------------------------------------------------

class Label(Gtk.Label):

    def __init__(self, label, **kwargs):
        if "visible" not in kwargs: kwargs["visible"] = True
        super(Label, self).__init__(label, **kwargs)

#------------------------------------------------------------------------------

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
        self.popup_enable()
        
        self.opentab = DocOpen(self)
        self.openbtn = StockButton("gtk-open", onclick = self.open)
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
        start.pack_start(StockButton("gtk-help", onclick = self.help), False, False, 0)
        self.set_action_widget(start, Gtk.PackType.START)

        end = Box(visible = True)
        self.set_action_widget(end, Gtk.PackType.END)
        self.connect("switch-page", self.onSwitchPage)

    def get_current_child(self):
        page = self.get_current_page()
        return self.get_nth_page(page)

    def add_page(self, name, child, prepend = False):
        label = HBox()
        label.pack_start(Label(name), True, False, 4)
        label.pack_start(Button(
            icon = "window-close-symbolic",
            name = "doc-close-btn",
            tooltip_text = "Close document",
            image_position = Gtk.PositionType.RIGHT,
            onclick = lambda: self.close(child),
            ),
            False, False, 0
        )

        if prepend:
            page = self.prepend_page(child, label)
        else:
            page = self.append_page(child, label)

        self.set_tab_reorderable(child, True)
        self.child_set_property(child, "tab-expand", True)
        self.child_set_property(child, "tab-fill", True)
        self.set_menu_label_text(child, name)
        child.show()
        self.set_current_page(page)
        return page
        
    def add(self, doc):
        self.add_page(doc.name, DocView(doc))

    def help(self):
        doc = project.Project.open(os.path.join(guidir, "ui"), "help.txt", force = True).load()
        doc.name = "Help"
        self.add(doc)

    def new(self):
        doc = project.Document(tree = project.Document.empty("New story"))
        self.add(doc)

    def save(self):
        page  = self.get_current_page()
        child = self.get_nth_page(page)
        if type(child) is DocView:
            child.save()

    def close(self, child):
        if child == self.opentab:
            self.opentab.hide()
            self.openbtn.enable()
        else:
            # Unmap first to update pane pos
            child.unmap()
            page = self.page_num(child)
            self.remove_page(page)

    def open(self):
        page = self.page_num(self.opentab)
        if page < 0:
            self.add_page("Open file...", self.opentab, prepend = False)
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

###############################################################################
#
# Document open view
#
###############################################################################

class DocOpen(Gtk.VBox):

    def __init__(self, notebook):
        super(DocOpen, self).__init__()
        self.notebook = notebook

        toolbar = HBox()
        toolbar.pack_start(Button("New", onclick = self.openNew), False, False, 0)

        text = Gtk.TextView()

        self.pack_start(toolbar, False, False, 0)
        self.pack_start(text, True, True, 0)
        self.show_all()

    def openNew(self):
        self.notebook.new()

###############################################################################
#
# Document view
#
###############################################################################

class DocView(Gtk.Frame):

    def __init__(self, doc):
        super(DocView, self).__init__()
        
        #if doc is None: doc = project.Document()
        self.doc = doc
        
        draft = doc.root.find("./body/part")
        notes = doc.root.find("./notes/part")

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

    position = -1

    def onMap(self, widget):
        if DocView.position < 0: return
        self.pane.set_position(DocView.position)
        #print("Set pos:", DocView.position)

    def save(self):
        if self.doc.filename is None:
            mainwindow = Gtk.Window.list_toplevels()[0]
            
            dialog = Gtk.FileChooserDialog(
                "Save as...", mainwindow,
                Gtk.FileChooserAction.SAVE,
                (
                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_SAVE, Gtk.ResponseType.OK
                )
            )

            if self.doc.origin:
                print("Origin:", self.doc.origin)
                suggested = os.path.splitext(self.doc.origin)[0] + ".mawe"
                dialog.set_filename(suggested)
                dialog.set_current_name(os.path.basename(suggested))

            response = dialog.run()
            dialog.destroy()
            
            if response != Gtk.ResponseType.OK:
                print("Cancelled")
                return
            self.doc.filename = dialog.get_filename()

        print("Saving as:", self.doc.filename)

    def onUnmap(self, widget):
        DocView.position = self.pane.get_position()
        #print("Update pos:", DocView.position)
    
    def create_view(self):

        def toolbar():
            box = HBox()

            selectnotes = ToggleButton(
                "Notes", draw_indicator = False,
            )

            def switchBuffer(self, widget):
                if not widget.get_active():
                    self.draftview.set_buffer(self.draftbuf)
                    self.scenelist.set_buffer(self.draftbuf)
                else:
                    self.draftview.set_buffer(self.notesbuf)
                    self.scenelist.set_buffer(self.notesbuf)
                
            selectnotes.connect("toggled", lambda w: switchBuffer(self, w))

            box.pack_start(IconButton("open-menu-symbolic", "Open menu"), False, False, 0)
            # Menu items
            # - Export
            # - Open containing folder
            # - Save
            # - Save as
            # - Revert
            # - Close
            box.pack_start(Button("Title"), False, False, 0)
            #box.pack_start(VSeparator(), False, False, 2)
            #box.pack_start(Button("Export"), False, False, 0)
            #box.pack_start(Button("Save"), False, False, 0)
            #box.pack_start(Button("Revert"), False, False, 0)
            box.pack_start(VSeparator(), False, False, 2)
            
            box.pack_start(Label(""), True, True, 0)

            box.pack_start(selectnotes, False, False, 0)
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
    
        # Create dual page stack: return stack & switcher
        def Stack(label, page1, page2):

            stack = Gtk.Stack()
            stack.add_named(page1, "1")
            stack.add_named(page2, "2")

            def switchStack(self, button, stack):
                name  = button.get_active() and "2" or "1"
                child = stack.get_child_by_name(name)
                stack.set_visible_child(child)
                
            switcher = ToggleButton(label, tooltip_text = "Switch to notes")
            switcher.connect("toggled", lambda w: switchStack(self, w, stack))

            return stack, switcher

        def toolbar(switcher):
            box = HBox()
            box.pack_start(switcher, False, False, 0)
            return box

        def scenelist():
            box = VBox()
            #box.pack_start(toolbar(), False, False, 0)
            box.pack_start(self.scenelist, True, True, 2)
            return box

        def notes():
            text = self.notesview

            #text.set_min_content_width(400)
            #text.set_max_content_width(800)
            #text.set_min_content_height(400)

            text.set_border_width(1)
            text.set_shadow_type(Gtk.ShadowType.IN)
            return text

        stack, switcher = Stack("Notes", scenelist(), notes())

        box = VBox()
        box.pack_start(toolbar(switcher), False, False, 0)
        box.pack_start(stack, True, True, 0)
        return box

###############################################################################
#
# Main window
#
###############################################################################

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

        self.connect("delete-event", lambda w, e: self.onDestroy(w))

        add_shortcuts(self, [
            ("<Ctrl>Q", lambda *a: self.onDestroy(self)),
            ("<Ctrl>O", lambda *a: self.docs.open()),
            ("<Ctrl>S", lambda *a: self.docs.save()),
            ("F1", lambda *a: self.docs.help()),
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
            for project in workset:
                print(project)
                doc = project.load()
                self.docs.add(doc)
        else:
            self.docs.new()

    def onDestroy(self, widget):
        try:
            settings = config["Window"]

            size = self.get_size()
            settings["Size"] = { "X": size.width, "Y": size.height }

            pos = self.get_position()
            settings["Position"] = { "X": pos.root_x, "Y": pos.root_y }

            # Unmap page from notebook to get pane position updated
            child = self.docs.get_current_child()
            if child: child.unmap()
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

