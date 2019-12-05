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
buf.set_highlight_matching_brackets(False)

marktag = buf.create_tag("mark", background = "#DDF")
hidetag = buf.create_tag("hide", background = "#FDD", invisible  = True)

def insert_hidden(prefix, hidden, postfix):
    insert = buf.get_iter_at_mark(buf.get_insert())
    start  = buf.create_mark(None, insert, True)
    buf.insert(insert, prefix)
    buf.insert_with_tags(insert, hidden, hidetag)
    buf.insert(insert, postfix)
    buf.apply_tag(marktag, buf.get_iter_at_mark(start), insert)
    buf.delete_mark(start)

def insert(text): buf.insert_at_cursor(text)

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
# Shortcuts
#------------------------------------------------------------------------------

def keypress(widget, event):
    if not (event.state & Gdk.ModifierType.CONTROL_MASK): return False
    key = Gtk.accelerator_name(event.keyval, 0)
    if key == "t":
        hidetag.set_property("invisible", not hidetag.get_property("invisible"))
        return True
    elif key == "f":
        start, end = buf.get_selection_bounds()
        buf.apply_tag(hidetag, start, end)
    elif key == "r":
        buf.remove_tag(hidetag, *buf.get_bounds())
    elif key == "q":
        Gtk.main_quit()
    #print(key)
    #    event.keyval,
    #    mods, #Gdk.ModifierType(mods)
    #)
    #print("Keyval:", keyval, "Mods:", Gdk.ModifierType(mods))
    #print("Combo:", self.combokey, "Key:", key)

#------------------------------------------------------------------------------
# Create view and window
#------------------------------------------------------------------------------

view = GtkSource.View.new_with_buffer(buf)
view.modify_font(Pango.FontDescription("monospace"))
view.set_show_line_numbers(True)
view.connect("key-press-event", keypress)

win = Gtk.Window()
win.add(view)

win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()

