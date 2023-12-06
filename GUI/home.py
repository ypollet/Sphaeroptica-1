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

sys.path.append('..')

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt

from scripts.helpers import Indexes

class HomeWidget(QWidget):

    def __init__(self, parent):
        super(HomeWidget, self).__init__(parent)

        self.parent = parent

        layout = QVBoxLayout()
        question  = QLabel("What do you want to do ?")
        question.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(question)

        # choices 
        choices = QHBoxLayout()
        cam_calib = QPushButton(text="Camera Calibration",parent=self)
        cam_calib.setFixedSize(500, 300)
        cam_calib.clicked.connect(self.camera_clicked)

        rec = QPushButton(text="3D reconstruction",parent=self)
        rec.setFixedSize(500, 300)
        rec.clicked.connect(self.rec_clicked)
        

        choices.addWidget(cam_calib)
        choices.addWidget(rec)
        choices.setContentsMargins(0,0,0,0)
        layout.addLayout(choices)

        self.setLayout(layout)
        
    def camera_clicked(self):
        self.parent.set_widget(Indexes.CAM)

    def rec_clicked(self):
        self.parent.set_widget(Indexes.REC)
    