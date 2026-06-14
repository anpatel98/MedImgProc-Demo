import os
import time
import collections
import numpy as np
from openpyxl import load_workbook
#import pydicom as dicom
from skimage.transform import rescale, resize, downscale_local_mean 
#import matplotlib.pyplot as plt


def random_patch_extract(x,y,z, img_orig,label, cutting_len_low, cutting_len_high, cutting_len_true):	

	patch_low = img_orig[int(x-cutting_len_low):int(x+cutting_len_low), int(y-cutting_len_low):int(y+cutting_len_low), int(z-cutting_len_low):int(z+cutting_len_low)]
	patch_high = patch_low[cutting_len_high:patch_low.shape[0]-cutting_len_high, cutting_len_high:patch_low.shape[1]-cutting_len_high, cutting_len_high:patch_low.shape[2]-cutting_len_high]
	patch_output_label = label[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true)]

	assert (patch_high.shape == input_size_high)
	assert (patch_low.shape == input_size_low)
	assert (patch_output_label.shape == output_size_label)

	return (patch_high, patch_low, patch_output_label)

def normalize(image):
	# Image is normalized in order to have zero mean and unit variance.
	image_normalized = (image - np.mean(image))/np.std(image)

	return image_normalized


path_images = '/projects/academic/vincentt/anpatel6/DeepMed_trial2/Original_Images_Binary/'
path_segmentations = '/projects/academic/vincentt/anpatel6/DeepMed_trial2/Segmentations_Binary/'
path_output = './Patches/'

# Define 3d patch size for normal and low resolution path
input_size_high = (40, 40, 40)
input_size_low = (64, 64, 64)
resize_low = (22, 22, 22)
output_size_label = (24, 24, 24)
		
difference = (input_size_low[0]-input_size_high[0])//2    	# Pad by 12 
cutting_len_high = difference  								# 12
cutting_len_low = input_size_low[0]//2         				# 32
cutting_len_true = output_size_label[0]//2      			# 12

start_time = time.time()

#loading the excel sheet with the caselist
wb = load_workbook(filename = '/projects/academic/vincentt/anpatel6/DeepMed_trial2/Caselist.xlsx')
sheet_ranges = wb['Sheet1']

#number of cases to be included:
number_of_cases = 40
start_number = 1
count_general = 0

