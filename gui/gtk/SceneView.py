from gui.gtk import Gtk, Gdk, Pango, GtkSource
from gui.gtk.SceneBuffer import SceneBuffer
import os

###############################################################################        

class ScrolledSceneList(Gtk.ScrolledWindow):

    def __init__(self, buffer, view = None):
        super(ScrolledSceneList, self).__init__()

        self.tree = SceneList(buffer, view)
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

        column = Gtk.TreeViewColumn("Words")
        self.append_column(column)

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

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text = 1)
        column.set_property("expand", True)
        self.append_column(column)

        self.connect("row-activated", self.onRowActivated)


    def onRowActivated(self, tree, path, col, *args):
        store = self.get_model()
        index = store.get_iter(path)
        mark = store.get_value(index, 0)
        at = self.buffer.get_iter_at_mark(mark)
        self.buffer.place_cursor(at)
        if self.view:
            self.view.scroll_to_mark(mark)
            self.view.grab_focus()

###############################################################################        

class ScrolledSceneView(Gtk.ScrolledWindow):

    def __init__(self, buffer, font = None):
        super(ScrolledSceneView, self).__init__()

        self.view = SceneView(buffer, font)
        self.add(self.view)

        #self.set_size_request(500, 500)

    #--------------------------------------------------------------------------

    def get_buffer(self): return self.view.get_buffer()
    def set_buffer(self, buffer): return self.view.set_buffer(buffer)

    def scroll_to_mark(self, mark = None, within = 0.2, use_align = True, xalign = 0.5, yalign = 0.5):
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

        self.set_pixels_inside_wrap(4)
        self.set_pixels_above_lines(2)
        self.set_pixels_below_lines(2)
        
        self.set_left_margin(30)
        self.set_right_margin(30)
        self.set_top_margin(30)
        self.set_bottom_margin(60)

        if font: self.modify_font(Pango.FontDescription(font))
        #self.modify_font(Pango.FontDescription("Times 12"))
        #self.modify_font(Pango.FontDescription("Sans 12"))
        #self.modify_font(Pango.FontDescription("Serif 12"))

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

    def set_hotkeys(self):    

        def undo():
            self.buffer.undo()
            return True

        def redo():
            self.buffer.redo()
            return True

        self._parse_keys({
            "<Ctrl>Z": undo,
            "<Ctrl><Shift>Z": redo,
            
            "<Alt>A": {
                "<Alt>A": self.fold_all,
                "<Alt>S": self.unfold_all,
            },
            "<Alt>F": self.toggle_fold,
            "<Alt>X": self.select_and_fold,
            
            #"<Alt>a": {
            #    "<Alt>f": self.fold_all,
            #    "<Alt>u": self.unfold_all,
            #},
            "<Alt>L": self.lorem,
            #"<Alt>c": self.toggle_comment,
            #"<Alt>x": self.toggle_fold,
            
            # Some fixed behaviour
            
            "<Ctrl>Up": self.fix_ctrl_up,
            "<Ctrl>Down": self.fix_ctrl_down,
            "<Ctrl><Shift>Up": self.fix_ctrl_shift_up,
            "<Ctrl><Shift>Down": self.fix_ctrl_shift_down,
            
            "<Alt>Up":   self.move_line_up,
            "<Alt>Down": self.move_line_down,
            "<Alt>Left": None,
            "<Alt>Right": None,

            "Return": self.unfold_current,
            "space":  self.unfold_current,
        })

    #--------------------------------------------------------------------------
    
    def _parse_keys(self, table):

        def parse_table(table):
            lookup = { }
            for shortcut, item in table.items():
                key = Gtk.accelerator_parse(shortcut)
                if type(item) is dict:
                    lookup[key] = parse_table(item)
                else:
                    lookup[key] = item
            return lookup
            
        self.combokeys = parse_table(table)
        self.combokey = None
        self.connect("key-press-event", self.onKeyPress)

    def onKeyPress(self, widget, event):
        mod = event.state & Gtk.accelerator_get_default_mod_mask()
        key = (event.keyval, mod)

        #print(Gtk.accelerator_name(event.keyval, mod))

        if self.combokey is None:
            if not key in self.combokeys: return False
            if type(self.combokeys[key]) is dict:
                self.combokey = self.combokeys[key]
                return True
            elif self.combokeys[key] is None:
                #self.parent.emit("key-press-event", event.copy())
                return True
            else:
                return self.combokeys[key]()
        else:
            combo = self.combokey
            self.combokey = None
            if key in combo:
                return combo[key]()

    #--------------------------------------------------------------------------
    
    def fix_ctrl_shift_up(self):   return self.fix_ctrl_up(True)
    def fix_ctrl_up(self, select = False):
        cursor = self.buffer.get_cursor_iter()
        if cursor.is_start(): return True
        if not cursor.starts_line():
            cursor = self.buffer.get_line_start_iter(cursor)
        else:
            cursor.backward_line()
            
        if select:
            self.buffer.move_mark(self.buffer.get_insert(), cursor)
        else:
            self.buffer.place_cursor(cursor)
        self.scroll_mark_onscreen(self.buffer.get_insert())
        return True
        
    def fix_ctrl_shift_down(self): return self.fix_ctrl_down(True)
    def fix_ctrl_down(self, select = False):
        cursor = self.buffer.get_cursor_iter()
        if cursor.is_end(): return True
        if not cursor.starts_line():
            cursor = self.buffer.get_line_end_iter(cursor)
            cursor.forward_char()
        else:
            cursor.forward_line()
            
        if select:
            self.buffer.move_mark(self.buffer.get_insert(), cursor)
        else:
            self.buffer.place_cursor(cursor)
        self.scroll_mark_onscreen(self.buffer.get_insert())
        return True
        
    #--------------------------------------------------------------------------
    
    def scroll_to_mark(self, mark = None, within = 0.2, use_align = True, xalign = 0.5, yalign = 0.5):
        if mark is None: mark = self.buffer.get_insert()
        super(SceneView, self).scroll_to_mark(mark, within, use_align, xalign, yalign)

    #--------------------------------------------------------------------------
    
    def toggle_fold(self):
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

    def fold_all(self):
        self.buffer.place_cursor(self.buffer.scene_start_iter())
        self.buffer.begin_user_action()
        self.foreach_scene(self.buffer.fold_on)
        self.buffer.end_user_action()
        self.scroll_to_mark()
        #self.scroll_mark_onscreen(self.buffer.get_insert())

    def unfold_all(self):
        self.buffer.begin_user_action()
        self.foreach_scene(self.buffer.fold_off)
        self.buffer.end_user_action()
        self.scroll_to_mark()
        #self.scroll_mark_onscreen(self.buffer.get_insert())

    def unfold_current(self):
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

    

    def select_and_fold(self):
        if self.buffer.get_has_selection():
            _, scene = self.buffer.get_selection_bounds()
            if(scene.is_end()): return
        else:
            scene = self.buffer.scene_start_iter()
            if not scene: return

            self.buffer.move_mark_by_name("insert", self.buffer.scene_start_iter())
        
        self.buffer.move_mark_by_name("selection_bound", self.buffer.scene_end_iter(scene))

        self.buffer.begin_user_action()
        self.buffer.fold_on(scene)
        self.buffer.end_user_action()
        self.scroll_mark_onscreen(self.buffer.get_insert())
    
    def move_line_up(self):
        return True
        #prev = self.scene_prev_iter(self.get_cursor_iter())
        #if not prev: prev = self.buffer.get_start_iter()
        #self.buffer.place_cursor(prev)
        #self.scroll_mark_onscreen(self.buffer.get_insert())
        #return True

    def move_line_down(self):
        return True
        #next = self.scene_next_iter(self.get_cursor_iter())
        #if not next: next = self.buffer.get_end_iter()
        #self.buffer.place_cursor(next)
        #self.scroll_mark_onscreen(self.buffer.get_insert())
        #return True
        
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

    def toggle_comment(self):
        self.buffer.begin_user_action()
        self.remove_block("<<")
        self.remove_block("#")
        self.toggle_block("//")
        self.buffer.end_user_action()

    def toggle_synopsis(self, accel, widget, keyval, modifiers):
        self.buffer.begin_user_action()
        self.remove_block("//")
        self.remove_block("#")
        self.toggle_block("<<")
        self.buffer.end_user_action()

    #--------------------------------------------------------------------------
    
    def lorem(self):
        self.buffer.begin_user_action()
        self.buffer.delete_selection(True, self.get_editable())
        cursor = self.buffer.get_insert()
        at     = self.buffer.get_iter_at_mark(cursor)
        self.buffer.insert(
            at,
            "*Lorem* ipsum dolor _sit_ amet, consectetur adipiscing " +
            "elit, sed do eiusmod tempor incididunt ut labore et " +
            "dolore magna aliqua. Ut enim ad minim veniam, quis " +
            "nostrud exercitation ullamco laboris nisi ut aliquip " +
            "ex ea commodo consequat. Duis aute irure dolor in " + 
            "reprehenderit in voluptate velit esse cillum dolore eu " +
            "fugiat nulla pariatur. Excepteur sint occaecat cupidatat " +
            "non proident, sunt in culpa qui officia deserunt mollit " +
            "anim id est laborum.\n",
            -1
        );
        self.buffer.end_user_action()
        self.scroll_mark_onscreen(self.buffer.get_insert())
        return True

