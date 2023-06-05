from logging.handlers import QueueHandler

import sys
# setting path
sys.path.append('./GUI')

from typing import Tuple
from PyQt6.QtWidgets import (
    QApplication
)

import GUI.main as main

app = QApplication(sys.argv)
w = main.MainWindow()
w.show()
app.exec()