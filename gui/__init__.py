###############################################################################
#
# MAWE GUI module
#
###############################################################################

from gui.tkinter.main import run

#------------------------------------------------------------------------------
# QT: QTextEdit looked promising, but it is crap for my purposes. HTML export
# from widget is unusable. It is hard to add schemantical elements to blocks
# so that you know what they are - and it is even harder for spans inside
# blocks. Hiding elements does not work.
#------------------------------------------------------------------------------

#from gui.qt.main import run

