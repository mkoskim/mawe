import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

def apply(widget, style):
    provider = Gtk.CssProvider()
    provider.load_from_data(style)
    widget.get_style_context().add_provider(
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

