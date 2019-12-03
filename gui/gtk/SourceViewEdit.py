from gui.gtk import Gtk, Gdk, Pango, GtkSource, GdkPixbuf
import os

#------------------------------------------------------------------------------

class SceneGroupEdit(Gtk.Window):

    def __init__(self, content = None):
        super(SceneGroupEdit, self).__init__(title = "mawesome")

        self.create_view()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(500, 500)
        scrolled.add(self.text)

        self.add(scrolled)
        self.set_default_size(600, 800)

        self.set_hotkeys()

        if content:
            self.buffer.begin_not_undoable_action()
            self.buffer.insert(self.buffer.get_start_iter(), content)
            self.buffer.end_not_undoable_action()

    def create_view(self):
        self.buffer = GtkSource.Buffer()
        self.buffer.set_highlight_matching_brackets(False)

        self.buffer.connect      ("delete-range", self.beforeDeleteRange)
        self.buffer.connect_after("delete-range", self.afterDeleteRange)
        self.buffer.connect_after("insert-text",  self.afterInsertText)

        self.text = GtkSource.View.new_with_buffer(self.buffer)

        provider = Gtk.CssProvider()
        provider.load_from_data(
            b"""
            .view {
                padding-left: 1cm;
                padding-right: 1cm;
                padding-top: 0.5cm;
                padding-bottom: 2cm;
            }
            """
        )
        self.text.get_style_context().add_provider(
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.text.modify_font(Pango.FontDescription("Times 12"))
        #self.text.modify_font(Pango.FontDescription("Sans 12"))
        #self.text.modify_font(Pango.FontDescription("Serif 12"))
        self.text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text.set_pixels_inside_wrap(4)
        self.text.set_pixels_above_lines(2)
        self.text.set_pixels_below_lines(2)
        
        #self.text.set_show_line_numbers(True)
        #self.text.set_show_right_margin(True)

        self.create_tags()
        self.create_source_mark_categories()

    def create_tags(self):
        self.tagtbl = self.buffer.get_tag_table()

        self.buffer.create_tag("bold",
            weight = Pango.Weight.BOLD,
        )

        self.buffer.create_tag("text")
        self.buffer.create_tag("noindent",
            indent = 0,
        )
        self.buffer.create_tag("indent",
            indent = 30,
        )
        self.buffer.create_tag("comment",
            paragraph_background = "#DFD",
        )
        self.buffer.create_tag("synopsis",
            paragraph_background = "#FFD",
        )
        self.buffer.create_tag("missing",
            foreground = "#B22",
        )

        self.buffer.create_tag("heading:scene",
            foreground = "#888",
            #justification = Gtk.Justification.CENTER,
            weight = Pango.Weight.BOLD,
            pixels_above_lines = 20,
            pixels_below_lines = 5,
        )
        self.tag_prot = self.buffer.create_tag("protected",
            editable = False,
            #background = "#EFE",
        )
        self.tag_hide = self.buffer.create_tag("hidden",
            editable   = False,
            invisible  = True,
            background = "#EDD",
        )

        self.buffer.create_tag("debug:update",
            background = "#DDD",
        )

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

        self.combokeys = {
            "<Primary>q": lambda: Gtk.main_quit(),
            "<Alt>a": {
                "<Alt>f": self.fold_all,
                "<Alt>u": self.unfold_all,
            },
            "<Alt>l": self.lorem,
            "<Alt>x": self.toggle_fold,
        }
        self.combokey = None
        self.connect("key-press-event", self.onKeyPress)

    def onKeyPress(self, widget, event):
        keyval = Gdk.keyval_to_lower(event.keyval)
        mods   = event.state & Gtk.accelerator_get_default_mod_mask()
        key = Gtk.accelerator_name_with_keycode(
            None,
            keyval,
            event.hardware_keycode,
            Gdk.ModifierType(mods)
        )
        print("Combo:", self.combokey, "Key:", key)
        if self.combokey == None:
            if not key in self.combokeys: return
            if type(self.combokeys[key]) is dict:
                self.combokey = key
            else:
                self.combokeys[key]()
        else:
            if key in self.combokeys[self.combokey]:
                self.combokeys[self.combokey][key]()
            self.combokey = None

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
        self.marks = {}
        #self.text.set_show_line_marks(True)
    
    def get_source_marks(self, category, start, end):
        marks = []
        iter = start.copy()
        while iter.compare(end) < 1:
            marks = marks + self.buffer.get_source_marks_at_iter(iter)
            if not self.buffer.forward_iter_to_source_mark(iter, category): break
        return marks

    def dump_mark(self, prefix, mark):
        if mark in self.marks:
            text = self.marks[mark]
        else:
            text = None
        category = mark.get_category()
        name = mark.get_name()
        line, offset = self.get_line_and_offset(self.buffer.get_iter_at_mark(mark))
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

    #--------------------------------------------------------------------------

    def testkey(self, accel, widget, keyval, modifiers):
        def insert_label():
            cursor = self.get_cursor_iter()
            label = Gtk.Label()
            label.set_text("...")
            label.set_visible(True)
            anchor = self.buffer.create_child_anchor(cursor)
            self.text.add_child_at_anchor(label, anchor)
            
        def toggle_tag_to_line(tagname):
            tag = self.tagtbl.lookup(tagname)
            cursor = self.get_cursor_iter()
            start, end = self.get_line_iter()
            start.backward_char()

            if cursor.has_tag(tag):
                self.buffer.remove_tag(tag, start, end)
            else:
                self.buffer.apply_tag(tag, start, end)

        def apply_source_mark_to_line():
            cursor = self.get_line_start_iter()
            self.toggle_source_mark("scene")

        #toggle_tag_to_line("folded")
        #apply_source_mark_to_line()

    #--------------------------------------------------------------------------
    
    def get_cursor_iter(self):
        return self.buffer.get_iter_at_mark(self.buffer.get_insert())
    
    def copy_iter(self, iter, line_delta, char_delta):
        iter = iter.copy()
        iter.forward_lines(line_delta)
        iter.forward_chars(char_delta)
        return iter

    def get_line_start_iter(self, iter = None):
        if iter is None: iter = self.get_cursor_iter()
        start = iter.copy()
        start.set_line_offset(0)
        return start
    
    def get_line_end_iter(self, iter = None):
        if iter is None: iter = self.get_cursor_iter()
        end = iter.copy()
        if not end.ends_line(): end.forward_to_line_end()
        return end
            
    def get_line_iter(self, iter = None):
        return self.get_line_start_iter(iter), self.get_line_end_iter(iter)

    def get_line_and_offset(self, iter = None):
        if iter is None: iter = self.get_cursor_iter()
        return iter.get_line(), iter.get_line_offset()

    def expect_forward(self, text, start):
        end = self.copy_iter(start, 0, len(text))
        return self.buffer.get_text(start, end, True) == text

    def expect_backward(self, text, end):
        start = self.copy_iter(end, 0, -len(text))
        return self.buffer.get_text(start, end, True) == text

    def line_starts_with(self, text, iter = None):
        if iter is None: iter = self.get_cursor_iter()
        return self.expect_forward(text, self.get_line_start_iter(iter))

    def line_ends_with(self, text, iter = None):
        if iter is None: iter = self.get_cursor_iter()
        return self.expect_backward(text, self.get_line_end_iter(iter))
        
    #--------------------------------------------------------------------------

    def dump_iter(self, prefix, iter):
        print("%s: %d:%d" % (prefix, *self.get_line_and_offset(iter)))
        
    def dump_range(self, prefix, start, end):
        print("%s: %d:%d - %d:%d" % (
            prefix,
            *self.get_line_and_offset(start),
            *self.get_line_and_offset(end)
        ))

    #--------------------------------------------------------------------------

    def afterInsertText(self, buffer, end, text, length, *args):
        start = self.copy_iter(end, 0, -length)
        self.remove_protection(start, end)
        self.remove_marks(start, end)
        self.update_tags(start, end)
    
    def beforeDeleteRange(self, buffer, start, end, *args):
        self.dump_range("Delete", start, end)
        self.remove_protection(start, end)
        self.remove_marks(start, end)
        
    def afterDeleteRange(self, buffer, start, end, *args):
        self.update_tags(start, end)
    
    def move_line_up(self, accel, widget, keyval, modifiers):
        print("Move up")

    def move_line_down(self, accel, widget, keyval, modifiers):
        print("Move down")

    #--------------------------------------------------------------------------
    # Scene mark mechanism: If line starts with '##', it is a scene header:
    #
    # \n<mark>##
    # |-prot--|
    #
    # We place the mark at the beginning of the line, and protect newline
    # and first '#'. This ensures that the mark moves with line. The second
    # '#' is not protected, which allows users to remove scene heading.
    #
    # Folding is indicated by ending the scene header with special 'tag'.
    # (see fold_marker). Adding this to the end of the header will protect
    # the entire header line (to prevent users to split the line), and hide
    # everything to the next scene header.
    #
    #--------------------------------------------------------------------------

    fold_marker = " ···"

    #--------------------------------------------------------------------------
    # Called at the beginning of the update cycle. This removes protection tags,
    # which are reapplied to correctly formed header lines. In addition, we scan
    # for marks that are no longer on the valid position, and remove them.

    def remove_protection(self, start, end):
        start = self.get_line_start_iter(start)
        end = self.get_line_end_iter(end)

        self.buffer.remove_tag(self.tag_prot, self.copy_iter(start, 0, -1), end)

    def remove_marks(self, start, end):
        start = self.get_line_start_iter(start)
        end   = self.get_line_end_iter(end)

        for mark in self.get_source_marks(None, start, end):
            self.dump_mark("Delete", mark)
            self.buffer.delete_mark(mark)
            del self.marks[mark]

    #--------------------------------------------------------------------------
    # Called from update cycle, when a valid scene header (starting with '##')
    # is found. Reapply protection, update scene name to buffer, and update
    # scene folding.

    def apply_scene(self, start, end):
        self.buffer.apply_tag_by_name("heading:scene", start, end)

        prot_start = self.copy_iter(start, 0, -1)
        prot_end   = self.copy_iter(start, 0, +1)
        self.buffer.apply_tag(self.tag_prot, prot_start, prot_end)

        # Create scene marker

        mark = self.buffer.create_source_mark(None, "scene", start)
        self.marks[mark] = self.buffer.get_text(start, end, False)[2:].strip()
        self.dump_mark("Created", mark)

        # Update folding

        next_scene = end.copy()
        if not self.buffer.forward_iter_to_source_mark(next_scene, "scene"):
            next_scene = self.buffer.get_end_iter()
            prot_to = next_scene
        else:
            prot_to = self.copy_iter(next_scene, 0, -1)

        if self.line_ends_with(self.fold_marker, end):
            if not end.has_tag(self.tag_prot):
                self.buffer.apply_tag(self.tag_prot, start, next_scene)
                self.buffer.apply_tag(self.tag_hide, end, next_scene)
        else:
            if end.has_tag(self.tag_prot):
                self.buffer.remove_tag(self.tag_hide, end, next_scene)
                self.buffer.remove_tag(self.tag_prot, start, prot_to)

    #--------------------------------------------------------------------------
    # Toggle fold marker at the end of the scene header line. Let the
    # update cycle to apply correct tags to buffer.

    def is_folded(self, iter):
        return self.line_ends_with(self.fold_marker, iter)

    def fold_off(self, iter):
        if not self.is_folded(iter): return
        end   = self.get_line_end_iter(iter)
        start = self.copy_iter(end, 0, -len(self.fold_marker))
        self.buffer.delete(start, end)

    def fold_on(self, iter):
        if self.is_folded(iter): return
        end = self.get_line_end_iter(iter)
        self.buffer.insert(end, self.fold_marker)

    def toggle_fold(self):
        cursor = self.get_cursor_iter()
        marks  = self.buffer.get_source_marks_at_iter(cursor, "scene")
        if not marks:
            if not self.buffer.backward_iter_to_source_mark(cursor, "scene"): return

        self.buffer.begin_user_action()

        if self.is_folded(cursor):
            self.fold_off(cursor)
        else:
            self.fold_on(cursor)
            self.buffer.place_cursor(self.get_line_start_iter(cursor))

        self.buffer.end_user_action()

    def foreach_scene(self, func, exclude_current = True):
        marks = self.get_source_marks(
            "scene",
            self.buffer.get_start_iter(),
            self.buffer.get_end_iter()
        )
        if not len(marks): return
        
        self.buffer.begin_user_action()

        for i in range(len(marks)):
            start  = self.buffer.get_iter_at_mark(marks[i])
            
            if exclude_current:
                if i < len(marks)-1:
                    end = self.buffer.get_iter_at_mark(marks[i+1])
                else:
                    end = self.buffer.get_end_iter()
                cursor = self.get_cursor_iter()
                if cursor.in_range(start, end): continue
            
            func(start)

        self.buffer.end_user_action()
        self.text.scroll_mark_onscreen(self.buffer.get_insert())
        
    def fold_all(self):
        print("Fold all")
        self.foreach_scene(self.fold_on, True)
        
    def unfold_all(self):
        print("Unfold all")
        self.foreach_scene(self.fold_off, True)
        
    #--------------------------------------------------------------------------
    # Updating text tags after changes (insert, delete)
    #--------------------------------------------------------------------------

    def has_tags(self, iter, *tagnames):
        for tagname in tagnames:
            tag = self.tagtbl.lookup(tagname)
            if iter.has_tag(tag): return True
        return False
        
    def update_tags(self, start, end):
        line = self.get_line_start_iter(start)
        while(line.compare(self.get_line_end_iter(end)) < 1):
            self.update_line_tags(line, self.get_line_end_iter(line))
            if line.is_end(): break
            line.forward_line()
        self.update_indent(*self.get_line_iter(line))

        #self.mark_range("debug:update", start, end)
        self.dump_source_marks(
            None,
            self.buffer.get_start_iter(),
            self.buffer.get_end_iter()
        )

    def update_line_tags(self, start, end):
        self.buffer.remove_all_tags(start, end)
        
        if self.line_starts_with("##", start):
            self.apply_scene(start, end)
            return
            
        if self.line_starts_with("//", start):
            self.buffer.apply_tag_by_name("comment", start, end)
        elif self.line_starts_with("<<", start):
            self.buffer.apply_tag_by_name("synopsis", start, end)
        elif self.line_starts_with("!!", start):
            self.buffer.apply_tag_by_name("missing", start, end)
        else:
            self.buffer.apply_tag_by_name("text", start, end)

        self.update_indent(start, end)
        self.update_spans(start, end)
        
    def update_indent(self, start, end):
        self.buffer.remove_tag_by_name("indent", start, end)

        if(start.is_start()): return
        if self.has_tags(start, "heading:scene"): return 
        
        prev_start = start.copy()
        while True:
            if(prev_start.is_start()): return
            prev_start.backward_line()
            prev_end = self.get_line_end_iter(prev_start)
            if(prev_start.equal(prev_end)): return
            if self.has_tags(prev_start, "heading:scene"): return
            if self.has_tags(prev_start, "comment", "synopsis"): continue
            break
            
        self.buffer.apply_tag_by_name("indent", start, end)
        #self.dump_range("Update indent", start, end)
    
    def update_spans(self, line_start, line_end):
        pass

    def mark_range(self, tagname, start, end):
        #self.dump_range("Update", start, end)
        self.buffer.remove_tag_by_name(
            tagname,
            self.buffer.get_start_iter(),
            self.buffer.get_end_iter()
        )
        self.buffer.apply_tag_by_name(tagname, start, end)
        
    #--------------------------------------------------------------------------

    def remove_block(self, starts_with):
        start = self.get_line_start_iter()
        end   = self.copy_iter(start, 0, len(starts_with))
        
        if self.buffer.get_text(start, end, True) == starts_with:
            self.buffer.delete(start, end)

    def toggle_block(self, starts_with):
        start = self.get_line_start_iter()
        end   = self.copy_iter(start, 0, len(starts_with))
        
        if self.buffer.get_text(start, end, True) == starts_with:
            self.buffer.delete(start, end)
        else:
            self.buffer.insert(start, starts_with)

    def toggle_comment(self, accel, widget, keyval, modifiers):
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
         
        def dump_source_marks_at(iter = None):
            for mark in self.get_source_marks(iter):
                print(mark.get_property("category"), mark.get_property("name"))

        def dump_text():
            text = self.buffer.get_text(
                self.buffer.get_start_iter(),
                self.buffer.get_end_iter(),
                True
            )
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
        iter   = self.buffer.get_iter_at_mark(cursor)
        self.buffer.insert(
            iter,
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
        self.text.scroll_mark_onscreen(self.buffer.get_insert())
        self.buffer.end_user_action()
        return True
