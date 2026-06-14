SESSIONS_CN=("BM60731" "BM99192" "CM02821" "IR02516" "LA07315" "LA08975" "ME00772" "ME06126" "ME10086" "ME14898" "ME19787" "ME31169" "ME40663" "ME78581" "ME89055" "MT01504" "NC00191" "NL00927" "OR00697" "PA00272" "PA01921" "PI01355" "SG18044" "SG60081" "SG97600" "TE00646" "YA00926" "YA06869" "YA08106")
SESSIONS_CHR=("BI02450" "BM73097" "CM02398" "IR00124" "IR00491" "IR01451" "IR01762" "IR05485" "IR08259" "IR08615" "IR09281" "LA00145" "LA00834" "LA04513" "LA05539" "LA10304" "LA12291" "LA14055" "MA06340" "MA06451" "MA08615" "ME03013" "ME04106" "ME04934" "ME04962" "ME05411" "ME11046" "ME12189" "ME20134" "ME20328" "ME20845" "ME21588" "ME21922" "ME25689" "ME25712" "ME27132" "ME31331" "ME33634" "ME33795" "ME35971" "ME48643" "ME50511" "ME53985" "ME56454" "ME58135" "ME67495" "ME67990" "ME73814" "ME74779" "ME77159" "ME79913" "ME81520" "ME98165" "MT00499" "MT05499" "MT07364" "MT08124" "MT09245" "MT12595" "MT13133" "MT15919" "NC02111" "NC03026" "NC03204" "NC04870" "NC10194" "NC11776" "NC12958" "NC17136" "NC17619" "NL01115" "NL06371" "NL09062" "NL09167" "NL10958" "NN01442" "NN04333" "NN04555" "NN05521" "OR02023" "OR03988" "OR06829" "PA00705" "PA01260" "PA01787" "PA01909" "PA03218" "PA06165" "PA07319" "PA08957" "PI01155" "PI03042" "PI08131" "PI08769" "PI08981" "PI10215" "PI10704" "SD03495" "SD05710" "SD06897" "SF03788" "SF05231" "SF10428" "SF10462" "SF12054" "SF14052" "SI00132" "SI00726" "SI03540" "SI04099" "SI07530" "TE00307" "TE04070" "TE06973" "TE13580" "TE15483" "WU01590" "WU04908" "WU06851" "WU08865" "YA03473" "YA04611" "YA05293" "YA09994" "YA11278" "YA13632" "YA16301")

RESULTS="cell_ratio_map fiber12_axial_map fiber12_radial_map fiber12_ratio_map fiber1_axial_map fiber1_radial_map fiber1_ratio_map fiber23_axial_map fiber23_radial_map fiber23_ratio_map fiber2_axial_map fiber2_radial_map fiber2_ratio_map fiber3_axial_map fiber3_radial_map fiber3_ratio_map fiber_axial_map fiber_radial_map fiber_ratio_map highhind_ratio_map hind_ratio_map lowhind_ratio_map"
#RESULTS="FA"

StudyFolder="/scratch/$USER/ProNET"
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
######## Walltime: HH:MM:SS ########
#SBATCH -t 7:00:00

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
SESSIONS_CHR=(${SESSIONS_CHR[@]})
index="$index"
StudyFolder="$StudyFolder"
ProcessName="$ProcessName"
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
	rsync -ravzh -i $StudyFolder/dMRI/${session}*/${session}*_dtifit_${index}.nii.gz ${tbssDIR}/CON_${num}_dtifit.nii.gz
done

for i in ${!SESSIONS_CHR[@]}; do
        session=${SESSIONS_CHR[$i]}
        num=$(($i+100))
	echo "$num"
        echo "Collecting $index data of subject $session"
        rsync -ravzh -i $StudyFolder/dMRI/${session}*/${session}*_dtifit_${index}.nii.gz ${tbssDIR}/PAT_${num}_dtifit.nii.gz
done

## Run TBSS steps on DTI generated data

cd $tbssDIR

## TBSS Step 1: Set up data folder structure for subsequent analysis
cmd1="tbss_1_preproc *.nii.gz"
echo $cmd1
eval $cmd1

## TBSS Step 2:Calculate transforms for each data onto MNI152 standard image
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

######## Copy $index data to Non_FA directory ########
for i in ${!SESSIONS_CN[@]}; do
        session=${SESSIONS_CN[$i]}
        num=$(($i+100))
        echo "Collecting $index data of subject $session"
        rsync -ravzh -i $StudyFolder/DBSI_new/${session}*/${session}*_${index}.nii.gz ${indexDIR}/CON_${num}_dtifit.nii.gz
done

for i in ${!SESSIONS_CHR[@]}; do
        session=${SESSIONS_CHR[$i]}
        num=$(($i+100))
        echo "Collecting $index data of subject $session"
        rsync -ravzh -i $StudyFolder/DBSI_new/${session}*/${session}*_${index}.nii.gz ${indexDIR}/PAT_${num}_dtifit.nii.gz
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
