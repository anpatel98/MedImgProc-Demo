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
from keras.layers import BatchNormalization
from keras import backend as K
from keras.losses import binary_crossentropy
from keras.utils.generic_utils import get_custom_objects
import matplotlib.pyplot as plt
from skimage.transform import rescale, resize, downscale_local_mean 
from scipy.io import savemat

# Patch, prediction saving directories
path_images = '/projects/academic/vincentt/anpatel6/DeepMedic/Original_Images_Binary/'
path_segmentations = '/projects/academic/vincentt/anpatel6/DeepMedic/Segmentations_Binary/'
#path_output = './Patches_predictions/'
path_output = './Predictions_overlap/' 

def dice(y_true,y_pred):
    smooth = 1
    P = y_pred.astype('float')
    L = y_true.astype('float')
    y_true_f = L.flatten()
    y_pred_f = P.flatten()
    intersection = np.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (np.sum(y_true_f) + np.sum(y_pred_f) + smooth)

def dice_coef(y_true,y_pred):
    smooth = 1
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth) 

def dice_coef_loss(y_true,y_pred):
    return 1-dice_coef(y_true,y_pred)

def bce_dice_loss(y_true, y_pred):
    return binary_crossentropy(y_true, y_pred) + dice_coef_loss(y_true, y_pred)

def jaccard_coef(y_true, y_pred):
    smooth = 1
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    sum_ = K.sum(y_true) + K.sum(y_pred)
    return (intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) - intersection + smooth)

def jaccard_coef_loss(y_true, y_pred):
    return 1-jaccard_coef(y_true, y_pred)

def bce_jaccard_loss(y_true, y_pred):
    return binary_crossentropy(y_true, y_pred) +  jaccard_coef_loss(y_true, y_pred)

def random_patch_extract(x,y,z, img_orig,label, cutting_len_low, cutting_len_high, cutting_len_true):	

	patch_low = img_orig[int(x-cutting_len_low):int(x+cutting_len_low), int(y-cutting_len_low):int(y+cutting_len_low), int(z-cutting_len_low):int(z+cutting_len_low)]
	patch_high = img_orig[int(x-cutting_len_high):int(x+cutting_len_high), int(y-cutting_len_high):int(y+cutting_len_high), int(z-cutting_len_high):int(z+cutting_len_high)]
	patch_output_label = label[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true)]

	assert (patch_high.shape == input_size_high)
	assert (patch_low.shape == input_size_low)
	assert (patch_output_label.shape == output_size_label)

	return (patch_high, patch_low, patch_output_label)

def Pad_image_divisible_by_n(img_orig, n):

	a1 = int(np.ceil(img_orig.shape[0]/ n))
	a2 = int(np.ceil(img_orig.shape[1]/ n))
	a3 = int(np.ceil(img_orig.shape[2]/ n))
	img_new = np.zeros((a1*n, a2*n, a3*n))
	img_new[0:img_orig.shape[0], 0:img_orig.shape[1], 0:img_orig.shape[2]] = img_orig

	return img_new

def normalize(image):
	# Image is normalized in order to have zero mean and unit variance.
	image_normalized = (image - np.mean(image))/np.std(image)

	return image_normalized

list_of_files = os.listdir('./best_model/')

for file in list_of_files:
	filename = file.split('.')
	if filename[1].lower()=='h5':
		MODEL_ID = filename[0]

# Configure custom activation/loss/optimizer used in model
get_custom_objects().update({'dice_coef': dice_coef})
get_custom_objects().update({'dice_coef_loss': dice_coef_loss}) 
get_custom_objects().update({'bce_dice_loss': bce_dice_loss}) 

# Load saved model
model = load_model('./best_model/' + MODEL_ID + '.h5', custom_objects={'bce_dice_loss': bce_dice_loss, 'dice_coef_loss': dice_coef_loss, 'dice_coef': dice_coef}) 

# Define 3d patch size for normal and low resolution path
input_size_high = (40, 40, 40)
input_size_low = (64, 64, 64)
resize_low = (22, 22, 22)
output_size_label = (24, 24, 24)

# Parameters to generate patches and pad images
difference = (input_size_low[0]-output_size_label[0])//2                # Pad by 20 
cutting_len_high = input_size_high[0]//2  				# 20
cutting_len_low = input_size_low[0]//2         				# 32
cutting_len_true = output_size_label[0]//2      			# 12
# Set offset for overlap
overlap_frac = 0.5 
stride = cutting_len_true*2 - cutting_len_true*2*overlap_frac 
#offset = input_size_low[0] - np.ceil(input_size_low[0]*overlap_frac)

#loading the excel sheet with the caselist
wb = load_workbook(filename = './Caselist.xlsx')
sheet_ranges = wb['Sheet1']

