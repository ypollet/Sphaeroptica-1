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

from PySide6.QtCore import Signal, QSettings, QFileInfo
from PySide6.QtWidgets import (QWidget, QFileDialog, QDialog, QDialogButtonBox, QVBoxLayout, QLineEdit, QHBoxLayout, QLabel, QPushButton, QCheckBox)

from bs4 import BeautifulSoup
import numpy as np 
import json

from scripts import helpers


class _DirWidget(QWidget):
    updated = Signal(object)
    def __init__(self):
        super(_DirWidget, self).__init__()
        # Choice of Directory
        get_dir = QHBoxLayout()
        label = QLabel("Image Directory : ")
        get_dir.addWidget(label)
        
        self.im_dir_edit= QLineEdit(self) 
        self.im_dir_edit.setFixedWidth(500)
        get_dir.addWidget(self.im_dir_edit)
        
        cam_calib = QPushButton(text="Browse...",parent=self)
        cam_calib.clicked.connect(self.open_directory)

        get_dir.addWidget(cam_calib)
        get_dir.setSpacing(20)
        self.setLayout(get_dir)
        
        get_dir.setContentsMargins(20,0,100,0)

    def open_directory(self):
        dir_ = QFileDialog.getExistingDirectory(None, 'Select a folder:', self.get_value(), QFileDialog.Option.ShowDirsOnly)
        self.im_dir_edit.setText(dir_)
        self.updated.emit(dir_)
    
    def get_value(self):
        return str(self.im_dir_edit.text())

class _IntrinsicsWidget(QWidget):
    updated = Signal(object)
    def __init__(self, path_img):
        super(_IntrinsicsWidget, self).__init__()

        self.path = path_img
        get_dir = QHBoxLayout()
        label = QLabel("Intrinsics : ")
        get_dir.addWidget(label)

        self.intrinsics_edit= QLineEdit(self) 
        self.intrinsics_edit.setFixedWidth(500)
        get_dir.addWidget(self.intrinsics_edit)
        
        cam_calib = QPushButton(text="Browse...",parent=self)
        cam_calib.clicked.connect(self.open_file)

        get_dir.addWidget(cam_calib)
        get_dir.setSpacing(20)
        self.setLayout(get_dir)
        
        get_dir.setContentsMargins(20,0,100,0)

    def open_file(self):
        intrinsics_val = QFileDialog.getOpenFileName(self, "Select intrinsics : ", self.path, "XML Files (*.xml)")
        self.intrinsics_edit.setText(intrinsics_val[0])
        intrinsics = self.get_intrinsics_values(intrinsics_val[0])
        self.updated.emit(intrinsics)

    def get_intrinsics_values(self, path):
        data = None
        with open(path, 'r') as f:
            data = f.read()
        Bs_data = BeautifulSoup(data, "xml")

        b_dist_coeffs = Bs_data.find('Distortion_Coefficients')
        rows_dist_coeffs = int(b_dist_coeffs.find('rows').text)
        cols_dist_coeffs = int(b_dist_coeffs.find('cols').text)
        dist_coeffs = b_dist_coeffs.find('data').text

        b_cam_mat = Bs_data.find('Camera_Matrix')
        rows_cam_mat = int(b_cam_mat.find('rows').text)
        cols_cam_mat = int(b_cam_mat.find('cols').text)
        cam_mat = b_cam_mat.find('data').text
        print(len(Bs_data.find('image_Width').text))
        print(Bs_data.find('image_Width').text)
        width = int(Bs_data.find('image_Width').text)
        
        height = int(Bs_data.find('image_Height').text)

        intrinsics = {}

        intrinsics["width"] = width
        intrinsics["height"] = height

        intrinsics["camera matrix"] = {}
        intrinsics["camera matrix"]["shape"] = [rows_cam_mat, cols_cam_mat]
        intrinsics["camera matrix"]["matrix"] = np.matrix(cam_mat).reshape((cols_cam_mat, rows_cam_mat)).tolist()

        intrinsics["distortion matrix"] = {}
        intrinsics["distortion matrix"]["shape"] = [rows_dist_coeffs, cols_dist_coeffs]
        intrinsics["distortion matrix"]["matrix"] = np.matrix(dist_coeffs).reshape((cols_dist_coeffs, rows_dist_coeffs)).tolist()

        print(intrinsics["camera matrix"]["matrix"])
        print(["Hello", "Bonjour"])

        return intrinsics
        
    
    def get_value(self):
        return str(self.intrinsics_edit.text())
    
    def set_path_image(self, path):
         self.path = path

