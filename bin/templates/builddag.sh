#!/bin/bash

OUT_DIR=$1
VERSION=$2
SIG_TYPE=$3

# environment params
export HOME=$HOME
export CURRENTDATE=`date +%d%m%y`
export ICETRAYENV=/home/vparrish/icecube/llp_ana/reco_studies/icetray/build/env-shell.sh
export PYTHONSCRIPT=/home/vparrish/icecube/llp_ana/reco_studies/icetray/src/online_filterscripts/resources/scripts/PFRaw_to_DST.py

# script used for condorVES
export CONDORSCRIPT=$(pwd)/bin/templates/DAGOneJobTemplate.submit
echo "CONDOR SCRIPT: $CONDORSCRIPT"


# define exepath to avoid condor incident
export EXEDIR=$(pwd)"/condor_exe_dirs/condor-$CURRENTDATE"

# define output and error directories
export OUTPUTDIR=$OUT_DIR/output/$VERSION/$CURRENTDATE/$SIG_TYPE/
export ERRORDIR=$OUT_DIR/error/$VERSION/$CURRENTDATE/$SIG_TYPE/
export LOGDIR=/scratch/vparrish/


# Ensure all directories exist
mkdir -p $EXEDIR
mkdir -p $OUTPUTDIR
mkdir -p $ERRORDIR

echo "EXE DIRECTORY: $EXEDIR"
echo "OUTPUT DIRECTORY: $OUTPUTDIR"
echo "LOG DIRECTORY: $LOGDIR"

# computing parameters
export NCPUS=1
export MEMORY=8GB
export DISK=2GB
export NGPUS=1


# Nominal submission variable definitions
sed -e 's#<pythonscript>#'$PYTHONSCRIPT'#g' \
    -e 's#<outputdir>#'$OUTPUTDIR'#g' \
    -e 's#<icetrayenv>#'$ICETRAYENV'#g' \
    -e 's#<logdir>#'$LOGDIR'#g' \
    -e 's#<errdir>#'$ERRORDIR'#g' \
    -e 's#<ncpus>#'$NCPUS'#g' \
    -e 's#<memory>#'$MEMORY'#g' \
    -e 's#<disk>#'$DISK'#g' \
    -e 's#<ngpus>#'$NGPUS'#g' \
    -e 's#<njobs>#'$NJOBS'#g' \
    -e 's#<currentdate>#'$CURRENTDATE'#g' \
    $CONDORSCRIPT > "$EXEDIR/DAGOneJob.submit"
