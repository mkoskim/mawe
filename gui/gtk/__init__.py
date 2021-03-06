#------------------------------------------------------------------------------
# GUI
#------------------------------------------------------------------------------

import os
guidir = os.path.dirname(__file__)

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkSource", "3.0")

#------------------------------------------------------------------------------
# GTK3 imports
#------------------------------------------------------------------------------

from gi.repository import (
    Gtk, Gdk, Gio, GObject,
    Pango,
    GtkSource,
    GdkPixbuf
)

#------------------------------------------------------------------------------
# Version info
#------------------------------------------------------------------------------

print("Gtk........:", Gtk._version)
print("GtkSource..:", GtkSource._version)

#------------------------------------------------------------------------------
# GTKSource3 interface
#------------------------------------------------------------------------------

if GtkSource._version in ["3.0"]:
    from gui.gtk.SceneBuffer import SceneBuffer
    from gui.gtk.SceneView   import (
        SceneView, ScrolledSceneView,
        SceneList, ScrolledSceneList,
    )
else:
    raise ImportError("GtkSource %s not supported." % GtkSource._version)

#------------------------------------------------------------------------------

import gui.gtk.dialog

from gui.gtk.ProjectView import ProjectView

from gui.gtk.DocBookPage import DocBookPage
from gui.gtk.OpenTab import OpenTab
from gui.gtk.DocTab import DocTab
from gui.gtk.DocBook import DocBook

