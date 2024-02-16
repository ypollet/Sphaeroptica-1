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

import json
import numpy as np
import pandas as pd
import argparse
from pathlib import Path

from scripts import helpers, reconstruction, converters

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True,
                    help="path to input JSON File")
    ap.add_argument("-d", "--dataframe", required=True,
                    help="path to old DataFrame")
    ap.add_argument("-o", "--output", required=False, default=None,
                    help="path to output CSV File")
    args = vars(ap.parse_args())

    input_path = Path(args["input"])

    calib_dict = {}

    with open(input_path, 'r') as f:
        calib_dict = json.load(f)

    intrinsics = calib_dict["intrinsics"]
    extrinsics = calib_dict["extrinsics"]

    int_mat = np.matrix(intrinsics["camera matrix"]["matrix"])
    dist_coeffs= np.matrix(intrinsics["distortion matrix"]["matrix"])
    cx, cy = int_mat.item(0,2), int_mat.item(1,2)

    proj_points = []
    for image in extrinsics:
        image_ext = np.matrix(extrinsics[image]["matrix"])
        image_ext = image_ext[0:3, 0:4]
        img_point_undistort = reconstruction.undistort_iter(np.array([cx, cy]).reshape((1,1,2)), int_mat, dist_coeffs)

        proj_mat = np.matmul(int_mat, image_ext)
        proj_point = helpers.ProjPoint(proj_mat, img_point_undistort)
        proj_points.append(proj_point)

    center = reconstruction.triangulate_point(proj_points)[:3]
    print(f'{center}')
    

    dist = 0
    i = 0
    for image in extrinsics:
        image_ext = np.matrix(extrinsics[image]["matrix"])
        image_ext = image_ext[0:3, 0:4]

        rotation = image_ext[0:3, 0:3]
        trans = np.array(image_ext[0:3, 3].T).squeeze()
        trans_w = np.array(converters.get_camera_world_coordinates(rotation, trans)).squeeze()
        dist += reconstruction.get_distance(center, trans_w)
        i += 1

    avg_dist = dist/i
    print("avg dist = ", avg_dist)

    df = pd.read_csv(Path(args["dataframe"]), sep="\t")

    new_df = pd.DataFrame(columns=["Label", "X", "Y", "Z"])

    # Stacked images loop
    for index, row in df.iterrows():
        print(index)
        split = row['Label'].split('.')
        print(split[0])
        trans_w = np.array([row["X"], row["Y"], row["Z"]])
        C_new_dist = avg_dist * (trans_w / np.linalg.norm(trans_w))
        new_df = pd.concat([new_df, pd.DataFrame({"Label":row['Label'],  "X":C_new_dist.item(0), "Y":C_new_dist.item(1), "Z":C_new_dist.item(2)}, index=[index])])

    '''# Step images loop
    for index, row in df.iterrows():
        print(index)
        split = row['Label'].split('.')
        print(split[0][:-6])
        trans_w = np.array([row["X"], row["Y"], row["Z"]])
        step = 8500
        while step >= 3500:
            C_new_dist = (avg_dist -((8500-step)/ 200000))* (trans_w / np.linalg.norm(trans_w))
            new_df = pd.concat([new_df, pd.DataFrame({"Label":f"{split[0][:-6]}0{step}_.jpg", "X":C_new_dist.item(0), "Y":C_new_dist.item(1), "Z":C_new_dist.item(2)}, index=[index])])
            print(reconstruction.get_distance(center, C_new_dist))
            step -= 250
    '''
    
    print(new_df)

    output_path = ""
    if args["output"] is None:
        output_path = Path(input("Where do you want to save the file ? "))
    else:
        output_path = Path(args["output"])

    new_df.to_csv(output_path, index=False, sep="\t")
