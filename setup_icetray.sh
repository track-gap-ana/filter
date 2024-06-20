# /bin/bash

# setting environment variables
HOME=$(pwd)

if [ ! -d "build" ]; then
    echo "Creating build directory..."
    mkdir build
    cd build
    echo "Creating envs directory..."
    mkdir envs
    cd envs
    echo "Creating Python virtual environment..."
    python3 -m venv tga
    cd $HOME
fi
if [ ! -d "outdir" ]; then
    echo "Creating outdir directory..."
    mkdir outdir
fi

PYENV=$HOME/build/envs/tga
echo "Activating Python virtual environment..."
source $PYENV/bin/activate

# install simweights if not installed
if ! python -c "import simweights" >/dev/null 2>&1; then
    echo "Installing simweights..."
    cd $PYENV
    pip install --upgrade pip
    pip install simweights
fi
# Check HDF5 version
cd $HOME/build/envs/tga/lib/python3.11/site-packages
HDF5_VERSION=$(python -c 'import h5py;print(h5py.version.version)')
REQUIRED_HDF5_VERSION="3.11.0"
if [[ "$HDF5_VERSION" != "$REQUIRED_HDF5_VERSION" ]]; then
    echo "HDF5 version is not $REQUIRED_HDF5_VERSION. Uninstalling old version and installing HDF5 version $REQUIRED_HDF5_VERSION..."
    # Install the correct version of HDF5
    HDF5_DIR=$SROOT/spack/opt/spack/linux-centos7-x86_64_v2/gcc-13.1.0/hdf5-1.14.0-4p2djysy6f7vful3egmycsguijjddkah pip install --no-binary=h5py h5py -U
fi
cd $HOME

eval $(/cvmfs/icecube.opensciencegrid.org/py3-v4.3.0/setup.sh)

read -p "Do you want to load the muon filter icetray? (y/n): " choice
if [ "$choice" == "y" ]; then
    /home/vparrish/icecube/llp_ana/reco_studies/icetray/build/env-shell.sh
else
    /cvmfs/icecube.opensciencegrid.org/py3-v4.3.0/RHEL_7_x86_64/metaprojects/icetray/v1.8.2/env-shell.sh
fi

