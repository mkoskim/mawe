import gi

#gi.require_version("Gtk", "3")
#gi.require_version("GtkSource", "4")
#gi.require_version("WebKit", "3.0")

from gi.repository import (
    Gtk, Gdk, Gio, Pango,
    GtkSource,
    GdkPixbuf
)

print("Gtk: %d.%d" % (Gtk.get_major_version(), Gtk.get_minor_version()))

from gui.gtk.SceneBuffer import SceneBuffer
from gui.gtk.SceneView   import (
    SceneView, ScrolledSceneView,
    SceneList, ScrolledSceneList,
)

import gui.gtk.dialog

import os
guidir = os.path.dirname(__file__)

