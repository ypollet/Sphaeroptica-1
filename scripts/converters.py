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
import numpy as np

def rad2degrees(rad):
    """rad to degree converter

    Args:
        rad (float): angle in radian

    Returns:
        float: angle in degree
    """

    return round(rad*180/math.pi, 10)

def degrees2rad(deg):
    """degree to rad converter

    Args:
        deg (float): angle in degree

    Returns:
        float: angle in radian
    """

    return round(deg*math.pi/180, 10)

def get_camera_world_coordinates(rotation, trans):
    """get world coordinates of the camera for the intrinsic matrix (rotation and translation matrices)

    Args:
        rotation (np.ndarray): rotation matrix
        trans (np.ndarray): translation matrix

    Returns:
        np.ndarray: world coordinate matrix
    """

    # - (R_t @ T)
    return -rotation.T.dot(trans)

def get_trans_vector(rotation, C):
    """Compute the translation matrix from the rotation matrix and the camera world coordinates

    Args:
        rotation (np.ndarray): rotation matrix
        C (np.ndarray): Camera coordinates

    Returns:
        np.ndarray: translation matrix
    """

    # -R @ C
    return np.array(-rotation.dot(C)).T


def get_long_lat(vector):
    """get geographic coordinates from a vector (centered at the origin (0,0,0))

    Args:
        vector (np.ndarray): given vector

    Returns:
        float: longitude
        float: latitude
    """

    C_normed = vector / np.linalg.norm(vector)
    x,y,z = C_normed.reshape((3,1)).tolist()
    x = x[0]
    y = y[0]
    z = z[0]
    latitude = math.atan2(z, math.sqrt(x**2 + y**2))
    longitude = math.atan2(y,x)
    return longitude, latitude

def get_unit_vector_from_long_lat(longitude, latitude):
    """comput a unit vector (centered at the origin (0,0,0) from geographic coordinates

    Args:
        longitude (float): longitude
        latitude (float): latitude

    Returns:
        np.ndarray: unit vector
    """

    x = math.cos(latitude)*math.cos(longitude)
    y = math.cos(latitude)*math.sin(longitude)
    z = math.sin(latitude)
    return np.matrix([x,y,z])