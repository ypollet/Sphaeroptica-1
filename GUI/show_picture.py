# Sphaeroptica - 3D Viewer on calibrated pictures

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


import cv2 as cv
from PySide6.QtCore import Qt, Signal, QSettings, QRectF, QRect, QSize
from PySide6.QtGui import QImage, QPixmap, QPalette, QPainter, QAction, QMouseEvent, QCloseEvent, QPen, QColor, QKeyEvent
from PySide6.QtWidgets import (QWidget, QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QApplication, QScrollBar, QHBoxLayout, 
                             QVBoxLayout, QPushButton, QSpinBox, QScroller)

from scripts import helpers, reconstruction

INIT_POINT_WIDTH = 3
class QImageLabel(QLabel):
    def __init__(self, parent : QWidget, image : QImage, base_factor : float, dots : list(), point_scale : int):
        super(QImageLabel, self).__init__(parent)
        self.dots = dots
        self.visible = [True for i in self.dots]
        self.point_scale = point_scale
        self.scaleFactor = base_factor
        self.image = QPixmap.fromImage(image)
        self.setPixmap(self.image.scaled(self.image.size()*self.scaleFactor, Qt.AspectRatioMode.KeepAspectRatio))
        self.paint_dots()

    def set_scale_point(self, val):
        self.point_scale = val
    
    def set_visible_point(self, index, is_visible):
        self.visible[index] = is_visible

    def set_visible_points(self, is_visible):
        for index in range(len(self.visible)):
            self.visible[index] = is_visible

    def points_hidden(self):
        for index in range(len(self.visible)):
            if self.visible[index]:
                return False  
        return True

    def mousePressEvent(self, ev: QMouseEvent) -> None: 
        if ev.buttons() & Qt.MouseButton.RightButton:
            return
        pos = ev.pos()
        point = helpers.Point(float(pos.x()), float(pos.y()))
        self.dots[self.window().point]["dot"] = point.scaled(1/self.scaleFactor)
        self.paint_dots()

    def paint_dots(self):
        canvas = self.image.scaled(self.image.size()*self.scaleFactor, Qt.AspectRatioMode.KeepAspectRatio)
        painter = QPainter(canvas)
        pen = QPen()
        pen.setWidth(self.point_scale)
        for index in range(len(self.dots)):
            dot = self.dots[index]
            pen.setColor(dot['color'])
            painter.setPen(pen)
            if(dot["dot"] is None):
                if not self.visible[index]:
                    continue
                if dot["position"] is not None:
                    point = dot["position"].scaled(self.scaleFactor)
                    painter.drawArc(QRectF(point.x, point.y,float(self.point_scale)/3,float(self.point_scale)/3), 0, 16*360)
                continue
            point = dot["dot"].scaled(self.scaleFactor)
            painter.drawPoint(int(point.x), int(point.y))

        painter.end()
        self.setPixmap(canvas)

    def normalSize(self):
        scaled_image = self.image.scaled(self.window().image_area.size() - QSize(2,2), Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(scaled_image)
        self.adjustSize()
        scale = self.size().width()/self.image.size().width()
        self.scaleFactor = scale
        self.paint_dots()

    def fullImage(self):
        old_scale = self.scaleFactor
        self.setPixmap(self.image)
        self.adjustSize()
        self.scaleFactor = 1.0
        self.paint_dots()

        return self.scaleFactor/old_scale

    def scaleImage(self, factor):
        old_scale = self.scaleFactor
        self.scaleFactor = round((self.scaleFactor+factor)*20) /20
        new_scale = self.scaleFactor
        scaled_image = self.image.scaled(self.image.size()*self.scaleFactor, Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(scaled_image)
        self.adjustSize()

        self.paint_dots()

        return new_scale/old_scale
    
class QPointButton(QPushButton):
    def __init__(self, label, action : helpers.Action):
        super(QPointButton, self).__init__(label)
        self.action = action


class QColorPixmap(QLabel):
    def __init__(self, size, color : QColor):
        super(QColorPixmap, self).__init__()
        pixmap = QPixmap(size, size)
        pixmap.fill(color)
        self.setPixmap(pixmap)

class QPointButtons(QWidget):
    button_clicked = Signal(object)
    def __init__(self, label, color, index):
        super(QPointButtons, self).__init__()
        layout = QHBoxLayout()

        self.select_button = QPointButton(label, helpers.Action.SELECT)
        self.select_button.setFixedHeight(helpers.HEIGHT_COMPONENT)
        self.select_button.setCheckable(True)
        self.select_button.clicked.connect(self.btnListener)
        layout.addWidget(self.select_button)

        self.color = QColorPixmap(self.select_button.height(), color)
        layout.addWidget(self.color)

        self.hide_button = QPointButton("hide", helpers.Action.HIDE)
        self.hide_button.clicked.connect(self.btnListener)
        self.hide_button.setFixedWidth(50)
        layout.addWidget(self.hide_button)

        self.delete_button = QPointButton("x", helpers.Action.DELETE)
        self.delete_button.clicked.connect(self.btnListener)
        self.delete_button.setFixedWidth(20)
        layout.addWidget(self.delete_button)

        self.index = index
        self.visible = True
        self.setLayout(layout)

    def setChecked(self, checked : bool):
        self.select_button.setChecked(checked)
    
    def btnListener(self):
        sender_button = self.sender()
        action = sender_button.action
        if action == helpers.Action.HIDE:
            self.visible = not self.visible
            sender_button.setText("hide" if self.visible else "show")
        self.button_clicked.emit(action)


class QPoints(QScrollArea):
    delete = Signal(object)
    showed = Signal(object)
    hidden = Signal(object)

    def __init__(self, points):
        super(QPoints, self).__init__()
        self.w = QWidget()
        self.vbox = QVBoxLayout()  
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.buttons = []
        index = 0
        for point in points:
            button = QPointButtons(point["label"], point["color"], index)
            self.buttons.append(button)
            button.button_clicked.connect(self.btnListener)
            self.vbox.addWidget(button)
            index += 1
        self.check(0)
        self.w.setLayout(self.vbox)

        self.setBackgroundRole(QPalette.ColorRole.Dark)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self.w)
        self.setMaximumWidth(250)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
    
    def check(self, index):
        for button in self.buttons:
            button.setChecked(False)
        self.buttons[index].setChecked(True)
    
    def delete_point(self, index):
        self.delete.emit(index)
    
    def show_point(self, show, index):
        if show:
            self.showed.emit(index)
        else:
            self.hidden.emit(index)

    def btnListener(self, action):
        sender_button = self.sender()
        if action == helpers.Action.SELECT:
            self.check(sender_button.index)
            self.window().point = sender_button.index
            return
        
        if action == helpers.Action.DELETE:
            print(f"Delete : {sender_button.index}")
            self.delete_point(sender_button.index)
            return

        # action == helpers.Action.HIDE
        self.show_point(sender_button.visible, sender_button.index)
        
        

class QScalePoint(QWidget):
    valChanged = Signal(object)
    def __init__(self, parent):
        super(QScalePoint, self).__init__(parent)

        self.init_settings()
        self.parent = parent
        full_layout = QHBoxLayout()

        self.label = QLabel("Point Scale: ", self)
        self.size = QSpinBox(self)
        self.size.setMinimum(1)
        self.size.setMaximum(30)
        self.size.setSuffix("px")
        self.size.setValue(INIT_POINT_WIDTH if not self.settings.contains("point_scale") else int(self.settings.value("point_scale")))
        self.size.valueChanged.connect(self.signal_value)
        full_layout.addWidget(self.label)
        full_layout.addWidget(self.size)
        self.setLayout(full_layout)
        self.setMaximumWidth(200)

    def signal_value(self, val):
        self.settings.setValue("point_scale", val)
        self.valChanged.emit(val)

    def get_value(self):
        return self.size.value()

    def init_settings(self):
        self.settings = QSettings("Sphaeroptica", "reconstruction") 

class QHideAll(QWidget):
    visibleChanged = Signal(object)
    def __init__(self, parent):
        super(QHideAll, self).__init__(parent)
        self.init_settings()
        self.parent = parent
        full_layout = QHBoxLayout()
        self.all_visible = True

        self.button = QPushButton("hide all", self)
        self.button.clicked.connect(self.clicked_visible)
        
        full_layout.addWidget(self.button)     

        self.setLayout(full_layout)
        self.setMaximumWidth(200)

    def clicked_visible(self):
        self.all_visible = not self.all_visible
        self.button.setText("hide all" if self.all_visible else "show all")
        self.visibleChanged.emit(self.all_visible)
    
    def set_visible(self, all_visible):
        self.all_visible = all_visible
        self.button.setText("hide all" if self.all_visible else "show all")
        self.visibleChanged.emit(self.all_visible)
    
    def set_visibility(self, all_visible):
        self.all_visible = all_visible
        self.button.setText("hide all" if self.all_visible else "show all")

    def init_settings(self):
        self.settings = QSettings("Sphaeroptica", "reconstruction")
 
  
class QImageViewer(QMainWindow):
    closeSignal = Signal(object)
    def __init__(self, path_name : str, dots : list, init_geometry : QRect = None):
        super(QImageViewer, self).__init__()

        self.setGeometry(init_geometry)

        self.init_settings()
        self.image = None
        self.point = 0
        full_layout = QHBoxLayout()

        # Open Image

        img = cv.imread(path_name, cv.IMREAD_UNCHANGED)
        img = cv.cvtColor(img, cv.COLOR_BGRA2RGBA)
        height, width, channel = img.shape
        bytesPerLine = 4 * width
        image = QImage(img.data, width, height, bytesPerLine, QImage.Format.Format_RGBA8888)
        if image.isNull():
            QMessageBox.information(self, "Image Viewer", "Cannot load %s." % path_name)
            self.close()
            return
    
        self.image_label = QImageLabel(self, image, 0.10, dots, INIT_POINT_WIDTH if self.settings.value("point_scale") is None else int(self.settings.value("point_scale")))
        
        self.image_label.setBackgroundRole(QPalette.ColorRole.Dark)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_label.setScaledContents(True)

        self.image_area = QScrollArea()
        QScroller.grabGesture(self.image_area, QScroller.ScrollerGestureType.RightMouseButtonGesture)
        self.image_area.setBackgroundRole(QPalette.ColorRole.Dark)
        self.image_area.setWidget(self.image_label)
        self.image_area.setVisible(False)
        self.image_area.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)
        self.image_area.setWidgetResizable(False)
        self.image_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        
        self.image_area.adjustSize()
        full_layout.addWidget(self.image_area)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Image Viewer")
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)

        self.image_area.setVisible(True)
        self.initActions()

        self.image_area.adjustSize()

        self.side_bar = QVBoxLayout()

        self.scale_point = QScalePoint(self)
        self.scale_point.valChanged.connect(self.changeScalePoint)

        self.hide_all_button = QHideAll(self)
        self.hide_all_button.visibleChanged.connect(self.changeVisibility)

        self.points = QPoints(dots)
        self.points.delete.connect(self.delete_point)
        self.points.showed.connect(self.show_point)
        self.points.hidden.connect(self.hide_point)

        self.side_bar.addWidget(self.scale_point)
        self.side_bar.addWidget(self.hide_all_button)
        self.side_bar.addWidget(self.points)

        full_layout.addLayout(self.side_bar)

        widget = QWidget()
        widget.setLayout(full_layout)

        self.setCentralWidget(widget)

        self.normalSize()

    
    def changeScalePoint(self, val):
        self.image_label.set_scale_point(val)
        self.image_label.paint_dots()
    
    def changeVisibility(self, bool):
        self.image_label.set_visible_points(bool)
        for i in range(len(self.points.buttons)):
            self.points.buttons[i].hide_button.setText("hide" if bool else "show")
            self.points.buttons[i].visible = bool
        self.image_label.paint_dots()        

    def show_point(self, index):
        self.image_label.set_visible_point(index, True)
        self.hide_all_button.set_visibility(True)
        self.image_label.paint_dots()

    def hide_point(self, index):
        self.image_label.set_visible_point(index, False)
        if self.image_label.points_hidden():
            self.hide_all_button.set_visibility(False)
        self.image_label.paint_dots()

    def delete_point(self, index):
        self.image_label.dots[index]["dot"] = None
        self.image_label.paint_dots()
    
    def update(self):
        self.image_label.paint_dots()

    def switchPoint(self, i : int):
        if self.point+i < len(self.image_label.dots) and self.point+i > 0:
            self.point += i
        self.points.check(self.point)

    def normalSize(self):
        self.image_label.normalSize()

    def fullImage(self):
        factor = self.image_label.fullImage()

        self.update(factor)

    def zoomIn(self):
        factor = self.image_label.scaleImage(0.05)
        self.update(factor)

    def zoomOut(self):
        factor = self.image_label.scaleImage(-0.05)
        self.update(factor)

    def update(self, factor):
        self.adjustScrollBar(self.image_area.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.image_area.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.image_label.scaleFactor < 2)
        self.zoomOutAct.setEnabled(self.image_label.scaleFactor > 0.10)

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                          "<p>The <b>Image Viewer</b> example shows how to combine "
                          "QLabel and QScrollArea to display an image. QLabel is "
                          "typically used for displaying text, but it can also display "
                          "an image. QScrollArea provides a scrolling view around "
                          "another widget. If the child widget exceeds the size of the "
                          "frame, QScrollArea automatically provides scroll bars.</p>"
                          "<p>The example demonstrates how QLabel's ability to scale "
                          "its contents (QLabel.scaledContents), and QScrollArea's "
                          "ability to automatically resize its contents "
                          "(QScrollArea.widgetResizable), can be used to implement "
                          "zooming and scaling features.</p>"
                          "<p>In addition the example shows how to use QPainter to "
                          "print an image.</p>")

    def createActions(self):
        self.exitAct = QAction("&Exit", self, shortcut="Ctrl+Q", triggered=self.close)
        self.zoomInAct = QAction("Zoom &In (5%)", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.zoomOutAct = QAction("Zoom &Out (5%)", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.normalSizeAct = QAction("Fit to Window", self, shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)
        self.fullImageAct = QAction("&Full Image", self, enabled=False, shortcut="Ctrl+F",
                                      triggered=self.fullImage)
        self.aboutAct = QAction("&About", self, triggered=self.about)
        self.aboutQtAct = QAction("About &Qt", self, triggered=QApplication.aboutQt)
    
    def initActions(self):
        self.zoomInAct.setEnabled(True)
        self.zoomOutAct.setEnabled(True)
        self.normalSizeAct.setEnabled(True)
        self.fullImageAct.setEnabled(True)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fullImageAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)


    def adjustScrollBar(self, scrollBar : QScrollBar, factor : float):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))


    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closeSignal.emit(self.image_label.dots)

    def keyPressEvent(self, ev: QKeyEvent) -> None:
        try:
            self.switchPoint(helpers.switch[ev.key()])
        except:
            pass

    def init_settings(self):
        self.settings = QSettings("Sphaeroptica", "reconstruction")    