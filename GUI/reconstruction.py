'''
Copyright Yann Pollet 2023
'''

import math
import glob
from PyQt6 import QtGui
import numpy as np
import cv2 as cv
import os
import json
from PIL import Image
from scripts import helpers, reconstruction
from GUI import show_picture, import_project
from collections import deque

from PyQt6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QGridLayout,
    QPushButton, QFileDialog, QColorDialog, QSizePolicy, QMessageBox, QScrollArea, QLineEdit,
    QComboBox
)
from PyQt6.QtGui import (
    QPixmap, QResizeEvent, QMouseEvent, QImage, QPalette,
    QPaintEvent, QPainter, QBrush, QColor, QKeyEvent, QDoubleValidator)
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QSettings, QFileInfo, QEvent


class _AngleValues(QWidget):
    clicked = pyqtSignal()
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self._background_color = QColor('white')
        self._text_Color = QColor('black')
        self.setMinimumHeight(50)
        self.setMinimumWidth(100)
    
    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter(self)

        brush = QBrush()
        brush.setColor(self._background_color)
        brush.setStyle(Qt.BrushStyle.SolidPattern)
        rect = QRect(0, 0, self.width(), self.height())
        painter.fillRect(rect, brush)

        values = self.parent()._angles_sphere

        pen = painter.pen()
        pen.setColor(self._text_Color)
        painter.setPen(pen)

        font = painter.font()
        font.setFamily("Times")
        font.setPointSize(18)
        painter.setFont(font)
        
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f'({values[0]},{values[1]})')

    def _trigger_refresh(self):
        self.update()
    
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        self.clicked.emit()

class PictureButton(QLabel):
    left_clicked = pyqtSignal(object)
    right_clicked = pyqtSignal(object)
    def __init__(self, parent, key : helpers.Keys, image : QImage):
        super(QWidget, self).__init__(parent)
        self.setPixmap(image)
        self.key = key
        self.setFixedWidth(helpers.HEIGHT_COMPONENT)
        self.setFixedHeight(helpers.HEIGHT_COMPONENT)
    
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        if a0.button() == Qt.MouseButton.LeftButton :
            self.left_clicked.emit(self.key)
            return
        if a0.button() == Qt.MouseButton.RightButton :
            self.right_clicked.emit(self.key)
            return       

class QColorPixmap(QLabel):
    color_changed = pyqtSignal(object)
    def __init__(self, size, color : QColor):
        super(QLabel, self).__init__()
        self.color = color
        pixmap = QPixmap(size, size)
        pixmap.fill(self.color)
        self.setPixmap(pixmap)

        self.color_dialog = QColorDialog()
    
    def mousePressEvent(self, ev: QMouseEvent) -> None:
        color = self.color_dialog.getColor(self.color)
        if color.isValid():
            print(color.name())
            self.color_changed.emit(color)


class QPointEntry(QWidget):
    delete_point = pyqtSignal()
    label_changed = pyqtSignal(object)
    color_changed = pyqtSignal(object)
    def __init__(self, point : helpers.Point3D):
        super(QWidget, self).__init__()
        layout = QHBoxLayout()

        self.point = point
        self.label = QLineEdit(self)
        self.label.setFixedHeight(helpers.HEIGHT_COMPONENT)
        self.label.setText(point.label)
        self.label.returnPressed.connect(self.change_label)
        layout.addWidget(self.label)

        self.color_label = QColorPixmap(self.label.height(), point.get_color())
        layout.addWidget(self.color_label)
        self.color_label.color_changed.connect(self.change_color)

        self.delete_button = QPushButton(text="x")
        self.delete_button.clicked.connect(self.delete)
        self.delete_button.setFixedWidth(20)
        layout.addWidget(self.delete_button)
        
        self.id = point.id
        self.setLayout(layout)
    
    def delete(self):
        self.delete_point.emit()
    
    def change_color(self, color):
        self.color_changed.emit(color)

    def change_label(self):
        self.label.clearFocus()
        self.label_changed.emit(self.label.text())

