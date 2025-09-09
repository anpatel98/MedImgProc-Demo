#SESSIONS="sk4001 sk4002 sk4002-2 sk4003 sk5002 sk5003 sk5005 sk5006 sk6001 sk6003 sk6004 sk6005"
#SESSIONS="sk4004 sk4005 sk4006 sk4007 sk4008 sk4009 sk4010 sk4011 sk4012 sk4015 sk4015-2 sk4016 sk4017 sk4018 sk4019 sk4020 sk4022 sk4023 sk4024 sk4025 sk4026 sk4027 sk4027-2 sk4029 sk4030 sk4031 sk4032 sk4034 sk4035 sk4036 sk4037 sk4038"
#SESSIONS="sk5007 sk5009 sk5011 sk5012 sk5013 sk5014 sk5016 sk5018 sk5019 sk5021 sk5022 sk5023 sk5024 sk5027 sk5028 sk5030 sk5032 sk5033 sk5034 sk5036 sk5037 sk5038 sk5041 sk5043 sk5044 sk5045 sk5047 sk5048 sk5049 sk5050"
#SESSIONS="sk6008 sk6010 sk6011 sk6011-2 sk6012 sk6016 sk6017 sk6017-2 sk6018 sk6019 sk6020 sk6020-2 sk6022 sk6025 sk6026 sk6027 sk6028 sk6029 sk6030 sk6033 sk6035 sk6039 sk6045"
#SESSIONS="sk6040 sk6041 sk6046"
#SESSIONS="sk4028 sk5031"
SESSIONS="sk6030"
StudyFolder="/scratch/$USER/QuNex_pr"
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
######## Walltime: 1 hour 30 mins########
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
ParamFile="${StudyFolder}/prisma_param.txt"

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
chmod 755 ${sbatchDIR}/${qunexScript}.sh

#sbatch ${sbatchDIR}/${sbatchScript}.sh
done
