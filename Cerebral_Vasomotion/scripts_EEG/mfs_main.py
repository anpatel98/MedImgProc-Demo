"""
Author: qiuchang
Description: This script performs MFS (Method of Fundamental Solutions) inversion on uterine
             geometry data across multiple visits, applying configuration parameters and saving
             reconstructed data. The script processes each USEI directory, loads geometry and signal
             data, applies MFS inversion, and generates output files in .mat and .plt formats.

Functions:
- Loads geometry and filtered signal data.
- Applies MFS inversion for each visit1.
- Saves output files including reconstructed matrices and animated .plt files for visualization.

Configuration Parameters:
- scaleFactor: Scaling factor for geometry data.
- deflationRatio, inflationRatio: Ratios for geometry scaling.
- lambda, gamma, power: Regularization and constraint parameters for MFS inversion.
- constrain: Type of constraint applied during inversion.
"""

import numpy as np
from scipy.io import savemat
import os
import json
from mfs_function import MFS_inverse, make_animation_pots_file

if __name__ == "__main__":
    # Define main data path and configuration for MFS processing
    Data_path = r'D:\usei_data'

    # Configuration for MFS inversion
    Config = {
        'scaleFactor': 0.1,
        'deflationRatio': 0.8,
        'inflationRatio': 1.2,
        'lambda': 0.0001,
        'gamma': 0.2,
        'power': 3,
        'constrain': 'e'
    }

    save_file_dir = 'recon_surface_python_0.0'  # Directory for saving reconstructed data

    # Loop through each USEI index directory
    for USEI_index in os.listdir(Data_path):
        if os.path.isdir(os.path.join(Data_path, USEI_index)):
            print(USEI_index.upper())  # Display current USEI index

            USEI_dir = os.path.join(Data_path, USEI_index)
            save_path = os.path.join(USEI_dir, save_file_dir)

            # Create save directory if it doesn't exist
            if not os.path.isdir(save_path):
                os.mkdir(save_path)

            # Save configuration as JSON in the save directory

            config_file_ = save_path + '/Config.json'
            with open(config_file_, 'w') as config_file:
                json.dump(Config, config_file, indent=4)

            status_signal = os.path.join(USEI_dir, 'Visit1')

            if os.path.isdir(status_signal):
                # Load and filter the signal data
                for selected_status in os.listdir(status_signal):
                # Load geometry data, channel data, and signal data for the current visit
                    selected_status = selected_status.replace('.bdf', '')
                    geo_data = np.load(USEI_dir + '/geometry_mfs/geometry_mfs.npy', allow_pickle=True).item()
                    remain_channel = np.load(USEI_dir + f'/filtered_signal/Visit1_{selected_status}_selected_channel.npy')
                    sig_inverse = np.load(USEI_dir + f'/filtered_signal/Visit1_{selected_status}_selected_signal.npy')

                    # Perform MFS inversion and get results
                    output_file_source = save_path + f'/Visit1_{selected_status}_source_point.png'
                    cortex_pp, cortex_mfs, mfs_cof, fwdA, mfsInvA, bound, tmpInvA = MFS_inverse(
                        geo_data, remain_channel, sig_inverse, Config, output_file_source, constrain=Config['constrain']
                    )

                    # Define paths for saving output .mat and .plt files
                    output_file_mat = save_path + f"/{USEI_index.replace('-', '')}-Visit{selected_status}-Record1-Recon.mat"
                    output_file_plt = save_path + f"/{USEI_index.replace('-', '')}-Visit{selected_status}-Record1.plt"

                    # Determine bad channels by excluding remaining channels from a total of 128
                    BadCh = np.delete(np.arange(64), remain_channel)

                    # Save the reconstructed data in .mat format
                    savemat(output_file_mat, {
                        'BadCh': BadCh,
                        'cortexPotsMfs_select': cortex_mfs,
                        'swSig_1Hz': cortex_pp
                    })

                    # Generate animation plot file for the reconstructed cortex potentials
                    make_animation_pots_file(
                        output_file_plt,
                        geo_data['cortex']['pts'][:, 0],
                        geo_data['cortex']['pts'][:, 1],
                        geo_data['cortex']['pts'][:, 2],
                        cortex_pp,
                        geo_data['cortex']['tri'] + 1
                    )
