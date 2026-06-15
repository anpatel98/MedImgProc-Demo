SESSIONS="USEI_1238_001_MRI USEI_1238_002_MRI USEI_1238_003_MRI USEI_1238_004_MRI USEI_1238_005_MRI USEI_1238_006_MRI USEI_1238_007_MRI USEI_1238_008_MRI USEI_1238_009_MRI USEI_1238_010_MRI"
#SESSIONS="USEI_1238_011_MRI USEI_1238_012_MRI USEI_1238_013_MRI USEI_1238_014_MRI USEI_1238_015_MRI USEI_1238_016_MRI USEI_1238_017_MRI USEI_1238_018_MRI USEI_1238_019_MRI USEI_1238_020_MRI"

StudyFolder="/scratch/$USER/USEI"
ProcessName="Diffusion_bedp"  #Shorthand text string to describe what we are doing
sbatchDIR=${StudyFolder}/sbatch
slogDIR=${sbatchDIR}/logs
mkdir -p ${slogDIR}

for Session in $SESSIONS; do

sbatchScript="SBATCH_${Session}_${ProcessName}"
qunexScript="run_qunex_${Session}_${ProcessName}"


######## create the sbatch launching script for each session ########

echo $sbatchScript
cat > ${sbatchDIR}/${sbatchScript}.sh <<EOF
#!/bin/bash
######## Job Name: $qunexScript ########
#SBATCH -J $qunexScript
######## Job Output File: $qunexScript.oJOBID ########
#SBATCH -o ${slogDIR}/$qunexScript.o%j
######## Job Error File: $qunexScript.eJOBID #######
#SBATCH -e ${slogDIR}/$qunexScript.e%j
######## Number of nodes: 1 ########
#SBATCH -N 1
######## Number of tasks: 1 ########
#SBATCH -n 1
######## Request a V100 or V100S GPU ########
#SBATCH --gres=gpu:1,vmem:32gb:1
######## Memory per node: 10 GB ########
#SBATCH --mem=10GB
######## Walltime: HH:MM:SS ########
#SBATCH -t 1:30:00

Session="$Session"
StudyFolder="$StudyFolder"
qunexScript="$qunexScript"
sbatchDIR="$StudyFolder/sbatch"
EOF

# Use quotes around EOF to echo text as literal, rather than shell evaluating the variables
cat >> ${sbatchDIR}/${sbatchScript}.sh <<'EOF'

module load singularity/3.7.0 cuda/9.1

Container=${StudyFolder}/qunex_suite-0.93.2.sif
runScript=${sbatchDIR}/${qunexScript}.sh

XTMPDIR=${StudyFolder}/tmp
mkdir -p $XTMPDIR

singularity exec --cleanenv \
    --nv \
    --bind $StudyFolder \
    --bind ${XTMPDIR}:/tmp \
    $Container $runScript
    
EOF


######## create the associated script to be run in QuNex for each session ########

echo $qunexScript

cat > ${sbatchDIR}/${qunexScript}.sh <<EOF
Session="$Session"
StudyFolder="$StudyFolder"
ProcessName="$ProcessName"

EOF

cat >> ${sbatchDIR}/${qunexScript}.sh <<'EOF'
# -- Define script name
scriptName=$(basename ${0})
scriptPath=$(dirname ${0})

# -- Templates --
ParamFile="${StudyFolder}/Mamah_sk_param.txt"

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
# -- key variables to set
OverwriteDmri='yes'  # Value for --overwrite argument in bedpostx

export StudyFolder

# only if overriding the default setting of /opt/HCP/HCPpipelines
#export con_HCPPIPEDIR="/opt/HCP/HCPpipelines"

TimeStamp=`date +%Y-%m-%d-%H-%M-%S`
mkdir -p ${StudyFolder}/processing/logs/envStatus &> /dev/null
LogFile="$StudyFolder/processing/logs/envStatus/${scriptName}_${TimeStamp}.log"

# Set up QuNex environment, and write to log file of this script
source /opt/qunex/env/qunex_environment.sh  >> ${LogFile}
source /opt/qunex/env/qunex_env_status.sh --envstatus >> ${LogFile}

# -- Report options
echo "-- ${scriptName}: Params - Start --"					  2>&1 | tee -a ${LogFile}
echo ""	 		                                                          2>&1 | tee -a ${LogFile}
echo "   QUNEX Study          : $StudyFolder"                                     2>&1 | tee -a ${LogFile}
echo "   QUNEX sessions folder: ${StudyFolder}/sessions"                          2>&1 | tee -a ${LogFile}
echo "   Overwrite dMRI?      : $OverwriteDmri"                                   2>&1 | tee -a ${LogFile}
echo "   Sessions to run      : $Session"                                         2>&1 | tee -a ${LogFile}
echo "   Log file output      : $LogFile"                                         2>&1 | tee -a ${LogFile}
echo ""                                                                           2>&1 | tee -a ${LogFile}
echo "-- ${scriptName}: Params - End --" 					  2>&1 | tee -a ${LogFile}
echo ""                                                                           2>&1 | tee -a ${LogFile}
echo "" 									  2>&1 | tee -a ${LogFile}

# -- Define QUNEX command
QUNEXCOMMAND="qunex"

log_Msg()
{
	local msg="$*"
	local dateTime
	dateTime=$(date)
	local toolname

	if [ -z "${log_toolName}" ]; then
		toolname=$(basename ${0})
	else
		toolname="${log_toolName}"
	fi

	echo ${dateTime} "-" ${toolname} "-" "${msg}"
}

main() {

ProcessingInfoDir=${StudyFolder}/ProcessingInfo
mkdir -p ${ProcessingInfoDir}
info_file="${ProcessingInfoDir}/${Session}.${ProcessName}.info"
echo $(date) > ${info_file}
log_Msg "Node: $(hostname)" >> ${info_file}

################ create_study ################
# Create QuNex study folder structure
${QUNEXCOMMAND} create_study --studyfolder="${StudyFolder}"
cd ${StudyFolder}/sessions

sleep 2

### BEGIN pipeline_specific ###

  ${QUNEXCOMMAND} dwi_bedpostx_gpu\
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --overwrite="${OverwriteDmri}" \
    --fibers='3'\
    --burnin='3000'\
    --model='3'

### END pipeline_specific ###


}

main $@

EOF
#chmod 755 ${sbatchDIR}/${qunexScript}.sh

#sbatch ${sbatchDIR}/${sbatchScript}.sh
done
