###############################################################################
#
#
#
###############################################################################

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sys

###############################################################################
#
#
#
###############################################################################

class SceneGroupEdit(QTextEdit):

    def __init__(self):
        super(SceneGroupEdit, self).__init__()

        # Setup the QTextEdit editor configuration
        self.setAutoFormatting(QTextEdit.AutoAll)
        #self.editor.selectionChanged.connect(self.update_format)

        self.setFont(QFont('Times', 12))
        self.setFontPointSize(12)

        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.report)
        
    def report(self): 
        print(self.toHtml())

###############################################################################
#
#
#
###############################################################################

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("mawesome")

        self.editor = SceneGroupEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        QShortcut(QKeySequence("Ctrl+Q"), self).activated.connect(self.close)
        self.show()

###############################################################################
#
#
#
###############################################################################

def run():
    app = QApplication(sys.argv)
    app.setApplicationName("mawe")

    window = MainWindow()
    app.exec_()

