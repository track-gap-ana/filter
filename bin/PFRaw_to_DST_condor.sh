#!/bin/bash
# simulation parameters
export NJOBS=1
# environment params
export HOME=$HOME
export VENV="$HOME/build/envs/tga/bin/activate"
export ICETRAYENV=/home/vparrish/icecube/llp_ana/reco_studies/icetray/build/env-shell.sh

# computing parameters
export NCPUS=1
export MEMORY=8GB
export DISK=2GB
export NGPUS=1

# script used for condorVES
export CONDORSCRIPT=$(pwd)/bin/templates/full_online.sub
export JOBFILETEMPLATE=$(pwd)/bin/templates/job_online.sh
echo "CONDOR SCRIPT: $CONDORSCRIPT"
echo "JOB FILE TEMPLATE: $JOBFILETEMPLATE"
export CURRENTDATE=`date +%d%m%y`

#create exepath to avoid condor incident
export EXEDIR=$(pwd)"/condor_exe_dirs/condor-$CURRENTDATE"

# import from python wrapper
INPUTFILE=$1
VERSION=$2
GCD_FILE=$3
SIG_TYPE=$4
OUT_DIR=$5

# job file
export PYTHONSCRIPT=/home/vparrish/icecube/llp_ana/reco_studies/icetray/src/online_filterscripts/resources/scripts/PFRaw_to_DST.py
export OUTPUTDIR=$OUT_DIR/output/$VERSION/$CURRENTDATE/$SIG_TYPE/
export ERRORDIR=$OUT_DIR/error/$VERSION/$CURRENTDATE/$SIG_TYPE/
export LOGDIR=/scratch/vparrish/

export BASENAME=$(basename $INPUTFILE .i3.gz)

# Ensure all directories exist
mkdir -p $EXEDIR
mkdir -p $OUTPUTDIR
mkdir -p $ERRORDIR

echo "EXE DIRECTORY: $EXEDIR"
echo "OUTPUT DIRECTORY: $OUTPUTDIR"
echo "LOG DIRECTORY: $LOGDIR"


export BASENAME="${VERSION}_online_preprocess_${BASENAME}"

export GCDFILE=$GCD_FILE

# Transform condor script
sed -e 's#<pythonscript>#'$PYTHONSCRIPT'#g' \
    -e 's#<outputdir>#'$OUTPUTDIR'#g' \
    -e 's#<basename>#'$BASENAME'#g' \
    -e 's#<inputfile>#'$INPUTFILE'#g' \
    -e 's#<gcdfile>#'$GCDFILE'#g' \
    -e 's#<logdir>#'$LOGDIR'#g' \
    -e 's#<errdir>#'$ERRORDIR'#g' \
    -e 's#<ncpus>#'$NCPUS'#g' \
    -e 's#<memory>#'$MEMORY'#g' \
    -e 's#<disk>#'$DISK'#g' \
    -e 's#<ngpus>#'$NGPUS'#g' \
    -e 's#<njobs>#'$NJOBS'#g' \
    -e 's#<currentdate>#'$CURRENTDATE'#g' \
    $CONDORSCRIPT > "$EXEDIR/condor.submit"
    # copy example of condor file to log directory
    cp "$EXEDIR/condor.submit" "$LOGDIR/condor_example.submit"

# transform job script
sed -e 's#<venv>#'$VENV'#g' \
    -e 's#<icetrayenv>#'$ICETRAYENV'#g' \
    $JOBFILETEMPLATE > "$EXEDIR/job.sh"
    # copy example of run file to log directory
    cp "$EXEDIR/job.sh" "$LOGDIR/job_example.sh"

#call condor script
echo "CALLING CONDOR SERVICE:"
cd $EXEDIR

# Submit the job to Condor
# condor_submit condor.submit

#back to original directory
echo "back to the original directory"
cd -