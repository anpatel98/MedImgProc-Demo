import os
#Arrays manipulations
import numpy as np
#Plotting library:
from matplotlib import pyplot, cm
#Reading excel files and accessing specific cells:
from openpyxl import load_workbook
#Tensorflow, Google's Deep Learning library, back end for Keras
import tensorflow as tf
#importing reading writing library 'Pickle'
import pickle

import keras

#CNN library, high level
from keras.models import model_from_json, load_model
from keras.models import Sequential, Model
from keras.layers.core import Dense, Flatten
from keras.layers import Convolution2D, MaxPooling2D, Input, Dropout, Concatenate
from keras.regularizers import l1, l2, l1_l2 
from keras.layers.normalization import BatchNormalization
from keras import backend as K
from keras.losses import binary_crossentropy
from keras.utils.generic_utils import get_custom_objects
import matplotlib.pyplot as plt
from skimage.transform import rescale, resize, downscale_local_mean 
from scipy.io import savemat

# Patch, prediction saving directories
path_images = './Original_Images_Binary/'
path_segmentations = './Segmentations_Binary/'
path_output = './Patches_prediction/' 


def dice_coef(y_true,y_pred):
    smooth = 1
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice(y_true,y_pred):
    smooth = 1
    P = y_pred.astype('float')
    L = y_true.astype('float')
    y_true_f = L.flatten()
    y_pred_f = P.flatten()
    intersection = np.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (np.sum(y_true_f) + np.sum(y_pred_f) + smooth)


def dice_coef_loss(y_true,y_pred):
    return 1-dice_coef(y_true,y_pred)

def bce_dice_loss(y_true, y_pred):
    return binary_crossentropy(y_true, y_pred) + dice_coef_loss(y_true, y_pred)

def random_patch_extract(x,y,z, img_orig,label, cutting_len):	

	patch_high = img_orig[int(x-cutting_len):int(x+cutting_len), int(y-cutting_len):int(y+cutting_len), int(z-cutting_len):int(z+cutting_len)]
	patch_output_label = label[int(x-cutting_len):int(x+cutting_len), int(y-cutting_len):int(y+cutting_len), int(z-cutting_len):int(z+cutting_len)]

	assert (patch_high.shape == input_size) 
	assert (patch_output_label.shape == output_size_label)

	return (patch_high, patch_output_label)

def Pad_image_divisible_by_n(img_orig, n):

	a1 = int(np.ceil(img_orig.shape[0]/ n))
	a2 = int(np.ceil(img_orig.shape[1]/ n))
	a3 = int(np.ceil(img_orig.shape[2]/ n))
	img_new = np.zeros((a1*n, a2*n, a3*n))
	img_new[0:img_orig.shape[0], 0:img_orig.shape[1], 0:img_orig.shape[2]] = img_orig

	return img_new

def normalize(image):
	# Image is normalized in order to have zero mean and unit variance.
	image_normalized = (image - np.mean(image))//np.std(image)

	return image_normalized

list_of_files = os.listdir('./model/')

for file in list_of_files:
	filename = file.split('.')
	if filename[1].lower()=='h5':
		MODEL_ID = filename[0]

# Configure custom activation/loss/optimizer used in model
get_custom_objects().update({'dice_coef': dice_coef})
get_custom_objects().update({'dice_coef_loss': dice_coef_loss})
get_custom_objects().update({'bce_dice_loss': bce_dice_loss}) 

# Load saved model
model = load_model('./model/' + MODEL_ID + '.h5', custom_objects={'bce_dice_loss': bce_dice_loss, 'dice_coef_loss': dice_coef_loss, 'dice_coef': dice_coef})
#model = load_model('./model/' + MODEL_ID + '.h5')

#print(model.summary())

# Threshold value for predicted mask
threshold = 0.499 
# Define 3d patch size for normal and low resolution path
input_size = (32, 32, 32) 
output_size_label = (32, 32, 32)
# Parameters to generate patches and pad images
cutting_len = output_size_label[0]//2      				# 16

#loading the excel sheet with the caselist
wb = load_workbook(filename = './Caselist.xlsx')
sheet_ranges = wb['Sheet1']

#number of cases to be included:
number_of_cases = 1
start_number = 56
count_general = 0