for i in np.arange(start_number+1,number_of_cases+start_number+1):
	#Patient Name:
	d = 'A' + str(i)
	e = sheet_ranges[d].value

	#matching the directory name with the name in the excel sheet:
	for j in os.listdir(path_images):
		if (e +'_Binary') == j:
			print(e)
			Case = e

			img_orig = np.load(path_images + Case + '_Binary')
			label = np.load(path_segmentations + Case + '_Segmentation_Binary')
			# Threshold CTA ROI between 100 to 700
			img_orig[img_orig<100] = 0
			img_orig[img_orig>700] = 0
			img_orig  = img_orig/np.max(img_orig)
			assert img_orig.shape==label.shape

			# Padd original and label image
			img_orig = np.pad(img_orig, pad_width = difference, mode='constant', constant_values=0)
			label = np.pad(label, pad_width = difference, mode='constant', constant_values=0)

			index_list = []
			total_patches = 1200
			percent = 0.5  # % of vessel-centric patches
			percent1 = 0.5  # % of sum greater than zero patches
			count_vessel = int(percent*total_patches)
			count_sum_1 = int(percent1*total_patches)
			count = 0
    		
			while count<count_vessel:

				# generate random x,y,z 
				x = np.random.randint(0+cutting_len_low, img_orig.shape[0] - cutting_len_low) + 0.5
				y = np.random.randint(0+cutting_len_low, img_orig.shape[1] - cutting_len_low) + 0.5
				z = np.random.randint(0+cutting_len_low, img_orig.shape[2] - cutting_len_low) + 0.5
				index = [x,y,z]

				if ( label[int(x),int(y),int(z)]==1 ):
					if index not in index_list:
						index_list.append(index)
						# generate patches
						patch_high, patch_low, patch_output_label = random_patch_extract(x, y, z, img_orig,label, cutting_len_low, cutting_len_high, cutting_len_true)

						# Write normal resolution patch
						out_file = open(path_output + 'Orig_high_' + str(input_size_high[0]) +'/'+ str(count_general),'wb')
						np.save(out_file, patch_high)
						# Write low resolution patch
						out_file = open(path_output + 'Orig_low_' + str(input_size_low[0]) +'/'+ str(count_general),'wb')
						np.save(out_file, resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])))
						# Write label patch
						out_file = open(path_output + 'True_' + str(output_size_label[0]) +'/'+ str(count_general),'wb')
						np.save(out_file, patch_output_label)

						print('Writing patch number : ' + str(count) + '/'+str(total_patches) + '.......'+'Current patch number : '+str(count_general))
						count = count + 1
						count_general = count_general + 1
						'''
						plt.figure()
						plt.subplot(1,3,1)
						abc = np.max(patch_output_label,axis=0)
						plt.title("Label patch ( $24^3$ )", fontsize=22)
						plt.imshow(abc)

						plt.subplot(1,3,2)
						abc = np.max(patch_high,axis=0)
						plt.title("High resolution patch ( $40^3$ )", fontsize=22)
						plt.imshow(abc)

						plt.subplot(1,3,3)
						#abc = np.max(resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])),axis=0)
						abc1 = np.max(patch_low,axis=0)
						plt.title("Low resolution patch ( $64^3$ )", fontsize=22)
						plt.imshow(abc1)

						plt.show()
						'''
					else:
						continue
				else:
					continue
					

			while count<(count_vessel+count_sum_1):

				# generate random x,y,z 
				x = np.random.randint(0+cutting_len_low, img_orig.shape[0] - cutting_len_low) + 0.5
				y = np.random.randint(0+cutting_len_low, img_orig.shape[1] - cutting_len_low) + 0.5
				z = np.random.randint(0+cutting_len_low, img_orig.shape[2] - cutting_len_low) + 0.5
				index = [x,y,z]

				if ( np.sum(label[int(x-cutting_len_true):int(x+cutting_len_true), int(y-cutting_len_true):int(y+cutting_len_true), int(z-cutting_len_true):int(z+cutting_len_true)])>0 ):
					if index not in index_list:
						index_list.append(index)
						# generate patches
						patch_high, patch_low, patch_output_label = random_patch_extract(x, y, z, img_orig,label, cutting_len_low, cutting_len_high, cutting_len_true)

						# Write normal resolution patch 
						out_file = open(path_output + 'Orig_high_' + str(input_size_high[0]) +'/'+ str(count_general),'wb')
						np.save(out_file, patch_high)
						# Write low resolution patch
						out_file = open(path_output + 'Orig_low_' + str(input_size_low[0]) +'/'+ str(count_general),'wb')
						np.save(out_file, resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])))
						# Write label patch
						out_file = open(path_output + 'True_' + str(output_size_label[0]) +'/'+ str(count_general),'wb')
						np.save(out_file, patch_output_label)
						
						print('Writing patch number : ' + str(count) + '/'+str(total_patches) + '.......'+'Current patch number : '+str(count_general))
						count = count + 1
						count_general = count_general + 1
						'''
						plt.figure()
						plt.subplot(1,3,1)
						abc = np.max(patch_output_label,axis=0)
						plt.imshow(abc)

						plt.subplot(1,3,2)
						abc = np.max(patch_high,axis=0)
						plt.imshow(abc)

						plt.subplot(1,3,3)
						#abc = np.max(resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])),axis=0)
						abc1 = np.max(patch_low,axis=0)
						plt.imshow(abc1)

						plt.show()
						'''
					else:
						continue
				else:
					continue

			while count<total_patches:

				# generate random x,y,z 
				x = np.random.randint(0+cutting_len_low, img_orig.shape[0] - cutting_len_low) + 0.5
				y = np.random.randint(0+cutting_len_low, img_orig.shape[1] - cutting_len_low) + 0.5
				z = np.random.randint(0+cutting_len_low, img_orig.shape[2] - cutting_len_low) + 0.5
				index = [x,y,z]

				if index not in index_list:
					index_list.append(index)
					# generate patches
					patch_high, patch_low, patch_output_label = random_patch_extract(x, y, z, img_orig,label, cutting_len_low, cutting_len_high, cutting_len_true)

					# Write normal resolution patch 
					out_file = open(path_output + 'Orig_high_' + str(input_size_high[0]) +'/'+ str(count_general),'wb')
					np.save(out_file, patch_high)
					# Write low resolution patch
					out_file = open(path_output + 'Orig_low_' + str(input_size_low[0]) +'/'+ str(count_general),'wb')
					np.save(out_file, resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])))
					# Write label patch
					out_file = open(path_output + 'True_' + str(output_size_label[0]) +'/'+ str(count_general),'wb')
					np.save(out_file, patch_output_label)
					
					print('Writing patch number : ' + str(count) + '/'+str(total_patches) + '.......'+'Current patch number : '+str(count_general))
					count = count + 1
					count_general = count_general + 1
					'''
					plt.figure()
					plt.subplot(1,3,1)
					abc = np.max(patch_output_label,axis=0)
					plt.imshow(abc)

					plt.subplot(1,3,2)
					abc = np.max(patch_high,axis=0)
					plt.imshow(abc)

					plt.subplot(1,3,3)
					#abc = np.max(resize(patch_low, (resize_low[0], resize_low[1], resize_low[2])),axis=0)
					abc1 = np.max(patch_low,axis=0)
					plt.imshow(abc1)

					plt.show()
					'''		
				else:
					continue

end_time = time.time()
hours, rem = divmod(end_time-start_time, 3600)
minutes, seconds = divmod(rem, 60)
print(str(count_general) + '  patches generated in ' + "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))