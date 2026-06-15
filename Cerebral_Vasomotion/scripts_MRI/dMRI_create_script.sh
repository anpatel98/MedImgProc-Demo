SESSIONS="USEI_1238_001_MRI USEI_1238_002_MRI USEI_1238_003_MRI USEI_1238_004_MRI USEI_1238_005_MRI USEI_1238_006_MRI USEI_1238_007_MRI USEI_1238_008_MRI USEI_1238_009_MRI USEI_1238_010_MRI"
#SESSIONS="USEI_1238_011_MRI USEI_1238_012_MRI USEI_1238_013_MRI USEI_1238_014_MRI USEI_1238_015_MRI USEI_1238_016_MRI USEI_1238_017_MRI USEI_1238_018_MRI USEI_1238_019_MRI USEI_1238_020_MRI"

StudyFolder="/scratch/$USER/USEI"
ProcessName="DiffusionPreproc"  #Shorthand text string to describe what we are doing
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
######## Walltime: 24 hours ########
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
ParamFile="${StudyFolder}/Mamah_sk_param.txt"
MappingFile="${StudyFolder}/Mamah_sk_Diffusion_mapping.txt"

# =-=-=-=-=-= GENERAL OPTIONS =-=-=-=-=-=
# -- key variables to set
Overwrite='yes'  # Value for --overwrite argument in import_dicom, create_session_info, and create_batch
OverwriteDmri='yes'  # Value for --overwrite argument in hcp_diffusion

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
  DmriFolderName=dMRI
  DmriFolder="${StudyFolder}/sessions/${Session}/${DmriFolderName}"
  mkdir -p "${DmriFolder}"
  rsync -av "${StudyFolder}/DICOM/${Session}/dMRI" "${DmriFolder}/inbox"

  ################ dicom2nii ################

  # import_dicom doesn't have a "merge" mode (this is actually a complicated issue).
  # It also doesn't have options to control the output directory/file name, and would
  # thus clash with existing outputs from structural preprocessing.
  # So, instead, we create a separate "DmriFolder" above (above), and separately call
  # 'sort_dicom' and 'dicom2niix`

  # Note: sort_dicom specifically looks for an 'inbox' folder, but don't include that 
  # as part of the --folder name itself.

  ${QUNEXCOMMAND} sort_dicom \
    --folder="${DmriFolder}"

  # Convert dicom data to NIFTI
  # Generates session.txt file for that session, describing the NIFTI for that session.
  # options -- extract image type, DwellTime, TR, PEDirection, EchoSpacing, and ReadoutDirection 
  #   from JSON sidecar files and add to session.txt file  
  # (03/16/2022) Change --options="addImageType:10|addJSONInfo:DwellTime,TR,PEDirection,ReadoutDirection" to 
  # --add_image_type & --add_json_info for the new version of qunex container (qunex_suite-0.93.2.sif)

  # NOTE: We do NOT include EchoSpacing as an extracted scan parameter because
  # dicom2niix returns that value in sec, but hcp_dwi_echospacing needs to be in msec (see below).
  # And, scan specific values (in the batch.txt file) take priority over parameters specified
  # in the call. So, we simply can't include EchoSpacing as an extracted scan-specific parameter.
  

  ${QUNEXCOMMAND} dicom2niix \
    --folder="${DmriFolder}" \
    --sessionid="${Session}" \
    --clean="${Overwrite}" \
    --unzip="yes" \
    --gzip="no" \
    --tool="dcm2niix" \
    --add_image_type=10 \
    --add_json_info="DwellTime:TR:PEDirection:ReadoutDirection"

  # Going forward, we'll make use of the target/sourcefile options, and output
  # to the "standard" location. Move session.txt to exist at that location,
  # and give it a unique name for the dMRI processing
  sessionTxtNew=${StudyFolder}/sessions/${Session}/session_${ProcessName}.txt
  mv ${DmriFolder}/session.txt ${sessionTxtNew}

  # But, we need to fix the hcp folder location (to match the default used for structural processing)
  BaseFolder=$(dirname ${DmriFolder})  # Remove ${DmriFolderName} from path
  sed -i "s|${DmriFolder}/hcp|${BaseFolder}/hcp|g" ${sessionTxtNew}

  ################ session_info ################
  # Generates session_hcp.txt for correct mapping to a folder structure supporting
  #   specific pipeline processing. Needs a mapping file.
  
  sessionHcpTxtNew=${StudyFolder}/sessions/${Session}/session_hcp_${ProcessName}.txt

  ${QUNEXCOMMAND} create_session_info \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --mapping="${MappingFile}" \
    --overwrite="${Overwrite}" \
    --sourcefile="${sessionTxtNew}" \
    --targetfile="${sessionHcpTxtNew}"


  ################ setup_hcp ################
  # Map images from session's nii folder to folder structure appropriate 
  # for HCP Pipelines. [Creates <session id>/hcp/unprocessed/...]

  ${QUNEXCOMMAND} setup_hcp \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --hcp_filename="userdefined" \
    --sourcefile="${sessionHcpTxtNew}"

  ################ create_batch ################
  # Prepare a batch file by specifying specific details via the ${ParamFile}
  # Joins the paramfile with session_hcp.txt

  SessionBatchFile="${StudyFolder}/processing/${Session}_${ProcessName}_batch.txt"

  ${QUNEXCOMMAND} create_batch \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${Session}" \
    --targetfile="${SessionBatchFile}" \
    --paramfile="${ParamFile}" \
    --overwrite="${Overwrite}" \
    --sourcefiles="${sessionHcpTxtNew}"
  
