"""
STOKECAM Post-Processing 
Drew Davey
Last updated: 2025-09-10

Point Cloud Viewer for L1, L2, and L3
"""

import os
import numpy as np
import open3d as o3d
from tkinter import filedialog, simpledialog
from utils import genL3ptCloud 

def main():
    # Select wave directory
    wave = filedialog.askdirectory(title="Select path to wave")
    if not wave:
        return

    # Choose level
    level = simpledialog.askstring("Select level", "Enter L1, L2, or L3:")
    if level not in ['L1', 'L2', 'L3']:
        print("Invalid level selected.")
        return

    viewFlag = True
    while viewFlag:
        if level == 'L1':
            ply_file = filedialog.askopenfilename(title="Select L1 .ply file", filetypes=[("PLY files", "*.ply")])
            if ply_file:
                pcd = o3d.io.read_point_cloud(ply_file)
                o3d.visualization.draw_geometries([pcd])

        elif level == 'L2':
            animate = simpledialog.askstring("Animate L2?", "Yes or No:")
            if animate.lower() == 'yes':
                ply_files = sorted([f for f in os.listdir(os.path.join(wave, 'L2')) if f.endswith('.ply')])
                cumulative_pcd = o3d.geometry.PointCloud()
                for ply_file in ply_files:
                    pcd = o3d.io.read_point_cloud(os.path.join(wave, 'L2', ply_file))
                    cumulative_pcd += pcd
                    o3d.visualization.draw_geometries([cumulative_pcd])
            else:
                ply_file = filedialog.askopenfilename(title="Select L2 .ply file", filetypes=[("PLY files", "*.ply")])
                if ply_file:
                    pcd = o3d.io.read_point_cloud(ply_file)
                    o3d.visualization.draw_geometries([pcd])

                    # Manual cleaning option
                    clean = simpledialog.askstring("Manually clean?", "Yes or No:")
                    if clean.lower() == 'yes':
                        # Use open3d's crop tool for selection
                        print("Use the cropping tool in the viewer to select points.")
                        o3d.visualization.draw_geometries_with_editing([pcd])
                        # After editing, save the cropped cloud
                        cropped_pcd = o3d.visualization.draw_geometries_with_editing([pcd])[0]
                        o3d.io.write_point_cloud(ply_file, cropped_pcd)

                    # Export to transect
                    export = simpledialog.askstring("Export selected to transect?", "Yes or No:")
                    if export.lower() == 'yes':
                        transect_dir = os.path.join(wave, 'transect')
                        os.makedirs(transect_dir, exist_ok=True)
                        pts = np.asarray(cropped_pcd.points)
                        np.save(os.path.join(transect_dir, os.path.basename(ply_file).replace('.ply', '.npy')), pts)

        elif level == 'L3':
            l3_file = os.path.join(wave, 'L3ptCloud.ply')
            if os.path.exists(l3_file):
                pcd = o3d.io.read_point_cloud(l3_file)
                o3d.visualization.draw_geometries([pcd])
            else:
                print("L3ptCloud.ply not found. Generate it first.")

        # Continue viewing?
        cont = simpledialog.askstring("View another?", "Yes or No:")
        if cont.lower() != 'yes':
            viewFlag = False
            if level == 'L2':
                genL3ptCloud(wave)  # Generate L3 after L2 viewing

if __name__ == "__main__":
    main()