#number of cases to be included:
number_of_cases = 20
start_number = 31
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
			#if not os.path.exists(path_output + Case):
				#os.mkdir(path_output + Case)
				#os.mkdir(path_output + Case +'/'+'True_' + str(output_size_label[0]))
				#os.mkdir(path_output + Case +'/'+'Orig_' + str(input_size_high[0])) 
				#os.mkdir(path_output + Case +'/'+'Predictions')

			img_orig = np.load(path_images + Case + '_Binary')
			label = np.load(path_segmentations + Case + '_Segmentation_Binary')
			a, b, c = img_orig.shape

			# Threshold CTA ROI between 100 to 700
			img_orig[img_orig<100] = 0
			img_orig[img_orig>700] = 0
			img_orig  = img_orig/np.max(img_orig) 
			assert img_orig.shape==label.shape
			
			img_orig = Pad_image_divisible_by_n(img_orig, output_size_label[0])
			label = Pad_image_divisible_by_n(label, output_size_label[0])
			assert img_orig.shape==label.shape

			# Padd original and label image to extract low resolution patches with higher context
			img_orig = np.pad(img_orig, pad_width = difference, mode='constant', constant_values=0)
			label = np.pad(label, pad_width = difference, mode='constant', constant_values=0)
			assert img_orig.shape==label.shape

			predicted_img = np.zeros((label.shape[0], label.shape[1], label.shape[2],1)) 
			divide_by_img = np.zeros((label.shape[0], label.shape[1], label.shape[2],1))

			count = 0 

			for z in np.arange(0+cutting_len_low, img_orig.shape[2]+cutting_len_true-cutting_len_low, stride):
				for y in np.arange(0+cutting_len_low, img_orig.shape[1]+cutting_len_true-cutting_len_low, stride):
					for x in np.arange(0+cutting_len_low, img_orig.shape[0]+cutting_len_true-cutting_len_low, stride):
						#index = [x,y,z]
						#print(index)
						patch_high, patch_low, patch_output_label = random_patch_extract(x,y,z, img_orig,label, cutting_len_low, cutting_len_high, cutting_len_true)
						patch_low = resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])) 

						X_high = np.empty((1, input_size_high[0], input_size_high[1], input_size_high[2], 1))
						X_low = np.empty((1, resize_low[0], resize_low[1], resize_low[2], 1))
						Y = np.empty((1, output_size_label[0], output_size_label[1], output_size_label[2], 1))

						X_high[0,:,:,:,0] = patch_high[:,:,:]
						X_low[0,:,:,:,0] = patch_low[:,:,:]
						Y[0,:,:,:,0] = patch_output_label[:,:,:] 

						prediction = model.predict([X_high, X_low])
 
						'Stiching patches to original image size'
						predicted_img[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true),:] = predicted_img[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true),:] + prediction 
						divide_by_img[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true),:] = divide_by_img[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true),:] + np.ones((output_size_label[0], output_size_label[1], output_size_label[2], 1))

						#dice_individual = dice(Y, prediction[0])
						#print('Dice coefficient of patch number ' + str(count) + ' is ' + str(dice_individual)) 

						'''
						plt.figure()
						plt.subplot(1,2,1)
						abc = np.max(predicted_img,axis=0)
						plt.imshow(abc)

						plt.subplot(1,2,2)
						abc1 = np.max(divide_by_img,axis=0)
						plt.imshow(abc1)
						plt.show()
						'''
						count = count + 1
						count_general = count_general + 1 

			'''
			plt.figure()
			abc = np.max(divide_by_img,axis=0)
			plt.imshow(abc)
			plt.show()
			'''
			# Bring predicted image to the original image shape
			predicted_img = predicted_img[0+difference : predicted_img.shape[0]-difference, 0+difference : predicted_img.shape[1]-difference, 0+difference : predicted_img.shape[2]-difference]
			predicted_img = predicted_img[0:int(a), 0:int(b), 0:int(c)]
			divide_by_img = divide_by_img[0+difference : divide_by_img.shape[0]-difference, 0+difference : divide_by_img.shape[1]-difference, 0+difference : divide_by_img.shape[2]-difference]
			divide_by_img = divide_by_img[0:int(a), 0:int(b), 0:int(c)]
			label = label[0+difference : label.shape[0]-difference, 0+difference : label.shape[1]-difference, 0+difference : label.shape[2]-difference]
			label = label[0:int(a), 0:int(b), 0:int(c)]

			if overlap_frac != 0:
				predicted_img = np.divide(predicted_img, divide_by_img, where=divide_by_img!=0)

			'''
			plt.figure()
			plt.subplot(1,2,1)
			abc = np.max(label,axis=0)
			plt.title("GT_" + Case, fontsize=18, y=1.05)
			plt.imshow(abc)

			plt.subplot(1,2,2)
			abc1 = np.max(predicted_img,axis=0)
			plt.title("Pred_" + Case, fontsize=18, y=1.05)
			plt.imshow(abc1)
			plt.savefig(path_output +'/'+ 'Comparison_GT_Pred_'+Case +'_overlap' + '.png') 
			'''
			#out_file = open(path_output +'/'+ 'Prediction_' + Case,'wb')
			#np.save(out_file, predicted_img)
			dictio = {'a': predicted_img} 
			savemat(path_output +'/'+ Case +'_Prediction.mat',dictio) 
			dictio1 = {'a1': label} 
			savemat(path_output +'/'+ Case +'_Label.mat',dictio1)  