for i in np.arange(start_number+1,number_of_cases+start_number+1):
	#Patient Name:
	d = 'A' + str(i)
	e = sheet_ranges[d].value

	List_ID = [] 
	#matching the directory name with the name in the excel sheet:
	for l in os.listdir(path_images):
		if (e +'_Binary') == l:
			print(e)
			Case = e
			#shutil.rmtree(path_output + Case)
			os.makedirs(path_output + Case)
			os.mkdir(path_output + Case +'/'+'True_' + str(output_size_label[0]))
			os.mkdir(path_output + Case +'/'+'Orig_' + str(input_size[0])) 
			os.mkdir(path_output + Case +'/'+'Predictions')

			img_orig = np.load(path_images + Case + '_Binary')
			label = np.load(path_segmentations + Case + '_Segmentation_Binary')
			#img_orig = normalize(img_orig)
			# Threshold CTA ROI between 100 to 700
			img_orig[img_orig<100] = 0
			img_orig[img_orig>700] = 0
			img_orig  = img_orig/np.max(img_orig)

			assert img_orig.shape==label.shape
			
			img_orig = Pad_image_divisible_by_n(img_orig, output_size_label[0])
			label = Pad_image_divisible_by_n(label, output_size_label[0])
			assert img_orig.shape==label.shape

			# Padd original and label image to extract low resolution patches with higher context
			#img_orig = np.pad(img_orig, pad_width = Pad_width, mode='constant', constant_values=0)
			#label = np.pad(label, pad_width = Pad_width, mode='constant', constant_values=0)
			#assert img_orig.shape==label.shape

			predicted_img = np.zeros((label.shape[0], label.shape[1], label.shape[2],1))

			out_file = open(path_output + Case + '/' + 'True_' + Case,'wb')
			np.save(out_file, label)
			#print(img_orig.shape)
			#print(label.shape)
			count = 0 

			for z in np.arange(0+cutting_len, img_orig.shape[2] - cutting_len+1, cutting_len*2):
				for y in np.arange(0+cutting_len, img_orig.shape[1] - cutting_len+1, cutting_len*2):
					for x in np.arange(0+cutting_len, img_orig.shape[0] - cutting_len+1, cutting_len*2):
						#index = [x,y,z]
						#print(index)
						patch_high, patch_output_label = random_patch_extract(x, y, z, img_orig, label, cutting_len)
						#patch_low = resize(patch_low, (resize_low[0], resize_low[1], resize_low[2]))

						'''
						plt.figure()
						plt.subplot(1,3,1)
						abc = np.max(patch_output_label,axis=0)
						plt.title("Label patch ( $24^3$ )", fontsize=16)
						plt.imshow(abc)

						plt.subplot(1,3,2)
						abc2 = np.max(patch_high,axis=0)
						plt.title("High resolution patch ( $40^3$ )", fontsize=16)
						plt.imshow(abc2)

						plt.subplot(1,3,3)
						#abc = np.max(resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])),axis=0)
						abc1 = np.max(patch_low,axis=0)
						plt.title("Low resolution patch ( $64^3$ )", fontsize=18)
						plt.imshow(abc1) 
						plt.show()
						'''

						# Write normal resolution patch
						out_file = open(path_output + Case + '/' + 'Orig_' + str(input_size[0]) + '/' + str(count),'wb')
						np.save(out_file, patch_high) 
						# Write label patch
						out_file = open(path_output + Case + '/' + 'True_' + str(output_size_label[0]) + '/' + str(count),'wb')
						np.save(out_file, patch_output_label)

						print('Writing patch number : ' + str(count) + '.......'+'Current patch number : '+str(count_general)) 

						#print(patch_high.shape) 
						#print(patch_output_label.shape) 
						
						#if np.sum(patch_output_label[:,:,:])>350:

						X = np.empty((1, input_size[0], input_size[1], input_size[2], 1))
						Y = np.empty((1, output_size_label[0], output_size_label[1], output_size_label[2], 1))

						X[0,:,:,:,0] = patch_high[:,:,:] 
						Y[0,:,:,:,0] = patch_output_label[:,:,:]

						'''
						plt.figure()
						plt.subplot(1,2,1)
						abc = np.max(X_high[0,:,:,:,0], axis=1)
						plt.title("High res.", fontsize=18, y=1.05)
						plt.imshow(abc)

						plt.subplot(1,2,2)
						abc1 = np.max(X_low[0,:,:,:,0], axis=1)
						plt.title("Low res", fontsize=18, y=1.05)
						plt.imshow(abc1)
						plt.show()
						''' 

						prediction = model.predict(X)

						#prediction[prediction <= threshold] = 0
						#prediction[prediction > threshold] = 1 
						'''
						plt.figure()
						plt.subplot(1,2,1)
						abc = np.max(Y[0,:,:,:,0], axis=1)
						plt.title("Ground Truth", fontsize=18, y=1.05)
						plt.imshow(abc)

						plt.subplot(1,2,2)
						abc1 = np.max(prediction[0,:,:,:,0], axis=1)
						plt.title("Prediction", fontsize=18, y=1.05)
						plt.imshow(abc1)
						plt.show()
						'''
						#plt.savefig(path_output + 'Comparison_GT_Pred_'+Case + '.png') 
						'Stiching patches to original image size'
						predicted_img[int(x-cutting_len):int(x+cutting_len), int(y-cutting_len):int(y+cutting_len), int(z-cutting_len):int(z+cutting_len),:] = prediction

						# Save predicted mask
						out_file = open(path_output + Case +'/'+'Predictions/' + str(count),'wb')
						np.save(out_file, prediction) 

						dice_individual = dice(Y, prediction)
						print('Dice coefficient of patch number ' + str(count) + ' is ' + str(dice_individual))

						#predicted_img[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true), :] = prediction

						count = count + 1
						count_general = count_general + 1
			'''
			out_file = open(path_output + Case + '/' + 'Reconstructed_' + Case,'wb')
			np.save(out_file, predicted_img)
			'''
			plt.figure()
			plt.subplot(1,2,1)
			abc = np.max(label,axis=0)
			plt.title("Ground Truth", fontsize=18, y=1.05)
			plt.imshow(abc)

			plt.subplot(1,2,2)
			abc1 = np.max(predicted_img,axis=0)
			plt.title("Reconstructed", fontsize=18, y=1.05)
			plt.imshow(abc1)
			plt.savefig(path_output + 'Comparison_GT_Pred_'+Case + '.png')

			
			out_file = open(path_output + Case + '/' + 'Prediction_' + Case,'wb')
			np.save(out_file, predicted_img)
			dictio = {'a': predicted_img}
			savemat(path_output + Case + '/'+'Prediction_wo_th.mat',dictio)
			