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


import math
import glob
import numpy as np
import cv2 as cv
import pandas as pd
import os
import json
from PIL import Image
from scripts import helpers, reconstruction, converters
from GUI import show_picture, import_project
from collections import deque

from PySide6.QtWidgets import (
    QLabel, QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QGridLayout,
    QPushButton, QFileDialog, QColorDialog, QSizePolicy, QScrollArea, QLineEdit,
    QComboBox, QCheckBox, QDialog, QDialogButtonBox
)
from PySide6.QtGui import (
    QPixmap, QResizeEvent, QMouseEvent, QImage, QPalette, QIcon,
    QPaintEvent, QPainter, QBrush, QColor, QKeyEvent, QDoubleValidator,
    QDragEnterEvent, QDropEvent, QDrag)
from PySide6.QtCore import Qt, QRect, Signal, QSettings, QFileInfo, QEvent, QLocale, QMimeData, QSize


class _AngleValues(QWidget):
    """Widget displaying the geographic value of the position of the virtual camera
    """

    clicked = Signal()
    def __init__(self, parent):
        super(_AngleValues, self).__init__(parent)
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
    """Widget for positional shortcut (front, back ...)
    """

    left_clicked = Signal(object)
    right_clicked = Signal(object)
    def __init__(self, parent, key : helpers.Keys, image : QImage):
        super(PictureButton, self).__init__(parent)
        self.setPixmap(image)
        self.key = key
        self.setFixedWidth(helpers.HEIGHT_COMPONENT)
        self.setFixedHeight(helpers.HEIGHT_COMPONENT)
    
    def mousePressEvent(self, a0: QMouseEvent) -> None:
        """_summary_

        Args:
            a0 (QMouseEvent): _description_
        """
        if a0.button() == Qt.MouseButton.LeftButton :
            #go to shortcutted image
            self.left_clicked.emit(self.key)
            return
        if a0.button() == Qt.MouseButton.RightButton :
            #set that image as shortcut
            self.right_clicked.emit(self.key)
            return       

class QColorPixmap(QLabel):
    """Widget that show the referenced color for a point
    """

    color_changed = Signal(object)
    def __init__(self, size, color : QColor):
        super(QColorPixmap, self).__init__()
        self.color = color
        pixmap = QPixmap(size, size)
        pixmap.fill(self.color)
        self.setPixmap(pixmap)

        self.color_dialog = QColorDialog()
    
    def mousePressEvent(self, ev: QMouseEvent) -> None:
        """Show a ColorDialog to select a new color for the point

        Args:
            ev (QMouseEvent): Mouse Event
        """
        color = self.color_dialog.getColor(self.color)
        if color.isValid():
            self.color_changed.emit(color)


class QPointEntry(QWidget):
    """Entry in the list of points
    """

    delete_point = Signal()
    reset_point = Signal()
    label_changed = Signal(object)
    color_changed = Signal(object)

    def __init__(self, point : reconstruction.Point3D):
        super(QPointEntry, self).__init__()
        layout = QHBoxLayout()

        self.drag_button = QLabel()
        pixmap = QIcon("icons/grid-dot.png").pixmap(QSize(20,20))
        self.drag_button.setPixmap(pixmap)
        self.drag_button.setFixedWidth(20)
        self.drag_button.setBackgroundRole(QPalette.ColorRole.Highlight)
        layout.addWidget(self.drag_button)

        self.point = point
        self.label = QLineEdit(self)
        self.label.setFixedHeight(helpers.HEIGHT_COMPONENT)
        self.label.setText(point.label)
        self.label.editingFinished.connect(self.change_label)
        layout.addWidget(self.label)

        self.color_label = QColorPixmap(self.label.height(), point.get_color())
        layout.addWidget(self.color_label)
        self.color_label.color_changed.connect(self.change_color)

        self.reset_button = QPushButton()
        self.reset_button.setIcon(QIcon("icons/arrow-circle-double-135.png"))
        self.reset_button.clicked.connect(self.reset)
        self.reset_button.setFixedWidth(20)
        layout.addWidget(self.reset_button)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(QIcon("icons/cross.png"))
        self.delete_button.clicked.connect(self.delete)
        self.delete_button.setFixedWidth(20)
        layout.addWidget(self.delete_button)
        
        self.id = point.id
        self.setLayout(layout)
    
    def delete(self):
        """Delete Entry
        TODO : Use a ModelView architecture for points
        """

        self.delete_point.emit()
    
    def reset(self):
        """Remove all landmarks and 3D position 
        TODO : Use a ModelView architecture for points
        """

        self.reset_point.emit()
    
    def change_color(self, color):
        """Change color of point
        TODO : Use a ModelView architecture for points

        Args:
            color (QColor): new color
        """

        self.color_changed.emit(color)

    def change_label(self):
        """edit the label of the point
        TODO : Use a ModelView architecture for points
        """

        self.label.clearFocus()
        self.label_changed.emit(self.label.text())

    def mouseMoveEvent(self, e):
        """Drag of Qpoints

        Args:
            e (QMouseEvent): event
        """
        print(f"Drag button {self.id}")
        if e.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.exec(Qt.DropAction.MoveAction)

