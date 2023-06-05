
import sys

import cv2 as cv
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QImage, QPixmap, QPalette, QPainter, QAction, QMouseEvent, QCloseEvent, QPen, QColor, QKeyEvent
from PyQt6.QtWidgets import QWidget, QLabel, QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QApplication, QScrollBar, QHBoxLayout, QVBoxLayout, QPushButton, QSpinBox

from scripts import helpers

INIT_POINT_WIDTH = 3
class QImageLabel(QLabel):
    def __init__(self, image : QImage, base_factor : float, dots : dict(), point_scale : int):
        super().__init__()
        self.dots = dots
        self.point_scale = point_scale
        self.scaleFactor = base_factor
        self.image = QPixmap.fromImage(image)
        self.setPixmap(self.image.scaled(self.image.size()*self.scaleFactor, Qt.AspectRatioMode.KeepAspectRatio))
        #self.init()
        self.paint_dots()

    def init(self) -> None :
        if self.dots[1]["dot"] is not None:
            return
        point = helpers.Point(self.image.width()/2, self.image.height()/2)
        self.dots[1]["dot"] = point

    def set_scale_point(self, val):
        self.point_scale = val
        self.paint_dots()

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        pos = ev.pos()
        point = helpers.Point(float(pos.x()), float(pos.y()))
        self.dots[self.window().point]["dot"] = point.scaled(1/self.scaleFactor)
        self.paint_dots()
    


    def paint_dots(self):
        canvas = self.image.scaled(self.image.size()*self.scaleFactor, Qt.AspectRatioMode.KeepAspectRatio)
        painter = QPainter(canvas)
        pen = QPen()
        pen.setWidth(self.point_scale)
        
        for i in self.dots:
            if(self.dots[i]["dot"] is None):
                continue
            if i == 0:
                pen.setColor(QColor('red'))
            else:
                if i == 1:
                    pen.setColor(QColor('green'))
                else:
                    pen.setColor(QColor('blue'))
            painter.setPen(pen)

            point = self.dots[i]["dot"].scaled(self.scaleFactor)
            painter.drawPoint(point.x, point.y)

        painter.end()
        self.setPixmap(canvas)

    def normalSize(self):
        scaled_image = self.image.scaled(self.window().image_area.size(), Qt.AspectRatioMode.KeepAspectRatio)
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
        super(QPushButton, self).__init__(label)
        self.action = action

class QPointButtons(QWidget):
    button_clicked = pyqtSignal(object)
    def __init__(self, label, id):
        super(QWidget, self).__init__()
        layout = QHBoxLayout()
        self.select_button = QPointButton(label, helpers.Action.SELECT)
        self.select_button.setCheckable(True)
        self.select_button.clicked.connect(self.btnListener)
        layout.addWidget(self.select_button)
        self.delete_button = QPointButton("x", helpers.Action.DELETE)
        self.delete_button.clicked.connect(self.btnListener)
        self.delete_button.setFixedWidth(20)
        layout.addWidget(self.delete_button)
        self.id = id
        self.setLayout(layout)

    def setChecked(self, checked : bool):
        self.select_button.setChecked(checked)
    
    def btnListener(self):
        sender_button = self.sender()
        action = sender_button.action
        self.button_clicked.emit(action)

class QPoints(QScrollArea):
    delete = pyqtSignal(object)
    def __init__(self, points):
        super().__init__()
        self.w = QWidget()
        self.vbox = QVBoxLayout()  
        self.buttons = []
        print(points)
        sorted_points_k = sorted(points)
        for i in sorted_points_k:
            print(points[i]["label"])
            button = QPointButtons(points[i]["label"],i)
            self.buttons.append(button)
            button.button_clicked.connect(self.btnListener)
            self.vbox.addWidget(button)
        self.check(0)
        self.w.setLayout(self.vbox)

        self.setBackgroundRole(QPalette.ColorRole.Dark)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self.w)
        self.setMaximumWidth(200)
    
    def check(self, id):
        for button in self.buttons:
            button.setChecked(False)
        self.buttons[id].setChecked(True)
    
    def delete_point(self, id):
        self.delete.emit(id)

    def btnListener(self, action):
        sender_button = self.sender()
        if action == helpers.Action.SELECT:
            self.check(sender_button.id)
        else:
            self.delete_point(sender_button.id)
        self.window().point = sender_button.id

class QScalePoint(QWidget):
    valChanged = pyqtSignal(object)
    def __init__(self, parent):
        super(QScalePoint, self).__init__(parent)
        self.init_settings()
        self.parent = parent
        full_layout = QHBoxLayout()

        self.label = QLabel("Point Scale: ", self)
        self.size = QSpinBox(self)
        self.size.setMinimum(1)
        self.size.setMaximum(15)
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
  
class QImageViewer(QMainWindow):
    closeSignal = pyqtSignal(object)
    def __init__(self, path_name : str, dots : dict):
        super().__init__()

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
    
        self.image_label = QImageLabel(image, 0.10, dots, INIT_POINT_WIDTH if self.settings.value("point_scale") is None else int(self.settings.value("point_scale")))
        self.image_label.setBackgroundRole(QPalette.ColorRole.Dark)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_label.setScaledContents(True)

        self.image_area = QScrollArea()
        self.image_area.setBackgroundRole(QPalette.ColorRole.Dark)
        self.image_area.setWidget(self.image_label)
        self.image_area.setVisible(False)
        self.image_area.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)
        self.image_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        full_layout.addWidget(self.image_area)

        self.createActions()
        self.createMenus()

        self.setWindowTitle("Image Viewer")
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding)
        
        self.resize(800,600)

        self.image_area.setVisible(True)
        self.initActions()

        self.image_area.adjustSize()

        self.side_bar = QVBoxLayout()

        self.scale_point = QScalePoint(self)
        self.scale_point.valChanged.connect(self.changeScalePoint)

        self.points = QPoints(dots)
        self.points.delete.connect(self.delete_point)

        self.side_bar.addWidget(self.scale_point)
        self.side_bar.addWidget(self.points)


        full_layout.addLayout(self.side_bar)

        widget = QWidget()
        widget.setLayout(full_layout)
        self.setCentralWidget(widget)
    
    def changeScalePoint(self, val):
        self.image_label.set_scale_point(val)

    def delete_point(self, id):
        self.image_label.dots[id]["dot"] = None
        self.image_label.paint_dots()

    def switchPoint(self, i : int):
        if self.point+i in self.image_label.dots:
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
        self.normalSizeAct = QAction("&Normal Size", self, shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)
        self.fullImageAct = QAction("&Fit to Window", self, enabled=False, shortcut="Ctrl+F",
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