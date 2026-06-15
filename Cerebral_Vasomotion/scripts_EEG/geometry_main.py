"""
Author: [qiuchang]
Description: This script processes geometry data for USEI indices, loading geometry information
             and saving it as a NumPy array for each USEI directory.
"""
from geometry_function import geo_load
import numpy as np
import os

if __name__ == "__main__":
    # Set the main data path where USEI directories are located
    Data_path = r'D:\usei_data'
    save_file_dir = 'geometry_mfs'  # Directory name for saving processed geometry data

    # Loop through each USEI index in the main data path
    for USEI_index in os.listdir(Data_path):
        # Check if the current item is a directory
        if os.path.isdir(os.path.join(Data_path, USEI_index)):
            print(USEI_index.upper())  # Display the USEI index in uppercase for reference
            USEI_dir = os.path.join(Data_path, USEI_index)  # Path for each USEI directory
            geometry_path = os.path.join(USEI_dir, 'Geometry')  # Path to Geometry folder
            patch_path = os.path.join(geometry_path, 'Patch')  # Path to Patch sub-folder
            save_path = os.path.join(USEI_dir, save_file_dir)  # Path to save processed data

            # Create the save directory if it doesn't exist
            if not os.path.isdir(save_path):
                os.mkdir(save_path)

            # Load geometry data using geo_load function
            Geo = geo_load(patch_path, geometry_path)

            # Define output file path and save geometry data as a .npy file
            output_file = save_path + '/geometry_mfs.npy'
            np.save(output_file, Geo)