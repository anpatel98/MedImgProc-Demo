#!/bin/bash

# "Author: Aakash Patel"
# "Email: aakash@wustl.edu"

home_dir="/data/aakash/RESEARCH-PROJECTS/CMET_FDG_MS/Subject_Data"
source ${FSLDIR}etc/fslconf/fsl.sh # Activate FSL

SESSIONS="1179301_mMR_v1 1179303_mMR_v1 1179307_mMR_v1 1179308_mMR_v1 1295_001_v1 1295_003_v1 1295_004_v1 1295_005_v1 1295_006_v1 1295_007_v1 1295_008_v1 1295_011_v1 1295_002_v1 1295_012_v1 1295_013_v1 1295_503_v1 1295_504_v1 1295_505_v1 1295_506_V1 1295_507_v1 1295_508_v1 1295-509-v1 1179302_mMR-V1 1179304_mMR_v1"
Data="FA AD RD cell_ratio_map fiber_ratio_map fiber_axial_map fiber_radial_map" # Combined DTI and DBSI parameters

#touch ${home_dir}/${data}.txt

for data in $Data;do
	# Get average diffusion parameter value in Normal Appearing White matter (NAWM) and White matter lesion (CWM)
	echo "$data" | tee -a ${home_dir}/cwm_dbsi_cmet.txt
	echo "NAWM CWM" | tee -a ${home_dir}/cwm_dbsi_cmet.txt

	for session in $SESSIONS;do
		cd ${home_dir}/${session}/REGISTRATION/DWI_to_Structural
		cmd1="fslmeants -i ${session}_${data}_to_T1w_biascorr.nii.gz -m ../${session}_lesion_to_T1w_biascorr_flipped.nii.gz"
		cmd2="fslmeants -i ${session}_${data}_to_T1w_biascorr.nii.gz -m ../${session}_lesion_to_T1w_biascorr.nii.gz"
		echo "$(eval $cmd1) $(eval $cmd2)" 2>&1 | tee -a ${home_dir}/cwm_dbsi_cmet.txt
	done
done
