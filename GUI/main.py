'''
Copyright Yann Pollet 2023
'''

import sys
# setting path
sys.path.append('.')

from PyQt6.QtWidgets import (
    QMainWindow, QStackedLayout, QWidget, QToolBar, QMenu
)
from PyQt6.QtGui import (
    QAction, QIcon, QKeyEvent
)
from PyQt6.QtCore import (
    QSettings, Qt, pyqtSignal
)
from GUI.reconstruction import ReconstructionWidget
from GUI.home import HomeWidget
from scripts.helpers import Indexes
from GUI.calibration import CalibrationWidget

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.init_settings()

        self.setWindowTitle("Sphaeroptica")

        self.layout = QStackedLayout()
        self.stack_widgets = []

        self.home = HomeWidget(self)
        self.calib = CalibrationWidget(self)
        self.rec = ReconstructionWidget(self)

        self.layout.addWidget(self.home)
        self.layout.addWidget(self.calib)
        self.layout.addWidget(self.rec)

        self.layout.setCurrentIndex(0)

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self._create_actions()
        self._create_menu_bar()

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
        self.camera_calibration_settings = QSettings("Sphaeroptica", "camera_calibration")
    
    def _create_actions(self):
        self.back_action = QAction(QIcon("icons/arrow-turn-180-left.png"), "Back", self)
        #self.back_action.setStatusTip("Go back")
        self.back_action.triggered.connect(self.get_back_widget)

        self.calibration_action = QAction("Calib.")
        self.calibration_action.triggered.connect(self.go_to_calib)
        
        self.new_action = QAction("New File..", self)
        self.new_action.triggered.connect(self.new_file)
        self.open_action = QAction("Open..", self)
        self.open_action.triggered.connect(self.open_file)


    def go_to_calib(self):
        print("Go_to_calib")
        self.set_widget(Indexes.CAM)

    def open_file(self):
        self.rec.reconstruction_settings.setValue("directory", None)
        self.rec.init.import_project()
        self.set_widget(Indexes.REC)

    def new_file(self):
        self.rec.reconstruction_settings.setValue("directory", None)
        self.rec.init.create_project()
        self.set_widget(Indexes.REC)

    def _create_menu_bar(self):
        menu = self.menuBar()
        
        menu.addAction(self.back_action)
        
        menu.addAction(self.calibration_action)

        file_menu = menu.addMenu("Reconst.")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        

