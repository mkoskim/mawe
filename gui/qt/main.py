###############################################################################
#
#
#
###############################################################################

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import sys
import tools

from project.Document import ET

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

        self.setMinimumWidth(500)
        self.setFont(QFont('Times', 12))
        self.setFontPointSize(12)

        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.report)
        QShortcut(QKeySequence("Alt+L"), self).activated.connect(self.lorem)

        #self.setPlainText(tools.readfile("../../Dropbox/tarinat/trillerit/ylimielet/ylimielet.moe"))
        
    def report(self): 
        #print(self.toHtml())
        self.Html2Mawe()

    def lorem(self):
        self.insertHtml(
            "<div class='x'>xxx</div>" +
            "<h1>Lorem</h1><p><b>ipsum</b> dolor sit amet, consectetur adipiscing elit, " +
            "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. " +
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris " +
            "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in " +
            "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla " +
            "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in " +
            "culpa qui officia deserunt mollit anim id est laborum." +
            "</p>"
        )

    def Mawe2Hml(self, tree):
        pass
        
    def Html2Mawe(self, text = None):
        if not text: text = self.toHtml()

        html = ET.fromstring(text)
        
        ET.dump(html)

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

