import json
import numpy as np
import pandas as pd

from scripts import helpers, reconstruction

file_path = "calibrate_mm.json"

calib_dict = {}

with open(file_path, 'r') as f:
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
print(center)

dist = 0
i = 0
for image in extrinsics:
    image_ext = np.matrix(extrinsics[image]["matrix"])
    image_ext = image_ext[0:3, 0:4]

    rotation = image_ext[0:3, 0:3]
    trans = np.array(image_ext[0:3, 3].T).squeeze()
    trans_w = np.array(helpers.get_camera_world_coordinates(rotation, trans)).squeeze()
    dist += reconstruction.get_distance(center, trans_w) + 0.0115
    i += 1

avg_dist = dist/i
print("avg dist = ", avg_dist)

df = pd.read_csv("./csv_import.csv", sep="\t")

new_df = pd.DataFrame(columns=["Label", "X", "Y", "Z"])

for index, row in df.iterrows():
    print(index)
    split = row['Label'].split('.')
    print(split[0][:-11])
    trans_w = np.array([row["X"], row["Y"], row["Z"]])
    C_new_dist = avg_dist * (trans_w / np.linalg.norm(trans_w))
    trans_w = np.array([row["X"], row["Y"], row["Z"]])
    new_df = pd.concat([new_df, pd.DataFrame({"Label":f"{split[0][:-11]}.jpg",  "X":C_new_dist.item(0), "Y":C_new_dist.item(1), "Z":C_new_dist.item(2)}, index=[index])])

''' Steps
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

new_df.to_csv("new_import_camera_stacked.csv", index=False, sep="\t")
