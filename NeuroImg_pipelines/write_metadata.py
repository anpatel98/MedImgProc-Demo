# "Author: Aakash Patel"

# Description: This code writes header of one Nifti file to another Nifti file

import os
import numpy as np
import nibabel as nib

FILENAMES=["b0_map_masked","b0_map","cell_adc_map","cell_ratio_map","fiber1_ratio_map","fiber23_ratio_map","fiber_ratio_map","highhind_ratio_map","hind_ratio_map","lowhind_ratio_map"]

SESSIONS=["SUB_1001","SUB_1002","SUB_1003","SUB_1004","SUB_1005","SUB_1006","SUB_1007","SUB_1008","SUB_1009","SUB_1010","SUB_1011","SUB_1012"]

path=os.path.join('/ceph/chpc/shared/aakash/HCPEP/')

for idx,session in enumerate(SESSIONS):
	outpath = os.path.join(path,'MDDW_sessions',session,'DBSI')
	try:
		os.mkdir(outpath)
	except:
		print('DBSI Directory exists!') 

	print(str(idx) + "---- Correcting files of session " + session)

	try:
		dmri_img = nib.load(path+ 'MDDW_sessions/'+ session +'/NIFTI/'+session + '_dwi_corrected.nii.gz')
		for file in FILENAMES:
			img = nib.load(path + 'DBSI_results_mddw/' + session +'/'+ session +'_'+ file +'.nii')
			data = img.get_fdata()
			data = np.nan_to_num(data)
			new_img = nib.Nifti1Image(data, dmri_img.affine, dmri_img.header)
			nib.save(new_img, path +'MDDW_sessions/'+ session +'/DBSI/'+ session +'_'+ file +'.nii.gz')
			#os.remove(path + 'DBSI_new/' + session +'/'+ session +'_'+ file +'.nii')
			print("Header of " + session +" written to " + file)
	except:
		print('File does not exist')
		pass
