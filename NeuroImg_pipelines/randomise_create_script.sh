#!/bin/bash

# "Author: Aakash Patel"
# "Email: aakash@wustl.edu"

RESULTS="FA AD RD cell_ratio_map fiber1_ratio_map fiber23_ratio_map fiber_axial_map fiber_radial_map fiber_ratio_map highhind_ratio_map hind_ratio_map lowhind_ratio_map"

StudyName="hcpep"
StudyFolder="/scratch/aakash/HCPEP"
ProcessName="randomise"  #Shorthand text string to describe what we are doing
tbssDIR=${StudyFolder}/TBSS
statsDIR="$tbssDIR/stats"

######## create directories for tbss analysis ########

sbatchDIR=${StudyFolder}/sbatch/randomise
slogDIR=${sbatchDIR}/logs
mkdir -p ${slogDIR}

for index in $RESULTS; do

sbatchScript="SBATCH_${index}_${ProcessName}"
jobName="run_${index}_${ProcessName}"

######## create the sbatch launching script for each analysis ########

echo $sbatchScript
cat > ${sbatchDIR}/${sbatchScript}.sh <<EOF
#!/bin/bash
######## Job Name: $jobName ########
#SBATCH -J $jobName
######## Job Output File: $jobName.oJOBID ########
#SBATCH -o ${slogDIR}/$jobName.o%j
######## Job Error File: $jobName.eJOBID #######
#SBATCH -e ${slogDIR}/$jobName.e%j
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
######## Memory per node: 48 GB ########
#SBATCH --mem=96GB
######## Walltime: 3 hours ########
#SBATCH -t 3:00:00

index="$index"
StudyName="$StudyName"
StudyFolder="$StudyFolder"
ProcessName="$ProcessName"
tbssDIR="$tbssDIR"
export statsDIR="$tbssDIR/stats"

EOF

cat >> ${sbatchDIR}/${sbatchScript}.sh <<'EOF'
module load fsl/6.0.5

cd $statsDIR

randomise_parallel \
        -i all_${index}_skeletonised \
        -o tbss_${StudyName}_${index} \
        -m mean_FA_skeleton_mask \
        -d design.mat \
        -t design.con \
        -n 5000 \
        --uncorrp \
        --T2
EOF

sbatch ${sbatchDIR}/${sbatchScript}.sh
done
