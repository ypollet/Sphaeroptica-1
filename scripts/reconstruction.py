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


import numpy as np
import math

from PySide6.QtGui import QColor
from scripts import helpers, converters



class Point3D():
    """Referenced Point with position of landmarks and its position
    """

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
        rep_point = project_points(np.matrix(self.position), intrinsics, extrinsics, distCoeffs) if self.position is not None else None
        return {"id": self.id,
                "label": self.label,
                "dot": self.dots[image] if image in self.dots else None,
                "color": self.color,
                "position": helpers.Point(rep_point.item(0),rep_point.item(1)) if rep_point is not None else None }

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

OPENCV_DISTORT_VALUES = 8

def get_distance(src, dst):
    """Computes the distance between two points in a 3-axis coordinate system

    Args:
        src (np.array): the source
        dst (np.array): the distance

    Returns:
        float: the distance
    """

    return round(math.sqrt(math.pow(dst[0]-src[0],2) + math.pow(dst[1]-src[1],2) + math.pow(dst[2]-src[2],2)),10)

def rotate_x_axis(omega):
    """Rotate the rotation matrix R such as R @ rotate_x_axis(omega) rotates it along the X-axis for an angle of omega

    Args:
        omega (float): angle to rotate in gradiant

    Returns:
        np.ndarray: the rotation matrix needed
    """

    Rx = np.matrix([[1, 0, 0],
                    [0, math.cos(omega), -math.sin(omega)],
                    [0, math.sin(omega), math.cos(omega)]])
    return Rx

def rotate_y_axis(phi):
    """Rotate the rotation matrix R such as R @ rotate_y_axis(phi) rotates it along the Y-axis for an angle of phi

    Args:
        phi (float): angle to rotate in gradiant

    Returns:
        np.ndarray: the rotation matrix needed
    """

    Ry = np.matrix([[math.cos(phi), 0, math.sin(phi)],
                    [0, 1, 0],
                    [-math.sin(phi), 0, math.cos(phi)]])
    return Ry

def rotate_z_axis(kappa):
    """Rotate the rotation matrix R such as R @ rotate_x_axis(kappa) rotates it along the Z-axis for an angle of kappa

    Args:
        kappa (float): angle to rotate in gradiant

    Returns:
        np.ndarray: the rotation matrix needed
    """

    Rz = np.matrix([[math.cos(kappa), -math.sin(kappa), 0],
                    [math.sin(kappa), math.cos(kappa), 0],
                    [0, 0, 1]])
    return Rz

def scale_homogeonous_point(point):
    """Scale the homogeonous_point such as point[-1] = 1

    Args:
        point (np.array): the homogeonous point

    Returns:
        np.array: the homogeonous point scaled
    """

    return np.array(point) / point[-1]

def triangulate_point(proj_points):
    """Triangulate the set landmarks to a 3D point 

    Args:
        proj_points (list): list of ProjPoints

    Returns:
        np.array: the 3D location of the point
    """
    A = None
    for point in proj_points:
        img_point = point.pixel_point
        img_point = img_point.reshape((2,1))
        proj_mat = point.proj_mat
        view = np.concatenate([img_point[1]*proj_mat[2, :]-proj_mat[1, :],
                             proj_mat[0, :] - img_point[0]*proj_mat[2, :]])
        A = np.concatenate([A, view]) if A is not None else view
        
    U, s, Vh = np.linalg.svd(A, full_matrices = False)

    X = np.squeeze(np.asarray(Vh[-1,:]))
    print(X.shape)

    return scale_homogeonous_point(X)

def project_points(point3D, intrinsics, extrinsics, dist_coeffs=np.matrix([0 for x in range(OPENCV_DISTORT_VALUES)])):
    """project the 3D point to the 2D image plane

    Args:
        point3D (np.array): 3D coordinates of the point
        intrinsics (np.ndarray): intrinsic matrix
        extrinsics (np.ndarray): extrinsic matrix
        dist_coeffs (np.ndarray, optional): distortion coefficients. Defaults to np.matrix([0 for x in range(OPENCV_DISTORT_VALUES)]).

    Returns:
        np.array: the pixel of the reprojection
    """

    point = intrinsics@extrinsics@point3D.T
    factor = point[2]
    pos = np.array([0,0])
    for i in range(len(pos)):
        pos[i] = (point[i]/float(factor)).item(0,0)
    pos = distort(pos, intrinsics, dist_coeffs)
    return pos.reshape(2,1)

