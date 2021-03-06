from gui.gtk import Gtk, Gdk, Pango, GtkSource, GObject
from gui.gtk.SceneBuffer import SceneBuffer
import os

from tools import *

###############################################################################        

###############################################################################        

class ScrolledSceneList(Gtk.ScrolledWindow):

    def __init__(self, buffer, view = None):
        super(ScrolledSceneList, self).__init__()

        self.tree = SceneList(buffer, view)
        #scrolled = Gtk.ScrolledWindow()
        #scrolled.add(self.tree)
        #self.add(scrolled)
        self.add(self.tree)

    def get_buffer(self): return self.tree.buffer
    def set_buffer(self, buffer):
        self.tree.buffer = buffer
        self.tree.set_model(buffer.marklist)
    def grab_focus(self): return self.tree.grab_focus()

#------------------------------------------------------------------------------

class SceneList(Gtk.TreeView):

    def __init__(self, buffer, view):
        super(SceneList, self).__init__(buffer.marklist)

        self.buffer = buffer
        self.view = view

        def dfNonZeros(col, cell, store, itr, args):
            words = store.get_value(itr, args)
            if words:
                cell.set_property("text", str(words))
            else:
                cell.set_property("text", "")

        #- Words --------------------------------------------------------------

        column = Gtk.TreeViewColumn("Words")
        column.set_property("expand", False)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1.0, 0.5)
        column.pack_start(renderer, False)
        column.add_attribute(renderer, 'text', 2)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1.0, 0.5)
        renderer.set_property("foreground", "green")
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, dfNonZeros, 3)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(1.0, 0.5)
        renderer.set_property("foreground", "red")
        column.pack_start(renderer, False)
        column.set_cell_data_func(renderer, dfNonZeros, 4)

        self.append_column(column)

        #- Name ---------------------------------------------------------------

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Name", renderer, text = 1)
        column.set_property("expand", True)
        #column.set_resizable(True)
        #column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        #column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        #column.set_fixed_width(200)
        #column.set_min_width(10)
        self.append_column(column)

        #----------------------------------------------------------------------
        
        self.connect("row-activated", self.onRowActivated)
        self.buffer.connect("current-scene", self.onCurrentScene)

        #----------------------------------------------------------------------
        # Drag'n'drop
        #----------------------------------------------------------------------
        
        return
        
        self.targets = [
            ("GTK_TREE_MODEL_ROWS", Gtk.TargetFlags.SAME_WIDGET, 0)
        ]
        
        self.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK,
            self.targets,
            Gdk.DragAction.MOVE
        )
        self.enable_model_drag_dest(self.targets, Gdk.DragAction.MOVE)

        #self.connect("drag-data-get", self.dragDataGet)
        #self.connect("drag-data-received", self.dragDataReceived)
        self.connect("drag-drop", self.dragDrop)

        self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        #self.drag_source_set_icon_stock(Gtk.STOCK_DND)
        
    #--------------------------------------------------------------------------
    
    def dragDrop(self, treeview, context, x, y, etime):
        dropzone = treeview.get_dest_row_at_pos(x,y)
        print("Drop at", dropzone)
        Gtk.drag_finish(context, False, False, etime)
        return True

    #--------------------------------------------------------------------------
    
    def onRowActivated(self, tree, path, col, *args):
        store = self.get_model()
        index = store.get_iter(path)
        mark = store.get_value(index, 0)
        at = self.buffer.get_iter_at_mark(mark)
        self.buffer.place_cursor(at)
        if self.view:
            self.view.scroll_to_mark(mark)
            self.view.grab_focus()

    def onCurrentScene(self, buf, mark):
        if mark:
            listiter = buf.markiter[mark]
            path = self.get_model().get_path(listiter)
            self.set_cursor(path)

###############################################################################        

class ScrolledSceneView(Gtk.ScrolledWindow):

    def __init__(self, buffer, font = None):
        super(ScrolledSceneView, self).__init__()

        self.view = SceneView(buffer, font)
        #scrolled = Gtk.ScrolledWindow()
        #scrolled.add(self.view)
        #self.add(scrolled)
        self.add(self.view)

        #self.set_size_request(500, 500)

    #--------------------------------------------------------------------------

    def get_buffer(self): return self.view.get_buffer()
    def set_buffer(self, buffer): return self.view.set_buffer(buffer)

    def scroll_to_mark(self, mark = None, within = 0.2, use_align = True, xalign = 0.5, yalign = 0.4):
        if mark is None: mark = self.view.get_buffer().get_insert()
        self.view.scroll_to_mark(mark, within, use_align, xalign, yalign)

    def grab_focus(self):
        self.view.grab_focus()

