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
        accel.connect(*Gtk.accelerator_parse("<Alt>X"), 0, self.toggle_scenebreak)
        accel.connect(*Gtk.accelerator_parse("<Ctrl>S"), 0, self.save)
        accel.connect(*Gtk.accelerator_parse("<Ctrl>Q"), 0, Gtk.main_quit)
        self.add_accel_group(accel)

        #self.buffer.connect("highlight-updated", self.onHighlightUpdated)
        #self.buffer.connect("mark-set", self.onMarkSet)
        #self.buffer.connect("mark-deleted", self.onMarkDelete)        
        #text.connect("key-press-event", self.edit_shortcuts)

        #print(self.buffer.get_serialize_formats())

    def set_highlight(self, lang, theme = None):
        if theme:
            theme = GtkSource.StyleSchemeManager.get_default().get_scheme(theme)
            self.buffer.set_style_scheme(theme)
            
        lang = GtkSource.LanguageManager.get_default().get_language(lang)
        self.buffer.set_language(lang);
        
        self.buffer.set_highlight_syntax(True)

    def set_tags(self):
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
            justification = Gtk.Justification.CENTER,
            weight = Pango.Weight.BOLD,
            pixels_above_lines = 20,
            pixels_below_lines = 5,
        )
        self.buffer.create_tag("folded",
            editable = False,
        )
        self.buffer.create_tag("hidden",
            editable = False,
            invisible = True,
        )
        self.buffer.create_tag("debug:update",
            background = "#DDD",
        )

    def set_source_marks(self):
        def add_category(category, pixmap = None, prio = 0):
            attr = GtkSource.MarkAttributes.new()
            if pixmap:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(pixmap)
                attr.set_pixbuf(pixbuf)
            self.text.set_mark_attributes(category, attr, prio)
            
        #add_category("comment", '/usr/share/pixmaps/faces/6_astronaut.jpg')
        add_category("comment")
        self.text.set_show_line_marks(True)
    
    def create_view(self):
        self.buffer = GtkSource.Buffer()
        self.buffer.set_highlight_matching_brackets(False)
        #self.set_highlight("mawe", "mawe")
        self.set_tags()
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
        #self.text.set_show_line_numbers(True)
        #self.text.set_show_right_margin(True)
        self.set_source_marks()

    #--------------------------------------------------------------------------
    
    def get_cursor_iter(self):
        return self.buffer.get_iter_at_mark(self.buffer.get_insert())
    
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

    def afterInsertText(self, buffer, iter, text, length, *args):
        start = iter.copy()
        start.backward_chars(length)
        self.update_tags(start, iter)
    
    def afterDeleteRange(self, buffer, start, end, *args):
        # start == end (delete already done)
        #self.dump_range("Delete", start, end)
        self.update_tags(start, end)
    
    def line_starts_with(self, text, iter = None):
        if iter is None: iter = self.get_cursor_iter()
        start = self.get_line_start_iter(iter)
        end = start.copy()
        end.forward_chars(len(text))
        return self.buffer.get_text(start, end, True) == text
        
    def update_indent(self, start, end):
        self.buffer.remove_tag_by_name("indent", start, end)
        if(start.is_start()): return
        
        prev_start = start.copy()
        while True:
            if(prev_start.is_start()): return
            prev_start.backward_line()
            prev_end = self.get_line_end_iter(prev_start)
            if(prev_start.equal(prev_end)): return
            tags = prev_start.get_tags()
            tags = map(lambda t: t.get_property("name"), tags)
            tags = list(tags)
            if "heading:scene" in tags: return
            if "comment" in tags: continue
            if "synopsis" in tags: continue
            break
            
        self.buffer.apply_tag_by_name("indent", start, end)
        #self.dump_range("Update indent", start, end)
    
    def update_spans(self, line_start, line_end):
        pass

    def update_line_tags(self, start, end):
        #end.forward_char()
        self.buffer.remove_all_tags(start, end)
        
        if self.line_starts_with("#", start):
            self.buffer.apply_tag_by_name("heading:scene", start, end)
        elif self.line_starts_with("//", start):
            self.buffer.apply_tag_by_name("comment", start, end)
            self.update_indent(start, end)
            self.update_spans(start, end)
        elif self.line_starts_with("<<", start):
            self.buffer.apply_tag_by_name("synopsis", start, end)
            self.update_indent(start, end)
            self.update_spans(start, end)
        elif self.line_starts_with("!!", start):
            self.buffer.apply_tag_by_name("missing", start, end)
            self.update_indent(start, end)
            self.update_spans(start, end)
        elif self.line_starts_with("...", start):
            fold_start = start.copy()
            fold_start.forward_chars(3)
            self.buffer.apply_tag_by_name("hidden", fold_start, end)
            self.update_indent(start, end)
        else:
            self.buffer.apply_tag_by_name("text", start, end)
            self.update_indent(start, end)
            self.update_spans(start, end)
        
    def mark_range(self, tagname, start, end):
        #self.dump_range("Update", start, end)
        self.buffer.remove_tag_by_name(
            tagname,
            self.buffer.get_start_iter(),
            self.buffer.get_end_iter()
        )
        self.buffer.apply_tag_by_name(tagname, start, end)
        
    def update_tags(self, start, end):
        line = self.get_line_start_iter(start)
        while(line.compare(self.get_line_end_iter(end)) < 1):
            self.update_line_tags(line, self.get_line_end_iter(line))
            if line.is_end(): break
            line.forward_line()
        self.update_indent(*self.get_line_iter(line))

        #self.mark_range("debug:update", start, end)

    #--------------------------------------------------------------------------

    def remove_block(self, starts_with):
        start = self.get_line_start_iter()
        end = start.copy()
        end.forward_chars(len(starts_with))
        
        if self.buffer.get_text(start, end, True) == starts_with:
            self.buffer.delete(start, end)

    def toggle_block(self, starts_with):
        start = self.get_line_start_iter()
        end = start.copy()
        end.forward_chars(len(starts_with))
        
        if self.buffer.get_text(start, end, True) == starts_with:
            self.buffer.delete(start, end)
        else:
            self.buffer.insert(start, starts_with)

    def toggle_comment(self, accel, widget, keyval, modifiers):
        tag = self.buffer.get_tag_table().lookup("comment")
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

    def add_source_mark(self, name, category, iter = None):
        # Place mark at the start of the line, otherwise it is not shown
        place = self.get_line_start_iter(iter)
        self.buffer.create_source_mark(name, category, place)

    def remove_source_mark(self, category, iter = None):
        self.buffer.remove_source_marks(*self.get_line_iter(), category)

    def get_source_marks(self, category = None, iter = None):
        # Get marks from the start of the line
        line, offset = self.get_line_and_offset()
        return self.buffer.get_source_marks_at_line(line, category)

    def toggle_source_mark(self, name, category, iter = None):
        if self.get_source_marks(category):
            self.remove_source_mark(category)
        else:
            self.add_source_mark(name, category)

    #--------------------------------------------------------------------------

    def toggle_scenebreak(self, accel, widget, keyval, modifiers):
        def insert_label():
            cursor = self.get_cursor_iter()
            label = Gtk.Label()
            label.set_text("...")
            label.set_visible(True)
            anchor = self.buffer.create_child_anchor(cursor)
            self.text.add_child_at_anchor(label, anchor)
            
        def toggle_tag_to_line(tagname):
            tag = self.buffer.get_tag_table().lookup(tagname)
            cursor = self.get_cursor_iter()
            start, end = self.get_line_iter()
            start.backward_char()

            if cursor.has_tag(tag):
                self.buffer.remove_tag(tag, start, end)
            else:
                self.buffer.apply_tag(tag, start, end)

        def apply_source_mark_to_line():
            #cursor = self.get_cursor_iter()
            self.toggle_source_mark(None, "comment")

        #toggle_tag_to_line("folded")
        #apply_source_mark_to_line()
    
    #--------------------------------------------------------------------------
    
    def save(self, accel, widget, keyval, modifiers):
        def dump_styles():
            for styleid in self.buffer.get_language().get_style_ids():
                style = self.buffer.get_style_scheme().get_style(styleid)
                print(styleid, style)
            
        def dumptag(tag):
            print(tag.get_property("name"))

        def dumptags():
            self.buffer.get_tag_table().foreach(dumptag)
         
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


