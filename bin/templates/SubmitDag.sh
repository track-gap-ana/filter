#!/bin/bash
echo "I'm in SubmitDag.sh"
# define exepath to avoid condor incident
export CURRENTDATE=`date +%d%m%y`
export EXEDIR=$1
echo "EXECUTION DIRECTORY: $EXEDIR"
current_dir=$(pwd)  # Store the current directory

# Ensure all directories exist
echo "Top 2 lines of myJobs.dag:"
if [[ -f "$EXEDIR/myJobs.dag" ]]; then
    echo "myJobs.dag exists."
    cat "$EXEDIR/myJobs.dag" | head -n 2
else
    echo "myJobs.dag does not exist."
    exit 1
fi

if [[ -f "$EXEDIR/DAGOneJob.submit" ]]; then
    echo "DAGOneJob.submit exists."
else
    echo "DAGOneJob.submit does not exist."
    exit 1
fi

echo "CALLING DAGMAN SERVICE:"
read -p "Do you want to submit the jobs? (y/n): " answer
if [[ $answer == "y" ]]; then
    # Assuming you want to remove -config or replace it with an actual config file path
    condor_submit_dag "$EXEDIR/myJobs.dag"
elif [[ $answer == "n" ]]; then
    echo "Exiting without submitting jobs."
    exit 0
else
    echo "Invalid input. Exiting..."
    exit 1
fi

echo "Back to the original directory"
cd "$current_dir"  # Use the stored directory to return