class QPoints(QScrollArea):
    dot_added = pyqtSignal()
    delete_dot = pyqtSignal(object)
    label_changed = pyqtSignal(object)
    color_changed = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__(parent)
        self.w = QWidget()
        self.add_pt_btn = QPushButton("Add point")
        self.add_pt_btn.clicked.connect(self.add_dot)

        self.load_points(self.window().dots)

        self.setBackgroundRole(QPalette.ColorRole.Dark)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding,
            QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMaximumWidth(200)
        self.installEventFilter(self)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
    
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.ShortcutOverride or event.type() == QEvent.Type.KeyPress:
            event.ignore()
            return True

        return super().eventFilter(source, event)

    def load_points(self, points):
        self.w = QWidget()
        self.vbox = QVBoxLayout()  
        self.buttons = []
        sorted_points_k = sorted(points)
        for i in sorted_points_k:
            button = QPointEntry(points[i])
            self.buttons.append(button)
            button.delete_point.connect(self.delete_point)
            button.label_changed.connect(self.change_label)
            button.color_changed.connect(self.change_color)
            self.vbox.addWidget(button)
        self.vbox.addWidget(self.add_pt_btn)
        self.w.setLayout(self.vbox)
        self.w.setSizePolicy(QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Maximum)
        self.setWidget(self.w)
    
    def delete_point(self):
        sender_button = self.sender()
        id = sender_button.id
        self.delete_dot.emit(id)

    def add_dot(self):
        self.dot_added.emit()

    def change_label(self, text):
        sender_button = self.sender()
        id = sender_button.id
        self.label_changed.emit([id, text])
    
    def change_color(self, color):
        sender_button = self.sender()
        id = sender_button.id
        self.color_changed.emit([id, color])


class DistanceWidget(QWidget):
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.full_layout = QVBoxLayout()
        self.selection = QHBoxLayout()
        self.left = QComboBox()
        self.right = QComboBox()
        self.left.addItem("",0)
        self.right.addItem("",0)
        
        self.load_points(self.window().dots)
        self.selection.addWidget(self.left)
        self.to = QLabel("to")
        self.to.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selection.addWidget(self.to)
        self.selection.addWidget(self.right)

        self.distance = QHBoxLayout()
        self.distance.addWidget(QLabel("Distance :"))
        self.value = QLineEdit()
        self.validator = QDoubleValidator()
        self.validator.setBottom(0)
        self.value.setValidator(self.validator)
        self.distance.addWidget(self.value)

        #wait init of all widgets to add the QCombobox listener
        self.left.currentIndexChanged.connect(self.update_dist)
        self.right.currentIndexChanged.connect(self.update_dist)

        self.full_layout.addLayout(self.selection)
        self.full_layout.addLayout(self.distance)

        self.setLayout(self.full_layout)
    
    def load_points(self, points):
        self.points = {}
        left_index = self.left.currentIndex()
        left_data = self.left.currentData()
        right_index = self.right.currentIndex()
        right_data = self.right.currentData()

        self.left.clear()
        self.right.clear()

        self.left.addItem("",0)
        self.right.addItem("",0)
        for i in points:
            point = points[i]
            if point.get_position() is None:
                continue
            self.points[i] = point
            self.left.addItem(point.get_label(),point.get_id())
            self.right.addItem(point.get_label(),point.get_id())
        
        if left_index is not None and self.left.itemData(left_index) == left_data:
            self.left.setCurrentIndex(left_index)
        else:
            self.left.setCurrentIndex(0)
        if right_index is not None and self.right.itemData(right_index) == right_data:
            self.right.setCurrentIndex(right_index)
        else:
            self.right.setCurrentIndex(0)

    def update_dist(self):
        if self.left.currentIndex() <= 0 or self.right.currentIndex() <= 0:
            self.value.setText("0.0")
            return
        self.value.setText(str(reconstruction.get_distance(self.points[self.left.currentData()].get_position(), self.points[self.right.currentData()].get_position())))

