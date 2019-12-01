import gi
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.0")
from gi.repository import Gtk, Gdk, Pango, WebKit2

import gui.gtk.style

#------------------------------------------------------------------------------

class SceneGroupEdit(Gtk.Window):

    def set_tags(self, text):
        buffer = text.get_buffer()

        gui.gtk.style.apply(
            text,
            b"""
            GtkTextView {
                padding-left: 1cm;
                padding-right: 1cm;
                padding-top: 0.5cm;
                padding-bottom: 2cm;
            }
            """
        )

        text.modify_font(Pango.FontDescription("Times 12"))
        text.set_pixels_inside_wrap(4)
        text.set_pixels_above_lines(2)
        text.set_pixels_below_lines(2)
        text.set_indent(30)

        buffer.create_tag("comment",
            paragraph_background="#DDFFDD",
            indent = 0,
            #left_margin = 50,
            pixels_above_lines = 6,
            pixels_below_lines = 6,
        )
        
        buffer.create_tag("synopsis",
            paragraph_background="#FFFFDD",
            indent = 0,
            pixels_above_lines = 6,
            pixels_below_lines = 6,
            #left_margin = 50,
        )
        
        buffer.create_tag("folded",
            invisible = True,
        )
        
        buffer.create_tag("scenebreak",
            background="#DDDDDD",
            justification = Gtk.Justification.CENTER,
            weight = Pango.Weight.BOLD,
            pixels_above_lines = 20,
            pixels_below_lines = 5,
        )
        
    def __init__(self):
        super(SceneGroupEdit, self).__init__(title = "mawesome")

        self.buffer = Gtk.TextBuffer()
        self.text = Gtk.TextView(buffer = self.buffer)
        self.text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.set_tags(self.text)

        #self.text = WebKit2.WebView()
        #self.text.set_editable(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(600, 800)
        #scrolled.set_vexpand(True)
        scrolled.add(self.text)

        self.add(scrolled)
        
        accel = Gtk.AccelGroup()
        accel.connect(*Gtk.accelerator_parse("<Alt>L"), 0, self.lorem)
        accel.connect(*Gtk.accelerator_parse("<Alt>C"), 0, self.toggle_comment)
        accel.connect(*Gtk.accelerator_parse("<Alt>S"), 0, self.toggle_synopsis)
        accel.connect(*Gtk.accelerator_parse("<Alt>X"), 0, self.toggle_scenebreak)
        accel.connect(*Gtk.accelerator_parse("<Ctrl>S"), 0, self.save)
        accel.connect(*Gtk.accelerator_parse("<Ctrl>Q"), 0, Gtk.main_quit)
        self.add_accel_group(accel)
        
        #text.connect("key-press-event", self.edit_shortcuts)

        #print(self.buffer.get_serialize_formats())

    def lorem(self, accel, widget, keyval, modifiers):
        cursor = self.buffer.get_insert()
        iter   = self.buffer.get_iter_at_mark(cursor)
        self.buffer.insert_markup(
            iter,
            "Lorem <b>ipsum</b> dolor sit amet, consectetur adipiscing " +
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
    
    def get_cursor_iter(self):
        return self.buffer.get_iter_at_mark(self.buffer.get_insert())
    
    def get_line_iter(self, cursor_iter = None):
        if cursor_iter is None: cursor_iter = self.get_cursor_iter()
        start = self.buffer.get_iter_at_line(cursor_iter.get_line())
        end   = self.buffer.get_iter_at_line(cursor_iter.get_line())
        end.forward_line()
        return start, end

    def remove_tag_by_name(self, tagname, start, end):
        tag = self.buffer.get_tag_table().lookup(tagname)
        self.buffer.remove_tag(tag, start, end)
    
    def apply_tag_by_name(self, tagname, start, end):
        tag = self.buffer.get_tag_table().lookup(tagname)
        self.buffer.apply_tag(tag, start, end)

    def toggle_tag_by_name(self, tagname, start, end):
        tag = self.buffer.get_tag_table().lookup(tagname)
        if start.has_tag(tag):
            self.buffer.remove_tag(tag, start, end)
        else:
            self.buffer.apply_tag(tag, start, end)
    
    #--------------------------------------------------------------------------
    
    def toggle_comment(self, accel, widget, keyval, modifiers):
        start, end = self.get_line_iter()
        self.remove_tag_by_name("scenebreak", start, end)
        self.remove_tag_by_name("synopsis", start, end)
        self.toggle_tag_by_name("comment", start, end)
        return True

    def toggle_synopsis(self, accel, widget, keyval, modifiers):
        start, end = self.get_line_iter()
        self.remove_tag_by_name("scenebreak", start, end)
        self.remove_tag_by_name("comment", start, end)
        self.toggle_tag_by_name("synopsis", start, end)
        return True

    def toggle_scenebreak(self, accel, widget, keyval, modifiers):
        tag = self.buffer.get_tag_table().lookup("scenebreak")
        
        if self.get_cursor_iter().has_tag(tag):
            start, end = self.get_line_iter()
            self.buffer.delete(start, end)
        else:
            cursor = self.get_cursor_iter()
            if cursor.get_chars_in_line() != 0:
                if(cursor.starts_line()):
                    self.buffer.insert(cursor, "\n")
                    cursor.backward_char()
                elif(cursor.ends_line()):
                    self.buffer.insert(cursor, "\n")
                else:
                    self.buffer.insert(cursor, "\n\n")
                    cursor.backward_char()
                
            self.buffer.insert(cursor, "<scene>")
            self.buffer.apply_tag(tag, *self.get_line_iter(cursor))

    def save(self, accel, widget, keyval, modifiers):
        format  = self.buffer.get_serialize_formats()[0]
        content = self.buffer.serialize(
            self.buffer,
            format,
            self.buffer.get_start_iter(),
            self.buffer.get_end_iter()
        )
        print(content)
        return True

#------------------------------------------------------------------------------

def run():
    win = SceneGroupEdit()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