class _ExtrinsicsWidget(QWidget):
    updated = Signal(object)
    def __init__(self, path_img):
        super(_ExtrinsicsWidget, self).__init__()
        self.path = path_img

        get_dir = QHBoxLayout()
        label = QLabel("Extrinsics : ")
        get_dir.addWidget(label)
        
        self.extrinsics_edit= QLineEdit(self) 
        self.extrinsics_edit.setFixedWidth(500)
        get_dir.addWidget(self.extrinsics_edit)
        
        cam_calib = QPushButton(text="Browse...",parent=self)
        cam_calib.clicked.connect(self.open_file)

        get_dir.addWidget(cam_calib)
        get_dir.setSpacing(20)
        self.setLayout(get_dir)
        
        get_dir.setContentsMargins(20,0,100,0)

    def open_file(self):
        extrinsics_file = QFileDialog.getOpenFileName(self, "Select extrinsics : ", self.path, "JSON (*.json)")
        self.extrinsics_edit.setText(extrinsics_file[0])

        extrinsics = None
        with open(extrinsics_file[0], 'r') as f:
            extrinsics = json.load(f)
        self.updated.emit(extrinsics)
    
    def get_value(self):
        return str(self.extrinsics_edit.text())

    def set_path_image(self, path):
         self.path = path

class _ThumbnailsFolderWidget(QHBoxLayout):
    updated = Signal(object)
    def __init__(self):
        super(_ThumbnailsFolderWidget, self).__init__()

        label = QLabel("Thumbnails folder : ")
        self.addWidget(label)

        self.thumb_edit= QLineEdit() 
        self.thumb_edit.setFixedWidth(500)
        self.addWidget(self.thumb_edit)
        
        self.thumbnail_browse = QPushButton(text="Browse...")
        self.thumbnail_browse.clicked.connect(self.open_directory)
        self.addWidget(self.thumbnail_browse)
    
    def set_state(self, boolean):
        self.thumb_edit.setReadOnly(not boolean)
        self.thumbnail_browse.setEnabled(boolean)

    def get_value(self):
        return str(self.thumb_edit.text())

    def open_directory(self):
        dir_ = QFileInfo(QFileDialog.getExistingDirectory(None, 'Select a folder:', self.get_value(), QFileDialog.Option.ShowDirsOnly))
        self.thumb_edit.setText(dir_.fileName())
        self.updated.emit(dir_)



class _ThumbnailsWidget(QWidget):
    updated = Signal(object)
    def __init__(self):
        super(_ThumbnailsWidget, self).__init__()
        self.full_layout = QVBoxLayout()
        self.toggle_layout = QHBoxLayout()
        self.folder_layout = _ThumbnailsFolderWidget()
        self.full_layout.addLayout(self.toggle_layout)
        self.full_layout.addLayout(self.folder_layout)
        self.folder_layout.set_state(False)

        label = QLabel("Existing thumbnail folder ? ")
        self.check_box = QCheckBox()
        self.check_box.setChecked(False)
        self.check_box.stateChanged.connect(self.update_folder_layout)
        self.toggle_layout.addWidget(label)
        self.toggle_layout.addWidget(self.check_box)

        self.setLayout(self.full_layout)
    
    def update_folder_layout(self):
        self.folder_layout.set_state(self.check_box.isChecked())

class QImportProject(QDialog):
    closeSignal = Signal(object)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import project")
        self.init_settings()

        self.calib = {}

        self.calib["commands"] = {
                    #Front is used as complete calibration for the angles
                    helpers.Keys.FRONT.name: (0,0),
                    helpers.Keys.POST.name: (-180, 0),
                    helpers.Keys.LEFT.name: (90, 0),
                    helpers.Keys.RIGHT.name: (-90, 0),
                    helpers.Keys.INFERIOR.name: (0, -90),
                    helpers.Keys.SUPERIOR.name: (0, 90)
                    }
        self.calib["thumbnails"] = "thumbnails"

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)

        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.dir_image = None

        self.layout = QVBoxLayout()
        
        self.dir_widget = _DirWidget()
        self.dir_widget.updated.connect(self.update_dir_image)
        self.dir_widget.updated.connect(self.enable_ok)
        self.layout.addWidget(self.dir_widget)

        self.int_widget = _IntrinsicsWidget(self.dir_image)
        self.int_widget.updated.connect(self.update_intrinsics)
        self.int_widget.updated.connect(self.enable_ok)
        self.layout.addWidget(self.int_widget)

        self.ext_widget = _ExtrinsicsWidget(self.dir_image)
        self.ext_widget.updated.connect(self.update_extrinsics)
        self.ext_widget.updated.connect(self.enable_ok)
        self.layout.addWidget(self.ext_widget)

        self.thumb_widget = _ThumbnailsWidget()
        self.thumb_widget.updated.connect(self.update_thumbnails)
        self.layout.addWidget(self.thumb_widget)
        
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
    
    def enable_ok(self):
        boolean = self.calib.get("intrinsics") is not None and self.calib.get("extrinsics") is not None and self.dir_image is not None
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(boolean)
    
    def update_dir_image(self, dir):
        self.dir_image = dir

    def update_intrinsics(self, intrinsics):
        self.calib["intrinsics"] = intrinsics

    def update_extrinsics(self, extrinsics):
        self.calib["extrinsics"] = extrinsics

    def update_thumbnails(self, thumb):
        self.thumbnails_bool = thumb[0]
        if self.thumbnails_bool:
            self.calib["thumbnails"] : thumb[1]
        else:
            self.calib["thumbnails"] = "thumbnails"
    
    def init_settings(self):
        self.settings = QSettings("Sphaeroptica", "reconstruction")    