class CommandsWidget(QWidget):
    dot_added = pyqtSignal()
    delete_dot = pyqtSignal(object)
    label_changed = pyqtSignal(object)
    color_changed = pyqtSignal(object)

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.v_layout = QVBoxLayout()

        # Shortcut important pictures
        self.grid_layout = QGridLayout()

        self.frontal = PictureButton(self, helpers.Keys.FRONT, QPixmap.fromImage(QImage("./icons/frontal.jpg")))
        self.posterior = PictureButton(self, helpers.Keys.POST, QPixmap.fromImage(QImage("./icons/posterior.jpg")))
        self.inferior = PictureButton(self, helpers.Keys.INFERIOR, QPixmap.fromImage(QImage("./icons/inferior.jpg")))
        self.superior = PictureButton(self, helpers.Keys.SUPERIOR, QPixmap.fromImage(QImage("./icons/superior.jpg")))
        self.left = PictureButton(self, helpers.Keys.LEFT, QPixmap.fromImage(QImage("./icons/left.jpg")))
        self.right = PictureButton(self, helpers.Keys.RIGHT, QPixmap.fromImage(QImage("./icons/right.jpg")))
        
        self.frontal.left_clicked.connect(self.left_clicked)
        self.posterior.left_clicked.connect(self.left_clicked)
        self.inferior.left_clicked.connect(self.left_clicked)
        self.superior.left_clicked.connect(self.left_clicked)
        self.left.left_clicked.connect(self.left_clicked)
        self.right.left_clicked.connect(self.left_clicked)

        self.frontal.right_clicked.connect(self.right_clicked)
        self.posterior.right_clicked.connect(self.right_clicked)
        self.inferior.right_clicked.connect(self.right_clicked)
        self.superior.right_clicked.connect(self.right_clicked)
        self.left.right_clicked.connect(self.right_clicked)
        self.right.right_clicked.connect(self.right_clicked)

        self.grid_layout.addWidget(self.superior, 0, 1)
        self.grid_layout.addWidget(self.left, 1, 0)
        self.grid_layout.addWidget(self.frontal, 1, 1)
        self.grid_layout.addWidget(self.right, 1, 2)
        self.grid_layout.addWidget(self.inferior, 2, 1)
        self.grid_layout.addWidget(self.posterior, 3, 1)
        

        self.v_layout.addLayout(self.grid_layout)

        # List of Points
        self.points = QPoints(self)
        self.points.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(self.points)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.points.delete_dot.connect(self.delete_point)
        self.points.label_changed.connect(self.change_label)
        self.points.color_changed.connect(self.change_color)
        self.points.dot_added.connect(self.add_dot)

        # Distance calculator

        self.distance_calculator = DistanceWidget(self)
        self.v_layout.addWidget(self.distance_calculator)

        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setLayout(self.v_layout)


    def left_clicked(self, key : helpers.Keys):
        self.parent().change_picture(key)
        
    def right_clicked(self, key : helpers.Keys):
        self.parent().set_picture(key)

    def delete_point(self, id):
        self.delete_dot.emit(id)
    
    def add_dot(self):
        self.dot_added.emit()

    def change_label(self, id_and_text):
        self.label_changed.emit(id_and_text)
    
    def change_color(self, id_and_color):
        self.color_changed.emit(id_and_color)

    def mousePressEvent(self, a0: QMouseEvent) -> None:
        print("Commands Pressed")