#------------------------------------------------------------------------------

class SceneView(GtkSource.View):

    def __init__(self, buffer, font = None):
        super(SceneView, self).__init__()

        self.buffer = buffer
        self.set_buffer(self.buffer)

        self.create_source_mark_categories()

        self.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        conf = config["TextView"]

        self.set_left_margin(30)
        self.set_right_margin(30)
        self.set_top_margin(30)
        self.set_bottom_margin(60)

        self.set_pixels_inside_wrap(2 * conf["linespacing"])
        self.set_pixels_above_lines(conf["linespacing"])
        self.set_pixels_below_lines(conf["linespacing"])

        font = Pango.FontDescription()
        font.set_family(conf["family"])
        font.set_size(conf["size"] * Pango.SCALE)
        self.modify_font(font)

        #self.set_show_line_numbers(True)
        #self.set_show_right_margin(True)
        #self.set_show_line_marks(True)
        #self.set_highlight_current_line(True)

        self.set_hotkeys()

    #--------------------------------------------------------------------------
    
    def create_source_mark_categories(self):
        def add_category(category, background = None, prio = 0):
            attr = GtkSource.MarkAttributes.new()
            if background:
                color = Gdk.RGBA()
                color.parse(background)
                attr.set_background(color)
            self.set_mark_attributes(category, attr, prio)
            
        add_category("scene")

    #--------------------------------------------------------------------------

    __gsignals__ = {
        "focus-left"  : (GObject.SIGNAL_RUN_LAST, None, ()),
        "focus-right" : (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    def set_hotkeys(self):    

        def undo(mod, key):
            self.buffer.undo()
            return True

        def redo(mod, key):
            self.buffer.redo()
            return True

        from gui.gtk.factory import ShortCut
        ShortCut.bind(self, {
            "<Ctrl>Z": undo,
            "<Ctrl><Shift>Z": redo,
            
            #"<Alt>A": {
                "<Alt>A": self.fold_all,
                "<Alt>S": self.unfold_all,
            #},
            "<Alt>F": self.toggle_fold,
            "<Alt>X": self.select_and_fold,
            
            #"<Alt>a": {
            #    "<Alt>f": self.fold_all,
            #    "<Alt>u": self.unfold_all,
            #},
            #"<Alt>c": self.toggle_comment,
            #"<Alt>x": self.toggle_fold,
            
            # Some fixed behaviour
            
            "<Ctrl>Up": self.paragraph_up,
            "<Ctrl>Down": self.paragraph_down,
            "<Ctrl><Shift>Up": self.paragraph_up,
            "<Ctrl><Shift>Down": self.paragraph_down,
            
            "<Alt>Up":   self.scene_up,
            "<Alt>Down": self.scene_down,
            "<Alt>Left": self.focus_left,
            "<Alt>Right": self.focus_right,

            "Return": self.unfold_current,
            "space":  self.unfold_current,
        })

    #--------------------------------------------------------------------------
    
    def focus_left(self, mod, key):
        self.emit("focus-left")
        return True

    def focus_right(self, mod, key):
        self.emit("focus-right")
        return True
    
    def paragraph_up(self, mod, key):
        cursor = self.buffer.get_cursor_iter()
        if cursor.is_start(): return True
        if not cursor.starts_line():
            cursor = self.buffer.get_line_start(cursor)
        else:
            cursor.backward_line()
            
        if mod & Gdk.ModifierType.SHIFT_MASK:
            self.buffer.move_mark(self.buffer.get_insert(), cursor)
        else:
            self.buffer.place_cursor(cursor)
        self.scroll_mark_onscreen(self.buffer.get_insert())
        return True
        
    def paragraph_down(self, mod, key):
        cursor = self.buffer.get_cursor_iter()
        if cursor.is_end(): return True
        if not cursor.starts_line():
            cursor = self.buffer.get_line_end(cursor)
            cursor.forward_char()
        else:
            cursor.forward_line()
            
        if mod & Gdk.ModifierType.SHIFT_MASK:
            self.buffer.move_mark(self.buffer.get_insert(), cursor)
        else:
            self.buffer.place_cursor(cursor)
        self.scroll_mark_onscreen(self.buffer.get_insert())
        return True
        
    def scene_up(self, mod, key):
        at = self.buffer.get_cursor_iter()
        scene_start = self.buffer.scene_start_iter(at)
        if at.equal(scene_start):
            scene_start = self.buffer.scene_prev_iter(at)
            if scene_start is None: scene_start = self.buffer.get_start_iter()
        self.buffer.place_cursor(scene_start)
        self.scroll_mark_onscreen(self.buffer.get_insert())
        
        return True

    def scene_down(self, mod, key):
        at = self.buffer.get_cursor_iter()
        scene_start = self.buffer.scene_next_iter(at)
        if scene_start is None: scene_start = self.buffer.get_end_iter()
        self.buffer.place_cursor(scene_start)
        self.scroll_mark_onscreen(self.buffer.get_insert())

        return True
        
    #--------------------------------------------------------------------------
    
    def scroll_to_mark(self, mark = None, within = 0.2, use_align = True, xalign = 0.5, yalign = 0.5):
        if mark is None: mark = self.buffer.get_insert()
        super(SceneView, self).scroll_to_mark(mark, within, use_align, xalign, yalign)

    #--------------------------------------------------------------------------
    
    def toggle_fold(self, mod, key):
        scene = self.buffer.scene_start_iter()

        if not scene: return
        
        self.buffer.begin_user_action()
        
        if self.buffer.is_folded(scene):
            self.buffer.fold_off(scene)
        else:
            if self.buffer.get_has_selection():
                self.buffer.move_mark(self.buffer.get_insert(), scene)
            else:
                self.buffer.place_cursor(scene)
            self.buffer.fold_on(scene)

        self.buffer.end_user_action()
        self.scroll_mark_onscreen(self.buffer.get_insert())

    def foreach_scene(self, func):
        scenes = self.buffer.get_marks("scene", *self.buffer.get_bounds())
        for scene in scenes:
            start = self.buffer.get_iter_at_mark(scene)
            func(start)

    def fold_all(self, mod, key):
        self.buffer.place_cursor(self.buffer.scene_start_iter())
        self.buffer.begin_user_action()
        self.foreach_scene(self.buffer.fold_on)
        self.buffer.end_user_action()
        self.scroll_to_mark()
        #self.scroll_mark_onscreen(self.buffer.get_insert())

    def unfold_all(self, mod, key):
        self.buffer.begin_user_action()
        self.foreach_scene(self.buffer.fold_off)
        self.buffer.end_user_action()
        self.scroll_to_mark()
        #self.scroll_mark_onscreen(self.buffer.get_insert())

    def unfold_current(self, mod, key):
        scene = self.buffer.scene_start_iter()

        if not scene: return
        if not self.buffer.is_folded(scene): return
        
        self.buffer.begin_user_action()
        self.buffer.fold_off(scene)
        self.buffer.end_user_action()
        
        cursor = self.buffer.get_cursor_iter()
        cursor.forward_line()
        self.buffer.place_cursor(cursor)
        self.scroll_mark_onscreen(self.buffer.get_insert())
        return True

    def select_and_fold(self, mod, key):
        if self.buffer.get_has_selection():
            _, scene = self.buffer.get_selection_bounds()
            if(scene.is_end()): return
        else:
            scene = self.buffer.scene_start_iter()
            if not scene: return

            self.buffer.move_mark_by_name("insert", self.buffer.scene_start_iter())
        
        self.buffer.move_mark_by_name("selection_bound", self.buffer.scene_end_iter(scene))

        self.buffer.begin_user_action()
        # self.buffer.fold_on(scene)
        self.buffer.end_user_action()
        self.scroll_mark_onscreen(self.buffer.get_insert())
    
    #--------------------------------------------------------------------------

    def remove_block(self, starts_with):
        start, end = self.buffer.get_line_iter()
        if self.buffer.line_starts_with(starts_with):
            self.buffer.delete(
                start,
                self.buffer.copy_iter(start, 0, len(starts_with))
            )

    def toggle_block(self, starts_with):
        start, end = self.buffer.get_line_iter()
        if self.buffer.line_starts_with(starts_with):
            self.buffer.delete(
                start,
                self.buffer.copy_iter(start, 0, len(starts_with))
            )
        else:
            self.buffer.insert(start, starts_with)

    def toggle_comment(self, mod, key):
        self.buffer.begin_user_action()
        self.remove_block("<<")
        self.remove_block("#")
        self.toggle_block("//")
        self.buffer.end_user_action()

    def toggle_synopsis(self, mod, key):
        self.buffer.begin_user_action()
        self.remove_block("//")
        self.remove_block("#")
        self.toggle_block("<<")
        self.buffer.end_user_action()

