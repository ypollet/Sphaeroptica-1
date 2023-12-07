# Sphaeroptica - 3D Viewer on calibrated

# Copyright (C) 2023 Yann Pollet, Royal Belgian Institute of Natural Sciences

#

# This program is free software: you can redistribute it and/or

# modify it under the terms of the GNU General Public License as

# published by the Free Software Foundation, either version 3 of the

# License, or (at your option) any later version.

# 

# This program is distributed in the hope that it will be useful, but

# WITHOUT ANY WARRANTY; without even the implied warranty of

# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU

# General Public License for more details.

#

# You should have received a copy of the GNU General Public License

# along with this program. If not, see <http://www.gnu.org/licenses/>.


import sys
# setting path
sys.path.append('.')

from PySide6.QtWidgets import (
    QMainWindow, QStackedLayout, QWidget
)
from PySide6.QtGui import (
    QAction, QIcon
)
from PySide6.QtCore import (
    QSettings
)
from GUI.reconstruction import ReconstructionWidget
from GUI.home import HomeWidget
from scripts.helpers import Indexes
from GUI.calibration import CalibrationWidget

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        #self.init_settings()

        self.setWindowTitle("Sphaeroptica")

        self.layout = QStackedLayout()
        self.stack_widgets = []

        # Stack of the different main widgets
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
        self.settings = QSettings("Sphaeroptica", "camera_calibration")
        self.settings.clear()

        self.settings = QSettings("Sphaeroptica", "reconstruction")
        self.settings.clear()
    
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
    
        

