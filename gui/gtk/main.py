import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

#------------------------------------------------------------------------------

class SceneGroupEdit(Gtk.Window):

    def __init__(self):
        super(SceneGroupEdit, self).__init__(title = "mawesome")

        text = Gtk.TextView()
        text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        print(text.get_buffer().get_serialize_formats())

        scrolled = Gtk.ScrolledWindow()
        #scrolled.set_vexpand(True)
        scrolled.set_size_request(400, 300)
        scrolled.add(text)

        self.add(scrolled)

#------------------------------------------------------------------------------

def run():
    win = SceneGroupEdit()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()

