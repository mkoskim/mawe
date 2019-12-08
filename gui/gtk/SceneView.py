from gui.gtk import Gtk, Gdk, Pango, GtkSource
from gui.gtk.SceneBuffer import SceneBuffer
import os

###############################################################################        
###############################################################################        
#
class SceneView(Gtk.ScrolledWindow):
#
###############################################################################        
###############################################################################        

    def __init__(self, buffer, font = None):
        super(SceneView, self).__init__()

        self.create_view(buffer)

        if font: self.text.modify_font(Pango.FontDescription(font))
        #self.text.modify_font(Pango.FontDescription("Times 12"))
        #self.text.modify_font(Pango.FontDescription("Sans 12"))
        #self.text.modify_font(Pango.FontDescription("Serif 12"))

        self.set_size_request(500, 500)
        self.add(self.text)

    #--------------------------------------------------------------------------
    
    def create_view(self, buffer):
        #self.buffer = Gtk.TextBuffer()
        #self.text = Gtk.TextView.new_with_buffer(self.buffer)
        self.buffer = buffer
        self.text = GtkSource.View.new_with_buffer(self.buffer)
        self.set_hotkeys()

        self.create_source_mark_categories()

        self.text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        self.text.set_pixels_inside_wrap(4)
        self.text.set_pixels_above_lines(2)
        self.text.set_pixels_below_lines(2)
        
        self.text.set_left_margin(30)
        self.text.set_right_margin(30)
        self.text.set_top_margin(30)
        self.text.set_bottom_margin(60)

        #self.text.set_show_line_numbers(True)
        #self.text.set_show_right_margin(True)
        #self.text.set_show_line_marks(True)
        #self.text.set_highlight_current_line(True)

    #--------------------------------------------------------------------------
    
    def create_source_mark_categories(self):
        def add_category(category, background = None, prio = 0):
            attr = GtkSource.MarkAttributes.new()
            if background:
                color = Gdk.RGBA()
                color.parse(background)
                attr.set_background(color)
            self.text.set_mark_attributes(category, attr, prio)
            
        add_category("scene")

    #--------------------------------------------------------------------------

    def set_hotkeys(self):    
        #accel = Gtk.AccelGroup()
        #accel.connect(*Gtk.accelerator_parse("<Alt>L"), 0, self.lorem)
        #accel.connect(*Gtk.accelerator_parse("<Alt>C"), 0, self.toggle_comment)
        #accel.connect(*Gtk.accelerator_parse("<Alt>S"), 0, self.toggle_synopsis)
        #accel.connect(*Gtk.accelerator_parse("<Alt>X"), 0, self.toggle_fold)

        #accel.connect(*Gtk.accelerator_parse("<Ctrl>S"), 0, self.save)
        #accel.connect(*Gtk.accelerator_parse("<Ctrl>Q"), 0, Gtk.main_quit)

        #accel.connect(*Gtk.accelerator_parse("<Alt>Up"), 0, self.move_line_up)
        #accel.connect(*Gtk.accelerator_parse("<Alt>Down"), 0, self.move_line_down)

        #self.add_accel_group(accel)

        def undo():
            self.buffer.undo()
            return True

        def redo():
            self.buffer.redo()
            return True

        self.combokeys = {
            "<Primary>z": undo,
            "<Primary><Shift>z": redo,
            "<Primary>q": lambda: Gtk.main_quit(),
            "<Alt>a": {
                "<Alt>f": self.fold_all,
                "<Alt>u": self.unfold_all,
            },
            "<Alt>c": self.toggle_comment,
            "<Alt>g": self.select_and_fold,
            "<Alt>l": self.lorem,
            "<Alt>x": self.toggle_fold,
            
            # Some fixed behaviour
            
            "<Primary>Up": self.fix_ctrl_up,
            "<Primary>Down": self.fix_ctrl_down,
            "<Primary><Shift>Up": self.fix_ctrl_shift_up,
            "<Primary><Shift>Down": self.fix_ctrl_shift_down,
            
            "<Alt>Up":   self.move_line_up,
            "<Alt>Down": self.move_line_down,
            
            "Return": self.enter,
        }
        self.combokey = None
        self.text.connect("key-press-event", self.onKeyPress)

    def onKeyPress(self, widget, event):
        #keyval = Gdk.keyval_to_lower(event.keyval)
        mods   = event.state & Gtk.accelerator_get_default_mod_mask()
        key = Gtk.accelerator_name(
            event.keyval,
            mods, #Gdk.ModifierType(mods)
        )
        #print("Key:", key, "Mods:", Gdk.ModifierType(mods))
        #print("Combo:", self.combokey, "Key:", key)
        if self.combokey == None:
            if not key in self.combokeys: return False
            if type(self.combokeys[key]) is dict:
                self.combokey = key
                return True
            else:
                return self.combokeys[key]()
        else:
            combo = self.combokey
            self.combokey = None
            if key in self.combokeys[combo]:
                return self.combokeys[combo][key]()

    #--------------------------------------------------------------------------

    def enter(self):
        cursor = self.buffer.get_cursor_iter()
        if cursor.has_tag(self.buffer.tag_scenefolded):
            self.buffer.fold_off(self.buffer.get_cursor_iter())
            return True
        return False
    
    #--------------------------------------------------------------------------
    
    def fix_ctrl_shift_up(self):   return self.fix_ctrl_up(True)
    def fix_ctrl_up(self, select = False):
        cursor = self.get_cursor_iter()
        if cursor.is_start(): return True
        if not cursor.starts_line():
            cursor = self.buffer.get_line_start_iter(cursor)
        else:
            cursor.backward_line()
            
        if select:
            self.buffer.move_mark(self.buffer.get_insert(), cursor)
        else:
            self.buffer.place_cursor(cursor)
        self.text.scroll_mark_onscreen(self.buffer.get_insert())
        return True
        
    def fix_ctrl_shift_down(self): return self.fix_ctrl_down(True)
    def fix_ctrl_down(self, select = False):
        cursor = self.get_cursor_iter()
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
        self.text.scroll_mark_onscreen(self.buffer.get_insert())
        return True
        
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
        self.text.scroll_mark_onscreen(self.buffer.get_insert())

    def foreach_scene(self, func, exclude_current = True):
        scenes = self.buffer.get_source_marks("scene", *self.buffer.get_bounds())
        for scene in scenes:
            start = self.buffer.get_iter_at_mark(scene)
            if exclude_current:
                end = self.buffer.scene_end_iter(start)
                cursor = self.buffer.get_cursor_iter()
                if cursor.in_range(start, end): continue
            func(start)

    def fold_all(self, exclude_current = True):
        self.buffer.begin_user_action()
        self.foreach_scene(self.buffer.fold_on, exclude_current)
        self.buffer.end_user_action()
        self.text.scroll_mark_onscreen(self.buffer.get_insert())

    def unfold_all(self, exclude_current = False):
        self.buffer.begin_user_action()
        self.foreach_scene(self.buffer.fold_off, exclude_current)
        self.buffer.end_user_action()
        self.text.scroll_mark_onscreen(self.buffer.get_insert())

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
        self.text.scroll_mark_onscreen(self.buffer.get_insert())
    
    def move_line_up(self):
        return True
        #prev = self.scene_prev_iter(self.get_cursor_iter())
        #if not prev: prev = self.buffer.get_start_iter()
        #self.buffer.place_cursor(prev)
        #self.text.scroll_mark_onscreen(self.buffer.get_insert())
        #return True

    def move_line_down(self):
        return True
        #next = self.scene_next_iter(self.get_cursor_iter())
        #if not next: next = self.buffer.get_end_iter()
        #self.buffer.place_cursor(next)
        #self.text.scroll_mark_onscreen(self.buffer.get_insert())
        #return True
        
    #--------------------------------------------------------------------------

    def remove_block(self, starts_with):
        if self.buffer.line_starts_with(starts_with):
            self.buffer.delete(start, end)

    def toggle_block(self, starts_with):
        if self.buffer.line_starts_with(starts_with):
            self.buffer.delete(start, end)
        else:
            self.buffer.insert(start, starts_with)

    def toggle_comment(self):
        tag = self.tagtbl.lookup("comment")
        visible = not tag.get_property("invisible")
        tag.set_property("invisible", visible)
        tag.set_property("editable",  not visible)
        #self.buffer.begin_user_action()
        #self.remove_block("<<")
        #self.remove_block("#")
        #self.toggle_block("//")
        #self.buffer.end_user_action()
        self.text.scroll_mark_onscreen(self.buffer.get_insert())

    def toggle_synopsis(self, accel, widget, keyval, modifiers):
        self.buffer.begin_user_action()
        self.remove_block("//")
        self.remove_block("#")
        self.toggle_block("<<")
        self.buffer.end_user_action()

    #--------------------------------------------------------------------------
    
    def save(self, accel, widget, keyval, modifiers):
        def dump_styles():
            for styleid in self.buffer.get_language().get_style_ids():
                style = self.buffer.get_style_scheme().get_style(styleid)
                print(styleid, style)
            
        def dumptag(tag):
            print(tag.get_property("name"))

        def dumptags():
            self.tagtbl.foreach(dumptag)
         
        def dump_source_marks_at(at = None):
            for mark in self.get_source_marks(at):
                print(mark.get_property("category"), mark.get_property("name"))

        def dump_text():
            text = self.buffer.get_text(*self.buffer.get_bounds(), True)
            print(text)

        #dump_source_marks_at()
        #dump_contexts_at(self.get_cursor_iter())
        dump_text()
        return True

    #--------------------------------------------------------------------------
    
    def lorem(self):
        self.buffer.begin_user_action()
        self.buffer.delete_selection(True, self.text.get_editable())
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
        self.text.scroll_mark_onscreen(self.buffer.get_insert())
        return True

