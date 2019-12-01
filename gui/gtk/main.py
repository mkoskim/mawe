from gui.gtk import Gtk, SceneGroupEdit, GtkSource
import os

#------------------------------------------------------------------------------

def run():
    langdir = os.path.join(os.path.dirname(__file__), "language-specs")

    stylemgr = GtkSource.StyleSchemeManager.get_default()
    path = stylemgr.get_search_path()
    path.append(langdir)
    stylemgr.set_search_path(path)

    langmgr = GtkSource.LanguageManager.get_default()
    path = langmgr.get_search_path()
    path.append(langdir)
    langmgr.set_search_path(path)

    win = SceneGroupEdit()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