class QPoints(QScrollArea):
    """ScrollArea containing the list of QPointsEntry
    """
    dot_added = Signal()
    delete_dot = Signal(object)
    reset_dot = Signal(object)
    label_changed = Signal(object)
    color_changed = Signal(object)

    def __init__(self, parent):
        super(QPoints, self).__init__(parent)
        self.w = QWidget()
        self.add_pt_btn = QPushButton("Add point")
        self.add_pt_btn.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum)
        self.add_pt_btn.clicked.connect(self.add_dot)

        self.load_points(self.window().dots)
        self.setBackgroundRole(QPalette.ColorRole.BrightText)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)
        self.installEventFilter(self)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
    
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.ShortcutOverride or event.type() == QEvent.Type.KeyPress:
            event.ignore()
            return True

        return super().eventFilter(source, event)

    def load_points(self, points):
        """Load each point to the list

        Args:
            points (list): list of points
        """

        self.w = QWidget()
        self.vbox = QVBoxLayout()

        self.pointbox = QVBoxLayout()
        self.buttons = []
        for point in points:
            button = QPointEntry(point)
            self.buttons.append(button)
            button.delete_point.connect(self.delete_point)
            button.reset_point.connect(self.reset_point)
            button.label_changed.connect(self.change_label)
            button.color_changed.connect(self.change_color)
            self.pointbox.addWidget(button)
        
        self.vbox.addLayout(self.pointbox)
        self.vbox.addWidget(self.add_pt_btn)
        self.w.setLayout(self.vbox)
        self.w.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum)
        self.setWidget(self.w)
        self.setAcceptDrops(True)
    
    def delete_point(self):
        """Sends a signal to delete point
        TODO : Use a ModelView architecture for points
        """

        sender_button = self.sender()
        id = sender_button.id
        self.delete_dot.emit(id)
    
    def reset_point(self):
        """Sends a signal to reset point
        TODO : Use a ModelView architecture for points
        """
        
        sender_button = self.sender()
        id = sender_button.id
        self.reset_dot.emit(id)

    def add_dot(self):
        """Sends a signal to add a new point
        TODO : Use a ModelView architecture for points
        """

        self.dot_added.emit()

    def change_label(self, text):
        """Sends a signal to change the label of the point
        TODO : Use a ModelView architecture for points
        """

        sender_button = self.sender()
        id = sender_button.id
        self.label_changed.emit([id, text])
    
    def change_color(self, color):
        """Sends a signal to change the color of the point
        TODO : Use a ModelView architecture for points
        """

        sender_button = self.sender()
        id = sender_button.id
        self.color_changed.emit([id, color])
    
    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        """Autorizes drag event

        Args:
            a0 (QDragEnterEvent): Drag Event
        """

        self.original_pos = a0.position()
        a0.accept()


    def dropEvent(self, a0: QDropEvent) -> None:
        """Authorize drop event and change list of points
        Add the dragged point over the first point it isn't under

        Args:
            a0 (QDragEnterEvent): Drag Event
        """

        pos = a0.position()
        widget = a0.source()

        desc = pos.y() > self.original_pos.y()

        last = self.pointbox.itemAt(self.pointbox.count()-1).widget()
        if pos.y() > last.y() + last.size().height() // 2:
            # The drag went under the last widget of the list
            self.window().rec.viewer.move_dot(self.pointbox.count()-1, widget.id)
        else:
            for n in range(self.pointbox.count()):
                # Get the widget at each index in turn.
                w = self.pointbox.itemAt(n).widget()
                print(f"{w.label.text()} : {pos.y()} < {w.y() + w.size().height() // 2}")
                if pos.y() < w.y() + w.size().height() // 2:
                    # We didn't drag past this widget.
                    # insert to the left of it.
                    self.window().rec.viewer.move_dot(n-1 if desc else n, widget.id)
                    break
        self.window().rec.viewer.update_points()
        a0.accept()


