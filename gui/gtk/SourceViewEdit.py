from gui.gtk import Gtk, Gdk, Pango, GtkSource, GdkPixbuf
import os

###############################################################################        
###############################################################################        
#
class SceneBuffer(GtkSource.Buffer):
#
###############################################################################        
###############################################################################        

    def __init__(self, content = None):
        super(SceneBuffer, self).__init__()

        self.create_tags()
        self.marks = {}

        self.set_highlight_matching_brackets(False)

        self.connect      ("delete-range", self.beforeDeleteRange)
        self.connect_after("delete-range", self.afterDeleteRange)
        self.connect_after("insert-text",  self.afterInsertText)

        if content:
            print("Loading")
            self.begin_not_undoable_action()
            self.insert(self.get_start_iter(), content)
            self.end_not_undoable_action()
            self.place_cursor(self.get_start_iter())
        else:
            print("Empty")

    def create_tags(self):

        # Span tags
        self.create_tag("bold",   weight = Pango.Weight.BOLD)
        self.create_tag("italic", style  = Pango.Style.ITALIC)

        # Block tags
        self.create_tag("indent", indent = 30)
        self.create_tag("text")
        self.create_tag("comment",
            #foreground = "#474",
            paragraph_background = "#DFD",
        )
        self.create_tag("synopsis",
            paragraph_background = "#FFD",
        )
        self.create_tag("missing",
            foreground = "#B22",
        )

        # Heading tags
        self.create_tag("scene:heading",
            foreground = "#777",
            #justification = Gtk.Justification.CENTER,
            #weight = Pango.Weight.HEAVY,
            pixels_above_lines = 20,
            pixels_below_lines = 5,
        )
        self.create_tag("scene:folded",
            #foreground = "#777",
            paragraph_background = "#EEE",
            pixels_above_lines = 10,
            pixels_below_lines = 5,
            indent = -30,
            editable = False,
        )
        
        # Folding tags
        self.create_tag("fold:protect",
            editable = False,
            #background = "#EAE",
            #foreground = "#DDD",
        )
        self.create_tag("fold:hidden",
            editable   = False,
            invisible  = True,
            #background = "#EDD",
        )

        self.create_tag("debug:update",
            background = "#DDD",
        )

        self.tagtbl = self.get_tag_table()
        self.tag_scenehdr    = self.tagtbl.lookup("scene:heading")
        self.tag_scenefolded = self.tagtbl.lookup("scene:folded")
        self.tag_fold_prot   = self.tagtbl.lookup("fold:protect")
        self.tag_fold_hide   = self.tagtbl.lookup("fold:hidden")

        self.tag_reapplied = [
            self.tag_scenehdr, self.tag_scenefolded,
            "comment", "synopsis", "missing", "text",
        ]

    #--------------------------------------------------------------------------
    
    def get_cursor_iter(self):
        return self.get_iter_at_mark(self.get_insert())
    
    def copy_iter(self, at, line_delta, char_delta):
        at = at.copy()
        at.forward_lines(line_delta)
        at.forward_chars(char_delta)
        return at

    def get_line_start_iter(self, at = None):
        if at is None: at = self.get_cursor_iter()
        start = at.copy()
        start.set_line_offset(0)
        return start
    
    def get_line_end_iter(self, at = None):
        if at is None: at = self.get_cursor_iter()
        end = at.copy()
        if not end.ends_line(): end.forward_to_line_end()
        return end
            
    def get_line_iter(self, at = None):
        return self.get_line_start_iter(at), self.get_line_end_iter(at)

    def get_line_and_offset(self, at = None):
        if at is None: at = self.get_cursor_iter()
        return at.get_line(), at.get_line_offset()

    #--------------------------------------------------------------------------

    def expect_forward(self, start, text):
        end = self.copy_iter(start, 0, len(text))
        return self.get_text(start, end, True) == text

    def expect_backward(self, end, text):
        start = self.copy_iter(end, 0, -len(text))
        return self.get_text(start, end, True) == text

    def line_starts_with(self, text, at = None):
        if at is None: at = self.get_cursor_iter()
        return self.expect_forward(self.get_line_start_iter(at), text)

    def line_ends_with(self, text, at = None):
        if at is None: at = self.get_cursor_iter()
        return self.expect_backward(self.get_line_end_iter(at), text)
        
    #--------------------------------------------------------------------------

    def afterInsertText(self, buffer, end, text, length, *args):
        start = self.copy_iter(end, 0, -length)
        #self.dump_range("Insert", start, end)
        self.remove_scene_marks(start, end)
        self.update_tags(start, end)
    
    def beforeDeleteRange(self, buffer, start, end, *args):
        #self.dump_range("Delete", start, end)
        self.remove_scene_marks(start, end)
        
    def afterDeleteRange(self, buffer, start, end, *args):
        self.update_tags(start, end)
    
    #--------------------------------------------------------------------------

    def dump_iter(self, prefix, at):
        print("%s: %d:%d" % (prefix, *self.get_line_and_offset(at)))
        
    def dump_range(self, prefix, start, end):
        print("%s: %d:%d - %d:%d" % (
            prefix,
            *self.get_line_and_offset(start),
            *self.get_line_and_offset(end)
        ))

    #--------------------------------------------------------------------------

    def has_scene_mark(self, at):
        marks = self.get_source_marks_at_iter(at, "scene")
        return len(marks) > 0

    def scene_first_iter(self):
        at = self.get_start_iter()
        if self.has_scene_mark(at): return at
        return self.scene_next_iter(at)

    def scene_next_iter(self, at):
        at = at.copy()
        if not self.forward_iter_to_source_mark(at, "scene"):
            return None
        return at

    def scene_prev_iter(self, at):
        at = at.copy()
        if not self.backward_iter_to_source_mark(at, "scene"):
            return None
        return at

    def scene_start_iter(self, at = None):
        if at is None: at = self.get_cursor_iter()
        if self.has_scene_mark(at): return at.copy()
        return self.scene_prev_iter(at)
        
    def scene_end_iter(self, at = None):
        if at is None: at = self.get_cursor_iter()
        end = self.scene_next_iter(at)
        if end is None: return self.get_end_iter()
        return end

    def get_source_marks(self, category, start, end):
        marks = []
        at = start.copy()
        while at.compare(end) < 1:
            marks = marks + self.get_source_marks_at_iter(at)
            if not self.forward_iter_to_source_mark(at, category): break
        return marks

    def dump_mark(self, prefix, mark):
        if mark in self.marks:
            text = self.marks[mark]
        else:
            text = None
        category = mark.get_category()
        name = mark.get_name()
        line, offset = self.get_line_and_offset(self.get_iter_at_mark(mark))
        print("%s %s.%s: %d:%d %s" % (
            prefix,
            category, name,
            line + 1, offset,
            text[:20]
        ))

    def dump_source_marks(self, category, start, end):
        print("Marks:")
        for mark in self.get_source_marks(category, start, end):
            self.dump_mark("-", mark)

    def create_scene_mark(self, at):
        mark = self.create_source_mark(None, "scene", at)
        start, end = self.get_line_iter(at)
        self.marks[mark] = self.get_text(start, end, False)[2:].strip()

        #self.dump_mark("Created", mark)
        if self.is_folded(start):
            scene_end = self.scene_end_iter(end)
            self.apply_tag(self.tag_fold_prot, self.copy_iter(end, 0, -len(self.fold_mark)), scene_end)
            self.apply_tag(self.tag_fold_hide, end, scene_end)
            #self.dump_range("- Hide", end, scene_end)
            
        return mark

    def remove_scene_mark(self, mark):
        #self.dump_mark("Delete", mark)

        start = self.get_iter_at_mark(mark)
        end   = self.scene_end_iter(start)
        #self.dump_range("- Unhide", start, end)
        self.remove_tag(self.tag_fold_hide, start, end)
        self.remove_tag(self.tag_fold_prot, start, end)
        
        self.delete_mark(mark)
        del self.marks[mark]

    def remove_scene_marks(self, start, end):
        start = self.get_line_start_iter(start)
        end   = self.get_line_end_iter(end)

        for mark in self.get_source_marks("scene", start, end):
            self.remove_scene_mark(mark)

    def update_scene(self, start, end):
        self.apply_tag(self.tag_scenehdr, start, end)
        if self.is_folded(start):
            self.apply_tag(self.tag_scenefolded,
                self.copy_iter(start, 0, -1),
                end
            )

        self.create_scene_mark(start)

    #--------------------------------------------------------------------------
    # Folding:
    #--------------------------------------------------------------------------

    #fold_mark = " [folded]"
    fold_mark = " [⋅⋅⋅]"
    #fold_mark = " ▶"
    #fold_mark = " ⋙"
    #fold_mark = " [•••]"
    #fold_mark = " [＋]"

    def is_folded(self, at):
        return self.line_ends_with(self.fold_mark, at)

    def fold_on(self, at):
        if self.is_folded(at): return
        end = self.get_line_end_iter(at)
        self.insert(end, self.fold_mark)
        
    def fold_off(self, at):
        if not self.is_folded(at): return
        end = self.get_line_end_iter(at)
        self.delete(self.copy_iter(end, 0, -len(self.fold_mark)), end)

    #--------------------------------------------------------------------------
    # Updating text tags after changes (insert, delete)
    #--------------------------------------------------------------------------

    def has_tags(self, at, *tags):
        for tag in tags:
            if type(tag) is str: tag = self.tagtbl.lookup(tag)
            if at.has_tag(tag): return True
        return False
    
    def remove_tags(self, start, end, *tags):
        for tag in tags:
            if type(tag) is str: tag = self.tagtbl.lookup(tag)
            self.remove_tag(tag, start, end)
    
    def update_tags(self, start, end):
        line = self.get_line_start_iter(start)
        while(line.compare(self.get_line_end_iter(end)) < 1):
            self.update_line_tags(line, self.get_line_end_iter(line))
            if line.is_end(): break
            line.forward_line()
        self.update_indent(*self.get_line_iter(line))

        #scene = self.scene_start_iter(start)
        #self.fold_off(scene)

        #self.mark_range("debug:update", start, end)
        #self.dump_source_marks(None, *self.get_bounds())

    def update_line_tags(self, start, end):
        self.remove_tags(start, end, *self.tag_reapplied)
        
        if self.line_starts_with("##", start):
            self.update_scene(start, end)
        else:            
            if self.line_starts_with("//", start):
                self.apply_tag_by_name("comment", start, end)
            elif self.line_starts_with("<<", start):
                self.apply_tag_by_name("synopsis", start, end)
            elif self.line_starts_with("!!", start):
                self.apply_tag_by_name("missing", start, end)
            else:
                self.apply_tag_by_name("text", start, end)
            self.update_spans(start, end)

        self.update_indent(start, end)
        
    def update_indent(self, start, end):
        self.remove_tags(start, end, "indent")
        if(start.is_start()): return
        if start.has_tag(self.tag_scenehdr): return 
        if start.has_tag(self.tag_scenefolded): return 
        
        prev_start = start.copy()
        if(prev_start.is_start()): return
        prev_start.backward_line()
        prev_end = self.get_line_end_iter(prev_start)
        if(prev_start.equal(prev_end)): return
        if self.has_tags(prev_start, self.tag_scenehdr): return
        if self.has_tags(prev_start, "comment", "synopsis"):
            if not self.has_tags(prev_start, "indent"): return
        self.apply_tag_by_name("indent", start, end)
        #self.dump_range("Update indent", start, end)
    
    def update_spans(self, line_start, line_end):
        pass

    def mark_range(self, tagname, start, end):
        #self.dump_range("Update", start, end)
        self.remove_tag_by_name(tagname, *self.get_bounds())
        self.apply_tag_by_name(tagname, start, end)


