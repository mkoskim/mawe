from gui.gtk import Gtk, Gdk, Pango, GtkSource, GdkPixbuf
import os

#------------------------------------------------------------------------------

class SceneGroupEdit(Gtk.Window):

    def __init__(self):
        super(SceneGroupEdit, self).__init__(title = "mawesome")

        self.create_view()
        scrolled = Gtk.ScrolledWindow()
        #scrolled.set_size_request(600, 800)
        scrolled.add(self.text)

        self.add(scrolled)
        self.set_default_size(600, 800)

        accel = Gtk.AccelGroup()
        accel.connect(*Gtk.accelerator_parse("<Alt>L"), 0, self.lorem)
        accel.connect(*Gtk.accelerator_parse("<Alt>C"), 0, self.toggle_comment)
        accel.connect(*Gtk.accelerator_parse("<Alt>S"), 0, self.toggle_synopsis)
        accel.connect(*Gtk.accelerator_parse("<Alt>X"), 0, self.toggle_fold)

        accel.connect(*Gtk.accelerator_parse("<Ctrl>S"), 0, self.save)
        accel.connect(*Gtk.accelerator_parse("<Ctrl>Q"), 0, Gtk.main_quit)
        self.add_accel_group(accel)

        #self.buffer.connect("highlight-updated", self.onHighlightUpdated)
        #self.buffer.connect("mark-set", self.onMarkSet)
        #self.buffer.connect("mark-deleted", self.onMarkDelete)        
        #text.connect("key-press-event", self.edit_shortcuts)

        #print(self.buffer.get_serialize_formats())

    def create_view(self):
        self.buffer = GtkSource.Buffer()
        self.buffer.set_highlight_matching_brackets(False)

        self.buffer.connect_after("insert-text", self.afterInsertText)
        self.buffer.connect_after("delete-range", self.afterDeleteRange)

        self.text = GtkSource.View.new_with_buffer(self.buffer)

        self.text.modify_font(Pango.FontDescription("Times 12"))
        #self.text.modify_font(Pango.FontDescription("Sans 12"))
        #self.text.modify_font(Pango.FontDescription("Serif 12"))
        self.text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text.set_pixels_inside_wrap(4)
        self.text.set_pixels_above_lines(2)
        self.text.set_pixels_below_lines(2)
        #self.text.set_indent(30)
        
        self.text.set_show_line_numbers(True)
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
        self.text.set_show_line_marks(True)
    
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
            text
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
    # Scene marks
    #--------------------------------------------------------------------------

    def fix_scene_marks(self, start, end):
        start = self.get_line_start_iter(start)
        end = self.get_line_end_iter(end)

        self.buffer.remove_tag(self.tag_prot, self.copy_iter(start, 0, -1), end)

        for mark in self.get_source_marks("scene", start, end):
            iter = self.buffer.get_iter_at_mark(mark)
            if not iter.starts_line() or not self.expect_forward("##", iter):
                self.buffer.delete_mark(mark)
                del self.marks[mark]

    def apply_scene(self, start, end):
        self.buffer.apply_tag_by_name("heading:scene", start, end)

        prot_start = self.copy_iter(start, 0, -1)
        prot_end   = self.copy_iter(start, 0, +1)
        self.buffer.apply_tag(self.tag_prot, prot_start, prot_end)

        # Update scene marker
        marks = self.get_source_marks("scene", prot_start, prot_end)
        if marks:
            #for mark in marks: self.dump_mark("Found", mark)
            mark = marks[0]
        else:
            mark = self.buffer.create_source_mark(None, "scene", start)
            #self.dump_mark("Created", mark)
        self.marks[mark] = self.buffer.get_text(start, end, False)[2:].strip()

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

    fold_marker = " ···"

    def toggle_fold(self, accel, widget, keyval, modifiers):
        cursor = self.get_cursor_iter()
        marks  = self.buffer.get_source_marks_at_iter(cursor, "scene")
        if not marks:
            if not self.buffer.backward_iter_to_source_mark(cursor, "scene"): return
        end = self.get_line_end_iter(cursor)

        self.buffer.begin_user_action()

        if self.line_ends_with(self.fold_marker, end):
            start = self.copy_iter(end, 0, -len(self.fold_marker))
            self.buffer.delete(start, end)
        else:
            self.buffer.insert(end, self.fold_marker)
            self.buffer.place_cursor(self.get_line_start_iter(end))

        self.buffer.end_user_action()

    #--------------------------------------------------------------------------
    # Updating text tags after changes
    #--------------------------------------------------------------------------

    def afterInsertText(self, buffer, iter, text, length, *args):
        start = self.copy_iter(iter, 0, -length)
        self.update_tags(start, iter)
    
    def afterDeleteRange(self, buffer, start, end, *args):
        # start == end (delete already done)
        #self.dump_range("Delete", start, end)
        self.update_tags(start, end)
    
    def has_tags(self, iter, *tagnames):
        for tagname in tagnames:
            tag = self.tagtbl.lookup(tagname)
            if iter.has_tag(tag): return True
        return False
        
    def update_tags(self, start, end):
        self.fix_scene_marks(start, end)

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
   
        def dump_contexts_at(iter):
            print(self.buffer.get_context_classes_at_iter(iter))
            
        dump_source_marks_at()
        #dump_contexts_at(self.get_cursor_iter())
        return True

    #--------------------------------------------------------------------------
    
    def lorem(self, accel, widget, keyval, modifiers):
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


