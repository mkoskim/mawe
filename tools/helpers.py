###############################################################################
#
# Generic helpers
#
###############################################################################

from tools.error import *

#-------------------------------------------------------------------------

import os

if os.name == "posix":

    # Open folders, text files, RTF, doc, links, PDF, EPUB, ...
    def xdgopen(filename):
        os.system("xdg-open %s &" % (filename))

    def xdgfolder(filename):
        xdgopen(os.path.dirname(filename))

elif os.name == "nt":

    def xdgopen(filename):
        os.system("start %s" % (filename))

    def xdgfolder(filename):
        xdgopen(os.path.dirname(filename))
        
else:
    ERROR("Unknown platform: %s" % os.name)

#-------------------------------------------------------------------------
# File reading/writing TODO: This is old code, need to check if Python
# can nowadays detect the file encoding automatically.
#-------------------------------------------------------------------------

def readfile(filename):
    f = open(filename, "rb")
    content = f.read()
    f.close()

    def decode(content):
        for codec in ["utf-8", "latin-1"]:
            try:
                content = content.decode(codec)
                return content
            except UnicodeDecodeError: pass
        ERROR("%s: Unknown encoding." % filename)

    return decode(content)    

def writefile(filename, content):
    f = open(filename, "w")
    f.write(content, encoding = "utf-8")
    f.close()

#------------------------------------------------------------------------------
# Idea was good, to resolve dependency problems on the fly. Sadly, we don't
# have root privileges to install packages.
#------------------------------------------------------------------------------

#class Pip:
#
#    from pip._internal import main as pipmain
#
#    def __init__(self):
#        pass
#        
#    def install(self, package):
#        pipmain(["install", package])
#
#pip = Pip()
