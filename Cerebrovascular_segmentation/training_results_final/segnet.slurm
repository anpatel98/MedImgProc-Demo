#!/bin/bash
#SBATCH --error=error1.err
#SBATCH --output=output1.out
#SBATCH --job-name=UN
#SBATCH --partition=scavenger
#SBATCH --qos=scavenger
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --constraint=P100
##SBATCH --exclusive
#SBATCH --mem=48000
#SBATCH --mail-user=anpatel6@buffalo.edu
#SBATCH --mail-type=ALL
#SBATCH --time=72:00:00

echo "SLURM_JOBID="$SLURM_JOBID
echo "SLURM_JOB_NODELIST"=$SLURM_JOB_NODELIST
echo "SLURM_NNODES"=$SLURM_NNODES
echo "SLURMTMPDIR="$SLURMTMPDIR
echo "workingdirectory="$SLURM_SUBMIT_DIR

module load tensorflow/1.12.0-gpu-py36
module load keras

echo "python Extract_patches_new.py"

echo "Patch Extraction Completed"

echo "python Unet.py"

python Predict_unet_overlap_50.py

echo "all done!!!"
