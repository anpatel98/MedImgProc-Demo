#!/bin/bash

# "Author: Aakash Patel"
# "Email: aakash@wustl.edu"

##### Description: Generate scripts to run TBSS steps on grouped data for each diffusion parameter.
##### Outputs: After sucessful run, whole brain and skeletonized 4D file should be generated in stats directory for each parameter.
##### Notes: Before running it please make sure diffusion data is processed and your choice of parameters are calculated.
#####       Set path as required. Name of data must be same as name given to FA data (Check FSL DTI page for more details).

SESSIONS_CN=("1010_01_MR" "1017_01_MR" "1024_01_MR" "1026_01_MR" "1028_01_MR" "1052_01_MR" "1064_01_MR" "1067_01_MR" "1078_01_MR" "1079_01_MR" "1080_01_MR" "1081_01_MR" "1082_01_MR" "1084_01_MR" "1085_01_MR" "1088_01_MR" "1091_01_MR" "1093_01_MR" "1104_01_MR" "2001_01_MR" "2004_01_MR" "2020_01_MR" "2031_01_MR" "2044_01_MR" "2046_01_MR" "2048_01_MR" "3001_01_MR" "3002_01_MR" "3027_01_MR" "3029_01_MR" "3030_01_MR" "3031_01_MR" "3032_01_MR" "3035_01_MR" "3039_01_MR" "4002_01_MR" "4003_01_MR" "4006_01_MR" "4010_01_MR" "4011_01_MR" "4012_01_MR" "4018_01_MR" "4022_01_MR" "4036_01_MR" "4047_01_MR" "4048_01_MR" "4063_01_MR" "4072_01_MR")
SESSIONS_SCZ=("1006_01_MR" "1009_01_MR" "1012_01_MR" "1013_01_MR" "1015_01_MR" "1018_01_MR" "1019_01_MR" "1020_01_MR" "1021_01_MR" "1025_01_MR" "1029_01_MR" "1033_01_MR" "1034_01_MR" "1035_01_MR" "1037_01_MR" "1040_01_MR" "1041_01_MR" "1043_01_MR" "1045_01_MR" "1047_01_MR" "1048_01_MR" "1050_01_MR" "1051_01_MR" "1053_01_MR" "1054_01_MR" "1056_01_MR" "1057_01_MR" "1060_01_MR" "1061_01_MR" "1063_01_MR" "1065_01_MR" "1069_01_MR" "1070_01_MR" "1071_01_MR" "1072_01_MR" "1073_01_MR" "1074_01_MR" "1075_01_MR" "1077_01_MR" "1087_01_MR" "1095_01_MR" "1098_01_MR" "1099_01_MR" "1105_01_MR" "2006_01_MR" "2007_01_MR" "2008_01_MR" "2010_01_MR" "2012_01_MR" "2014_01_MR" "2015_01_MR" "2016_01_MR" "2019_01_MR" "2023_01_MR" "2029_01_MR" "2033_01_MR" "2041_01_MR" "2045_01_MR" "2062_01_MR" "3009_01_MR" "3011_01_MR" "3017_01_MR" "3020_01_MR" "3022_01_MR" "3025_01_MR" "3034_01_MR" "4005_01_MR" "4014_01_MR" "4015_01_MR" "4024_01_MR" "4030_01_MR" "4040_01_MR" "4049_01_MR" "4059_01_MR" "4065_01_MR" "4069_01_MR" "4074_01_MR" "4075_01_MR" "4091_01_MR")

RESULTS="FA AD RD cell_ratio_map fiber1_axial_map fiber1_radial_map fiber1_ratio_map fiber23_axial_map fiber23_radial_map fiber23_ratio_map fiber_axial_map fiber_radial_map fiber_ratio_map highhind_ratio_map hind_ratio_map lowhind_ratio_map"

StudyFolder="/scratch/$USER/HCPEP" # Specify path as required
ProcessName="TBSS"  #Shorthand text string to describe what we are doing

######## create directories for tbss analysis ########
tbssDIR=${StudyFolder}/TBSS
mkdir -p ${tbssDIR}

sbatchDIR=${StudyFolder}/sbatch
slogDIR=${sbatchDIR}/logs
mkdir -p ${slogDIR}

for index in $RESULTS; do

if [ $index == "FA" ]; then
	DATA="FA"
else
	DATA="Non_FA"
fi

sbatchScript="SBATCH_${index}_${ProcessName}"
runScript="run_${index}_${ProcessName}"

######## create the sbatch launching script for each session ########

