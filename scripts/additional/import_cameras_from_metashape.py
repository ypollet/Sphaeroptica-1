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

import sys

sys.path.append("/home/broot/Numerisation/Sphaeroptica")

import json
import pandas as pd
import numpy as np
import math
import argparse
from pathlib import Path

import sys

from scipy.spatial.transform import Rotation as R

from scripts import reconstruction, converters

if __name__ == '__main__':

    print(print(sys.path))
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True,
                    help="path to input OPK File")
    ap.add_argument("-f", "--format", required=True,
                    help="format of the files")
    ap.add_argument("-o", "--output", required=False, default=None,
                    help="path to output JSON File")
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

        omega = converters.degrees2rad(row["Omega"])
        phi = converters.degrees2rad(row["Phi"])
        kappa = converters.degrees2rad(row["Kappa"])

        
        r11 = row["r11"]
        r12 = row["r12"]
        r13 = row["r13"]
        r21 = row["r21"]
        r22 = row["r22"]
        r23 = row["r23"]
        r31 = row["r31"]
        r32 = row["r32"]
        r33 = row["r33"]
        
        #looks like it's zyx
        mat = reconstruction.rotate_x_axis(math.radians(180)) @ np.matrix([[r11, r12, r13],
                        [r21, r22, r23],
                        [r31, r32, r33]])
        t = np.array(-mat.dot(t_w)).T

        o_p_k = np.array([-np.pi-omega, phi, kappa])
        rot = R.from_euler('xyz', o_p_k)
        rot_mat = rot.as_matrix()

        rot_mat2 = reconstruction.rotate_x_axis(np.pi+omega)  @ reconstruction.rotate_y_axis(phi) @ reconstruction.rotate_z_axis(kappa)

        print(mat)
        print(rot_mat)
        print(rot_mat2)
        print("-----------------------------------------------------------")
        hola = np.hstack((mat, t))
        ext_mat = np.vstack((hola, [0,0,0,1]))
        
        extrinsics[f'{row["Label"]}.{Path(args["format"])}'] = {"matrix" : ext_mat.tolist()}
    
    output_path = ""
    if args["output"] is None:
        output_path = Path(input("Where do you want to save the file ? "))
    else:
        output_path = Path(args["output"])


    with open(output_path, "w") as file:
        json.dump(extrinsics,file)