###############################################################################        
###############################################################################        
#
class SceneEdit(Gtk.Frame):
#
###############################################################################        
###############################################################################        

    def __init__(self, buffer, font = None):
        super(SceneEdit, self).__init__()

        self.create_view(buffer)

        if font: self.text.modify_font(Pango.FontDescription(font))
        #self.text.modify_font(Pango.FontDescription("Times 12"))
        #self.text.modify_font(Pango.FontDescription("Sans 12"))
        #self.text.modify_font(Pango.FontDescription("Serif 12"))

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(400, 400)
        scrolled.add(self.text)

        self.add(scrolled)
        #self.set_default_size(600, 800)

        self.set_hotkeys()

    def create_view(self, buffer):
        #self.buffer = Gtk.TextBuffer()
        #self.text = Gtk.TextView.new_with_buffer(self.buffer)
        self.buffer = buffer
        self.text = GtkSource.View.new_with_buffer(self.buffer)

        self.create_source_mark_categories()

        self.text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        self.text.set_pixels_inside_wrap(4)
        self.text.set_pixels_above_lines(2)
        self.text.set_pixels_below_lines(2)
        
        self.text.set_left_margin(40)
        self.text.set_right_margin(40)
        self.text.set_top_margin(40)
        self.text.set_bottom_margin(80)

        #self.text.set_show_line_numbers(True)
        #self.text.set_show_right_margin(True)
        self.text.set_show_line_marks(True)
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
        }
        self.combokey = None
        self.connect("key-press-event", self.onKeyPress)

    def onKeyPress(self, widget, event):
        #keyval = Gdk.keyval_to_lower(event.keyval)
        mods   = event.state & Gtk.accelerator_get_default_mod_mask()
        key = Gtk.accelerator_name(
            event.keyval,
            mods, #Gdk.ModifierType(mods)
        )
        #print("Keyval:", keyval, "Mods:", Gdk.ModifierType(mods))
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

            self.buffer.move_mark_by_name("insert", self.scene_start_iter())
        
        self.buffer.move_mark_by_name("selection_bound", self.scene_end_iter(scene))

        self.buffer.begin_user_action()
        self.buffer.fold_on(scene)
        self.buffer.end_user_action()
        self.text.scroll_mark_onscreen(self.buffer.get_insert())
    
    def move_line_up(self):
        return False
        #prev = self.scene_prev_iter(self.get_cursor_iter())
        #if not prev: prev = self.buffer.get_start_iter()
        #self.buffer.place_cursor(prev)
        #self.text.scroll_mark_onscreen(self.buffer.get_insert())
        #return True

    def move_line_down(self):
        return False
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

