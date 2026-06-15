"""
Author: qiuchang
Description: This script processes and filters physiological signal data from multiple visits for each USEI directory.
             It applies a bandpass filter based on configured frequency limits, saves the filtered signals,
             and stores the configuration settings for reproducibility.

Workflow:
1. Iterates over each USEI directory in the main data path.
2. For each status, loads raw signal data, applies filtering, and performs channel selection.
3. Saves the filtered signal and remaining channel data in both .npy and .mat formats for compatibility.
4. Stores the filtering configuration as a JSON file in each USEI directory.

Configuration Parameters:
- f_low: Lower cutoff frequency for bandpass filtering.
- f_high: Upper cutoff frequency for bandpass filtering.

Functions:
- signal_data_load: Loads and filters signal data based on provided configuration and optional manual channel selection.
"""
from scipy.io import savemat
import os
from signal_function import signal_data_load
import numpy as np
import json

if __name__ == "__main__":
    # Define the main data path and configuration for filtering
    Data_path = r'D:\usei_data'
    Config = {
        'f_low': 0.01,   # Lower cutoff frequency
        'f_high': 0.1   # Upper cutoff frequency
    }
    save_file_dir = 'filtered_signal'  # Directory for saving filtered signals

    # Loop through each directory in the main data path
    for USEI_index in os.listdir(Data_path):
        if os.path.isdir(os.path.join(Data_path, USEI_index)):
            USEI_dir = os.path.join(Data_path, USEI_index)  # Directory for each USEI index
            save_path = os.path.join(USEI_dir, save_file_dir)

            # Create the save directory if it doesn't exist
            if not os.path.isdir(save_path):
                os.mkdir(save_path)

            # Save configuration settings as a JSON file in the save directory
            config_file_ = save_path + '/Config.json'
            with open(config_file_, 'w') as config_file:
                json.dump(Config, config_file, indent=4)

            Raw_file = os.path.join(USEI_dir, 'Visit1')
            save_file = save_path + '/Visit1'

            if os.path.isdir(Raw_file):
                # Load and filter the signal data
                for selected_file in os.listdir(Raw_file):

                    sig_filtered, remain_channel = signal_data_load(Raw_file, selected_file, Config, manual=False)
                    # Save the filtered signal and channel data as .npy files
                    selected_file = selected_file.replace('.bdf','')
                    output_file_signal = save_file + f'_{selected_file}_selected_signal.npy'
                    output_file_channel = save_file + f'_{selected_file}_selected_channel.npy'
                    np.save(output_file_signal, sig_filtered)
                    np.save(output_file_channel, remain_channel)

                    # Save the filtered signal and channel data as .mat files
                    output_file_signal_mat = save_file + f'_{selected_file}_selected_signal.mat'
                    savemat(output_file_signal_mat, {'signal': sig_filtered})
                    output_file_channel_mat = save_file + f'_{selected_file}_selected_channel.mat'
                    savemat(output_file_channel_mat, {'channel': remain_channel})
