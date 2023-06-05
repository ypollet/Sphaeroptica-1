import sys

sys.path.append('..')

from random import randint, seed

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QRect

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
    