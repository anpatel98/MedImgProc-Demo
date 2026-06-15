"""
Author: qiuchang
Description: This script provides functions to load and save geometry data for USEI indices. It reads geometry
             information from .csv files, processes the data to extract vertices, triangles, and normals,
             and saves the geometry as a NumPy array for each USEI directory.
"""
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from stl import mesh


def stl_read(filepath):
    m = mesh.Mesh.from_file(filepath)
    normals = m.normals
    pts = m.vectors.reshape(-1, 3)

    pts_, indices = np.unique(pts, axis=0, return_inverse=True)
    #     vertices_unique, indices = np.unique(vertices, axis=0, return_inverse=True)

    # Triangular face
    tri = indices.reshape(-1, 3)
    name = os.path.basename(filepath)
    return pts_, tri, normals, name

def patch_load(patch_path):
    try:
        for file_name in os.listdir(patch_path):
            if file_name.endswith('.csv'):
                csv_path = os.path.join(patch_path, file_name)
                patch_index = pd.read_csv(csv_path,header=None)
                x = patch_index.iloc[:, 0]
                x = x.astype(float)
                y = patch_index.iloc[:, 1]
                y = y.astype(float)
                z = patch_index.iloc[:, 2]
                z = z.astype(float)
                new_tri, new_ptX, new_ptY, new_ptZ = meshpts(x, y, z)
                return new_tri, new_ptX, new_ptY, new_ptZ
    except FileNotFoundError as e:
        print(e)


def meshpts(x, y, z, plot=False):
    """
    Generates a mesh grid from x, y, z coordinates, centers the coordinates, and transforms them
    into spherical coordinates. Optionally, displays the mesh plot.
    """
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    z = z[~np.isnan(z)]
    center = np.mean(np.column_stack([x, y, z]), axis=0)
    x -= center[0]
    y -= center[1]
    z -= center[2]

    theta, phi, rho = cart2sph(x, y, z)
    new_x = np.cos(phi) * np.cos(theta)
    new_y = np.cos(phi) * np.sin(theta)
    new_z = np.sin(phi)
    tri = ConvexHull(np.column_stack([new_x, new_y, new_z])).simplices

    X = x + center[0]
    Y = y + center[1]
    Z = z + center[2]

    if plot:
        PlotMeshAndSphere(tri, new_x, new_y, new_z, X, Y, Z)

    return tri, X, Y, Z


def cart2sph(x, y, z):
    """
    Converts Cartesian coordinates (x, y, z) to spherical coordinates (theta, phi, rho).
    """
    hxy = np.hypot(x, y)
    rho = np.hypot(hxy, z)
    theta = np.arctan2(y, x)
    phi = np.arctan2(z, hxy)
    return theta, phi, rho


def PlotMeshAndSphere(tri, new_xx, new_yy, new_zz, interpx, interpy, interpz):
    """
    Plots the mesh and spherical surface using 3D plots for visual comparison.
    """
    fig = plt.figure(figsize=(10, 5))
    ax1 = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122, projection='3d')

    ax1.plot_trisurf(new_xx, new_yy, new_zz, triangles=tri, cmap='viridis')
    ax2.plot_trisurf(interpx, interpy, interpz, triangles=tri, cmap='viridis')


def geo_load(patch_path,geometry_path):
    new_tri, new_ptX, new_ptY, new_ptZ = patch_load(patch_path)
    G = {}
    G['skull'] = {'pts': np.column_stack((new_ptX, new_ptY, new_ptZ)), 'tri': new_tri}
    for file_name in os.listdir(geometry_path):
        if file_name.endswith('inner_brain.stl'):
            stl_path = os.path.join(geometry_path, file_name)
            cortexPts, cortexTri, cortexNor, cortexName = stl_read(stl_path)
    G['cortex'] = {'pts': cortexPts, 'tri': cortexTri, 'norm': cortexNor}
    return G
