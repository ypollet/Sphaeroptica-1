'''
Copyright Yann Pollet 2023
'''

import numpy as np
import math
import cv2 as cv

#import helpers
from scripts import helpers

OPENCV_DISTORT_VALUES = 8

def get_distance(src, dst):
    return round(math.sqrt(math.pow(dst[0]-src[0],2) + math.pow(dst[1]-src[1],2) + math.pow(dst[2]-src[2],2)),10)

def rotate_x_axis(omega):
    Rx = np.matrix([[1, 0, 0],
                    [0, math.cos(omega), -math.sin(omega)],
                    [0, math.sin(omega), math.cos(omega)]])
    return Rx

def rotate_y_axis(phi):
    Ry = np.matrix([[math.cos(phi), 0, math.sin(phi)],
                    [0, 1, 0],
                    [-math.sin(phi), 0, math.cos(phi)]])
    return Ry

def rotate_z_axis(kappa):
    Rz = np.matrix([[math.cos(kappa), -math.sin(kappa), 0],
                    [math.sin(kappa), math.cos(kappa), 0],
                    [0, 0, 1]])
    return Rz

def scale_homogeonous_point(point):
    return np.array(point) / point[-1]


def old_triangulate_point(img_point1, img_point2, projMat1, projMat2):
    view_1 = np.concatenate([img_point1[1]*projMat1[2, :]-projMat1[1, :],
                             projMat1[0, :] - img_point1[0]*projMat1[2, :]])
    view_2 = np.concatenate([img_point2[1]*projMat2[2, :]-projMat2[1, :],
                             projMat2[0, :] - img_point2[0]*projMat2[2, :]])
    A = np.concatenate([view_1, view_2])
    U, s, Vh = np.linalg.svd(A, full_matrices = False)

    X = Vh[-1,:]
    return scale_homogeonous_point(X)

def triangulate_point(proj_points):
    A = None
    for point in proj_points:
        img_point = point.pixel_point
        img_point = img_point.reshape((2,1))
        proj_mat = point.proj_mat
        view = np.concatenate([img_point[1]*proj_mat[2, :]-proj_mat[1, :],
                             proj_mat[0, :] - img_point[0]*proj_mat[2, :]])
        A = np.concatenate([A, view]) if A is not None else view
        
    U, s, Vh = np.linalg.svd(A, full_matrices = False)
    X = Vh[-1,:]
    return X / X[3]

def project_points(point3D, intrinsics, extrinsics, dist_coeffs=np.matrix([0 for x in range(OPENCV_DISTORT_VALUES)])):
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
    k1,k2,p1,p2,k3,k4,k5,k6 = [x[0] for x in np.concatenate([dist_coeffs, np.matrix([0 for x in range(OPENCV_DISTORT_VALUES - dist_coeffs.shape[1])])], axis=1).reshape((8,1)).tolist()]

    # normalize the pixel
    x_u ,y_u = normalize_pixel(point, intrinsics)

    r2 = x_u ** 2 + y_u ** 2
    x = (x_u * (1+k1*r2 + k2*(r2**2) + k3*(r2**3))/(1+k4*r2+k5*(r2**2) + k6*(r2**3))) + 2*p1*x_u*y_u + p2*(r2+2*(x_u**2))
    y = (y_u * (1+k1*r2 + k2*(r2**2) + k3*(r2**3))/(1+k4*r2+k5*(r2**2) + k6*(r2**3))) + 2*p2*x_u*y_u + p1*(r2+2*(y_u**2))

    # denormalize the pixel

    return denormalize_pixel([x, y], intrinsics).T

def normalize_pixel(point, intrinsics):
    x_u,y_u = point

    fx, fy = intrinsics.item(0,0), intrinsics.item(1,1)
    cx, cy = intrinsics.item(0,2), intrinsics.item(1,2)
    # normalize the pixel
    x_u = (x_u - cx) / fx
    y_u = (y_u - cy) / fy

    return x_u, y_u

def denormalize_pixel(point, intrinsics):
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

def get_ray_direction(img_point, intrinsics, extrinsics):
    rotation = extrinsics[0:3, 0:3]
    trans = extrinsics[0:3, 3]
    P = intrinsics@extrinsics
    P_inv = P.T @ np.linalg.inv(P @ P.T)
    #img_point[0], img_point[1] = normalize_pixel(img_point[:2], intrinsics) 
    C = helpers.get_camera_world_coordinates(rotation, trans)
    direction_ray = scale_homogeonous_point(P_inv @ img_point)[:-1] - C
    direction_ray_norm = direction_ray / np.linalg.norm(direction_ray)

    return direction_ray_norm

def find_homography_svd(src_points, dst_points):
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
