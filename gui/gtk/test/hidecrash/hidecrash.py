#!/usr/bin/env python3
###############################################################################
#
# Test crashing with hidden text.
#
###############################################################################

import gi
from gi.repository import Gtk, Gdk, GtkSource, Pango

#------------------------------------------------------------------------------
# Create buffer, set up tags and add text
#------------------------------------------------------------------------------

buf = GtkSource.Buffer()

#------------------------------------------------------------------------------

buf.set_highlight_matching_brackets(False)

marktag = buf.create_tag("mark", background = "#DDF")
hidetag = buf.create_tag("hide", background = "#FDD", invisible  = True)

def get_insert_iter():
    return buf.get_iter_at_mark(buf.get_insert())

def insert_hidden(prefix, hidden, postfix):
    insert = get_insert_iter()
    start  = buf.create_mark(None, insert, True)
    buf.insert(insert, prefix)
    buf.insert_with_tags(insert, hidden, hidetag)
    buf.insert(insert, postfix)
    buf.apply_tag(marktag, buf.get_iter_at_mark(start), insert)
    buf.delete_mark(start)

def insert(text): buf.insert_at_cursor(text)

#------------------------------------------------------------------------------

insert(
    "Test cases for hidden texts in text/sourceview.\n" +
    "\n" +
    "   Ctrl - T       Toggle visibility\n" +
    "   Ctrl - F       Apply hide tag to selection\n" +
    "   Ctrl - R       Remove hide tags from buffer\n" +
    "   Ctrl - Q       Quit\n" +
    "\n"
)

#------------------------------------------------------------------------------

insert("marked: -->")
#buf.create_source_mark("a", "mark", get_insert_iter())
insert("\nLine 1\nLine 2\nLine 3\n")
buf.create_source_mark("b", "mark", get_insert_iter())
insert("<--\n\n")

#------------------------------------------------------------------------------

insert("Text with hidden parts in between (no crash):\n\n")
insert("Hidden text: ")
insert_hidden("-->", "Hidden text", "<--")
insert("\n\n")

#------------------------------------------------------------------------------

insert("Hidden text with newlines (no crash):\n\n")

insert("Trailing <cr> hidden\n\n")
insert_hidden("-->", "Hidden Lines:\nLine 1\nLine 2\nLine 3", "<--")
insert("\n\n")

#------------------------------------------------------------------------------

insert("Trailing <cr> not hidden\n\n")
insert_hidden("-->", "\nHidden Lines\nLine 1\nLine 2\nLine 3\n", "<--")
insert("\n\n")

#------------------------------------------------------------------------------
# Insert/delete callbacks
#------------------------------------------------------------------------------

def hide_marked(start, end):
    print("Hide: %d:%d - %d:%d" % (
        start.get_line() + 1, start.get_line_offset(),
        end.get_line()   + 1, end.get_line_offset()
    ))
    print("Hide range: %d chars" % (
        end.get_offset() - start.get_offset()    
    ))
    buf.apply_tag(hidetag, start, end)

def check(at):
    end = get_insert_iter()
    start = end.copy()
    start.backward_chars(2)
    if buf.get_text(start, end, True) == "++":
        start = at.copy()
        start.forward_to_line_end()
        end = start.copy()
        buf.forward_iter_to_source_mark(end, "mark")
        hide_marked(start, end)

def afterInsertText(buffer, end, text, length, *args):
    start = end.copy()
    start.backward_chars(length)
    check(start)
    
def afterDeleteRange(buffer, start, end, *args):
    check(start)
    
buf.connect_after("delete-range", afterDeleteRange)
buf.connect_after("insert-text",  afterInsertText)

#------------------------------------------------------------------------------
# Shortcuts
#------------------------------------------------------------------------------

def keypress(widget, event):
    if not (event.state & Gdk.ModifierType.CONTROL_MASK): return False
    key = Gtk.accelerator_name(event.keyval, 0)
    if key == "t":
        hidetag.set_property("invisible", not hidetag.get_property("invisible"))
        return True
    elif key == "f":
        #start, end = buf.get_selection_bounds()
        #buf.apply_tag(hidetag, start, end)
        hide_marked()
    elif key == "r":
        buf.remove_tag(hidetag, *buf.get_bounds())
    elif key == "q":
        Gtk.main_quit()

#------------------------------------------------------------------------------
# Create view and window
#------------------------------------------------------------------------------

view = GtkSource.View.new_with_buffer(buf)
#view.modify_font(Pango.FontDescription("monospace"))
view.modify_font(Pango.FontDescription("Times 12"))
view.set_show_line_numbers(True)
view.connect("key-press-event", keypress)

view.set_mark_attributes("mark", GtkSource.MarkAttributes.new(), 0)

win = Gtk.Window()
#win.add(view)

scrolled = Gtk.ScrolledWindow()
scrolled.set_size_request(500, 500)
scrolled.add(view)
win.add(scrolled)

win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

