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
# install h5py since the version that comes with the setup below is not compatible with the version of HDF5 used for writing 
echo "HDF5 version is less than 2.10.0. Uninstalling old version and installing HDF5 version 2.10.0"
# Uninstall current version of HDF5
#pip uninstall -y h5py
# Install the correct version of HDF5
#HDF5_DIR=/cvmfs/icecube.opeinnsciencegrid.org/py3-v4.1.1/RHEL_7_x86_64/spack/opt/spack/linux-centos7-x86_64/gcc-9.2.0spack/hdf5-1.10.5-tzqwgit6tpz6facq4b3kuuudvcygayc4 pip install --no-binary=h5py h5py==2.10.0
cd $HOME

eval $(/cvmfs/icecube.opensciencegrid.org/py3-v4.3.0/setup.sh)
/cvmfs/icecube.opensciencegrid.org/py3-v4.3.0/RHEL_7_x86_64/metaprojects/icetray/v1.8.2/env-shell.sh 
