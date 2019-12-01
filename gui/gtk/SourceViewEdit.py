from gui.gtk import Gtk, Gdk, Pango, GtkSource, GdkPixbuf
import os

#------------------------------------------------------------------------------

class SceneGroupEdit(Gtk.Window):

    def __init__(self):
        super(SceneGroupEdit, self).__init__(title = "mawesome")

        self.buffer = GtkSource.Buffer()

        theme = GtkSource.StyleSchemeManager.get_default().get_scheme('mawe')
        lang = GtkSource.LanguageManager.get_default().get_language("mawe")

        self.buffer.set_style_scheme(theme)
        self.buffer.set_language(lang);
        self.buffer.set_highlight_matching_brackets(False)
        self.buffer.set_highlight_syntax(True)
        
        self.buffer.create_tag("folded",
            #invisible = True,
            editable = False,
            foreground = "#DDDDDD",
        )
        
        self.text = GtkSource.View.new_with_buffer(self.buffer)

        self.text.modify_font(Pango.FontDescription("Times 12"))
        self.text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text.set_pixels_inside_wrap(4)
        self.text.set_pixels_above_lines(2)
        self.text.set_pixels_below_lines(2)
        self.text.set_indent(30)
        #self.text.set_show_line_numbers(True)
        #self.text.set_show_right_margin(True)
        self.text.set_show_line_marks(True)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file('/usr/share/pixmaps/faces/6_astronaut.jpg')
        attr = GtkSource.MarkAttributes.new()
        attr.set_pixbuf(pixbuf)
        self.text.set_mark_attributes("a", attr, 0)

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

        #self.buffer.connect_after("insert-text", self.onAfterInsertText)
        #self.buffer.connect("delete-range", self.onDeleteRange)
        #self.buffer.connect("mark-set", self.onMarkSet)
        #self.buffer.connect("mark-deleted", self.onMarkDelete)        
        #text.connect("key-press-event", self.edit_shortcuts)

        #print(self.buffer.get_serialize_formats())

    #--------------------------------------------------------------------------
    
    def get_cursor_iter(self):
        return self.buffer.get_iter_at_mark(self.buffer.get_insert())
    
    def get_line_iter(self, cursor_iter = None):
        if cursor_iter is None: cursor_iter = self.get_cursor_iter()
        start = self.buffer.get_iter_at_line(cursor_iter.get_line())
        end   = self.buffer.get_iter_at_line(cursor_iter.get_line())
        end.forward_line()
        return start, end

    #--------------------------------------------------------------------------
    
    def lorem(self, accel, widget, keyval, modifiers):
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
        return True

    #--------------------------------------------------------------------------

    def remove_block(self, starts_with):
        start, end = self.get_line_iter()
        end = start.copy()
        end.forward_chars(len(starts_with))
        
        if self.buffer.get_text(start, end, True) == starts_with:
            self.buffer.delete(start, end)

    def toggle_block(self, starts_with):
        start, end = self.get_line_iter()
        end = start.copy()
        end.forward_chars(len(starts_with))
        
        if self.buffer.get_text(start, end, True) == starts_with:
            self.buffer.delete(start, end)
        else:
            self.buffer.insert(start, starts_with)

    def toggle_comment(self, accel, widget, keyval, modifiers):
        self.remove_block("<<")
        self.remove_block("#")
        self.toggle_block("//")

    def toggle_synopsis(self, accel, widget, keyval, modifiers):
        self.remove_block("//")
        self.remove_block("#")
        self.toggle_block("<<")

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
            cursor = self.get_cursor_iter()
            self.buffer.create_source_mark(None, "a", start)
        
        toggle_tag_to_line("folded")
    
    #--------------------------------------------------------------------------
    
    def save(self, accel, widget, keyval, modifiers):
        for styleid in self.buffer.get_language().get_style_ids():
            style = self.buffer.get_style_scheme().get_style(styleid)
            print(styleid, style)
        
        def dumptag(tag):
            print(tag.get_property("name"))

        self.buffer.get_tag_table().foreach(dumptag)
        return True