class DistanceWidget(QWidget):
    """Widget that show the distance between two chosen points
    """

    def __init__(self, parent):
        super(DistanceWidget, self).__init__(parent)
        self.init_settings()

        self.full_layout = QVBoxLayout()
        self.selection = QHBoxLayout()
        self.left = QComboBox()
        self.right = QComboBox()
        self.left.addItem("",0)
        self.right.addItem("",0)

        self.reset_layout = QHBoxLayout()
        self.reset_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.reset_button = QPushButton("Reset Factor")
        self.reset_button.clicked.connect(self.reset_scale_factor)
        self.reset_layout.addWidget(self.reset_button)
        self.full_layout.addLayout(self.reset_layout)
        
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
        self.validator.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.value.setValidator(self.validator)
        self.distance.addWidget(self.value)
        
        self.scale_widget = QComboBox(self)
        for key in helpers.Scale._member_map_.keys():
            self.scale_widget.addItem(key)
        print(f"Current scale : {self.reconstruction_settings.value('scale')}")

        self.scale_widget.setCurrentText(self.reconstruction_settings.value("scale").name if self.reconstruction_settings.value("scale") is not None else helpers.Scale.M.name)
        self.scale_widget.currentTextChanged.connect(self.update_scale_settings)
        self.distance.addWidget(self.scale_widget)

        self.scale_factor = 1.0
        self.original_value = 0.0
        self.value.editingFinished.connect(self.update_scale)

        #wait init of all widgets to add the QCombobox listener
        self.left.currentIndexChanged.connect(self.update_dist)
        self.right.currentIndexChanged.connect(self.update_dist)
        self.scale_widget.currentIndexChanged.connect(self.update_dist)

        self.full_layout.addLayout(self.selection)
        self.full_layout.addLayout(self.distance)

        self.setLayout(self.full_layout)
    
    def init_settings(self):
        """Get QSettings to get persistent data
        """

        self.reconstruction_settings = QSettings("Sphaeroptica", "reconstruction")
    
    def update_scale_settings(self):
        """Update scale of the distance (M, CM or MM)
        """

        print(f"current text scale : {helpers.Scale[str(self.scale_widget.currentText())]}")
        self.reconstruction_settings.setValue("scale", helpers.Scale[str(self.scale_widget.currentText())])
    
    def update_scale(self):
        """Update scale factor
        """

        if self.original_value == 0.0:
            self.value.setText("0.0")
            print("Impossible to update scale from a nul value")
            return
        # There is already a double validator on the QLineEdit
        value = float(self.value.text())
        self.scale_factor = value * helpers.Scale[str(self.scale_widget.currentText())].value / self.original_value
        self.value.setCursorPosition(0)
        print(f"Scale factor set at {self.scale_factor}")
    
    def reset_scale_factor(self):
        """Reset scale factor to 1
        """

        self.scale_factor = 1.0
        print("Scale factor reset")
        self.update_dist()

    def load_points(self, points):
        """Load each point that has a 3D position to the widget

        Args:
            points (list): list of points
        """

        self.points = list()
        self.points.append(None)
        left_index = self.left.currentIndex()
        left_data = self.left.currentData()
        right_index = self.right.currentIndex()
        right_data = self.right.currentData()

        self.left.clear()
        self.right.clear()

        self.left.addItem("",0)
        self.right.addItem("",0)
        for point in points:
            if point.get_position() is None:
                continue
            self.points.append(point)
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
        """Computes the distance between two points and updates the widget
        """

        if self.left.currentIndex() <= 0 or self.right.currentIndex() <= 0:
            self.value.setText("0.0")
            self.original_value = 0.0
            return
        self.original_value = reconstruction.get_distance(self.points[self.left.currentIndex()].get_position(), self.points[self.right.currentIndex()].get_position())
        self.value.setText(str(self.original_value * self.scale_factor / helpers.Scale[str(self.scale_widget.currentText())].value))
        self.value.setCursorPosition(0)

class CommandsWidget(QWidget):
    """Right side of the window, Widget containing everything, shortcuts, points and distance
    """

    dot_added = Signal()
    delete_dot = Signal(object)
    reset_dot = Signal(object)
    label_changed = Signal(object)
    color_changed = Signal(object)
    export = Signal()

    def __init__(self, parent):
        super(CommandsWidget, self).__init__(parent)
        self.v_layout = QVBoxLayout()

        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.setVerticalSpacing(10)
        self.grid_layout.setHorizontalSpacing(30)

        self.v_layout.addLayout(self.grid_layout)

        # List of Points
        self.points = QPoints(self)
        self.points.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout.addWidget(self.points)

        self.points.delete_dot.connect(self.delete_point)
        self.points.reset_dot.connect(self.reset_point)
        self.points.label_changed.connect(self.change_label)
        self.points.color_changed.connect(self.change_color)
        self.points.dot_added.connect(self.add_dot)

        # Distance calculator

        self.distance_calculator = DistanceWidget(self)
        self.v_layout.addWidget(self.distance_calculator)

        # Export Button
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.to_export)
        self.v_layout.addWidget(self.export_button)

        self.setLayout(self.v_layout)


    def left_clicked(self, key : helpers.Keys):
        self.parent().change_picture(key)
        
    def right_clicked(self, key : helpers.Keys):
        self.parent().set_picture(key)

    def delete_point(self, id):
        self.delete_dot.emit(id)

    def reset_point(self, id):
        self.reset_dot.emit(id)
    
    def add_dot(self):
        self.dot_added.emit()

    def change_label(self, id_and_text):
        self.label_changed.emit(id_and_text)
    
    def change_color(self, id_and_color):
        self.color_changed.emit(id_and_color)
    
    def to_export(self):
        self.export.emit()