### END preparing data ###   

### BEGIN pipeline_specific ###

  ################ hcp_diffusion ################

  # Need a json file to define how the slices/MB-groups were acquired ("SliceTiming").
  # As of 0.91.11 container, QuNex doesn't propagate the jsons into the 
  # hcp/$Session/unprocessed/Diffusion folder, so need to find a dMRI json in the nii folder.
  # Note: We assume here, WITHOUT CHECKING, that all the scans of type 'DWI' listed in session_hcp.txt
  # were acquired with a consistent protocol (i.e., same SliceTiming) and thus are interchangeable.
  
  DWIscanNum=$(grep 'DWI:' ${sessionHcpTxtNew} | cut -d ':' -f 1 | head -n 1 | tr -d '[:space:]')
  json_file="${DmriFolder}/nii/${DWIscanNum}.json"
  echo "json_file=${json_file}"
  if [[ ! -e ${json_file} ]]; then
     echo "ERROR: File doesn't exist: ${json_file}" >&2
     exit -1
  fi
  echo "###### BEGIN, json contents ######"
  cat ${json_file}
  echo "###### END, json contents ######"
  echo 

  # Also, the hcp_dwi_echospacing input to hcp_Diffusion needs to be in msec.
  # But, the value for EchoSpacing in the session*.txt (if included) files
  # is expressed in sec, and as of the 0.91.11 container, is not converted to msec 
  # as part of passing to hcp_diffusion.
  # So, we need to explicitly provide that value, rather than relying on qunex to 
  # handle that automatically.
  # We'll get the value from the json that we've identified, since (per above) we did
  # not include EchoSpacing as an extracted scan parameter in batch.txt
  
  # Ideally, would use the json parser 'jq', but not available inside qunex, so we'll use
  # the following hack (which will potentially break if the json is formatted differently)
  echoSpacingSec=$(grep EffectiveEchoSpacing ${json_file} | awk '{print $2}' | cut -d ',' -f 1)
  echoSpacingMsec=$(echo "$echoSpacingSec * 1000" | bc -l)
  echo "EchoSpacing in msec: $echoSpacingMsec"

  # Use eddy_cuda9.1 (which is also the default)
  # Changed s2v_niter from 6 to 5 (12/21/2021)

  ${QUNEXCOMMAND} hcp_diffusion \
    --sessionsfolder="${StudyFolder}/sessions" \
    --sessions="${SessionBatchFile}" \
    --sessionids="${Session}" \
    --overwrite="${OverwriteDmri}" \
    --hcp_dwi_cudaversion="9.1" \
    --hcp_dwi_echospacing="$echoSpacingMsec" \
    --hcp_dwi_extraeddyarg="--niter=8|--fwhm=10,8,6,4,2,0,0,0|--nvoxhp=2000|--repol|--ol_type=both|--ol_nstd=5|--with_outliers|--mporder=16|--s2v_niter=5|--json=${json_file}|--estimate_move_by_susceptibility|--mbs_niter=15|--residuals|--initrand|--very_verbose"

### END pipeline_specific ###


}

main $@

EOF
chmod 755 ${sbatchDIR}/${qunexScript}.sh

sbatch ${sbatchDIR}/${sbatchScript}.sh
done
