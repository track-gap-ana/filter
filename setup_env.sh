# setting environment variables
HOME=$(pwd)
PYENV=$HOME/build/envs/tga

echo "Activating Python virtual environment..."
source $PYENV/bin/activate
export PYTHONPATH="build/envs/tga/lib/python3.11/site-packages:$(pwd)/src:$PYTHONPATH"
export PATH=$PATH:$HOME/bin:$HOME/bin/templates