class Sphere3D(QWidget):
    def __init__(self, calibration : QFileInfo):
        super(QWidget, self).__init__()
        self.activated = False
        self.last_pos = None
        self._angles_sphere = (0,0) #(180,90)
        self._old_angles = (0,0)

        # Point3D.id -> Point3D
        self.dots = dict()
        self.dots[0] = helpers.Point3D(0, 'Front', QColor('blue'))#, position=(0.010782485813073936, 0.00032211282041287505, 0.03141674225785502, 1.0)) , position=(0.0,0.0,0.0,1.0)
        self.dots[1] = helpers.Point3D(1, 'Middle', QColor('red'))#, position=(0.00503536251302613, 0.0007932051327948597, 0.03249463969616948, 1.0))
        self.dots[2] = helpers.Point3D(2, 'Back', QColor('green'))#, position=(-0.012919467433220783, 0.0035218895786182747, 0.024576051668865468, 1.0))

        self.counter = 0

        # inverse
        self.move_from_arrow = {
            Qt.Key.Key_Up : (0,-1),
            Qt.Key.Key_Down : (0,1),
            Qt.Key.Key_Left : (-1,0),
            Qt.Key.Key_Right : (1,0),
        }
        self.v_layout = QVBoxLayout()
        self.h_layout = QHBoxLayout()
        self.sphere = QLabel()
        self.sphere.setBackgroundRole(QPalette.ColorRole.Dark)
        self.directory = ""
        self.calibration_dict = {}
        self.images = {}
        self.calibration_file = ""
        self.thumbnails = ""
        self.current_image = None

        if calibration is not None:
            self.load(calibration)
        
        self.sphere.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.sphere.setContentsMargins(0,0,0,0)
        self.sphere.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sphere_values = _AngleValues(self)
        self._sphere_values.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self._sphere_values.clicked.connect(self.values_clicked)

        self.v_layout.addWidget(self.sphere)
        self.v_layout.addWidget(self._sphere_values)

        
        self.commands_widget = CommandsWidget(self)
        self.commands_widget.delete_dot.connect(self.delete_dot)
        self.commands_widget.label_changed.connect(self.change_label)
        self.commands_widget.color_changed.connect(self.change_color)
        self.commands_widget.dot_added.connect(self.add_dot)

        self.commands_widget.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Minimum)
        self.commands_widget.setContentsMargins(0,0,0,0)
        self.h_layout.setSpacing(0)
        self.h_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        
        self.h_layout.addLayout(self.v_layout)
        self.h_layout.addWidget(self.commands_widget)


        self.setLayout(self.h_layout)

        self.setContentsMargins(0,0,0,0)
    
    def load(self, calibration):
        self.directory = calibration.absolutePath()
        self.calibration_file = calibration.fileName()
        self.current_image = None
        images_thumbnails = None
        with open(f'{self.directory}/{self.calibration_file}', "r") as f:
            self.calibration_dict = json.load(f)
            self.thumbnails = self.calibration_dict["thumbnails"]
            images_thumbnails = glob.glob(f'{self.directory}/{self.thumbnails}/*')
        image_calibration = {}
        self.center = np.matrix([0,0,0]).T
        intrinsics = np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])
        distCoeffs = np.matrix(self.calibration_dict["intrinsics"]["distortion matrix"]["matrix"])

        self.w = int(self.calibration_dict["intrinsics"]["width"])
        self.h = int(self.calibration_dict["intrinsics"]["height"])
        self.thumb_w = int(self.calibration_dict["thumbnails_width"])
        self.thumb_h = int(self.calibration_dict["thumbnails_height"])
        factor = self.thumb_w /  self.w
        second_factor = self.thumb_h /  self.h

        factor_mat = np.matrix([[factor, 0, 0],[0, second_factor, 0],[0,0,1]])
        self.intrinsics_thumbnails = factor_mat @ np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])

        cx, cy = intrinsics.item(0,2), intrinsics.item(1,2)
        image_sorted = sorted(images_thumbnails)
        point = helpers.Point3D(-1, "center")
        print(len(image_sorted))
        for path in image_sorted:
            file_name = os.path.basename(path)
            if file_name not in self.calibration_dict["extrinsics"]:
                #this checks if it's an image and if it's calibrated
                continue
            mat = np.matrix(self.calibration_dict["extrinsics"][file_name]["matrix"])
            rotation = mat[0:3, 0:3]
            trans = mat[0:3, 3]
            C = helpers.get_camera_world_coordinates(rotation, trans)
            point.add_dot(file_name, helpers.Point(cx, cy))

            image_calibration[file_name] = C

            self.center = self.center + C
        point.set_position(self.estimate_position(point))
        print(point)
        self.center = np.matrix(point.get_position()[:3]).T

        print(f"Center = {self.center}")

        keys = sorted(image_calibration.keys())

        mean_error = 0
        nbr_img = 0
        self.lowest_lat = -90#float('inf')
        self.highest_lat = 90#-float('inf')
        for file_name in keys:
            # compute error
            
            pos = np.matrix([list(point.position)])
            img_point_1 = np.matrix([point.get_image_dots(file_name).to_array()])

            extrinsics = np.matrix(self.calibration_dict["extrinsics"][file_name]["matrix"])[0:3, 0:4]
                    
            imgpoints2 = reconstruction.project_points(pos, intrinsics, extrinsics, distCoeffs).reshape((1,2))
            error = cv.norm(img_point_1, imgpoints2, cv.NORM_L2)/len(imgpoints2)
            mean_error += error
            nbr_img += 1

            # add long, lat to key
            C = image_calibration[file_name]
            vec = C - self.center
            print(f'{file_name} : {reconstruction.get_distance(C, self.center)}')
            longitude, latitude = helpers.get_long_lat(vec)
            key = (longitude, latitude) 
            lat_deg = int(helpers.rad2degrees(latitude))+1
            if lat_deg < self.lowest_lat :
                self.lowest_lat = lat_deg
            if lat_deg > self.highest_lat :
                self.highest_lat = lat_deg
            self.images[key] = file_name

            rotation = extrinsics[0:3,0:3]
            print(f"{file_name} : {helpers.get_euler_angles(rotation)}")
        if nbr_img != 0:
            print(f"total error: {mean_error/nbr_img}")
        
        print(f"Number images = {nbr_img}")

        self.current_image = self.next_image()

        #init dots again
        self.dots[0] = helpers.Point3D(0, 'Front', QColor('blue'))
        self.dots[1] = helpers.Point3D(1, 'Middle', QColor('red'))
        self.dots[2] = helpers.Point3D(2, 'Back', QColor('green'))

    def delete_dot(self, id):
        self.dots.pop(id)
        self.commands_widget.points.load_points(self.dots)
        self.commands_widget.distance_calculator.load_points(self.dots)
    
    def change_label(self, id_and_text):
        id, text = id_and_text[0], id_and_text[1]
        self.dots[id].set_label(text)
    
    def update_points(self):
        self.commands_widget.points.load_points(self.dots)
    
    def change_color(self, id_and_color):
        id, color = id_and_color[0], id_and_color[1]
        self.dots[id].set_color(color)
        self.update_points()
    
    def add_dot(self):
        max_id = max(self.dots)+1
        self.dots[max_id] = helpers.Point3D(max_id, f'Point_{max_id}')
        self.update_points()

    def get_nearest_image(self, pos):
        best_angle = float('inf')
        best_pos = None
        rad_pos = (helpers.degrees2rad(pos[0]), helpers.degrees2rad(pos[1]))
        for img_pos in self.images.keys():
            sinus = math.sin(img_pos[1]) * math.sin(rad_pos[1])
            cosinus = math.cos(img_pos[1]) * math.cos(rad_pos[1])* math.cos(abs(img_pos[0]-rad_pos[0]))
            cent_angle = math.acos(sinus + cosinus)
            if cent_angle < best_angle:
                best_angle = cent_angle
                best_pos = img_pos
        return self.images[best_pos]
    
    def next_image(self):
        
        self.current_image = self.get_nearest_image(self._angles_sphere)
        '''extrinsics = np.matrix(self.calibration_dict["extrinsics"][self.current_image]["matrix"])[0:3, 0:4]
        extrinsics_dst = self.virtual_camera_extrinsics(extrinsics)
        homography_image = self.homography(extrinsics, extrinsics_dst)

        img = cv.imread(f"{self.directory}/{self.thumbnails}/{self.current_image}", cv.IMREAD_UNCHANGED)

        
        new_image = cv.warpPerspective(img, homography_image, (self.thumb_w, self.thumb_h))
        new_image = cv.cvtColor(new_image, cv.COLOR_BGRA2RGBA)
        
        height, width, channel = new_image.shape
        bytesPerLine = 4 * width
        qImg = QImage(new_image.data, width, height, bytesPerLine, QImage.Format.Format_RGBA8888)

        pixmap = QPixmap.fromImage(qImg)'''
        pixmap = QPixmap(f'{self.directory}/{self.thumbnails}/{self.current_image}')

        pixmap = pixmap.scaled(self.sphere.height(), self.sphere.width(), Qt.AspectRatioMode.KeepAspectRatio)
        self.sphere.setPixmap(pixmap)

    def virtual_camera_extrinsics(self, extrinsics):
        rotation = extrinsics[0:3, 0:3]
        trans = extrinsics[0:3, 3]
        C = helpers.get_camera_world_coordinates(rotation, trans)

        dist = reconstruction.get_distance(self.center, C)

        long, lat = self._angles_sphere
        long, lat = helpers.degrees2rad(long), helpers.degrees2rad(lat)
        long_img, lat_img = helpers.get_long_lat(C-self.center)
        
        delta_long = long - long_img
        delta_lat = lat - lat_img

        direction_vector = helpers.get_unit_vector_from_long_lat(long, lat)
        dist_vec = direction_vector * dist 
        C_new = np.transpose(dist_vec) + self.center

        z = direction_vector / np.linalg.norm(direction_vector)
        x,y,z = direction_vector.item(0),direction_vector.item(1),direction_vector.item(2)
        omega = math.asin(-y)
        phi = math.atan2(math.sqrt(x*x + y*y),z)

        rotation_new = reconstruction.rotate_x_axis(lat) @ reconstruction.rotate_y_axis(long) @ reconstruction.rotate_z_axis(math.radians(-90)) @ reconstruction.rotate_y_axis(math.radians(90)) 
        
        trans_new = helpers.get_trans_vector(rotation_new, C_new).T

        return np.hstack((rotation_new, trans_new))


    def homography(self, ext_src, ext_dst):
        rotation = ext_src[0:3, 0:3]
        trans = ext_src[0:3, 3]
        C = helpers.get_camera_world_coordinates(rotation, trans)

        middle_x = int(self.thumb_w/2)
        middle_y = int(self.thumb_h/2)

        pix_src_1 = np.matrix([float(middle_x-50),float(middle_y-50),1]).T
        pix_src_2 = np.matrix([float(middle_x-50),float(middle_y+50),1]).T
        pix_src_3 = np.matrix([float(middle_x+50),float(middle_y-50),1]).T
        pix_src_4 = np.matrix([float(middle_x+50),float(middle_y+50),1]).T

        ray_1 = reconstruction.get_ray_direction(pix_src_1, self.intrinsics_thumbnails, ext_src)
        ray_2 = reconstruction.get_ray_direction(pix_src_2, self.intrinsics_thumbnails, ext_src)
        ray_3 = reconstruction.get_ray_direction(pix_src_3, self.intrinsics_thumbnails, ext_src)
        ray_4 = reconstruction.get_ray_direction(pix_src_4, self.intrinsics_thumbnails, ext_src)

        # compute normal
        cx, cy = self.intrinsics_thumbnails.item(0,2), self.intrinsics_thumbnails.item(1,2)
        ray = reconstruction.get_ray_direction(np.matrix([cx,cy,1]).T, self.intrinsics_thumbnails, ext_src)
        ray = (rotation[2]).T
        int_1 = reconstruction.intersectPlane((np.array(ray)).squeeze(), np.array([0,0,0]), np.array(C).squeeze(), np.array(ray_1).squeeze())
        int_2 = reconstruction.intersectPlane((np.array(ray)).squeeze(), np.array([0,0,0]), np.array(C).squeeze(), np.array(ray_2).squeeze())
        int_3 = reconstruction.intersectPlane((np.array(ray)).squeeze(), np.array([0,0,0]), np.array(C).squeeze(), np.array(ray_3).squeeze())
        int_4 = reconstruction.intersectPlane((np.array(ray)).squeeze(), np.array([0,0,0]), np.array(C).squeeze(), np.array(ray_4).squeeze())

        pix_dst_1 = reconstruction.project_points(np.matrix(int_1), self.intrinsics_thumbnails, ext_dst)
        pix_dst_2 = reconstruction.project_points(np.matrix(int_2), self.intrinsics_thumbnails, ext_dst)
        pix_dst_3 = reconstruction.project_points(np.matrix(int_3), self.intrinsics_thumbnails, ext_dst)
        pix_dst_4 = reconstruction.project_points(np.matrix(int_4), self.intrinsics_thumbnails, ext_dst)

        return reconstruction.find_homography_inhomogeneous(np.array([pix_src_1[:2], pix_src_2[:2], pix_src_3[:2], pix_src_4[:2]]), np.array([pix_dst_1[:2], pix_dst_2[:2], pix_dst_3[:2], pix_dst_4[:2]]))


    # to refactor in utils
    def get_next_angle(self, old_angle, move, min, max):
        difference = max - min
        return ((difference + old_angle-min - move) % difference) + min

    def get_new_angle(self, new_pos):
        #horizontal -180 -> 179, vertical -90 -> 90
        x = self.get_next_angle(self._old_angles[0], int((new_pos.x() - self.last_pos.x())/2), -180, 180)
        # ((360 + self._old_angles[0]+180 + int((self.last_pos.x()-new_pos.x())/2)) % 360) - 180 # +180 to go back to 0-359 and -180 at the end
        y = max(self.lowest_lat, min(self._old_angles[1] + int((new_pos.y() - self.last_pos.y())/2), self.highest_lat))
        
        return (x,y)
        
    def move_arrow(self, key: helpers.Arrows):
        move = self.move_from_arrow[key.value]
        x = self.get_next_angle(self._old_angles[0], move[0], -180, 180)
        y = max(self.lowest_lat, min((self._old_angles[1] + move[1]), self.highest_lat))
        self._angles_sphere = (x, y)
        self._sphere_values._trigger_refresh()
        self.next_image()
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])

    def set_picture(self, key: helpers.Keys):
        self.commands[key.name] = self._angles_sphere
        self.calibration_dict["commands"][key.name] = self._angles_sphere
        with open(f"{self.directory}/{self.calibration_file}", "w") as f_to_write:
            json.dump(self.calibration_dict, f_to_write)

    def change_picture(self, key: helpers.Keys):
        self._angles_sphere = self.commands[key.name]
        self._sphere_values._trigger_refresh()
        self.next_image()
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        new_pos = ev.pos()
        if self.activated:
            self._angles_sphere = self.get_new_angle(new_pos)
            self._sphere_values._trigger_refresh()
            self.next_image()
    
    def mousePressEvent(self, ev: QMouseEvent) -> None:
        self.activated = True
        self.last_pos = ev.pos()
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        self.activated = False
        self.last_pos = None
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])
    
    def resizeEvent(self, a0: QResizeEvent) -> None:
        try:
            self.current_image = self.get_nearest_image(self._angles_sphere)
            pixmap = self.sphere.pixmap()
            pixmap = pixmap.scaled(self.sphere.height(), self.sphere.width(), Qt.AspectRatioMode.KeepAspectRatio)
            self.sphere.setPixmap(pixmap)
        except:
            pass


    def values_clicked(self) -> None:
        intrinsics = np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])
        distCoeffs = np.matrix(self.calibration_dict["intrinsics"]["distortion matrix"]["matrix"])
        extrinsics = np.matrix(self.calibration_dict["extrinsics"][self.current_image]["matrix"])
        extrinsics = extrinsics[0:3, 0:4]

        dots = {k:dot.to_tuple(self.current_image, intrinsics, extrinsics, distCoeffs) for k, dot in self.dots.items()}
        self.win = show_picture.QImageViewer(f'{self.directory}/{self.current_image}', dots)
        self.win.show()
        self.win.closeSignal.connect(self.get_dots)
    
    def get_dots(self, dots):
        nbr_img = 0
        mean_error = 0
        intrinsics = np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])
        distCoeffs = np.matrix(self.calibration_dict["intrinsics"]["distortion matrix"]["matrix"])

        for dot in dots:
            self.dots[dot].add_dot(self.current_image, dots[dot]["dot"])
            pos = self.estimate_position(self.dots[dot])
            if pos is not None:
                self.dots[dot].set_position(pos)
            print(f"{self.dots[dot].label} : {self.dots[dot].get_position()}")
            if self.dots[dot].get_position() is not None:
                dot_images = self.dots[dot].get_dots()
                for image in dot_images:
                    if dot_images[image] is None:
                        continue
                    point = np.matrix([list(self.dots[dot].position)])
                    img_point_1 = np.matrix([dot_images[image].to_array()])

                    extrinsics = np.matrix(self.calibration_dict["extrinsics"][image]["matrix"])
                    extrinsics = extrinsics[0:3, 0:4]
                    
                    imgpoints2 = reconstruction.project_points(point, intrinsics, extrinsics, distCoeffs).reshape((1,2))
                    error = cv.norm(img_point_1, imgpoints2, cv.NORM_L2)/len(imgpoints2)
                    mean_error += error
                    nbr_img += 1
        if nbr_img != 0:
            print(f"total error: {mean_error/nbr_img}")
        
        self.commands_widget.distance_calculator.load_points(self.dots)

        
    
    def estimate_position(self, point: helpers.Point3D):
        dots_no_None = {k:v for (k,v) in point.dots.items() if v is not None}

        if len(dots_no_None) <2 :
            return None
        intrinsics = np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])
        dist_coeffs = np.matrix(self.calibration_dict["intrinsics"]["distortion matrix"]["matrix"])
        dots = list(dots_no_None.items())
        w = int(self.calibration_dict["intrinsics"]["width"])
        h = int(self.calibration_dict["intrinsics"]["height"])
        
        proj_points = []
        for dot in dots:
            image_ext = np.matrix(self.calibration_dict["extrinsics"][dot[0]]["matrix"])
            image_ext = image_ext[0:3, 0:4]
            proj_mat = np.matmul(intrinsics, image_ext)
            img_point = np.matrix([dot[1].to_array()]).T
            img_point_undistort = reconstruction.undistort_iter(np.array([img_point]).reshape((1,1,2)), intrinsics, dist_coeffs)
            proj_point = helpers.ProjPoint(proj_mat, img_point_undistort)
            proj_points.append(proj_point)
        points3D = reconstruction.triangulate_point(proj_points)
        return tuple(points3D)

