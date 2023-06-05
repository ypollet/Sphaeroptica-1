import sys
# setting path
sys.path.append('.')

from PyQt6.QtWidgets import (
    QMainWindow, QStackedLayout, QWidget, QToolBar
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeyEvent
)
from PyQt6.QtCore import (
    QSettings, Qt
)
from reconstruction import ReconstructionWidget
from home import HomeWidget
from scripts.helpers import Indexes
from calibration import CalibrationWidget

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.init_settings()

        self.setWindowTitle("Ins3cD")

        self.layout = QStackedLayout()
        self.stack_widgets = []

        self.layout.addWidget(HomeWidget(self))
        self.layout.addWidget(CalibrationWidget(self))
        self.layout.addWidget(ReconstructionWidget(self))

        self.layout.setCurrentIndex(0)

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        toolbar = ToolBar("My main toolbar", self)
        self.addToolBar(toolbar)

    def set_widget(self, id : Indexes):
        print(f"{self.layout.currentIndex()} -> {id.value}")
        self.stack_widgets.append(self.layout.currentIndex())
        self.layout.setCurrentIndex(id.value)
    
    def get_back_widget(self):
        if(len(self.stack_widgets) != 0): 
            # if list not empty
            back = self.stack_widgets.pop()
            print(f"{self.layout.currentIndex()} -> {back}")
            self.layout.setCurrentIndex(back)
    
    def init_settings(self):
        self.camera_calibration_settings = QSettings("Ins3cD", "camera_calibration")
    

class ToolBar(QToolBar):

    def __init__(self, string, parent):
        super(QToolBar, self).__init__(string, parent=parent)
        self.parent = parent
        button_action = QAction(QIcon("icons/arrow-turn-180-left.png"), "back", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(parent.get_back_widget)
        self.addAction(button_action)

