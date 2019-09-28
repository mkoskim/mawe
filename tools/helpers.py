###############################################################################
#
# Generic helpers
#
###############################################################################

#------------------------------------------------------------------------------
# Idea was good, to resolve dependency problems on the fly. Sadly, we don't
# have root privileges to install packages.
#------------------------------------------------------------------------------

class Pip:

    from pip._internal import main as pipmain

    def __init__(self):
        pass
        
    def install(self, package):
        pipmain(["install", package])

pip = Pip()

