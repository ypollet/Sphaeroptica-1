import sys
import os
 
# setting path
print(__file__)
sys.path.append(os.path.realpath(f"{__file__}/../.."))


import json
import pandas as pd
import numpy as np
import math
import argparse
from pathlib import Path

from scipy.spatial.transform import Rotation as R

from scripts import helpers, reconstruction

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True,
                    help="path to input OPK File")
    ap.add_argument("-o", "--output", required=False, default=None,
                    help="path to output CSV File")
    args = vars(ap.parse_args())

    input_path = Path(args["input"])

    df = pd.read_csv(input_path, sep='\t', header=None, names=["Label","X","Y","Z","Omega","Phi","Kappa","r11","r12","r13","r21","r22","r23","r31","r32","r33"])

    df = df.dropna()

    extrinsics = dict()

    for index, row in df.iterrows():
        print(row["Label"])
        x = row["X"]
        y = row["Y"]
        z = row["Z"]

        t_w = np.array([x,y,z])

        omega = helpers.degrees2rad(-row["Omega"])
        phi = helpers.degrees2rad(-row["Phi"])
        kappa = helpers.degrees2rad(-row["Kappa"])

        
        r11 = row["r11"]
        r12 = row["r12"]
        r13 = row["r13"]
        r21 = row["r21"]
        r22 = row["r22"]
        r23 = row["r23"]
        r31 = row["r31"]
        r32 = row["r32"]
        r33 = row["r33"]
        
        # OPK
        
        # Matrix omega
        Rx = np.matrix([[1, 0, 0],
                        [0, math.cos(omega), -math.sin(omega)],
                        [0, math.sin(omega), math.cos(omega)]])
        # Matrix phi
        Ry = np.matrix([[math.cos(phi), 0, math.sin(phi)],
                        [0, 1, 0],
                        [-math.sin(phi), 0, math.cos(phi)]])
        # Matrix kappa
        Rz = np.matrix([[math.cos(kappa), -math.sin(kappa), 0],
                        [math.sin(kappa), math.cos(kappa), 0],
                        [0, 0, 1]])


        #looks like it's zyx
        mat = reconstruction.rotate_x_axis(math.radians(180))@ np.matrix([[r11, r12, r13],
                        [r21, r22, r23],
                        [r31, r32, r33]])
        mat_mul = np.matmul(Rx, np.matmul(Ry, Rz))
        #mat = Rx.dot(Ry.dot(Rz))
        # t = -RC

        t = np.array(-mat.dot(t_w)).T
        
        C = -np.transpose(mat)@t
        print(f"{t_w} -> {C}")

        hola = np.hstack((mat, t))
        ext_mat = np.vstack((hola, [0,0,0,1]))
        
        extrinsics[f'{row["Label"]}.jpg'] = {"matrix" : ext_mat.tolist()}
    
    output_path = ""
    if args["output"] is None:
        output_path = Path(input("Where do you want to save the file ? "))
    else:
        output_path = Path(args["output"])



    with open(output_path, "w") as file:
        json.dump(extrinsics,file)