from PyQt6 import QtGui
from PyQt6.QtCore import pyqtSignal, QSettings
from PyQt6.QtGui import QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import (QWidget, QFileDialog, QDialog, QDialogButtonBox, QVBoxLayout, QLineEdit, QHBoxLayout, QLabel, QPushButton, QCheckBox)

from bs4 import BeautifulSoup
import numpy as np 

from scripts import helpers


class _DirWidget(QWidget):
    updated = pyqtSignal(object)
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
    updated = pyqtSignal(object)
    def __init__(self, path_img):
        super(_IntrinsicsWidget, self).__init__()

        self.path = path_img
        get_dir = QHBoxLayout()
        label = QLabel("Intrinsics : ")
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
        intrinsics_val = QFileDialog.getOpenFileName(self, "Select intrinsics : ", self.path, "XML Files (*.xml)")
        self.extrinsics_edit.setText(intrinsics_val[0])
        intrinsics = self.get_intrinsics_values(intrinsics_val[0])
        print(intrinsics)
        self.updated.emit(intrinsics)

    def get_intrinsics_values(self, path):
        data = None
        with open('data/geonemus-geoffroyii/export_intrinsics.xml', 'r') as f:
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

        width = Bs_data.find('image_Width').text
        height = Bs_data.find('image_Height').text

        intrinsics = {}

        intrinsics["width"] = width
        intrinsics["height"] = height

        intrinsics["camera matrix"] = {}
        rows_cam_mat = int(b_cam_mat.find('rows').text)
        intrinsics["camera matrix"]["shape"] = [rows_cam_mat, cols_cam_mat]
        intrinsics["camera matrix"]["matrix"] = np.matrix(cam_mat).reshape((rows_cam_mat, cols_cam_mat))

        intrinsics["distortion matrix"] = {}
        rows_dist_coeffs = int(b_dist_coeffs.find('rows').text)
        intrinsics["distortion matrix"]["shape"] = [rows_dist_coeffs, cols_dist_coeffs]
        intrinsics["distortion matrix"]["matrix"] = np.matrix(dist_coeffs).reshape((rows_dist_coeffs, cols_dist_coeffs))

        return intrinsics
        
    
    def get_value(self):
        return str(self.extrinsics_edit.text())
    
    def set_path_image(self, path):
         self.path = path

class _ExtrinsicsWidget(QWidget):
    updated = pyqtSignal(object)
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
        with open('data/geonemus-geoffroyii/export_intrinsics.xml', 'r') as f:
            extrinsics = f.read()
        self.updated.emit(extrinsics)
    
    def get_value(self):
        return str(self.extrinsics_edit.text())

    def set_path_image(self, path):
         self.path = path

class _ThumbnailsFolderWidget(QHBoxLayout):
    updated = pyqtSignal(object)
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
        dir_ = QFileDialog.getExistingDirectory(None, 'Select a folder:', self.get_value(), QFileDialog.Option.ShowDirsOnly)
        self.thumb_edit.setText(dir_)
        self.updated.emit(dir_)



class _ThumbnailsWidget(QWidget):
    updated = pyqtSignal(object)
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
    closeSignal = pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import project")
        self.init_settings()

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.dir_image = None
        self.intrinsics = None
        self.extrinsics = None
        self.thumbnails_bool = False
        self.thumbnails = True

        self.project_dict = {}

        self.layout = QVBoxLayout()
        
        self.dir_widget = _DirWidget()
        self.dir_widget.updated.connect(self.update_dir_image)
        self.layout.addWidget(self.dir_widget)

        self.int_widget = _IntrinsicsWidget(self.dir_image)
        self.int_widget.updated.connect(self.update_intrinsics)
        self.layout.addWidget(self.int_widget)

        self.ext_widget = _ExtrinsicsWidget(self.dir_image)
        self.ext_widget.updated.connect(self.update_dir_image)
        self.layout.addWidget(self.ext_widget)

        self.thumb_widget = _ThumbnailsWidget()
        self.thumb_widget.updated.connect(self.update_dir_image)
        self.layout.addWidget(self.thumb_widget)
        
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
    
    def update_dir_image(self, dir):
        self.dir_image = dir

    def update_intrinsics(self, intrinsics):
        self.intrinsics = intrinsics

    def update_extrinsics(self, extrinsics):
        self.extrinsics = extrinsics

    def update_thumbnails(self, thumb):
        self.thumbnails_bool = thumb[0]
        if self.thumbnails_bool:
            self.thumbnails : thumb[1]
        else:
            self.thumbnails = "thumbnails"
    
    def closeEvent(self, a0: QCloseEvent) -> None:
        calib = {}

        if not self.thumbnails_bool:
            pass

        calib["thumbnails"] = self.thumbnails
        calib["intrinsics"] = self.intrinsics
        calib["extrinsics"] = self.extrinsics
        calib["commands"] = {
                    #Front is used as complete calibration for the angles
                    helpers.Keys.FRONT.name: (0,0),
                    helpers.Keys.POST.name: (-180, 0),
                    helpers.Keys.LEFT.name: (90, 0),
                    helpers.Keys.RIGHT.name: (-90, 0),
                    helpers.Keys.INFERIOR.name: (0, -90),
                    helpers.Keys.SUPERIOR.name: (0, 90)
                    }

    def init_settings(self):
        self.settings = QSettings("Sphaeroptica", "reconstruction")    