# Since distort() is non-linear, need a non linear solver
# fast solver from opencv
def undistort_iter(point, intrinsics, dist_coeffs, nbr_iter=500):
    """non linear solver to undistort a projection considering the distortion coefficients

    Args:
        point (np.array): distorted pixel
        intrinsics (np.ndarray): intrinsic matrix
        dist_coeffs (np.ndarray): distortion coefficients
        nbr_iter (int, optional): number of maximum iteration of the solver. Defaults to 500.

    Returns:
        np.array: the undistorted pixel
    """

    point = point.reshape((2,1))
    k1,k2,p1,p2,k3,k4,k5,k6 = [x[0] for x in np.concatenate([dist_coeffs, np.matrix([0 for x in range(OPENCV_DISTORT_VALUES - dist_coeffs.shape[1])])], axis=1).reshape((8,1)).tolist()]

    x, y = normalize_pixel(point, intrinsics)
    x0 = x
    y0 = y
    i = 0
    for _ in range(nbr_iter):
        r2 = x ** 2 + y ** 2
        k_inv = (1 + k4 * r2 + k5 * r2**2 + k6 * r2**3) / (1 + k1 * r2 + k2 * r2**2 + k3 * r2**3)
        delta_x = 2 * p1 * x*y + p2 * (r2 + 2 * x**2)
        delta_y = p1 * (r2 + 2 * y**2) + 2 * p2 * x*y
        xant = x
        yant = y
        x = (x0 - delta_x) * k_inv
        y = (y0 - delta_y) * k_inv
        e = (xant - x)**2+ (yant - y)**2
        i += 1
        if e == 0:
            break
    
    return denormalize_pixel([x, y], intrinsics).reshape(2,1)

# Non Linear from Amy Tabb
def distort(point, intrinsics, dist_coeffs):
    """Non linear algorithm of lens distortion (explained by Amy Tabb)

    Args:
        point (np.array): undistorted pixel
        intrinsics (np.ndarray): intrinsic matrix
        dist_coeffs (np.ndarray): distortion coefficients

    Returns:
        np.array: distorted pixel
    """

    k1,k2,p1,p2,k3,k4,k5,k6 = [x[0] for x in np.concatenate([dist_coeffs, np.matrix([0 for x in range(OPENCV_DISTORT_VALUES - dist_coeffs.shape[1])])], axis=1).reshape((8,1)).tolist()]

    # normalize the pixel
    x_u ,y_u = normalize_pixel(point, intrinsics)

    r2 = x_u ** 2 + y_u ** 2
    x = (x_u * (1+k1*r2 + k2*(r2**2) + k3*(r2**3))/(1+k4*r2+k5*(r2**2) + k6*(r2**3))) + 2*p1*x_u*y_u + p2*(r2+2*(x_u**2))
    y = (y_u * (1+k1*r2 + k2*(r2**2) + k3*(r2**3))/(1+k4*r2+k5*(r2**2) + k6*(r2**3))) + 2*p2*x_u*y_u + p1*(r2+2*(y_u**2))

    # denormalize the pixel

    return denormalize_pixel([x, y], intrinsics).T

def normalize_pixel(point, intrinsics):
    """Normalize the pixel value around the center of projection

    Args:
        point (np.array): pixel
        intrinsics (np.ndarray): intrinsic matrix

    Returns:
        np.array: pixel normalized
    """

    x_u,y_u = point

    fx, fy = intrinsics.item(0,0), intrinsics.item(1,1)
    cx, cy = intrinsics.item(0,2), intrinsics.item(1,2)
    # normalize the pixel
    x_u = (x_u - cx) / fx
    y_u = (y_u - cy) / fy

    return x_u, y_u

def denormalize_pixel(point, intrinsics):
    """Get the true value of the normalized pixel

    Args:
        point (np.array): normalized pixel
        intrinsics (np.ndarray): intrinsic matrix

    Returns:
        np.array: pixel
    """

    x, y = point
    fx, fy = intrinsics.item(0,0), intrinsics.item(1,1)
    cx, cy = intrinsics.item(0,2), intrinsics.item(1,2)
    return np.array([x * fx + cx, y * fy + cy])

def intersectPlane(normal, center_plane, start_ray, ray):
    # assuming vectors are all normalized
    # Check if ray is parralel to plane
    denom = np.dot(ray, normal)
    if (abs(denom) > 1e-10):
        d = np.dot(center_plane - start_ray, normal) / np.dot(ray, normal)
        p = start_ray + d*ray
        return np.append(p, [1])
    #if it's parralel there is no intersection
    return None