class InitWidget(QWidget):

    def __init__(self, parent):
        super(InitWidget, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.question  = QLabel("Import or create project")
        self.question.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout.addWidget(self.question)

        # choices 
        self.choices = QHBoxLayout()
        self.cam_calib = QPushButton(text="Import",parent=self)
        self.cam_calib.setFixedSize(500, 300)
        self.cam_calib.clicked.connect(self.import_project)


        rec = QPushButton(text="Create new project",parent=self)
        rec.setFixedSize(500, 300)
        rec.clicked.connect(self.create_project)

        self.choices.addWidget(self.cam_calib)
        self.choices.addWidget(rec)

        self.layout.addLayout(self.choices)
        self.setLayout(self.layout)
    
    def import_project(self):
        dir_ = QFileInfo(QFileDialog.getOpenFileName(self, "Open Calibration File", ".", "JSON (*.json)")[0])
        self.parent().load_dir(dir_)
        self.parent().layout.setCurrentIndex(1)
    
    def fixed_directory(self, directory):
        print(f"dir : {self.dir} vs {directory} : {self.dir == directory}")

        if self.dir != directory:
            self.dlg_save.setDirectory(self.dir)

    
    def create_project(self):
        dlg = import_project.QImportProject()
        dlg.setWindowModality(Qt.WindowModality.NonModal)
        if dlg.exec():
            print("accepted")
            self.dir = dlg.dir_image
            self.calib = dlg.calib
            self.calib_file_name = QFileDialog.getSaveFileName(self, "Save Calibration File", self.dir+"/.json","Json Files (*.json)")[0]
            print(self.calib_file_name)
            
            print(not self.calib_file_name.strip())
            if not self.calib_file_name.strip():
                # canceled
                return
            
            # Checker les thumbnails
            
            if not os.path.exists(f'{self.dir}/{self.calib["thumbnails"]}'):
                os.makedirs(f'{self.dir}/{self.calib["thumbnails"]}')
            
            images_thumbnails = set(glob.glob(f'{self.dir}/{self.calib["thumbnails"]}/*'))

            print(os.path.exists(f'{self.dir}/{self.calib["thumbnails"]}'))
            print(f'{self.dir}/{self.calib["thumbnails"]}')


            print(len(images_thumbnails))
            print(type(images_thumbnails))

            queue_img_to_make = deque()
            
            thumb_w = thumb_h = 640
            #sauver les thumbnails
            for key in self.calib["extrinsics"]:
                #print(key)
                if f'{self.dir}/{self.calib["thumbnails"]}/{key}' not in images_thumbnails:
                    print(key)
                    queue_img_to_make.append(key)
                else:
                    #get dimensions
                    print(f'{self.dir}/{self.calib["thumbnails"]}/{key}')
                    with Image.open(f'{self.dir}/{self.calib["thumbnails"]}/{key}') as im:
                        thumb_w = im.width
                        thumb_h = im.height
            
            print(len(queue_img_to_make))
            while len(queue_img_to_make) != 0:
                print(len(queue_img_to_make))
                img = queue_img_to_make.pop()
                print(img)
                with Image.open(f'{self.dir}/{img}') as im_basic:
                    im_basic.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
                    thumb_w = im_basic.width
                    thumb_h = im_basic.height
                    im_basic.save(f'{self.dir}/{self.calib["thumbnails"]}/{img}')

            self.calib["thumbnails_width"] = thumb_w
            self.calib["thumbnails_height"] = thumb_h
            with open(self.calib_file_name, "w") as f_to_write:
                json.dump(self.calib, f_to_write)
            
            self.parent().load_dir(QFileInfo(self.calib_file_name))
            self.parent().layout.setCurrentIndex(1)


class ReconstructionWidget(QWidget):

    def __init__(self, parent):
        super(ReconstructionWidget, self).__init__(parent)

        self.init_settings()
        try:
            file_settings = self.reconstruction_settings.value("directory")
            self.dir_images = QFileInfo(file_settings) if file_settings is not None and QFileInfo(file_settings).exists() else None
        except:
            self.reconstruction_settings.setValue("directory", None)
            self.dir_images = None

        self.parent = parent
        self.setWindowTitle("3D reconstruction")

        # import or create json file
        self.init = InitWidget(self)
        # viewer
        self.viewer = Sphere3D(self.dir_images)
        self.viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.layout = QStackedLayout()
        self.layout.addWidget(self.init)
        self.layout.addWidget(self.viewer)
        self.layout.setContentsMargins(0,0,0,0)

        self.setLayout(self.layout)
        
        if self.dir_images is None:
            self.layout.setCurrentIndex(0)
        else:
            # Display Sphere
            self.layout.setCurrentIndex(1)
    
    def init_settings(self):
        self.reconstruction_settings = QSettings("Sphaeroptica", "reconstruction")
    
    def load_dir(self, dir):
        self.viewer.load(dir)
        self.reconstruction_settings.setValue("directory", dir.absoluteFilePath())
    
    def keyPressEvent(self, keys_pressed: QKeyEvent) -> None:
        modifiers = keys_pressed.modifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            self.set_picture(keys_pressed.key())
        else:
            # depending on the key pressed, it will throw an exception and ignore it
            self.change_picture(keys_pressed.key())
            self.move_sphere(keys_pressed.key())
    
    def move_sphere(self, key):
        try:
            key = helpers.Arrows(key)
            self.viewer.move_arrow(key)
        except Exception as e:
            pass
    
    def change_picture(self, key):
        try:
            key = helpers.Keys(key)
            self.viewer.change_picture(key)
        except Exception as e:
            pass
    
    def set_picture(self, key):
        try:
            key = helpers.Keys(key)
            self.viewer.set_picture(key)
        except Exception as e:
            pass