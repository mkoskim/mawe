###############################################################################
#
# Dialogs
#
###############################################################################

from gui.gtk import (
    Gtk, Gdk, Gio,
)

import os

#------------------------------------------------------------------------------

def SaveAs(self, suggested, directory):
    mainwindow = self.get_toplevel()
    
    dialog = Gtk.FileChooserDialog(
        "Save as...", mainwindow,
        Gtk.FileChooserAction.SAVE,
        (
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
    )

    dialog.set_do_overwrite_confirmation(True)

    if suggested:
        suggested = os.path.splitext(suggested)[0] + ".mawe"
        dialog.set_filename(suggested)
        dialog.set_current_name(os.path.basename(suggested))

    dialog.set_current_folder(directory)
    #print(suggested, directory)

    answer = dialog.run()
    name   = dialog.get_filename()
    dialog.destroy()
    
    return answer == Gtk.ResponseType.OK and name or None

#------------------------------------------------------------------------------

def SaveOrDiscard(self, question):
    mainwindow = self.get_toplevel()

    dialog = Gtk.MessageDialog(
        parent = mainwindow,
        flags = Gtk.DialogFlags.MODAL,
        type = Gtk.MessageType.WARNING,
        message_format = question,
    )
    dialog.add_buttons(
        Gtk.STOCK_SAVE, Gtk.ResponseType.YES,
        "Close without Saving", Gtk.ResponseType.NO,
        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL
    )
    answer = dialog.run()
    dialog.destroy()
    return answer            

#------------------------------------------------------------------------------

def YesNo(self, question):
    mainwindow = self.get_toplevel()

    dialog = Gtk.MessageDialog(
        parent = mainwindow,
        flags = Gtk.DialogFlags.MODAL,
        type = Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.YES_NO,
        message_format = question,
    )
    answer = dialog.run()
    dialog.destroy()
    return answer            