echo $sbatchScript
cat > ${sbatchDIR}/${sbatchScript}.sh <<EOF
#!/bin/bash
######## Job Name: $runScript ########
#SBATCH -J $runScript
######## Job Output File: $runScript.oJOBID ########
#SBATCH -o ${slogDIR}/$runScript.o%j
######## Job Error File: $runScript.eJOBID #######
#SBATCH -e ${slogDIR}/$runScript.e%j
######## Which group is to be charged for service? ########
######## Look at available services for your group "sacctmgr list accounts -P" ########
#SBATCH --account=daniel_mamah
######## check partitions "sinfo -s" ########
#SBATCH --partition=tier2_cpu
######## Number of nodes: 1 ########
#SBATCH -N 1
######## Number of tasks: 1 ########
#SBATCH -n 1
######## Request a CPU or V100 or V100S GPU gres=gpu:1 --cpus-per-task=12########
#SBATCH --cpus-per-task=24
######## Memory per node: 5 GB ########
#SBATCH --mem=36GB
######## Walltime: 1 hour ########
#SBATCH -t 1:00:00

export StudyFolder="$StudyFolder"
sbatchDIR="$sbatchDIR"
runScript="$runScript"

EOF

# Use quotes around EOF to echo text as literal, rather than shell evaluating the variables
cat >> ${sbatchDIR}/${sbatchScript}.sh <<'EOF'
module load fsl/6.0.5

bash ${sbatchDIR}/${runScript}.sh

EOF

######## create the associated script to be run for each index ########

echo $runScript

cat > ${sbatchDIR}/${runScript}.sh <<EOF
SESSIONS_CN=(${SESSIONS_CN[@]})
SESSIONS_SCZ=(${SESSIONS_SCZ[@]})
index="$index"
StudyFolder="$StudyFolder"
ProcessName="$ProcessName"  #Shorthand text string to describe what we are doing
tbssDIR="$tbssDIR"

EOF

if [ $DATA == "FA" ]; then
echo "FA"
cat >> ${sbatchDIR}/${runScript}.sh <<'EOF'

######## Copy FA data to tbss directory ########
for i in ${!SESSIONS_CN[@]}; do
	session=${SESSIONS_CN[$i]}
	num=$(($i+100))
	echo "$num"
	echo "Collecting $index data of subject $session"
	rsync -ravzh -i $StudyFolder/dMRI/$session/${session}_dtifit_${index}.nii.gz ${tbssDIR}/CON_${num}_dtifit.nii.gz
done

for i in ${!SESSIONS_SCZ[@]}; do
        session=${SESSIONS_SCZ[$i]}
        num=$(($i+100))
	echo "$num"
        echo "Collecting $index data of subject $session"
        rsync -ravzh -i $StudyFolder/dMRI/$session/${session}_dtifit_${index}.nii.gz ${tbssDIR}/PAT_${num}_dtifit.nii.gz
done

## Run TBSS steps on DTI generated data

cd $tbssDIR

## TBSS Step 1: Set up data folder structure for subsequent analysis
cmd1="tbss_1_preproc *.nii.gz"
echo $cmd1
eval $cmd1

## TBSS Step 2:Calculate transforms for each data onto MNI152 atlas image
cmd2="tbss_2_reg -T"
echo $cmd2
eval $cmd2

## TBSS Step 3: Apply transform
cmd3="tbss_3_postreg -T"
echo $cmd3
eval $cmd3

## TBSS Step 4: Generate skeletonized data
cmd4="tbss_4_prestats 0.2"
echo $cmd4
eval $cmd4

EOF
fi

if [ $DATA == "Non_FA" ]; then
echo "Non FA"
cat >> ${sbatchDIR}/${runScript}.sh <<'EOF'

######## Create Non_FA data directory ########
indexDIR=$tbssDIR/$index
mkdir -p $indexDIR

######## Copy data to Non_FA directory ########
for i in ${!SESSIONS_CN[@]}; do
        session=${SESSIONS_CN[$i]}
        num=$(($i+100))
        echo "Collecting $index data of subject $session"
        rsync -ravzh -i $StudyFolder/DBSI_new/$session/${session}_${index}.nii.gz ${indexDIR}/CON_${num}_dtifit.nii.gz
done

for i in ${!SESSIONS_SCZ[@]}; do
        session=${SESSIONS_SCZ[$i]}
        num=$(($i+100))
        echo "Collecting $index data of subject $session"
        rsync -ravzh -i $StudyFolder/DBSI_new/$session/${session}_${index}.nii.gz ${indexDIR}/PAT_${num}_dtifit.nii.gz
done

## Run TBSS steps on Non FA data

cd $tbssDIR
echo "$tbssDIR"
cmd1="tbss_non_FA $index"
echo $cmd1
eval $cmd1

EOF

fi

sbatch ${sbatchDIR}/${sbatchScript}.sh
done