def intersectionVectors(points, lines):
    if len(points) != len(lines):
        return None
    A = None
    b = None
    for i in range(len(points)):
        
        A = np.concatenate([A, view]) if A is not None else view
        b = np.concatenate([b, sol]) if b is not None else sol
    
    U, s, Vh = np.linalg.svd(A, full_matrices = False)
    b_prime = np.transpose(U)@b
    
    y = (b_prime.T/s).T

    h = np.transpose(Vh)@y
    h = np.concatenate([h, np.matrix([1.0])])
    return h.reshape(3,3)



###########################################################################################################
#
# Deprecated functions used for the virtual camera 
#
###########################################################################################################

def get_ray_direction(img_point, intrinsics, extrinsics):
    """ Deprecated (works but not used)
    get the unit vector of the ray projection of a pixel on a calibrated image

    Args:
        img_point (np.array): pixel
        intrinsics (np.ndarray): intrinsic matrix of the calibrated image
        extrinsics (np.ndarray): extrinsic matrix of the calibrated image

    Returns:
        np.array: direction vector
    """
     
    rotation = extrinsics[0:3, 0:3]
    trans = extrinsics[0:3, 3]
    P = intrinsics@extrinsics
    P_inv = P.T @ np.linalg.inv(P @ P.T)
    #img_point[0], img_point[1] = normalize_pixel(img_point[:2], intrinsics) 
    C = converters.get_camera_world_coordinates(rotation, trans)
    direction_ray = scale_homogeonous_point(P_inv @ img_point)[:-1] - C
    direction_ray_norm = direction_ray / np.linalg.norm(direction_ray)

    return direction_ray_norm

def find_homography_svd(src_points, dst_points):
    """ Deprecated (works but not used)
    Computes the homography matrix

    Args:
        src_points (list): list of points on source image
        dst_points (list): list of correspondent points on destination image

    Returns:
        np.ndarray: homography matrix
    """
    if len(src_points) != len(dst_points):
        return None
    A = None
    for i in range(len(src_points)):
        x_a, y_a = src_points[i].item(0), src_points[i].item(1)
        x_b, y_b = dst_points[i].item(0), dst_points[i].item(1)
        view = np.matrix([[-x_a, -y_a, -1, 0, 0, 0, x_a*x_b, y_a*x_b, x_b],
                          [0, 0, 0, -x_a, -y_a, -1, x_a*y_b, y_a*y_b, y_b]])
        A = np.concatenate([A, view]) if A is not None else view
    
    print(A.shape)
        
    U, s, Vh = np.linalg.svd(A, full_matrices = False)
    X = Vh[-1,:].reshape((3,3))
    factor = np.linalg.norm(X)
    return X / factor


def find_homography_inhomogeneous(src_points, dst_points):
    """ Deprecated (works but not used)
    Homography computation thanks to an inhomogeneous solution

    Args:
        src_points (list): list of points on source image
        dst_points (list): list of correspondent points on destination image

    Returns:
        np.ndarray: homography matrix
    """
    if len(src_points) != len(dst_points):
        return None
    A = None
    b = None
    for i in range(len(src_points)):
        x_a, y_a = src_points[i].item(0), src_points[i].item(1)
        x_b, y_b = dst_points[i].item(0), dst_points[i].item(1)
        '''view = np.matrix([[x_a, y_a, 1, 0, 0, 0, -x_a*x_b, -y_a*x_b],
                          [0, 0, 0, x_a, y_a, 1, -x_a*y_b, -y_a*y_b]])
        sol = np.matrix([[x_b],
                         [y_b]])'''
        view = np.matrix([[x_a, y_a, 1, 0, 0, 0, -x_a*x_b, -y_a*x_b],
                          [0, 0, 0, -x_a, -y_a, -1, x_a*y_b, y_a*y_b]])
        sol = np.matrix([[x_b],
                         [-y_b]])
        A = np.concatenate([A, view]) if A is not None else view
        b = np.concatenate([b, sol]) if b is not None else sol
    
    U, s, Vh = np.linalg.svd(A, full_matrices = False)
    b_prime = np.transpose(U)@b
    
    y = (b_prime.T/s).T

    h = np.transpose(Vh)@y
    h = np.concatenate([h, np.matrix([1.0])])
    return h.reshape(3,3)
