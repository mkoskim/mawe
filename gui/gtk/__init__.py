import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit", "3.0")
gi.require_version("GtkSource", "3.0")

from gi.repository import (
    Gtk, Gdk, Pango,
    WebKit, GtkSource,
    GdkPixbuf
)

from gui.gtk.SourceViewEdit import SceneGroupEdit
#from gui.gtk.TextViewEdit import SceneGroupEdit
#from gui.gtk.WebKitEdit import SceneGroupEdit

