from gui.gtk import Gtk, Gdk, Pango, WebKit

#------------------------------------------------------------------------------

class SceneGroupEdit(Gtk.Window):

    def __init__(self):
        super(SceneGroupEdit, self).__init__(title = "mawesome")

        self.text = WebKit.WebView()
        self.text.set_editable(True)

        self.text.load_html_string("<html><body>test</body></html>", "file:///")

        scrolled = Gtk.ScrolledWindow()
        #scrolled.set_size_request(600, 800)
        scrolled.add(self.text)

        self.add(scrolled)
        self.set_default_size(600, 800)

        accel = Gtk.AccelGroup()
        accel.connect(*Gtk.accelerator_parse("<Alt>L"), 0, self.lorem)
        #accel.connect(*Gtk.accelerator_parse("<Alt>C"), 0, self.toggle_comment)
        #accel.connect(*Gtk.accelerator_parse("<Alt>S"), 0, self.toggle_synopsis)
        #accel.connect(*Gtk.accelerator_parse("<Alt>X"), 0, self.toggle_scenebreak)
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
    
    def lorem(self, accel, widget, keyval, modifiers):
        cursor = self.buffer.get_insert()
        iter   = self.buffer.get_iter_at_mark(cursor)
        self.buffer.insert(
            iter,
            "Lorem ipsum dolor sit amet, consectetur adipiscing " +
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
    
    def save(self, accel, widget, keyval, modifiers):
        #content = self.text.get_dom_document()
        #help(content)
        #content = self.text.get_main_frame().get_data_source().get_data().str
        #print(content)

        return True

