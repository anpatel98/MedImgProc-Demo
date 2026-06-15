"""
Author: [qiuchang]
Description: This script provides functions for signal processing, including
             downsampling, filtering, and channel selection from BDF files.
"""
import numpy as np
import os
from signal_viewer import SignalViewer
from scipy.signal import butter, filtfilt, detrend
import mne



def downsampleRwn(timeIn, sigIn, r):
    sigLength = sigIn.shape[1]
    numChannels = sigIn.shape[0]
    modLength = sigLength % r
    sigIn = sigIn[:, :sigLength - modLength]
    sigLength = sigIn.shape[1]
    downsampledSigLen = sigLength // r
    SigDs = np.zeros((numChannels, downsampledSigLen, r+1))
    for jCh in range(numChannels):
        for idx in range(r):
            SigDs[jCh, :, idx] = sigIn[jCh, idx::r]
        SigDs[jCh, :, r] = np.mean(SigDs[jCh, :, :r], axis=1)
    sigOut = SigDs[:, :, -1]
    timeOut = timeIn[:len(timeIn) - modLength:r]
    return timeOut, sigOut

def butter_highpass_sw(sigIn, fc, fs, order=2):
    Wn = fc / (fs / 2)
    b, a = butter(order, Wn, btype='high')
    return filtfilt(b, a, sigIn, axis=0)

def butter_lowpass_sw(sigIn, fc, fs, order=4):
    Wn = fc / (fs / 2)
    b, a = butter(order, Wn, btype='low')
    return filtfilt(b, a, sigIn, axis=0)

def bandpass_denoise_butter(sigIn, timeIn, fs, f_low, f_high, detrend_flag=True):
    r=2048
    timeOut, sigRwn = downsampleRwn(timeIn, sigIn ,r)
    sigOut = sigRwn
    fs = fs / r
    sigOut = butter_highpass_sw(sigOut.T, fc=f_low, fs=fs)
    if detrend_flag:
        sigOut = detrend(sigOut, type='constant')
    sigOut = sigOut.T
    sigOut = butter_lowpass_sw(sigOut.T, fc=f_high, fs=fs)
    if detrend_flag:
        sigOut = detrend(sigOut, type='constant')
    sigOut = sigOut.T
    return timeOut, sigOut

def auto_select_channel(sig_out):
    variances = np.var(sig_out, axis=1)
    Q1 = np.percentile(variances, 25)
    Q3 = np.percentile(variances, 75)
    IQR = Q3 - Q1
    variance_threshold = Q3 + 1 * IQR

    mask = variances <= variance_threshold
    filtered_sig_out = sig_out[mask]
    remaining_channels = np.arange(sig_out.shape[0])[mask]
    bad_channels = np.arange(sig_out.shape[0])[~mask]
    return filtered_sig_out,remaining_channels,bad_channels


def read_bdf_files(directory,selected_file):
    # List all BDF files in the directory

    full_path = os.path.join(directory, selected_file)
    print(f"Reading file: {full_path}")

    bdf_data = mne.io.read_raw_bdf(full_path, preload=True)
    signal_data = bdf_data.get_data()
    signal_fs = bdf_data.info['sfreq']  # Sampling frequency
    signal_times = bdf_data.times

    # Extract EXG1, EXG2, and EXG3 channels for ground reference signal
    exg_indices = [bdf_data.ch_names.index(ch) for ch in ['EXG1', 'EXG2', 'EXG3'] if ch in bdf_data.ch_names]
    gnd_signal = signal_data[exg_indices, :]
    gnd_signal_mean = np.mean(gnd_signal, axis=0)

    # Subtract ground reference signal from the first 128 channels
    data_gnd = signal_data[:64, :] - gnd_signal_mean

    return data_gnd, signal_fs, signal_times

def signal_data_load(Raw_file,selected_file,Config,manual=True):
    siganl_data, Raw_siganl_fs, Raw_siganl_times = read_bdf_files(Raw_file,selected_file)
    time_out, band_sig_out = bandpass_denoise_butter(siganl_data, Raw_siganl_times, Raw_siganl_fs, Config['f_low'],
                                                     Config['f_high'])
    band_sig_out = band_sig_out * 1000

    if manual:
        auto_sig_inverse, auto_remain_channel, bad_channels= auto_select_channel(band_sig_out)
        viewer = SignalViewer(band_sig_out, bad_channels)
        viewer.run()
        manual_sig_inverse, manual_remain_channel = viewer.get_data()
        return manual_sig_inverse, manual_remain_channel
    else:
        auto_sig_inverse, auto_remain_channel,bad_channels = auto_select_channel(band_sig_out)
        return auto_sig_inverse, auto_remain_channel