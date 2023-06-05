import sys

sys.path.append('..')

import numpy
import json

from random import randint, seed

from PyQt6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSpinBox, QFrame,
    QPushButton, QFileDialog, QSizePolicy, QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QSettings, QRect

from scripts.helpers import Scale
from scripts.calibration import calibrate

class _DirWidget(QWidget):
    def __init__(self,parent):
        super(_DirWidget, self).__init__(parent)
        self.parent = parent
        # Choice of Directory
        get_dir = QHBoxLayout()
        label = QLabel("Directory : ")
        get_dir.addWidget(label)
        
        self.cal_dir_edit=QLineEdit(self) 
        self.cal_dir_edit.setText(parent.dir_images)
        get_dir.addWidget(self.cal_dir_edit)
        
        cam_calib = QPushButton(text="Browse...",parent=self)
        cam_calib.clicked.connect(self.open_directory)

        get_dir.addWidget(cam_calib)
        get_dir.setSpacing(20)
        self.setLayout(get_dir)
        
        get_dir.setContentsMargins(20,0,100,0)

    def open_directory(self):
        dir_ = QFileDialog.getExistingDirectory(None, 'Select a folder:', self.parent.dir_images + "..", QFileDialog.Option.ShowDirsOnly)
        self.cal_dir_edit.setText(dir_)
        self.parent.dir_images = dir_
    
    def get_value(self):
        return str(self.cal_dir_edit.text())

class CheckboardDimensionsWidget(QWidget):

    def __init__(self, parent):
        super(CheckboardDimensionsWidget, self).__init__(parent)

        self.init_settings()
        full_layout = QVBoxLayout()

        self.dimension_widget = _DimensionsWidget(self)
        self.length_widget = _SizeWidget(self, "Length")
        self.width_widget = _SizeWidget(self, "Width")
        self.scale_widget = QComboBox(self)
        for key in Scale._member_map_.keys():
            self.scale_widget.addItem(key)
        self.scale_widget.setCurrentText(self.camera_calibration_settings.value("scale").name if self.camera_calibration_settings.value("scale") is not None else Scale.M.name)

        full_layout.addWidget(self.dimension_widget)
        full_layout.addWidget(self.length_widget)
        full_layout.addWidget(self.width_widget)
        full_layout.addWidget(self.scale_widget)

        self.setLayout(full_layout)
    
    def get_values(self):
        dims = self.dimension_widget.get_value()
        length = self.length_widget.get_value()
        width = self.width_widget.get_value()
        scale = Scale[str(self.scale_widget.currentText())]

        return dims, length, width, scale
    
    def init_settings(self):
        self.camera_calibration_settings = QSettings("Sphaeroptica", "camera_calibration")

class _DimensionsWidget(QWidget):

    def __init__(self, parent):
        super(_DimensionsWidget, self).__init__(parent)

        self.init_settings()
        # Dimensions 
        self.dimension_layout = QHBoxLayout()
        self.dimension_label = QLabel("Dimensions : ", self)
        self.dimension_length = QSpinBox(self)
        self.dimensions_times = QLabel("*", self)
        self.dimension_width = QSpinBox(self)

        self.dimension_length.setMinimum(0)
        self.dimension_width.setMinimum(0)
        dims = numpy.array([0,0]) if not self.camera_calibration_settings.contains("dimensions") else self.camera_calibration_settings.value("dimensions")
        self.dimension_length.setValue(dims[0])
        self.dimension_width.setValue(dims[1])


        self.dimension_layout.addWidget(self.dimension_label)
        self.dimension_layout.addWidget(self.dimension_length)
        self.dimension_layout.addWidget(self.dimensions_times)
        self.dimension_layout.addWidget(self.dimension_width)
        self.setLayout(self.dimension_layout)

    def get_value(self):
        length = self.dimension_length.value()
        width = self.dimension_width.value()
        return (length, width)

    def init_settings(self):
        self.camera_calibration_settings = QSettings("Sphaeroptica", "camera_calibration")
        


class _SizeWidget(QWidget):
    def __init__(self, parent, label):
        super(_SizeWidget, self).__init__(parent)
        self.init_settings()
        self.parent = parent
        full_layout = QHBoxLayout()

        self.label = QLabel(label + " : ", self)
        self.size = QSpinBox(self)
        self.size.setMinimum(0)
        self.size.setValue(0 if not self.camera_calibration_settings.contains(label.lower()) else int(self.camera_calibration_settings.value(label.lower())))
        
        full_layout.addWidget(self.label)
        full_layout.addWidget(self.size)
        self.setLayout(full_layout)

    def get_value(self):
        return self.size.value()

    def init_settings(self):
        self.camera_calibration_settings = QSettings("Sphaeroptica", "camera_calibration")

