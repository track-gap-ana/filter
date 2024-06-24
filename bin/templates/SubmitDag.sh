#!/bin/sh
current_dir=$(pwd)  # Store the current directory
mv myJobs.dag $EXEDIR

echo "CALLING DAGMAN SERVICE:"
read -p "Do you want to submit the jobs? (y/n): " answer
if [[ $answer == "y" ]]; then
    # Assuming you want to remove -config or replace it with an actual config file path
    condor_submit_dag -force $EXEDIR/myJobs.dag > $EXEDIR/output.log 2>&1
elif [[ $answer == "n" ]]; then
    echo "Exiting without submitting jobs."
    exit 0
else
    echo "Invalid input. Exiting..."
    exit 1
fi

echo "Back to the original directory"
cd "$current_dir"  # Use the stored directory to return