class Sphere3D(QWidget):
    """Left Size of the Window, Virtual Camera + Angle Values
    """

    def __init__(self, calibration : QFileInfo):
        super(Sphere3D, self).__init__()
        self.activated = False
        self.last_pos = None
        self._angles_sphere = (0,0) #(180,90)
        self._old_angles = (0,0)

        self.init_dots()

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
            #load last calibration file used
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
        self.commands_widget.reset_dot.connect(self.reset_dot)
        self.commands_widget.label_changed.connect(self.change_label)
        self.commands_widget.color_changed.connect(self.change_color)
        self.commands_widget.dot_added.connect(self.add_dot)
        self.commands_widget.export.connect(self.export)

        self.commands_widget.setSizePolicy(QSizePolicy.Policy.Maximum,QSizePolicy.Policy.Minimum)
        self.commands_widget.setContentsMargins(0,0,0,0)
        self.h_layout.setSpacing(0)
        self.h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        
        self.h_layout.addLayout(self.v_layout)
        self.h_layout.addWidget(self.commands_widget)


        self.setLayout(self.h_layout)

        self.setContentsMargins(0,0,0,0)
    
    def init_dots(self):
        """Creates the first dot when we open the app
        """
         
        # Point3D.id -> Point3D
        self.dots = list()
        self.dots.append(reconstruction.Point3D(0, 'Point_0', QColor('blue')))
        QColor('blue').value()
    
    def load(self, calibration : QFileInfo):
        """load a calibration file into the project

        Args:
            calibration (QFileInfo): calibration file
        """

        print("LOAD")
        self.images = {}
        self.directory = calibration.absolutePath()
        self.calibration_file = calibration.fileName()
        self.current_image = None
        images_thumbnails = None

        #Load the calibration file as a dict
        with open(f'{self.directory}/{self.calibration_file}', "r") as f:
            self.calibration_dict = json.load(f)
            self.thumbnails = self.calibration_dict["thumbnails"]
            images_thumbnails = glob.glob(f'{self.directory}/{self.thumbnails}/*')
        image_calibration = {}
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
        
        #Compute an approximately estimated center of the sphere of images
        cx, cy = intrinsics.item(0,2), intrinsics.item(1,2)
        image_sorted = sorted(images_thumbnails)
        point = reconstruction.Point3D(-1, "center")
        for path in image_sorted:
            file_name = os.path.basename(path)
            if file_name not in self.calibration_dict["extrinsics"]:
                #checks if it's an image and if it's calibrated
                continue
            mat = np.matrix(self.calibration_dict["extrinsics"][file_name]["matrix"])
            rotation = mat[0:3, 0:3]
            trans = mat[0:3, 3]
            C = converters.get_camera_world_coordinates(rotation, trans)
            point.add_dot(file_name, helpers.Point(cx, cy))

            image_calibration[file_name] = C

        point.set_position(self.estimate_position(point))
        self.center = np.matrix(point.get_position()[:3]).T

        print(f"Center = {self.center}")

        keys = sorted(image_calibration.keys())

        mean_error = 0
        nbr_img = 0
        self.lowest_lat = float('inf')
        self.highest_lat = -float('inf')
        for file_name in keys:
            
            # compute error of the estimated center (can be high) 
            pos = np.matrix([list(point.position)])
            img_point_1 = np.matrix([point.get_image_dots(file_name).to_array()])

            extrinsics = np.matrix(self.calibration_dict["extrinsics"][file_name]["matrix"])[0:3, 0:4]
                    
            imgpoints2 = reconstruction.project_points(pos, intrinsics, extrinsics, distCoeffs).reshape((1,2))
            error = cv.norm(img_point_1, imgpoints2, cv.NORM_L2)/len(imgpoints2)
            mean_error += error
            nbr_img += 1

            # compute geographic coordinates and use them as key for the virtual camera
            C = image_calibration[file_name]
            vec = C - self.center
            longitude, latitude = converters.get_long_lat(vec)
            key = (longitude, latitude) 
            lat_deg = int(converters.rad2degrees(latitude))+1
            if lat_deg < self.lowest_lat :
                self.lowest_lat = lat_deg
            if lat_deg > self.highest_lat :
                self.highest_lat = lat_deg
            self.images[key] = file_name

            rotation = extrinsics[0:3,0:3]
        if nbr_img != 0:
            print(f"total error: {mean_error/nbr_img}")
        
        print(f"Lowest = {self.lowest_lat}; Highest = {self.highest_lat}")
        print(f"Number images = {nbr_img}")

        self.current_image = self.next_image()

        self.init_dots()

    def delete_dot(self, id):
        """Deletes dot
        TODO : Use a ModelView architecture for points
        Args:
            id (int): Id of the dot to delete
        """

        self.dots.remove(id)
        self.update_points()
    
    def reset_dot(self, id):
        """Resets dot
        TODO : Use a ModelView architecture for points
        Args:
            id (int): Id of the dot to delete
        """

        index = self.dots.index(id)
        self.dots[index].reset_point()
        self.update_points()
    
    def change_label(self, id_and_text):
        """Change the label of the point
        TODO : Use a ModelView architecture for points
        Args:
            id_and_text (tuple(int, string)): id, new label
        """

        id, text = id_and_text[0], id_and_text[1]
        index = self.dots.index(id)
        self.dots[index].set_label(text)
    
    def change_color(self, id_and_color):
        """Change the coloe of the point
        TODO : Use a ModelView architecture for points
        Args:
            id_and_text (tuple(int, Qcolor)): id, new coloe
        """

        id, color = id_and_color[0], id_and_color[1]
        index = self.dots.index(id)
        self.dots[index].set_color(color)
        self.update_points()
    
    def add_dot(self):
        """Add new point to the list
        TODO : Use a ModelView architecture for points
        """

        max_id = max({i.id for i in self.dots}, default=(-1))+1
        self.dots.append(reconstruction.Point3D(max_id, f'Point_{max_id}'))
        self.update_points()
    
    def move_dot(self, index, id):
        """move dot to new index 

        Args:
            index (int): new index
            id (int): id of point
        """

        old_index = self.dots.index(id)
        
        dot = self.dots.pop(old_index)
        self.dots.insert(index, dot)
        

    def update_points(self):
        """Update QPointsWidget and DistanceWidget
        """

        self.commands_widget.points.load_points(self.dots)
        self.commands_widget.distance_calculator.load_points(self.dots)
    
    def get_nearest_image(self, pos):
        """gets the 

        Args:
            pos (np.array): the position of the virtual camera (longitude and latitude)

        Returns:
            string: the image path
        """

        best_angle = float('inf')
        best_pos = None
        rad_pos = (converters.degrees2rad(pos[0]), converters.degrees2rad(pos[1]))
        for img_pos in self.images.keys():
            sinus = math.sin(img_pos[1]) * math.sin(rad_pos[1])
            cosinus = math.cos(img_pos[1]) * math.cos(rad_pos[1])* math.cos(abs(img_pos[0]-rad_pos[0]))
            cent_angle = math.acos(sinus + cosinus)
            if cent_angle < best_angle:
                best_angle = cent_angle
                best_pos = img_pos
        return self.images[best_pos]
    
    def next_image(self):
        """Updates the image on the sphere
        """

        self.current_image = self.get_nearest_image(self._angles_sphere)
        
        '''
        # DEPRECATED Computes the homography matrix for the virtual camera
        extrinsics = np.matrix(self.calibration_dict["extrinsics"][self.current_image]["matrix"])[0:3, 0:4]
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
        """Deprecated Computes the virtual camera extrinsics

        Args:
            extrinsics (np.ndarray): extrinsic matrix of the nearest image

        Returns:
            np.ndarray: extrinsic matrix of the virtual camera
        """

        rotation = extrinsics[0:3, 0:3]
        trans = extrinsics[0:3, 3]
        C = converters.get_camera_world_coordinates(rotation, trans)

        dist = reconstruction.get_distance(self.center, C)

        long, lat = self._angles_sphere
        long, lat = converters.degrees2rad(long), converters.degrees2rad(lat)

        direction_vector = converters.get_unit_vector_from_long_lat(long, lat)
        dist_vec = direction_vector * dist 
        C_new = np.transpose(dist_vec) + self.center

        rotation_new = reconstruction.rotate_x_axis(lat) @ reconstruction.rotate_y_axis(long) @ reconstruction.rotate_z_axis(math.radians(-90)) @ reconstruction.rotate_y_axis(math.radians(90)) 
        
        trans_new = converters.get_trans_vector(rotation_new, C_new).T

        return np.hstack((rotation_new, trans_new))


    def homography(self, ext_src, ext_dst):
        """Deprecated Computes the homography matrix

        Args:
            ext_src (np.ndarray): extrinsic matrix of source image
            ext_dst (np.ndarray): extrinsic matrix of virtual camera

        Returns:
            np.ndarray: homography matrix
        """

        rotation = ext_src[0:3, 0:3]
        trans = ext_src[0:3, 3]
        C = converters.get_camera_world_coordinates(rotation, trans)

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
        """Increment/decrement angle and go back to min if angle+move > max

        Args:
            old_angle (int): _description_
            move (int): the angle to add
            min (int): minimum angle allowed
            max (int): maximum angle allowed

        Returns:
            int: next angle 
        """

        difference = max - min
        return ((difference + old_angle-min - move) % difference) + min

    def get_new_angle(self, new_pos):
        """Compute new postion of the virtual camera

        Args:
            new_pos (QPoint): position of the mouse

        Returns:
            tuple(int, int): new longitude and latitude angles
        """
        
        #horizontal -180 -> 179, vertical -90 -> 90
        x = self.get_next_angle(self._old_angles[0], int((new_pos.x() - self.last_pos.x())/2), -180, 180)
        # ((360 + self._old_angles[0]+180 + int((self.last_pos.x()-new_pos.x())/2)) % 360) - 180 # +180 to go back to 0-359 and -180 at the end
        y = max(self.lowest_lat, min(self._old_angles[1] + int((new_pos.y() - self.last_pos.y())/2), self.highest_lat))
        
        return (x,y)
        
    def move_arrow(self, key: helpers.Arrows):
        """Move the virtual camera by using your key arrows

        Args:
            key (helpers.Arrows): key that has been pressed + the corresponding move
        """

        move = self.move_from_arrow[key.value]
        x = self.get_next_angle(self._old_angles[0], move[0], -180, 180)
        y = max(self.lowest_lat, min((self._old_angles[1] + move[1]), self.highest_lat))
        self._angles_sphere = (x, y)
        self._sphere_values._trigger_refresh()
        self.next_image()
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])

    def set_picture(self, key: helpers.Keys):
        """set shortcut picture

        Args:
            key (helpers.Keys): key pressed
        """

        self.calibration_dict["commands"][key.name] = self._angles_sphere
        with open(f"{self.directory}/{self.calibration_file}", "w") as f_to_write:
            json.dump(self.calibration_dict, f_to_write)

    def change_picture(self, key: helpers.Keys):
        """Move to the shortcut picture asked

        Args:
            key (helpers.Keys): key pressed
        """

        self._angles_sphere = self.calibration_dict["commands"][key.name]
        self._sphere_values._trigger_refresh()
        self.next_image()
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:
        """MouseEvent to move the virtual camera

        Args:
            ev (QMouseEvent): event
        """

        new_pos = ev.pos()
        if self.activated:
            self._angles_sphere = self.get_new_angle(new_pos)
            self._sphere_values._trigger_refresh()
            self.next_image()
    
    def mousePressEvent(self, ev: QMouseEvent) -> None:
        """Start MouseEvent Process

        Args:
            ev (QMouseEvent): event
        """

        self.activated = True
        self.last_pos = ev.pos()
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        """MouseEvent stop process

        Args:
            ev (QMouseEvent): event
        """

        self.activated = False
        self.last_pos = None
        self._old_angles = (self._angles_sphere[0], self._angles_sphere[1])
    
    def resizeEvent(self, a0: QResizeEvent) -> None:
        """When resizing the window, resize the image

        Args:
            a0 (QResizeEvent): event
        """

        try:
            self.current_image = self.get_nearest_image(self._angles_sphere)
            pixmap = QPixmap(f'{self.directory}/{self.thumbnails}/{self.current_image}')
            pixmap = pixmap.scaled(self.sphere.height(), self.sphere.width(), Qt.AspectRatioMode.KeepAspectRatio)
            self.sphere.setPixmap(pixmap)
        except Exception as e:
            print("Error in ResizeEvent")
            pass

    def export(self):
        """Export points into a csv
        """

        df = pd.DataFrame(columns=["Color", "X", "Y", "Z", "X_adjusted", "Y_adjusted", "Z_adjusted"])
        df.rename_axis("Label")
        centroid_x = []
        centroid_y = []
        centroid_z = []
        scale_factor = self.commands_widget.distance_calculator.scale_factor

        dots_with_pos = [dot for dot in self.dots if dot.get_position() is not None]

        if len(dots_with_pos) == 0:
            print("Export cancelled")
            return

        # QDialog to get list of points use to compute the centroid
        list_dots_centroid = self.get_list_dots_for_centroid(dots_with_pos)

        if list_dots_centroid is None:
            return

        for dot in dots_with_pos:
            pos = dot.get_position()
            
            df.loc[dot.get_label()] = [dot.get_color().name(), pos[0], pos[1], pos[2], pos[0]*scale_factor, pos[1]*scale_factor, pos[2]*scale_factor]
            if dot.id in list_dots_centroid :
                centroid_x.append(pos[0])
                centroid_y.append(pos[1])
                centroid_z.append(pos[2])
        if len(centroid_x) > 0:
            center_x, center_y, center_z = sum(centroid_x)/len(centroid_x), sum(centroid_y)/len(centroid_y), sum(centroid_z)/len(centroid_z)
            df.loc["centroid"] = ["#000000", center_x, center_y, center_z, center_x*scale_factor, center_y*scale_factor, center_z*scale_factor]
        
        export_file_name = QFileDialog.getSaveFileName(self, "Save File", self.directory+"/.csv","CSV (*.csv *.txt)")[0]
        if len(export_file_name.strip()) != 0:
            df.to_csv(export_file_name, index=True, index_label="Label", sep="\t")
    
    def get_list_dots_for_centroid(self, points_with_pos):
        """Launch Dialog to have the list of points that will count to compute the centroid

        Args:
            points_with_pos (list): list of points that have a position

        Returns:
            set: set of ids of points that will be used to compute the centroid
        """

        msg = CentroidMessage(points_with_pos)
        msg.setWindowModality(Qt.WindowModality.ApplicationModal)
        set_points_chosen = set()
            
        retval = msg.exec()
        print("value of pressed message box button:", retval)
        if not retval :
            print("Cancelled")
            return None
        
        for i in range(len(msg.checkboxes)):
            checkbox = msg.checkboxes[i]
            if checkbox.isChecked():
                set_points_chosen.add(msg.dots[i].id)
        return set_points_chosen

    def values_clicked(self) -> None:
        """Shows picture and allows to put landmarks on it
        """

        intrinsics = np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])
        distCoeffs = np.matrix(self.calibration_dict["intrinsics"]["distortion matrix"]["matrix"])
        extrinsics = np.matrix(self.calibration_dict["extrinsics"][self.current_image]["matrix"])
        extrinsics = extrinsics[0:3, 0:4]

        dots = [dot.to_tuple(self.current_image, intrinsics, extrinsics, distCoeffs) for dot in self.dots]
        self.win = show_picture.QImageViewer(f'{self.directory}/{self.current_image}', dots, self.window().geometry())
        self.win.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.win.show()
        self.win.closeSignal.connect(self.get_dots)
    
    def get_dots(self, dots):
        """Executed when show_picture is closed
        Triangulate all the possible points and get their positions

        Args:
            dots (_type_): _description_
        """

        nbr_img = 0
        mean_error = 0
        intrinsics = np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])
        distCoeffs = np.matrix(self.calibration_dict["intrinsics"]["distortion matrix"]["matrix"])

        for dot in dots:
            index = self.dots.index(dot["id"])
            self.dots[index].add_dot(self.current_image, dot["dot"])
            pos = self.estimate_position(self.dots[index])
            if pos is not None:
                self.dots[index].set_position(pos)
            if self.dots[index].get_position() is not None:
                dot_images = self.dots[index].get_dots()

                for image in dot_images:
                    #Computation of the reprojection error
                    if dot_images[image] is None:
                        continue
                    point = np.matrix([list(self.dots[index].position)])
                    img_point_1 = np.matrix([dot_images[image].to_array()])

                    extrinsics = np.matrix(self.calibration_dict["extrinsics"][image]["matrix"])
                    extrinsics = extrinsics[0:3, 0:4]
                    
                    imgpoints2 = reconstruction.project_points(point, intrinsics, extrinsics, distCoeffs).reshape((1,2))
                    error = cv.norm(img_point_1, imgpoints2, cv.NORM_L2)/len(imgpoints2)
                    mean_error += error
                    nbr_img += 1
        if nbr_img != 0:
            print(f"total error: {mean_error/nbr_img}")
        
        self.update_points()

        
    
    def estimate_position(self, point: reconstruction.Point3D):
        """Triangulate a point

        Args:
            point (reconstruction.Point3D): 3d point with all the landmarks

        Returns:
            np.ndarray: the 3D position of the point
        """
        dots_no_None = {k:v for (k,v) in point.dots.items() if v is not None}

        if len(dots_no_None) <2 :
            # We need at least 2 landmarks to triangulate
            return None
        intrinsics = np.matrix(self.calibration_dict["intrinsics"]["camera matrix"]["matrix"])
        dist_coeffs = np.matrix(self.calibration_dict["intrinsics"]["distortion matrix"]["matrix"])
        dots = list(dots_no_None.items())
        w = int(self.calibration_dict["intrinsics"]["width"])
        h = int(self.calibration_dict["intrinsics"]["height"])
        
        proj_points = []
        for dot in dots:
            #  For each landmark, we need to compute the undistorted position on the image
            image_ext = np.matrix(self.calibration_dict["extrinsics"][dot[0]]["matrix"])
            image_ext = image_ext[0:3, 0:4]
            proj_mat = np.matmul(intrinsics, image_ext)
            img_point = np.matrix([dot[1].to_array()]).T
            img_point_undistort = reconstruction.undistort_iter(np.array([img_point]).reshape((1,1,2)), intrinsics, dist_coeffs)
            proj_point = helpers.ProjPoint(proj_mat, img_point_undistort)
            proj_points.append(proj_point)
        
        # Triangulation computation with all the undistorted landmarks
        points3D = reconstruction.triangulate_point(proj_points)
        return tuple(points3D)

class CentroidMessage(QDialog):
    """Dialog with checkboxes to select points needed for centroid
    """

    def __init__(self, dots_with_pos):
        super(CentroidMessage, self).__init__()
        self.setWindowTitle("MessageBox demo")

        v_layout = QVBoxLayout()
        v_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.check_all_button = QPushButton("hide all")
        self.check_all_button.clicked.connect(self.check_all)
        v_layout.addWidget(self.check_all_button)
        self.visible = True

        self.checkboxes = list()
        self.dots = list()
        for i in dots_with_pos:
            checkbox = QCheckBox(i.get_label())
            checkbox.setCheckState(Qt.CheckState.Checked)
            checkbox.clicked.connect(self.check_visibility)
            self.checkboxes.append(checkbox)
            self.dots.append(i)
            v_layout.addWidget(checkbox)
        
        Qbtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.button_box = QDialogButtonBox(Qbtn)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        v_layout.addWidget(self.button_box)

        v_layout.setSpacing(20)
        self.setLayout(v_layout)

        
    
    def check_all(self):
        """Check or Uncheck all boxes
        """

        for i in self.checkboxes:
            print(f"Button {i.text()} : {Qt.CheckState.Unchecked if self.visible else Qt.CheckState.Checked}")
            i.setCheckState(Qt.CheckState.Unchecked if self.visible else Qt.CheckState.Checked)
        self.visible = not self.visible
        self.check_all_button.setText("hide all" if self.visible else "show all")
    
    def check_visibility(self):
        """Updates visible if needed
        """

        self.visible = self.check_visible()
        self.check_all_button.setText("hide all" if self.visible else "show all")
        
    def check_visible(self):
        """Checks the state of all checkboxe
        """
        
        for i in self.checkboxes:
            if i.isChecked():
                return True
        return False

class InitWidget(QWidget):
    """Wiget when a calibration file is not loaded

    Args:
        QWidget (_type_): _description_
    """

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
        """Import a calibration file
        """
        dir_ = QFileInfo(QFileDialog.getOpenFileName(self, "Open Calibration File", ".", "JSON (*.json)")[0])
        self.parent().load_dir(dir_)
        self.parent().layout.setCurrentIndex(1)

    
    def create_project(self):
        """Create calibration file

            We need :
            - a directory containing all the image
            - an XML file containing the intrinsic parameters (in Opencv format)
            - a Json file containing the extrinsics
            - the folder containing the thumbnails if it exists
        """
        dlg = import_project.QImportProject()
        dlg.setWindowModality(Qt.WindowModality.NonModal)
        if dlg.exec():
            self.dir = dlg.dir_image
            self.calib = dlg.calib
            self.calib_file_name = QFileDialog.getSaveFileName(self, "Save Calibration File", self.dir+"/.json","Json Files (*.json)")[0]
            
            if not self.calib_file_name.strip():
                # canceled
                return
            
            # Checker les thumbnails
            
            if not os.path.exists(f'{self.dir}/{self.calib["thumbnails"]}'):
                os.makedirs(f'{self.dir}/{self.calib["thumbnails"]}')
            
            images_thumbnails = set(glob.glob(f'{self.dir}/{self.calib["thumbnails"]}/*'))

            queue_img_to_make = deque()
            
            thumb_w = thumb_h = 1000
            #sauver les thumbnails
            for key in self.calib["extrinsics"]:
                if f'{self.dir}/{self.calib["thumbnails"]}/{key}' not in images_thumbnails:
                    queue_img_to_make.append(key)
                else:
                    #get dimensions
                    with Image.open(f'{self.dir}/{self.calib["thumbnails"]}/{key}') as im:
                        thumb_w = im.width
                        thumb_h = im.height
            
            while len(queue_img_to_make) != 0:
                print(len(queue_img_to_make))
                img = queue_img_to_make.pop()
                print(img)
                with Image.open(f'{self.dir}/{img}') as im_basic:
                    im_basic.thumbnail((thumb_w, thumb_h), Image.LANCZOS)
                    im_basic.save(f'{self.dir}/{self.calib["thumbnails"]}/{img}')
                    print(f"Saved thumbnail : {img} : {im_basic.width}:{im_basic.height}")

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
        self.viewer.update_points()
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
    
