SESSIONS="USEI_1238_001_MRI USEI_1238_002_MRI USEI_1238_003_MRI USEI_1238_004_MRI USEI_1238_005_MRI USEI_1238_006_MRI USEI_1238_007_MRI USEI_1238_008_MRI USEI_1238_009_MRI USEI_1238_010_MRI"
#SESSIONS="USEI_1238_011_MRI USEI_1238_012_MRI USEI_1238_013_MRI USEI_1238_014_MRI USEI_1238_015_MRI USEI_1238_016_MRI USEI_1238_017_MRI USEI_1238_018_MRI USEI_1238_019_MRI USEI_1238_020_MRI"

StudyFolder="/scratch/$USER/USEI"
ProcessName="Structural"  #Shorthand text string to describe what we are doing
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
######## Memory per node: 50 GB ########
#SBATCH --mem=50GB
######## Walltime: HH:MM:SS ########
#SBATCH -t 24:00:00

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
ParamFile="${StudyFolder}/ProNET_pr_param.txt"
MappingFile="${StudyFolder}/ProNET_pr_Structural_mapping.txt"

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
# -- key variables to set
Overwrite='yes'  # Value for --overwrite argument in import_dicom, create_session_info, and create_batch

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
echo "   Overwrite?           : $Overwrite"                                       2>&1 | tee -a ${LogFile}
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

### BEGIN preparing data ###

  ##### Copy DICOMs #####
  SessionInbox=${StudyFolder}/sessions/${Session}/inbox/MR
  mkdir -p "${SessionInbox}"
  rsync -av "${StudyFolder}/sessions/${Session}/scans" "${StudyFolder}/sessions/${Session}/inbox"

  ################ dicom2nii ################
  # Convert dicom data to NIFTI
  # Generates session.txt file for that session, describing the NIFTI for that session.
  # check=any -- continue if any packages are ready to process; report error otherwise
  # options -- extract image type, DwellTime, TR, PEDirection, EchoSpacing, and ReadoutDirection 
  #   from JSON sidecar files and add to session.txt file  

  ${QUNEXCOMMAND} import_dicom \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --masterinbox="none" \
    --tool=dcm2niix \
    --check="any" \
    --unzip="yes" \
    --gzip="no" \
    --overwrite="${Overwrite}" \
    --add_json_info="DwellTime:TR:PEDirection:EchoSpacing:RepetitionTime:ReadoutDirection"
    
  ################ session_info ################
  # Generates session_hcp.txt for correct mapping to a folder structure supporting
  #   specific pipeline processing. Needs a mapping file.
  # Here, we choose the non-norm T1w and T2w to become the T1w and T2w inputs
  # used in the HCP Pipeline.
  
  ${QUNEXCOMMAND} create_session_info \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --mapping="${MappingFile}" \
    --overwrite="${Overwrite}"
## Following locations for source/target files are same as the defaults
#    --sourcefile="${StudyFolder}/sessions/${Session}/session.txt" \
#    --targetfile="${StudyFolder}/sessions/${Session}/session_hcp.txt"

  ################ setup_hcp ################
  # Map images from session's nii folder to folder structure appropriate 
  # for HCP Pipelines. [Creates <session id>/hcp/unprocessed/...]

  ${QUNEXCOMMAND} setup_hcp \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --hcp_filename="userdefined"

  ################ create_batch ################
  # Prepare a batch file by specifying specific details via the ${ParamFile}
  # Joins the paramfile with session_hcp.txt

  SessionBatchFile="${StudyFolder}/processing/${Session}_batch.txt"

  ${QUNEXCOMMAND} create_batch \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --targetfile="${SessionBatchFile}" \
    --paramfile="${ParamFile}" \
    --overwrite="${Overwrite}"
  
### END preparing data ###   

### BEGIN pipeline_specific ###

  ################ prefreesurfer ################
  ${QUNEXCOMMAND} hcp_pre_freesurfer \
    --sessionsfolder="${StudyFolder}/sessions"  \
    --sessions="${SessionBatchFile}" \
    --sessionids="${Session}" \
    --overwrite="${Overwrite}"

  ################ freesurfer ################

  ## Hack for insidious bug that appears to involve an interaction of some sort
  ## between Singularity, the tcsh shell (used by recon-all), and perhaps BeeGFS as well,
  ## which results in the mounted (--bind) $StudyFolder somehow getting mapped to $HOME
  ## (as revealed by $PWD and the directory stack), which then because of the manner in 
  ## which recon-all uses pushd/popd, otherwise results in a "No such file or directory" problem.
  unset HOME

  ${QUNEXCOMMAND} hcp_freesurfer \
    --sessionsfolder="${StudyFolder}/sessions"  \
    --sessions="${SessionBatchFile}" \
    --sessionids="${Session}" \
    --overwrite="${Overwrite}"

  ################ postfreesurfer ################

#  ${QUNEXCOMMAND} hcp_post_freesurfer \
#    --sessionsfolder="${StudyFolder}/sessions"  \
#    --sessions="${SessionBatchFile}" \
#    --sessionids="${Session}" \
#    --overwrite="${Overwrite}"

### END pipeline_specific ###


}

main $@

EOF
#chmod 755 ${sbatchDIR}/${qunexScript}.sh

#sbatch ${sbatchDIR}/${sbatchScript}.sh
done
