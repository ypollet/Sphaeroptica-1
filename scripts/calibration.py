'''
Copyright Yann Pollet 2023
'''

import numpy as np
import cv2 as cv
import glob
import time
import imutils


def calibrate(dir_path : str, dims : np.ndarray, sizes : np.ndarray):
    # termination criteria
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((dims[0]*dims[1],3), np.float32)
    objp[:,:2] = (sizes*np.mgrid[0:dims[0],0:dims[1]].T).reshape(-1,2)

    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.
    imgs = []
    images = glob.glob(f'{dir_path}/*')
    for fname in images:
        print(fname)
        img = cv.imread(fname)
        
        if(img is None):
            #Check if it is an image
            print(f'{fname} is not an image')
            continue
        
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, (dims[0],dims[1]), None)
        # If found, add object points, image points (after refining them)
        print(ret)
        if ret == True:
            imgs.append(fname)
            objpoints.append(objp)
            corners2 = cv.cornerSubPix(gray,corners, (5,5), (-1,-1), criteria)
            imgpoints.append(corners2)
            
            # Draw and display the corners
            cv.drawChessboardCorners(img, (dims[0],dims[1]), corners2, ret)
            img_resized = imutils.resize(img, width=800)
    
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    print(mtx)
    print(dist)

    ext = {}

    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        error = cv.norm(imgpoints[i], imgpoints2, cv.NORM_L2)/len(imgpoints2)
        mean_error += error
        
        fname = imgs[i]
        r_mat, _ = cv.Rodrigues(rvecs[i])
        t_vec = tvecs[i]
        print(r_mat)
        print(t_vec)

        mat = np.hstack((r_mat, t_vec))
        ext[fname] = {"matrix" : mat.tolist()}

    print( "total error: {}".format(mean_error/len(objpoints)) )

    return mtx, dist, ext


