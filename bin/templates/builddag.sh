#!/bin/bash
echo "I'm in builddag.sh"

OUTPUTDIR=$1
LOGDIR=$2
ERRORDIR=$3
EXEDIR=$4
PROCESS=$5


# environment params
export HOME=$HOME
export EXDIR=$EXEDIR
export CONDORSCRIPT=$(pwd)/bin/templates/DAGOneJobTemplate.submit

if [ "$PROCESS" == "online" ]; then
    export PYTHONSCRIPT=/home/vparrish/icecube/llp_ana/reco_studies/icetray/src/online_filterscripts/resources/scripts/PFRaw_to_DST.py
    export ARGUMENTS="-s"
    
elif
    export PYTHONSCRIPT=/home/vparrish/icecube/llp_ana/reco_studies/icetray/src/offline_filterscripts/resources/scripts/filter_SDST.py
    export ARGUMENTS=""
else
    export PYTHONSCRIPT=/home/vparrish/icecube/llp_ana/reco_studies/microNN_filter/bin/trackgapana.py
    export ARGUMENTS=$6
fi


# script used for condorVES
echo "CONDOR SCRIPT: $CONDORSCRIPT"

# computing parameters
export NCPUS=1
export MEMORY=8GB
export DISK=2GB
export NGPUS=1


# Nominal submission variable definitions
sed -e 's#<pythonscript>#'$PYTHONSCRIPT'#g' \
    -e 's#<arguments>#'$ARGUMENTS'#g' \
    -e 's#<outputdir>#'$OUTPUTDIR'#g' \
    -e 's#<icetrayenv>#'$ICETRAYENV'#g' \
    -e 's#<logdir>#'$LOGDIR'#g' \
    -e 's#<errdir>#'$ERRORDIR'#g' \
    -e 's#<ncpus>#'$NCPUS'#g' \
    -e 's#<memory>#'$MEMORY'#g' \
    -e 's#<disk>#'$DISK'#g' \
    -e 's#<ngpus>#'$NGPUS'#g' \
    -e 's#<njobs>#'$NJOBS'#g' \
    "$CONDORSCRIPT" > "$EXDIR/DAGOneJob.submit"
