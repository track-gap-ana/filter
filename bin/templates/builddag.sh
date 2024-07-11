#!/bin/bash
echo "I'm in builddag.sh"

OUT_DIR=$1
VERSION=$2
SIG_TYPE=$3
EXEDIR=$4
PROCESS=$5

# environment params
export HOME=$HOME
export EXDIR=$EXEDIR
export CURRENTDATE=`date +%d%m%y`

if [ "$PROCESS" == "online" ]; then
    export PYTHONSCRIPT=/home/vparrish/icecube/llp_ana/reco_studies/icetray/src/online_filterscripts/resources/scripts/PFRaw_to_DST.py
    export CONDORSCRIPT=$(pwd)/bin/templates/DAGOneJobTemplate_online.submit
else
    export PYTHONSCRIPT=/home/vparrish/icecube/llp_ana/reco_studies/icetray/src/offline_filterscripts/resources/scripts/filter_SDST.py
    export CONDORSCRIPT=$(pwd)/bin/templates/DAGOneJobTemplate_offline.submit
fi

# script used for condorVES
echo "CONDOR SCRIPT: $CONDORSCRIPT"

# define output and error directories
export OUTPUTDIR=$OUT_DIR/output/$VERSION/$CURRENTDATE/$SIG_TYPE/
export LOGDIR=$OUT_DIR/output/$VERSION/$CURRENTDATE/$SIG_TYPE/out/
export ERRORDIR=$OUT_DIR/error/$VERSION/$CURRENTDATE/$SIG_TYPE/


# Ensure all directories exist
mkdir -p $OUTPUTDIR
mkdir -p $ERRORDIR
mkdir -p $LOGDIR

echo "OUTPUT DIRECTORY: $OUTPUTDIR"
echo "ERROR DIRECTORY: $ERRORDIR"
echo "EXEDIR: $EXEDIR"

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
    "$CONDORSCRIPT" > "$EXDIR/DAGOneJob.submit"