class _ResultsWidget(QWidget):

    def __init__(self, parent):
        super(_ResultsWidget, self).__init__(parent)
        full_layout = QHBoxLayout()

        self.label_cam_matrix = QLabel("Camera matrix : ")
        self.cam_matrix = QLabel("")
        self.label_dis_matrix = QLabel("Distortion matrix :")
        self.dis_matrix = QLabel("")

        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        

        full_layout.addWidget(self.label_cam_matrix)
        full_layout.addWidget(self.cam_matrix)
        full_layout.addWidget(line)
        full_layout.addWidget(self.label_dis_matrix)
        full_layout.addWidget(self.dis_matrix)
        self.setLayout(full_layout)
    
    def update_results(self, cam_matrix, dis_matrix):
        self.cam_matrix.setText(cam_matrix)
        self.dis_matrix.setText(dis_matrix)
   
class CalibrationWidget(QWidget):

    def __init__(self, parent):
        super(CalibrationWidget, self).__init__(parent)

        self.init_settings()
        self.dir_images = self.camera_calibration_settings.value("directory") if self.camera_calibration_settings.value("directory") is not None else ""
        self.cam_matrix = numpy.ndarray((3,3))
        self.dist_matrix = numpy.ndarray((3,3))
        self.parent = parent
        self.setWindowTitle("Calibration")

        full_layout = QVBoxLayout()
        full_layout.setContentsMargins(0,0,0,0)

        label = QLabel("Camera Calibration with Zhang's method")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        full_layout.addWidget(label)

        # Choice of Directory
        self.get_dir = _DirWidget(self)
        full_layout.addWidget(self.get_dir)

        # add dimensions of checkboard
        self.dim_check = CheckboardDimensionsWidget(self)
        full_layout.addWidget(self.dim_check)

        # Add button save

        self.calibrate_button = QPushButton("Calibrate Scanner", self)
        self.calibrate_button.clicked.connect(self.on_calibrate)
        full_layout.addWidget(self.calibrate_button)

        
        #add 
        self.results = _ResultsWidget(self)
        self.results.hide()
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.on_save)
        self.save_button.hide()
        full_layout.addWidget(self.results)
        full_layout.addWidget(self.save_button)

        full_layout.setContentsMargins(20,20,20,20)


        self.setLayout(full_layout)

    def init_settings(self):
        self.camera_calibration_settings = QSettings("Sphaeroptica", "camera_calibration")
        
    def on_calibrate(self):
        dir_name = self.get_dir.get_value()
        print(dir_name)
        dimensions, length, width, scale = self.dim_check.get_values()

        self.camera_calibration_settings.setValue("directory", dir_name)
        self.camera_calibration_settings.setValue("dimensions", dimensions)
        self.camera_calibration_settings.setValue("length", length)
        self.camera_calibration_settings.setValue("width", width)
        self.camera_calibration_settings.setValue("scale", scale)

        cam_matrix, dist_matrix, ext = calibrate(dir_name, dimensions, numpy.array([length*scale.value, width*scale.value]))

        self.results.update_results(str(cam_matrix), str(dist_matrix))
        self.cam_matrix = cam_matrix
        self.dist_matrix = dist_matrix
        self.extrinsics = ext

        self.results.show()
        self.save_button.show()

    def on_save(self):
        file_name = QFileDialog.getSaveFileName(self, "Save Calibration File", self.get_dir.get_value()+"/.json","Json Files (*.json)")

        dict = self.camera_calibration_settings.value("directory")
        dimensions = self.camera_calibration_settings.value("dimensions")
        length = self.camera_calibration_settings.value("length")
        width = self.camera_calibration_settings.value("width")
        scale = self.camera_calibration_settings.value("scale")
        json_dict = {
            "intrinsics":{
                "camera matrix" : {
                    "shape" : self.cam_matrix.shape,
                    "matrix" : self.cam_matrix.tolist()
                },
                "distortion matrix" : {
                    "shape" : self.dist_matrix.shape,
                    "matrix" : self.dist_matrix.tolist()
                }
            },
            "extrinsics":self.extrinsics
        }
        print(file_name)
        with open(file_name[0], 'w', encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=4)

        print(json_dict)