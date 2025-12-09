"""
STOKECAM Post-Processing 
Drew Davey
Last updated: 2025-09-10

Point Cloud Viewer for L1, L2, and L3
"""

import os
import numpy as np
import open3d as o3d
import laspy
from tkinter import filedialog, simpledialog
from utils import genL3ptCloud 


def ask_yes(title, prompt):
    """Return True if the user answers yes; handle cancel/empty safely."""
    response = simpledialog.askstring(title, prompt)
    if not response:
        return False
    return response.strip().lower() == 'yes'

def las_to_o3d(las_path):
    """Convert LAS file to Open3D point cloud"""
    las = laspy.read(las_path)
    points = np.column_stack([las.x, las.y, las.z])
    colors = np.column_stack([las.red, las.green, las.blue]) / 65535.0  # Scale to 0-1
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd

def o3d_to_las(pcd, las_path):
    """Save Open3D point cloud as LAS file"""
    points = np.asarray(pcd.points)
    colors = np.asarray(pcd.colors) * 65535.0  # Scale to 16-bit
    
    header = laspy.LasHeader(point_format=3, version="1.2")
    las_out = laspy.LasData(header)
    
    las_out.x = points[:, 0]
    las_out.y = points[:, 1]
    las_out.z = points[:, 2]
    las_out.red = colors[:, 0].astype(np.uint16)
    las_out.green = colors[:, 1].astype(np.uint16)
    las_out.blue = colors[:, 2].astype(np.uint16)
    
    las_out.write(las_path)

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
            las_file = filedialog.askopenfilename(title="Select L1 .las file", filetypes=[("LAS files", "*.las")])
            if las_file:
                pcd = las_to_o3d(las_file)
                o3d.visualization.draw_geometries([pcd])

        elif level == 'L2':
            if ask_yes("Animate L2?", "Yes or No:"):
                las_files = sorted([f for f in os.listdir(os.path.join(wave, 'L2')) if f.endswith('.las')])
                cumulative_pcd = o3d.geometry.PointCloud()
                for las_file in las_files:
                    pcd = las_to_o3d(os.path.join(wave, 'L2', las_file))
                    cumulative_pcd += pcd
                    o3d.visualization.draw_geometries([cumulative_pcd])
            else:
                las_file = filedialog.askopenfilename(title="Select L2 .las file", filetypes=[("LAS files", "*.las")])
                if las_file:
                    pcd = las_to_o3d(las_file)
                    o3d.visualization.draw_geometries([pcd])

                    # Manual cleaning option
                    if ask_yes("Manually clean?", "Yes or No:"):
                        # Use open3d's crop tool for selection
                        print("Use the cropping tool in the viewer to select points.")
                        cropped_pcd = o3d.visualization.draw_geometries_with_editing([pcd])[0]
                        o3d_to_las(cropped_pcd, las_file)

                    # Export to transect
                    if ask_yes("Export selected to transect?", "Yes or No:"):
                        transect_dir = os.path.join(wave, 'transect')
                        os.makedirs(transect_dir, exist_ok=True)
                        pts = np.asarray(pcd.points)
                        np.save(os.path.join(transect_dir, os.path.basename(las_file).replace('.las', '.npy')), pts)

        elif level == 'L3':
            l3_file = os.path.join(wave, 'L3ptCloud.las')
            if os.path.exists(l3_file):
                pcd = las_to_o3d(l3_file)
                o3d.visualization.draw_geometries([pcd])
            else:
                print("L3ptCloud.las not found. Generate it first.")
                genL3ptCloud(wave)  # Try to generate it
                if os.path.exists(l3_file):
                    pcd = las_to_o3d(l3_file)
                    o3d.visualization.draw_geometries([pcd])

        # Continue viewing?
        if not ask_yes("View another?", "Yes or No:"):
            viewFlag = False
            if level == 'L2':
                genL3ptCloud(wave)  # Generate L3 after L2 viewing

if __name__ == "__main__":
    main()