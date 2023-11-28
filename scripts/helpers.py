'''
Copyright Yann Pollet 2023
'''

from enum import Enum
import math
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from scripts import reconstruction

HEIGHT_COMPONENT = 25

class Indexes(Enum):
    HOME = 0
    CAM = 1
    REC = 2

class Scale(Enum):
    M = 1
    CM = 0.01
    MM = 0.001

class Action(Enum):
    SELECT = 0
    DELETE = 1
    HIDE = 2


class Arrows(Enum):
    UP = Qt.Key.Key_Up
    DOWN = Qt.Key.Key_Down
    RIGHT = Qt.Key.Key_Right
    LEFT = Qt.Key.Key_Left

switch = {
    Qt.Key.Key_Plus : 1,
    Qt.Key.Key_Minus : -1,
}

class Keys(Enum):
    FRONT = Qt.Key.Key_F
    POST = Qt.Key.Key_P
    RIGHT = Qt.Key.Key_R
    LEFT = Qt.Key.Key_L
    INFERIOR = Qt.Key.Key_I
    SUPERIOR = Qt.Key.Key_S

class ProjPoint():
    def __init__(self, proj_mat, pixel_point) -> None:
        self.proj_mat = proj_mat
        self.pixel_point = pixel_point
    
    def __str__(self) -> str:
        return f"{self.proj_mat} x {self.pixel_point}"

class Point3D():
    def __init__(self, id, label, color=QColor('blue'), position = None, dots = None) -> None:
        self.id = id
        self.label = label
        self.color = color
        self.dots = dots if dots is not None else dict()
        self.position = position

    def get_label(self):
        return self.label
    
    def get_id(self):
        return self.id
    
    def set_label(self, label):
        self.label = label
    
    def get_position(self):
        return self.position

    def set_position(self, pos):
        self.position = pos

    def get_color(self):
        return self.color

    def set_color(self, color):
        self.color = color
    
    def add_dot(self, image, dot):
        self.dots[image] = dot

    def reset_point(self):
        self.dots = dict()
        self.position = None
    
    def get_image_dots(self, image):
        return self.dots[image] if image in self.dots else None
    
    def get_dots(self):
        return self.dots
    
    def to_tuple(self, image, intrinsics, extrinsics, distCoeffs):
        rep_point = reconstruction.project_points(np.matrix(self.position), intrinsics, extrinsics, distCoeffs) if self.position is not None else None
        return {"id": self.id,
                "label": self.label,
                "dot": self.dots[image] if image in self.dots else None,
                "color": self.color,
                "position": Point(rep_point.item(0),rep_point.item(1)) if rep_point is not None else None }

    def __eq__(self, other):
        if isinstance(other, Point3D):
            return self.id == other.id
        if isinstance(other, int):
            return self.id == other
        return False
    
    def __str__(self) -> str:
        string = f"{self.label} : {self.position}\n"
        for x in self.dots:
            if self.dots[x] is not None:
                string += f"{x} : {self.dots[x]}\n"
        return string

class Point():
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)  
    
    def scaled(self, factor):
        return Point(round(self.x*factor), round(self.y*factor))
    
    def __str__(self) -> str:
        return (self.x, self.y).__str__()
    
    def to_array(self) -> tuple:
        return [self.x, self.y]

def rad2degrees(rad):
    return round(rad*180/math.pi, 10)

def degrees2rad(deg):
    return round(deg*math.pi/180, 10)

def get_camera_world_coordinates(rotation, trans):
    # - R_t @ T
    return -rotation.T.dot(trans)

def get_trans_vector(rotation, C):
    # -R @ C
    return np.array(-rotation.dot(C)).T

def is_rotation_matrix(R) :
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype = R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6

def get_long_lat(vector):
    C_normed = vector / np.linalg.norm(vector)
    x,y,z = C_normed.reshape((3,1)).tolist()
    x = x[0]
    y = y[0]
    z = z[0]
    latitude = math.atan2(z, math.sqrt(x**2 + y**2))
    longitude = math.atan2(y,x)
    return longitude, latitude

def get_unit_vector_from_long_lat(longitude, latitude):
    x = math.cos(latitude)*math.cos(longitude)
    y = math.cos(latitude)*math.sin(longitude)
    z = math.sin(latitude)
    return np.matrix([x,y,z])

def get_euler_angles(matrix):
    matrix = np.matrix(matrix)

    if(not is_rotation_matrix(matrix)):
        print("The matrix given isn't a valid rotation matrix")
        return
    
    # yaw pitch roll - phi theta psi - alpha beta gamma
    # Yaw / Alpha / Phi : Rotation on the Z-axis (-180 -> 180)
    # Pitch / Beta / Theta : Rotation on the Y-axis (-90 -> 90)
    # Roll / Gamma / psi : Rotation on the X-axis (-180 -> 180)
    theta_1 = - math.asin(matrix.item(2,0))
    #theta_2 = math.pi - theta_1
    if(math.cos(theta_1) == 0):
        print("Use case not implemented")
        return -1
    psi_1 = math.atan2(matrix.item(2,1)/math.cos(theta_1), matrix.item(2,2)/math.cos(theta_1))
    #psi_2 = math.atan2(matrix.item(2,1)/math.cos(theta_2), matrix.item(2,2)/math.cos(theta_2))
    phi_1 = math.atan2(matrix.item(1,0)/math.cos(theta_1), matrix.item(0,0)/math.cos(theta_1))
    #phi_2 = math.atan2(matrix.item(1,0)/math.cos(theta_2), matrix.item(0,0)/math.cos(theta_2))
    
    return (rad2degrees(phi_1), rad2degrees(theta_1), rad2degrees(psi_1))

# Calculates Rotation Matrix given euler angles.
def get_rot_matrix_from_euler(yaw, pitch, roll) :
 
    R_x = np.array([[1,         0,                  0                   ],
                    [0,         math.cos(roll), -math.sin(roll) ],
                    [0,         math.sin(roll), math.cos(roll)  ]
                    ])
 
    R_y = np.array([[math.cos(pitch),    0,      math.sin(pitch)  ],
                    [0,                     1,      0                   ],
                    [-math.sin(pitch),   0,      math.cos(pitch)  ]
                    ])
 
    R_z = np.array([[math.cos(yaw),    -math.sin(yaw),    0],
                    [math.sin(yaw),    math.cos(yaw),     0],
                    [0,                     0,                      1]
                    ])
 
    R = np.dot(R_z, np.dot( R_y, R_x ))
 
    return R

def get_quaternion_from_euler(yaw, pitch, roll):
  """
  Convert an Euler angle to a quaternion.
   
  Input
    :param roll: The roll (rotation around x-axis) angle in radians.
    :param pitch: The pitch (rotation around y-axis) angle in radians.
    :param yaw: The yaw (rotation around z-axis) angle in radians.
 
  Output
    :return qx, qy, qz, qw: The orientation in quaternion [x,y,z,w] format
  """
  qx = np.sin(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) - np.cos(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
  qy = np.cos(roll/2) * np.sin(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.cos(pitch/2) * np.sin(yaw/2)
  qz = np.cos(roll/2) * np.cos(pitch/2) * np.sin(yaw/2) - np.sin(roll/2) * np.sin(pitch/2) * np.cos(yaw/2)
  qw = np.cos(roll/2) * np.cos(pitch/2) * np.cos(yaw/2) + np.sin(roll/2) * np.sin(pitch/2) * np.sin(yaw/2)
 
  return [qx, qy, qz, qw]