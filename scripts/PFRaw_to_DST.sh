#!/bin/bash

# Check if the directory is provided as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIRECTORY=/data/user/axelpo/LLP-data/

# Check if the directory exists
if [ ! -d "$DIRECTORY" ]; then
    echo "Directory does not exist: $DIRECTORY"
    exit 1
fi

# Define the path to the GCD file
GCD_PATH="/data/user/axelpo/LLP-at-IceCube/dark-leptonic-scalar-simulation/resources/GeoCalibDetectorStatus_2021.Run135903.T00S1.Pass2_V1b_Snow211115.i3.gz"

# Define the output directory
OUTPUT_DIR="/home/vparrish/icecube/llp_ana/reco_studies/microNN_filter/outdir/new_muon_filter/post_filter/online_process"

# Ensure the output directory exists
mkdir -p "$OUTPUT_DIR"

# Function to process files
process_files() {
    for INPUT_FILE in "$1"/*; do
        # Check if the item is a file
        if [ -f "$INPUT_FILE" ]; then
            # Extract the base name for the output file
            BASENAME=$(basename -- "$INPUT_FILE")
            OUTPUT_FILE="${OUTPUT_DIR}/${BASENAME%.i3.gz}_online.i3.gz"

            # Run the Python script with the current file
            echo "Processing $INPUT_FILE..."
            online_filterscripts/resources/scripts/PFRaw_to_DST.py -i "$INPUT_FILE" -s -o "$OUTPUT_FILE" --gcd "$GCD_PATH"
            echo "Output generated: $OUTPUT_FILE"
        fi
    done
}
